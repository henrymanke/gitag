import pytest
from pathlib import Path
from gitag.version_manager import VersionManager
from gitag.config import BumpLevel


@pytest.fixture(autouse=True)
def temp_pyproject(tmp_path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("")  # Leeres pyproject
    monkeypatch.chdir(tmp_path)


def create_vm(prefix="v", suffix=""):
    """Erstellt eine VersionManager-Instanz mit definiertem Prefix/Suffix."""
    vm = VersionManager()
    vm.prefix = prefix
    vm.suffix = suffix
    return vm


def test_bump_patch():
    vm = create_vm()
    assert vm.bump_version("1.2.3", BumpLevel.PATCH) == "v1.2.4"


def test_bump_minor():
    vm = create_vm()
    assert vm.bump_version("1.2.3", BumpLevel.MINOR) == "v1.3.0"


def test_bump_major():
    vm = create_vm()
    assert vm.bump_version("1.2.3", BumpLevel.MAJOR) == "v2.0.0"


def test_pre_and_build_metadata():
    vm = create_vm()
    version = vm.bump_version("1.2.3", BumpLevel.PATCH, pre="alpha.1", build="abc123")
    assert version == "v1.2.4-alpha.1+abc123"


def test_pattern_strategy_detection():
    vm = create_vm()
    assert vm.determine_bump(["fix: bug"]) == BumpLevel.PATCH
    assert vm.determine_bump(["feat: new feature"]) == BumpLevel.MINOR
    assert vm.determine_bump(["BREAKING CHANGE: refactor"]) == BumpLevel.MAJOR
    assert vm.determine_bump(["feat: new", "BREAKING CHANGE: boom"]) == BumpLevel.MAJOR


def test_patterns_in_pyproject(tmp_path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(r"""
[tool.gitag]
version_pattern = "^v?(\\d+)\\.(\\d+)\\.(\\d+)$"
prefix = "v"

[tool.gitag.patterns]
major = ["^Start", "^.*!:", "BREAKING CHANGE:"]
minor = ["^feat:", "^.*#:", "(?i)feat:", "???"]
patch = ["^fix:"]
""")
    monkeypatch.chdir(tmp_path)

    vm = VersionManager()

    assert vm.determine_bump(["Start: change"]) == BumpLevel.MAJOR
    assert vm.determine_bump(["feat!: feature"]) == BumpLevel.MAJOR
    assert vm.determine_bump(["BREAKING CHANGE: change"]) == BumpLevel.MAJOR
    assert vm.determine_bump(["BREAKING!: change"]) == BumpLevel.MAJOR

    assert vm.determine_bump(["???"]) == BumpLevel.MINOR
    assert vm.determine_bump(["feat: new"]) == BumpLevel.MINOR
    assert vm.determine_bump(["FEAT: new"]) == BumpLevel.MINOR
    assert vm.determine_bump(["minor#: new"]) == BumpLevel.MINOR

    assert vm.determine_bump(["fix: minor bug"]) == BumpLevel.PATCH
    assert vm.determine_bump(["bREAKING CHANGE: major"]) == BumpLevel.PATCH


def test_empty_pyproject_uses_defaults():
    vm = create_vm()
    assert isinstance(vm, VersionManager)


def test_invalid_version_format():
    vm = create_vm()
    with pytest.raises(ValueError):
        vm.bump_version("invalid", BumpLevel.PATCH)


def test_prefix_and_suffix_handling():
    vm = create_vm(prefix="ver-", suffix="-stable")
    result = vm.bump_version("1.2.3", BumpLevel.PATCH)
    assert result == "ver-1.2.4-stable"


@pytest.mark.parametrize("prefix,suffix,current_version,expected", [
    ("v", "", "1.2.3", "v1.2.4"),
    ("", "-stable", "1.2.3", "1.2.4-stable"),
    ("ver-", "-prod", "1.2.3", "ver-1.2.4-prod"),
    ("release-", "", "1.2.3", "release-1.2.4"),
    ("", "", "1.2.3", "1.2.4"),
])
def test_patch_with_prefix_suffix(prefix, suffix, current_version, expected):
    vm = create_vm(prefix=prefix, suffix=suffix)
    assert vm.bump_version(current_version, BumpLevel.PATCH) == expected


def test_categorize_commits_correctly():
    vm = create_vm()
    categorized = vm.categorize_commits(["fix: bug", "feat: x", "BREAKING CHANGE: wow"])
    assert categorized[str(BumpLevel.PATCH)] == ["fix: bug"]
    assert categorized[str(BumpLevel.MINOR)] == ["feat: x"]
    assert categorized[str(BumpLevel.MAJOR)] == ["BREAKING CHANGE: wow"]


def test_invalid_pyproject_logs_error(tmp_path, monkeypatch, caplog):
    broken_file = tmp_path / "pyproject.toml"
    broken_file.write_text("{ not: valid: toml")
    monkeypatch.chdir(tmp_path)
    with caplog.at_level("ERROR"):
        VersionManager()
        assert "Error loading" in caplog.text


def test_determine_bump_type_error():
    vm = create_vm()
    with pytest.raises(TypeError):
        vm.determine_bump("not-a-list")
    with pytest.raises(TypeError):
        vm.determine_bump([123])


def test_bump_version_invalid_level_string():
    vm = create_vm()
    with pytest.raises(ValueError) as exc:
        vm.bump_version("1.2.3", "INVALID")
    assert "Invalid bump level" in str(exc.value)


def test_get_default_version_with_prefix_suffix():
    vm = create_vm(prefix="v", suffix="-beta")
    assert vm.get_default_version() == "v0.0.0-beta"


def test_pattern_setter_and_getter():
    vm = create_vm()
    new_pattern = r"^v(\d+)\.(\d+)\.(\d+)$"
    vm.pattern = new_pattern
    assert vm.pattern == new_pattern


def test_regex_fallback_to_patch_if_no_match():
    vm = create_vm()
    assert vm.determine_bump(["some random message"]) == BumpLevel.PATCH


def test_strip_prefix_suffix_full():
    # deckt prefix- und suffix-Entfernung ab (lines 107, 109)
    vm = create_vm(prefix="ver-", suffix="-beta")
    # strip_prefix_suffix soll aus "ver-1.2.3-beta" → "1.2.3" machen
    assert vm.strip_prefix_suffix("ver-1.2.3-beta") == "1.2.3"


def test_missing_default_and_user_config_warns(monkeypatch, tmp_path, caplog):
    # simuliert, dass weder default_pyproject.toml noch pyproject.toml existieren
    import gitag.version_manager as vm_mod
    monkeypatch.chdir(tmp_path)
    # Path.exists überall false machen
    monkeypatch.setattr(vm_mod.Path, "exists", lambda self: False)
    with caplog.at_level("WARNING"):
        vm_mod.VersionManager()
    # beide Warnungen sollten im Log stehen (lines 34 & 47)
    assert "Default config" in caplog.text
    assert "User config" in caplog.text
