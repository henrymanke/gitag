import re
from unittest import mock
import datetime
import pytest
from pathlib import Path
from gitag.changelog_writer import ChangelogWriter
from gitag.config import BumpLevel


def test_write_changelog_default(tmp_path):
    path = tmp_path / "CHANGELOG.md"
    writer = ChangelogWriter(path=path)
    commits = {
        str(BumpLevel.PATCH): ["fix: typo"],
        str(BumpLevel.MINOR): ["feat: something new"],
        str(BumpLevel.MAJOR): ["BREAKING CHANGE: removed endpoint"]
    }
    writer.write("v1.2.3", commits)

    content = path.read_text()
    assert "## v1.2.3" in content
    assert "- fix: typo" in content
    assert "- feat: something new" in content
    assert "- BREAKING CHANGE: removed endpoint" in content


def test_write_changelog_with_date(tmp_path):
    path = tmp_path / "CHANGELOG.md"
    writer = ChangelogWriter(path=path, include_date=True)
    tag = "v1.2.4"
    commits = {"patch": ["fix: one thing"]}
    writer.write(tag, commits)

    today = datetime.date.today().isoformat()
    content = path.read_text()
    assert f"## {tag} - {today}" in content
    assert "- fix: one thing" in content


def test_write_changelog_overwrite(tmp_path):
    path = tmp_path / "CHANGELOG.md"
    path.write_text("OLD CONTENT")

    writer = ChangelogWriter(path=path, mode="overwrite")
    commits = {"minor": ["feat: brand new"]}
    writer.write("v2.0.0", commits)

    content = path.read_text()
    assert "OLD CONTENT" not in content
    assert "- feat: brand new" in content


def test_write_changelog_empty_sections(tmp_path):
    path = tmp_path / "CHANGELOG.md"
    writer = ChangelogWriter(path=path)
    commits = {"patch": [], "minor": [], "major": []}
    writer.write("v1.3.0", commits)

    content = path.read_text()
    assert "## v1.3.0" in content
    assert "Patch Changes" not in content
    assert "Minor Changes" not in content
    assert "Major Changes" not in content


def test_custom_sections_order(tmp_path):
    path = tmp_path / "CHANGELOG.md"
    writer = ChangelogWriter(path=path)
    commits = {
        "major": ["BREAKING: drop python 3.6"],
        "minor": ["feat: dashboard"],
        "patch": ["fix: typo"]
    }
    writer.write("v3.0.0", commits)

    content = path.read_text()
    major_pos = content.find("### Major Changes")
    minor_pos = content.find("### Minor Changes")
    patch_pos = content.find("### Patch Changes")

    assert major_pos < minor_pos < patch_pos


def test_write_changelog_no_changes(tmp_path):
    path = tmp_path / "CHANGELOG.md"
    writer = ChangelogWriter(path=path)
    writer.write("v0.1.0", {})

    content = path.read_text()
    assert "- No changes detected." in content


def test_append_to_existing_changelog(tmp_path):
    path = tmp_path / "CHANGELOG.md"
    # Fake existing changelog with TOC and old tag
    path.write_text("""# 📘 Changelog Overview
| Version | Date | Major | Minor | Patch |
|:-------:|:----:|:-----:|:-----:|:-----:|

## v0.9.0 - 2024-01-01

### Patch Changes

- fix: old bug
""")

    writer = ChangelogWriter(path=path, mode="append")
    commits = {str(BumpLevel.MINOR): ["feat: added stuff"]}
    writer.write("v1.0.0", commits)

    content = path.read_text()
    assert "## v1.0.0" in content
    assert "## v0.9.0" in content  # Old block must be preserved
    assert "fix: old bug" in content
    assert "feat: added stuff" in content
    assert content.count("📘 Changelog Overview") == 1  # TOC was replaced, not duplicated


def test_write_changelog_without_date(tmp_path):
    path = tmp_path / "CHANGELOG.md"
    writer = ChangelogWriter(path=path, include_date=False)
    commits = {"patch": ["fix: silent error"]}
    writer.write("v1.2.5", commits)

    content = path.read_text()

    # ✅ Extract only the relevant line (entry header)
    lines = content.splitlines()
    entry_line = next(line for line in lines if line.startswith("## v1.2.5"))

    # ✅ Ensure that NO date is included in the header
    assert entry_line.strip() == "## v1.2.5"


def test_append_with_only_toc(tmp_path):
    path = tmp_path / "CHANGELOG.md"
    path.write_text("""# 📘 Changelog Overview
| Version | Date | Major | Minor | Patch |
|:-------:|:----:|:-----:|:-----:|:-----:|
""")

    writer = ChangelogWriter(path=path, mode="append")
    commits = {"minor": ["feat: fresh start"]}
    writer.write("v1.0.1", commits)

    content = path.read_text()
    assert "feat: fresh start" in content
    assert "## v1.0.1" in content


def test_append_block_without_match(tmp_path):
    path = tmp_path / "CHANGELOG.md"
    path.write_text("""# 📘 Changelog Overview
| Version | Date | Major | Minor | Patch |
|:-------:|:----:|:-----:|:-----:|:-----:|

---  # Leerer Block ohne ##-Header
Random garbage
""")

    writer = ChangelogWriter(path=path, mode="append")
    commits = {"minor": ["feat: new feature"]}
    writer.write("v1.0.1", commits)

    content = path.read_text()
    assert "## v1.0.1" in content
    assert "feat: new feature" in content
    # The block without a match must not appear
    assert "Random garbage" not in content


def test_append_block_with_same_tag(tmp_path):
    path = tmp_path / "CHANGELOG.md"
    path.write_text("""# 📘 Changelog Overview
| Version | Date | Major | Minor | Patch |
|:-------:|:----:|:-----:|:-----:|:-----:|

## v1.2.5 - 2024-01-01

### Patch Changes

- fix: old patch
""")

    writer = ChangelogWriter(path=path, mode="append")
    # same tag version, should not appear twice
    commits = {"patch": ["fix: new fix"]}
    writer.write("v1.2.5", commits)

    content = path.read_text()
    # only 1x of the header allowed
    assert content.count("## v1.2.5") == 1
    assert "fix: new fix" in content
    assert "fix: old patch" not in content
