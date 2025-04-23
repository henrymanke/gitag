import pytest
from unittest import mock
from gitag.auto_tagger import GitAutoTagger


def test_run_dry():
    tagger = GitAutoTagger(debug=True)
    tagger.repo.get_latest_tag = mock.Mock(return_value="v1.0.0")
    tagger.repo.get_commit_messages = mock.Mock(return_value=["feat: x"])
    tagger.repo.create_tag = mock.Mock(return_value=True)
    tagger.versioning.determine_bump = mock.Mock(return_value="minor")
    tagger.versioning.bump_version = mock.Mock(return_value="v1.1.0")
    tagger.run(dry_run=True)


def test_run_no_commits(caplog):
    tagger = GitAutoTagger(debug=True)
    tagger.repo.get_latest_tag = mock.Mock(return_value="v1.0.0")
    tagger.repo.get_commit_messages = mock.Mock(return_value=[])
    with caplog.at_level("WARNING"):
        tagger.run()
        assert "No new commits found" in caplog.text


def test_run_with_pre_and_build(caplog):
    tagger = GitAutoTagger(debug=True, pre="alpha", build="001")
    tagger.repo.get_latest_tag = mock.Mock(return_value="v1.0.0")
    tagger.repo.get_commit_messages = mock.Mock(return_value=["feat: x"])
    tagger.repo.create_tag = mock.Mock(return_value=True)
    tagger.versioning.determine_bump = mock.Mock(return_value="minor")
    tagger.versioning.bump_version = mock.Mock(return_value="v1.1.0")

    with caplog.at_level("INFO"):
        tagger.run(dry_run=True)
        assert "pre=alpha" in caplog.text
        assert "build=001" in caplog.text


def test_run_with_changelog_written():
    tagger = GitAutoTagger(debug=True, changelog=True)
    tagger.repo.get_latest_tag = mock.Mock(return_value="v1.0.0")
    tagger.repo.get_commit_messages = mock.Mock(return_value=["feat: x"])
    tagger.repo.create_tag = mock.Mock(return_value=True)
    tagger.versioning.determine_bump = mock.Mock(return_value="patch")
    tagger.versioning.bump_version = mock.Mock(return_value="v1.0.1")
    tagger.versioning.categorize_commits = mock.Mock(return_value={"feat": ["feat: x"]})
    tagger.changelog_writer.write = mock.Mock()

    tagger.run(dry_run=True)
    tagger.changelog_writer.write.assert_called_once_with(
        tag="v1.0.1",
        categorized_commits={"feat": ["feat: x"]}
    )


def test_run_creates_tag_and_prints_success(caplog):
    tagger = GitAutoTagger(debug=True)
    tagger.repo.get_latest_tag = mock.Mock(return_value="v1.0.0")
    tagger.repo.get_commit_messages = mock.Mock(return_value=["fix: a"])
    tagger.versioning.determine_bump = mock.Mock(return_value="patch")
    tagger.versioning.bump_version = mock.Mock(return_value="v1.0.1")
    tagger.repo.create_tag = mock.Mock(return_value=True)

    with caplog.at_level("INFO"):
        tagger.run()
        assert "Tag v1.0.1 created" in caplog.text


def test_run_tag_already_exists(caplog):
    tagger = GitAutoTagger(debug=True)
    tagger.repo.get_latest_tag = mock.Mock(return_value="v1.0.0")
    tagger.repo.get_commit_messages = mock.Mock(return_value=["fix: a"])
    tagger.versioning.determine_bump = mock.Mock(return_value="patch")
    tagger.versioning.bump_version = mock.Mock(return_value="v1.0.1")
    tagger.repo.create_tag = mock.Mock(return_value=False)

    with caplog.at_level("INFO"):
        tagger.run()
        assert "already exists" in caplog.text


def test_run_without_previous_tag_uses_default(caplog):
    tagger = GitAutoTagger(debug=True)
    tagger.repo.get_latest_tag = mock.Mock(return_value=None)
    tagger.versioning.get_default_version = mock.Mock(return_value="v0.1.0")
    tagger.repo.get_commit_messages = mock.Mock(return_value=["feat: init"])
    tagger.versioning.determine_bump = mock.Mock(return_value="minor")
    tagger.versioning.bump_version = mock.Mock(return_value="v0.2.0")
    tagger.repo.create_tag = mock.Mock(return_value=True)

    with caplog.at_level("INFO"):
        tagger.run()
        assert "No previous tag found" in caplog.text
        assert tagger.versioning.get_default_version.called
