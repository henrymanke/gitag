import pytest
from pathlib import Path
from gitag.version_manager import VersionManager


def test_config_validation_warns_invalid_prefix(tmp_path, caplog):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("""
[tool.gitag]
prefix = 123
""")
    with caplog.at_level("WARNING"):
        VersionManager(config_path=str(pyproject))
    assert "prefix must be a string" in caplog.text


def test_config_validation_warns_invalid_keywords_type(tmp_path, caplog):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("""
[tool.gitag]
prefix = "v"
patterns = "invalid"
""")
    with caplog.at_level("WARNING"):
        VersionManager(config_path=str(pyproject))
    assert "patterns must be a dictionary" in caplog.text


def test_config_validation_warns_invalid_levels(tmp_path, caplog):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("""
[tool.gitag.patterns]
unknown = ["foo:"]
patch = "fix"
""")
    with caplog.at_level("WARNING"):
        VersionManager(config_path=str(pyproject))
    assert "Invalid bump level: 'unknown'" in caplog.text
    assert "Values for patterns['patch'] must be a list of strings" in caplog.text


def test_config_validation_warns_invalid_suffix(tmp_path, caplog):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("""
[tool.gitag]
suffix = 123
""")
    with caplog.at_level("WARNING"):
        VersionManager(config_path=str(pyproject))
    assert "suffix must be a string" in caplog.text


def test_config_validation_warns_invalid_version_pattern(tmp_path, caplog):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("""
[tool.gitag]
version_pattern = 123
""")
    with caplog.at_level("WARNING"):
        VersionManager(config_path=str(pyproject))
    assert "version_pattern must be a string" in caplog.text
