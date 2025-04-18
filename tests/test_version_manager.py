import pytest
from pathlib import Path
from gitag.version_manager import VersionManager
from gitag.config import BumpLevel


def test_bump_patch():
    vm = VersionManager()
    assert vm.bump_version("1.2.3", BumpLevel.PATCH) == "1.2.4"


def test_bump_minor():
    vm = VersionManager()
    assert vm.bump_version("1.2.3", BumpLevel.MINOR) == "1.3.0"


def test_bump_major():
    vm = VersionManager()
    assert vm.bump_version("1.2.3", BumpLevel.MAJOR) == "2.0.0"


def test_pre_and_build_metadata():
    vm = VersionManager()
    version = vm.bump_version("1.2.3", BumpLevel.PATCH, pre="alpha.1", build="abc123")
    assert version == "1.2.4-alpha.1+abc123"


def test_default_strategy_detection(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    vm = VersionManager()
    assert vm.determine_bump(["fix: bug"]) == BumpLevel.PATCH
    assert vm.determine_bump(["feat: feature"]) == BumpLevel.MINOR
    assert vm.determine_bump(["BREAKING CHANGE: refactor"]) == BumpLevel.MAJOR
    assert vm.determine_bump(["feat: new", "BREAKING CHANGE: boom"]) == BumpLevel.MAJOR


def test_empty_strategy_detection(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text("")
    monkeypatch.chdir(tmp_path)

    vm = VersionManager()
    assert vm.determine_bump(["fix: bug"]) == BumpLevel.PATCH
    assert vm.determine_bump(["feat: feature"]) == BumpLevel.MINOR
    assert vm.determine_bump(["BREAKING CHANGE: refactor"]) == BumpLevel.MAJOR
    assert vm.determine_bump(["feat: new", "BREAKING CHANGE: boom"]) == BumpLevel.MAJOR


def test_empty_bump_keywords(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text("""
[tool.gitag.bump_keywords]
""")
    monkeypatch.chdir(tmp_path)

    vm = VersionManager()
    assert vm.determine_bump(["feat: feature"]) == BumpLevel.MINOR


def test_invalid_version_format():
    vm = VersionManager()
    with pytest.raises(ValueError):
        vm.bump_version("invalid", BumpLevel.PATCH)


def test_custom_strategy_from_pyproject(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("""
[tool.gitag]
version_pattern = "^v?(\\\\d+)\\\\.(\\\\d+)\\\\.(\\\\d+)$"

[tool.gitag.bump_keywords]
major = ["BREAKING"]
minor = ["feature:"]
""")

    vm = VersionManager(config_path=str(pyproject))
    assert vm.determine_bump(["BREAKING fix"]) == BumpLevel.MAJOR
    assert vm.determine_bump(["feature: X"]) == BumpLevel.MINOR
    assert vm.determine_bump(["fix: nothing"]) == BumpLevel.PATCH


def test_prefix_and_suffix():
    vm = VersionManager()
    vm.prefix = "ver-"
    vm.suffix = "-stable"
    result = vm.bump_version("ver-1.2.3-stable", BumpLevel.PATCH)
    assert result == "ver-1.2.4-stable"


@pytest.mark.parametrize("prefix,suffix,old_version,expected", [
    ("v", "", "v1.2.3", "v1.2.4"),
    ("", "-stable", "1.2.3-stable", "1.2.4-stable"),
    ("ver-", "-prod", "ver-1.2.3-prod", "ver-1.2.4-prod"),
    ("release-", "", "release-1.2.3", "release-1.2.4"),
    ("", "", "1.2.3", "1.2.4"),
])
def test_patch_with_prefix_suffix(prefix, suffix, old_version, expected):
    vm = VersionManager()
    vm.prefix = prefix
    vm.suffix = suffix
    assert vm.bump_version(old_version, BumpLevel.PATCH) == expected


def test_config_path_defaults_to_pyproject(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    # kein pyproject vorhanden → default wird geladen (kein Fehler)
    vm = VersionManager()
    assert isinstance(vm, VersionManager)  # kein Crash, default greift


def test_invalid_bump_keywords_warns(tmp_path, caplog, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("""
[tool.gitag.bump_keywords]
nonsense = ["xyz"]
""")
    monkeypatch.chdir(tmp_path)

    with caplog.at_level("INFO"):
        _ = VersionManager()
        assert "No valid bump_keywords found" in caplog.text or "Ignoring invalid bump levels" in caplog.text


def test_categorize_commits_correctly():
    vm = VersionManager()
    categorized = vm.categorize_commits(["fix: bug", "feat: x", "BREAKING CHANGE: wow"])
    assert categorized[str(BumpLevel.PATCH)] == ["fix: bug"]
    assert categorized[str(BumpLevel.MINOR)] == ["feat: x"]
    assert categorized[str(BumpLevel.MAJOR)] == ["BREAKING CHANGE: wow"]


def test_custom_strategy_and_pattern_setters():
    vm = VersionManager()
    vm.strategy = lambda msg: BumpLevel.MINOR
    assert vm.determine_bump(["anything"]) == BumpLevel.MINOR

    vm.pattern = r"^(\d+)\.(\d+)\.(\d+)$"
    assert vm.pattern == r"^(\d+)\.(\d+)\.(\d+)$"


def test_uses_default_pyproject_path(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    # Kein config_path übergeben → default = pyproject.toml
    (tmp_path / "pyproject.toml").write_text("")  # leer = valid
    vm = VersionManager()
    assert isinstance(vm, VersionManager)


def test_logs_info_on_empty_bump_keywords(tmp_path, caplog, monkeypatch):
    (tmp_path / "pyproject.toml").write_text("""
[tool.gitag.bump_keywords]
""")
    monkeypatch.chdir(tmp_path)
    with caplog.at_level("INFO"):
        VersionManager()
        assert "No valid bump_keywords found" in caplog.text


def test_version_pattern_mismatch_logs_and_raises(caplog):
    vm = VersionManager()
    vm.pattern = r"^v(\d+)\.(\d+)\.(\d+)$"  # verlangt 'v' Präfix

    with caplog.at_level("ERROR"):
        with pytest.raises(ValueError):
            vm.bump_version("1.2.3", BumpLevel.PATCH)

        assert "Invalid version format" in caplog.text


def test_categorize_commits_all_levels():
    vm = VersionManager()
    commits = ["fix: bug", "feat: feature", "BREAKING CHANGE: wow"]
    categorized = vm.categorize_commits(commits)

    assert categorized[str(BumpLevel.PATCH)] == ["fix: bug"]
    assert categorized[str(BumpLevel.MINOR)] == ["feat: feature"]
    assert categorized[str(BumpLevel.MAJOR)] == ["BREAKING CHANGE: wow"]


def test_pattern_setter_works():
    vm = VersionManager()
    new_pattern = r"^v(\d+)\.(\d+)\.(\d+)$"
    vm.pattern = new_pattern
    assert vm.pattern == new_pattern


def test_default_strategy_returns_patch_on_no_match():
    from gitag.version_manager import default_bump_strategy
    assert default_bump_strategy("this does not match anything") == BumpLevel.PATCH


def test_pyproject_load_error(monkeypatch, tmp_path, caplog):
    broken_file = tmp_path / "pyproject.toml"
    broken_file.write_text("{ not: valid: toml")  # absichtlich kaputt
    monkeypatch.chdir(tmp_path)

    with caplog.at_level("ERROR"):
        VersionManager()
        assert "Error loading" in caplog.text


def test_determine_bump_type_error():
    vm = VersionManager()
    with pytest.raises(TypeError):
        vm.determine_bump("not-a-list")
    with pytest.raises(TypeError):
        vm.determine_bump([123])


def test_bump_version_invalid_level_string():
    vm = VersionManager()
    with pytest.raises(ValueError) as exc:
        vm.bump_version("1.2.3", "INVALID")
    assert "Invalid bump level" in str(exc.value)


def test_get_default_version_with_prefix_suffix():
    vm = VersionManager()
    vm.prefix = "v"
    vm.suffix = "-beta"
    assert vm.get_default_version() == "v0.0.0-beta"
