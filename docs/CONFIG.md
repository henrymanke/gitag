# 🔧 Git Auto Tag – Configuration Guide

[← Back to README](https://github.com/henrymanke/gitag/blob/main/README.md)

The `gitag` tool supports custom configuration via the `pyproject.toml` file.

---

## 📋 Configuration Overview

| Option                  | Type      | Default                | Description                                                                 |
|-------------------------|-----------|------------------------|-----------------------------------------------------------------------------|
| `prefix`                | `string`  | `""`                  | Optional prefix added before version tags (e.g. `v1.2.3`)                   |
| `suffix`                | `string`  | `""`                  | Optional suffix added after version tags (e.g. `1.2.3-beta`)                |
| `version_pattern`       | `string`  | Semantic Versioning    | Regex with named groups to match tags (`major`, `minor`, `patch`, …)        |
| `merge_strategy`        | `string`  | `"auto"`             | Controls which commits are considered during a merge (see below)            |
| `[tool.gitag.patterns]` | `table`   | predefined             | Regex-based bump detection, grouped by major/minor/patch                     |
| `patterns.major`        | `list`    | `["BREAKING CHANGE", "!:"]` | Triggers a **major** bump (`1.2.3` → `2.0.0`)                               |
| `patterns.minor`        | `list`    | `["feat:", "feature:"]` | Triggers a **minor** bump (`1.2.0` → `1.3.0`)                               |
| `patterns.patch`        | `list`    | see below              | Triggers a **patch** bump (`1.2.3` → `1.2.4`)                               |

---

## 🗂 Section Declaration

All configuration must be nested under:

```toml
[tool.gitag]
```

---

## ⚙️ Core Options

### `prefix` _(optional)_

Add a string before version tags:

```toml
prefix = "v"
```

➡️ Results in: `v1.2.3`

---

### `suffix` _(optional)_

Add a string after version tags:

```toml
suffix = "-beta"
```

➡️ Results in: `1.2.3-beta`

---

### `version_pattern` _(optional)_

Regex pattern to match existing tags.

> Must contain named groups: `major`, `minor`, `patch`  
> Optionally: `prerelease`, `buildmetadata`

```toml
version_pattern = "^v?(?P<major>\\d+)\\.(?P<minor>\\d+)\\.(?P<patch>\\d+)(?:-(?P<prerelease>[\\w\\.]+))?(?:\\+(?P<buildmetadata>[\\w\\.]+))?$"
```

Supports:

- `v1.2.3`
- `1.2.3-beta`
- `1.2.3+build.42`
- `1.2.3-beta+build.42`

---

### `merge_strategy` _(optional)_

Determines which commits are considered during a merge.

| Value         | Description                                                               |
|---------------|---------------------------------------------------------------------------|
| `auto`        | Detects a merge commit and uses only the merged feature branch commits.   |
| `always`      | Uses all commits since the last tag (`<tag>..HEAD`).                      |
| `merge_only`  | Always uses only the feature branch (HEAD must be a merge commit).        |

```toml
merge_strategy = "auto"
```

Recommended: keep `"auto"` for best coverage.

---

## 🚀 Bump Strategy via Commit Messages

Bump levels are auto-detected via commit message patterns under:

```toml
[tool.gitag.patterns]
```

Each key maps to a version level and accepts a list of regex patterns.

### 🔼 Major

```toml
[tool.gitag.patterns]
major = [
  "!:",            # any commit with '!' in header
  "BREAKING CHANGE" # explicit breaking change footer
]
```

Triggers bump: `1.2.3` → `2.0.0`

### 🔽 Minor

```toml
[tool.gitag.patterns]
minor = [
  "feat:",         # new features
  "feature:"        # alternate keyword
]
```

Triggers bump: `1.2.3` → `1.3.0`

### 🛠 Patch

```toml
[tool.gitag.patterns]
patch = [
  "fix:",          # bug fixes
  "perf:",         # performance improvements
  "refactor:",     # code restructuring
  "docs:",         # documentation changes
  "style:",        # formatting/style
  "chore:",        # maintenance tasks
  "test:",         # tests
  "ci:",           # CI config
  "build:",        # build system
  "[PATCH]"        # explicit patch tag
]
```

Triggers bump: `1.2.3` → `1.2.4`

---

## 📌 Default Configuration

Used if no user config is found:

```toml
[tool.gitag]
merge_strategy   = "auto"
prefix           = ""
suffix           = ""
version_pattern  = "^v?(?P<major>\\d+)\\.(?P<minor>\\d+)\\.(?P<patch>\\d+)$"

[tool.gitag.patterns]
major = ["BREAKING CHANGE"]
minor = ["feat:"]
patch = ["fix:", "perf:", "refactor:", "docs:", "style:", "chore:", "test:", "ci:", "build:"]
```

---

## ✅ Example Configuration

```toml
[tool.gitag]
prefix          = "v"
suffix          = "-rc"
merge_strategy  = "merge_only"
version_pattern = "^v?(?P<major>\\d+)\\.(?P<minor>\\d+)\\.(?P<patch>\\d+)(?:-(?P<prerelease>[\\w\\.]+))?(?:\\+(?P<buildmetadata>[\\w\\.]+))?$"

[tool.gitag.patterns]
major = ["!:", "BREAKING CHANGE", "[MAJOR]"]
minor = ["feat:", "feature:", "[MINOR]"]
patch = ["fix:", "chore:", "docs:", "[PATCH]"]
```

---

## 🧪 Advanced

To override bump logic programmatically, see:

```python
VersionManager.load_config_from_pyproject()
```
