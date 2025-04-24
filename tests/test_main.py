import os
from gitag.main import detect_ci_context
import pytest
from unittest import mock
from gitag import main as main_module


@mock.patch("gitag.main.GitAutoTagger")
def test_main_dry_run(mock_tagger):
    result = main_module.main(["--dry-run", "--no-merges", "--merge-strategy", "always"])
    assert result == 0
    mock_tagger.assert_called_once()
    mock_tagger.return_value.run.assert_called_once_with(dry_run=True, since_tag=None)


@mock.patch("gitag.main.GitAutoTagger")
@mock.patch.dict("os.environ", {
    "GITHUB_ACTIONS": "true",
    "GITHUB_EVENT_NAME": "pull_request",
    "GITHUB_REF": "refs/heads/feature-branch"
})
def test_main_ci_detection_pr(mock_tagger):
    result = main_module.main(["--ci"])
    assert result == 0
    mock_tagger.return_value.run.assert_called_once()
    # dry_run sollte erzwungen werden
    args, kwargs = mock_tagger.call_args
    assert kwargs["push"] is False
    assert kwargs["debug"] is False


@mock.patch("gitag.main.GitAutoTagger")
@mock.patch.dict("os.environ", {
    "GITHUB_ACTIONS": "true",
    "GITHUB_EVENT_NAME": "push",
    "GITHUB_REF": "refs/heads/main"
})
def test_main_ci_main_branch_enables_push(mock_tagger):
    result = main_module.main(["--ci"])
    assert result == 0
    mock_tagger.return_value.run.assert_called_once()
    args, kwargs = mock_tagger.call_args
    assert kwargs["push"] is True


@mock.patch.dict(os.environ, {
    "GITLAB_CI": "true",
    "CI_MERGE_REQUEST_ID": "123",
    "CI_COMMIT_REF_NAME": "main"
}, clear=True)
def test_detect_gitlab_ci():
    assert detect_ci_context() == ("gitlab", True, True)


@mock.patch.dict(os.environ, {
    "CIRCLECI": "true",
    "CIRCLE_PULL_REQUEST": "true",
    "CIRCLE_BRANCH": "main"
}, clear=True)
def test_detect_circleci():
    assert detect_ci_context() == ("circleci", True, True)


@mock.patch.dict(os.environ, {
    "BITBUCKET_BUILD_NUMBER": "123",
    "BITBUCKET_PR_ID": "1",
    "BITBUCKET_BRANCH": "main"
}, clear=True)
def test_detect_bitbucket():
    assert detect_ci_context() == ("bitbucket", True, True)


@mock.patch.dict(os.environ, {
    "JENKINS_HOME": "/var/jenkins_home",
    "CHANGE_ID": "5",
    "BRANCH_NAME": "main"
}, clear=True)
def test_detect_jenkins():
    assert detect_ci_context() == ("jenkins", True, True)


@mock.patch.dict(os.environ, {}, clear=True)
def test_detect_unknown_ci():
    assert detect_ci_context() == ("unknown", False, False)


def test_main_entrypoint(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog", "--dry-run"])
    with mock.patch("gitag.main.GitAutoTagger") as mock_tagger:
        mock_tagger.return_value.run.return_value = None
        assert main_module.main() == 0


@mock.patch("gitag.main.GitAutoTagger")
@mock.patch.dict("os.environ", {
    "GITHUB_ACTIONS": "true",
    "GITHUB_EVENT_NAME": "push",
    "GITHUB_REF": "refs/heads/dev"
})
def test_main_ci_non_main_branch_enables_dry_run(mock_tagger, caplog):
    caplog.set_level("INFO")

    result = main_module.main(["--ci"])
    assert result == 0
    mock_tagger.return_value.run.assert_called_once_with(dry_run=True, since_tag=None)
    assert any("dry run fallback" in msg.lower() for msg in caplog.messages)


def test_main_as_entrypoint(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog", "--dry-run", "--no-merges"])
    with mock.patch("gitag.main.GitAutoTagger") as mock_tagger:
        mock_tagger.return_value.run.return_value = None
        result = main_module.main()
        assert result == 0


@mock.patch("gitag.main.GitAutoTagger")
def test_main_debug_logging_enabled(mock_tagger, caplog):
    caplog.set_level("DEBUG")
    result = main_module.main(["--dry-run", "--debug"])
    assert result == 0
    assert "🔧 Debug logging enabled." in caplog.text


@mock.patch("gitag.main.GitAutoTagger.run", side_effect=RuntimeError("boom"))
def test_main_debug_raises_exception(mock_run):
    with pytest.raises(RuntimeError, match="boom"):
        main_module.main(["--dry-run", "--debug"])


@mock.patch("gitag.main.GitAutoTagger.run", side_effect=RuntimeError("boom"))
def test_main_exception_without_debug(mock_run, caplog):
    caplog.set_level("ERROR")
    result = main_module.main(["--dry-run"])  # kein --debug
    assert result == 1
    assert "❌ gitag failed: boom" in caplog.text
