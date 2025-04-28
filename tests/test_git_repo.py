import os
from gitag.config import MergeStrategy
import subprocess
import pytest
from gitag.git_repo import GitRepo
from unittest import mock


def test_get_latest_tag_mock():
    with mock.patch("subprocess.run") as mocked:
        mocked.side_effect = [
            mock.Mock(returncode=0),  # fetch
            mock.Mock(returncode=0, stdout="v1.2.3\n")
        ]
        repo = GitRepo(debug=True)
        assert repo.get_latest_tag() == "v1.2.3"


def test_get_commit_messages_mock():
    with mock.patch("subprocess.run") as mocked:
        mocked.return_value = mock.Mock(stdout="fix: bug\nfeat: new", returncode=0)
        repo = GitRepo(debug=True)
        commits = repo.get_commit_messages("v1.0.0")
        assert commits == ["fix: bug", "feat: new"]


def test_get_commit_messages_non_merge_commit():
    with mock.patch("subprocess.run") as mocked:
        # Simuliere: HEAD ist kein Merge (nur 2 Einträge in rev-list)
        mocked.side_effect = [
            mock.Mock(stdout="abc123 def456\n"),  # rev-list
            mock.Mock(stdout="fix: bug\nfeat: new", returncode=0),
        ]

        repo = GitRepo(debug=True)
        commits = repo.get_commit_messages("v1.0.0")
        cmd = mocked.call_args_list[1][0][0]
        assert any("v1.0.0..HEAD" in arg for arg in cmd)
        assert commits == ["fix: bug", "feat: new"]


def test_get_commit_messages_merge_commit():
    with mock.patch("subprocess.run") as mocked:
        # Simuliere Merge-Commit HEAD
        mocked.side_effect = [
            mock.Mock(stdout="abc123 def456 ghi789\n"),  # rev-list: merge commit
            mock.Mock(stdout="feat: merge commit!", returncode=0),
        ]

        repo = GitRepo(debug=True, merge_strategy=MergeStrategy.MERGE_ONLY)
        commits = repo.get_commit_messages(since_tag="v1.0.0")

        # Prüfe, ob parent1..parent2 verwendet wurde
        cmd = mocked.call_args_list[1][0][0]
        assert "def456..ghi789" in cmd[-1]
        assert commits == ["feat: merge commit!"]


def test_get_commit_messages_no_merges_flag():
    with mock.patch("subprocess.run") as mocked:
        # Simulate a non-merge HEAD
        mocked.side_effect = [
            mock.Mock(stdout="abc123 def456\n"),  # rev-list (2 parts)
            mock.Mock(stdout="fix: bug\n", returncode=0),
        ]

        repo = GitRepo(debug=True, include_merges=False)
        commits = repo.get_commit_messages("v1.0.0")

        log_call = mocked.call_args_list[1][0][0]
        assert "--no-merges" in log_call
        assert commits == ["fix: bug"]


def test_merge_strategy_always():
    with mock.patch("subprocess.run") as mocked:
        mocked.return_value = mock.Mock(stdout="fix: always strategy", returncode=0)
        repo = GitRepo(debug=True, merge_strategy=MergeStrategy.ALWAYS)
        commits = repo.get_commit_messages("v1.0.0")
        cmd = mocked.call_args_list[0][0][0]
        assert "v1.0.0..HEAD" in cmd[-1]
        assert commits == ["fix: always strategy"]


def test_merge_strategy_merge_only_merge_commit():
    with mock.patch("subprocess.run") as mocked:
        # HEAD is merge
        mocked.side_effect = [
            mock.Mock(stdout="abc def ghi\n"),  # rev-list output: merge commit
            mock.Mock(stdout="fix: merge_only", returncode=0),
        ]
        repo = GitRepo(debug=True, merge_strategy=MergeStrategy.MERGE_ONLY)
        commits = repo.get_commit_messages("v1.0.0")
        cmd = mocked.call_args_list[1][0][0]
        assert "def..ghi" in cmd[-1]
        assert commits == ["fix: merge_only"]


def test_merge_strategy_merge_only_not_merge_commit():
    with mock.patch("subprocess.run") as mocked:
        # HEAD is NOT merge
        mocked.side_effect = [
            mock.Mock(stdout="abc def\n"),  # rev-list: no merge
            mock.Mock(stdout="fix: fallback", returncode=0),
        ]
        repo = GitRepo(debug=True, merge_strategy=MergeStrategy.MERGE_ONLY)
        commits = repo.get_commit_messages("v1.0.0")
        cmd = mocked.call_args_list[1][0][0]
        assert "v1.0.0..HEAD" in cmd[-1]
        assert commits == ["fix: fallback"]


@pytest.fixture
def fresh_git_repo(tmp_path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=repo_path, check=True)
    old_cwd = os.getcwd()
    os.chdir(repo_path)
    yield repo_path
    os.chdir(old_cwd)


def test_tag_creation_and_existence(fresh_git_repo):
    repo = GitRepo()
    subprocess.run(["touch", "file.txt"], check=True)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "initial"], check=True)

    assert not repo.tag_exists("test-tag")
    repo.create_tag("test-tag", push=False)
    assert repo.tag_exists("test-tag")


def test_get_latest_tag_returns_created_tag(fresh_git_repo):
    repo = GitRepo()
    subprocess.run(["touch", "file.txt"], check=True)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "initial"], check=True)

    repo.create_tag("v1.2.3", push=False)
    latest = repo.get_latest_tag()
    assert latest == "v1.2.3"


def test_get_commit_messages_since_tag(fresh_git_repo):
    repo = GitRepo()

    subprocess.run(["touch", "a.txt"], check=True)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "feat: first"], check=True)
    repo.create_tag("v0.1.0", push=False)

    subprocess.run(["touch", "b.txt"], check=True)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "fix: second"], check=True)

    commits = repo.get_commit_messages("v0.1.0")
    assert any("fix: second" in msg for msg in commits)


def test_configure_remote_sets_git_config(monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "dummy-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "user/repo")

    with mock.patch("subprocess.run") as mocked:
        repo = GitRepo(debug=True)
        repo.configure_remote()

        calls = [call[0][0] for call in mocked.call_args_list]
        assert any("user.name" in c for c in calls)
        assert any("remote" in c and "set-url" in c for c in calls)


def test_configure_remote_skips_if_no_token(monkeypatch):
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)

    with mock.patch("subprocess.run") as mocked:
        repo = GitRepo(debug=True)
        repo.configure_remote()
        mocked.assert_not_called()


def test_get_latest_tag_fallback_used():
    with mock.patch("subprocess.run") as mocked:
        # describe schlägt fehl
        def fake_run(cmd, **kwargs):
            if "describe" in cmd:
                raise subprocess.CalledProcessError(1, cmd)
            elif "tag" in cmd:
                return mock.Mock(stdout="v9.9.9\n", returncode=0)
            else:
                return mock.Mock(returncode=0)

        mocked.side_effect = fake_run

        repo = GitRepo(debug=True)
        tag = repo.get_latest_tag()
        assert tag == "v9.9.9"


def test_get_commit_messages_raises_and_exits():
    with mock.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git log")), \
            mock.patch("sys.exit") as exit_mock:
        repo = GitRepo(debug=True)
        repo.get_commit_messages("v0.1.0")
        exit_mock.assert_called_once_with(1)


def test_tag_exists_true_false(monkeypatch):
    with mock.patch("subprocess.run") as mocked:
        mocked.return_value = mock.Mock(stdout="v1.0.0\nv2.0.0\n", returncode=0)
        repo = GitRepo()
        assert repo.tag_exists("v2.0.0")
        assert not repo.tag_exists("v9.9.9")


def test_create_tag_fails_if_exists(caplog):
    with mock.patch("gitag.git_repo.GitRepo.tag_exists", return_value=True):
        repo = GitRepo()
        success = repo.create_tag("v1.2.3", push=False)
        assert success is False
        assert "already exists" in caplog.text


def test_create_tag_and_push(monkeypatch):
    with mock.patch("gitag.git_repo.GitRepo.tag_exists", return_value=False), \
            mock.patch("subprocess.run") as mocked:
        repo = GitRepo()
        result = repo.create_tag("v3.0.0", push=True)
        assert result is True
        assert any("push" in c[0][0] for c in mocked.call_args_list)


def test_create_tag_push_fails(monkeypatch):
    with mock.patch("gitag.git_repo.GitRepo.tag_exists", return_value=False), \
            mock.patch("subprocess.run", side_effect=[None, subprocess.CalledProcessError(1, "push")]), \
            mock.patch("sys.exit") as exit_mock:
        repo = GitRepo()
        repo.create_tag("v3.3.3", push=True)
        exit_mock.assert_called_once_with(1)


def test_get_latest_tag_fallback_no_tags():
    with mock.patch("subprocess.run", side_effect=[
        subprocess.CalledProcessError(1, "describe"),
        subprocess.CalledProcessError(1, "tag")
    ]):
        repo = GitRepo(debug=True)
        tag = repo.get_latest_tag()
        assert tag is None


def test_tag_exists_git_fails():
    with mock.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git tag")):
        repo = GitRepo(debug=True)
        result = repo.tag_exists("v0.0.1")
        assert result is False


def test_get_commit_messages_with_merges():
    with mock.patch("subprocess.run") as mocked:
        mocked.return_value = mock.Mock(stdout="feat: with merge", returncode=0)
        repo = GitRepo(debug=True, include_merges=True)
        commits = repo.get_commit_messages("v1.0.0")
        log_cmd = mocked.call_args_list[0][0][0]
        assert "--no-merges" not in log_cmd
        assert commits == ["feat: with merge"]


def test_merge_strategy_always_triggers_debug(caplog):
    caplog.set_level("DEBUG")
    with mock.patch("subprocess.run") as mocked:
        mocked.return_value = mock.Mock(stdout="commit message", returncode=0)
        repo = GitRepo(debug=True, merge_strategy=MergeStrategy.ALWAYS)
        repo.get_commit_messages("v1.0.0")

    # Normalize for debug output
    assert any("Using full commit range" in msg for msg in caplog.messages)


def test_merge_strategy_invalid(caplog):
    caplog.set_level("DEBUG")

    class FakeStrategy:
        value = "invalid"

    repo = GitRepo(debug=True)
    repo.merge_strategy = FakeStrategy()

    with mock.patch("subprocess.run") as mocked:
        mocked.return_value = mock.Mock(stdout="feat: unknown", returncode=0)
        repo.get_commit_messages("v1.0.0")

    assert any("not recognized" in msg for msg in caplog.messages)


def test_get_commit_messages_exit_with_debug(caplog):
    caplog.set_level("DEBUG")
    with mock.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, ["git", "log"])), \
            mock.patch("sys.exit") as exit_mock:

        repo = GitRepo(debug=True)
        repo.get_commit_messages("v0.1.0")

        assert any("❌ Error" in msg for msg in caplog.messages)
        assert any("Command '['git', 'log']'" in msg for msg in caplog.messages)
        exit_mock.assert_called_once_with(1)


def test_get_commit_messages_exit_without_debug(caplog):
    caplog.set_level("DEBUG")
    with mock.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, ["git", "log"])), \
            mock.patch("sys.exit") as exit_mock:

        repo = GitRepo(debug=False)
        repo.get_commit_messages("v0.1.0")

        assert any("❌ Error" in msg for msg in caplog.messages)
        assert all("Command '['git', 'log']'" not in msg for msg in caplog.messages)
        exit_mock.assert_called_once_with(1)
