# 🔧 Git Auto Tag – Configuration Guide

The `gitag` tool supports custom configuration via the `pyproject.toml` file.

---

## 📋 Configuration Overview

| Option                              | Type      | Default                | Description                                                                 |
|-------------------------------------|-----------|------------------------|-----------------------------------------------------------------------------|
| `prefix`                            | `string`  | `""`                   | Optional prefix added before version tags (e.g. `v1.2.3`)                   |
| `suffix`                            | `string`  | `""`                   | Optional suffix added after version tags (e.g. `1.2.3-beta`)               |
| `version_pattern`                   | `string`  | Semantic Versioning    | Regex with named groups to match tags (`major`, `minor`, `patch`, …)       |
| `merge_strategy`                    | `string`  | `"auto"`               | Controls which commits are considered during a merge (see below)           |
| `[tool.gitag.bump_keywords]` | `table`   | predefined             | Keyword-based bump detection by level (see below)                           |
| `bump_keywords.major`               | `list`    | `["BREAKING CHANGE"]`  | Triggers a **major** bump (`1.0.0` → `2.0.0`)                               |
| `bump_keywords.minor`               | `list`    | `["feat:"]`            | Triggers a **minor** bump (`1.2.0` → `1.3.0`)                               |
| `bump_keywords.patch`              | `list`    | see below              | Triggers a **patch** bump (`1.2.3` → `1.2.4`)                               |

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
version_pattern = "^v?(\\d+)\\.(\\d+)\\.(\\d+)(?:-([\\w\\.]+))?(?:\\+([\\w\\.]+))?$"
```

Supports:

- `v1.2.3`
- `1.2.3-beta`
- `1.2.3+build.42`
- `1.2.3-beta+build.42`

---

### `merge_strategy` _(optional)_

Determines which commits are considered during a merge.

| Value         | Description                                                                 |
|---------------|-----------------------------------------------------------------------------|
| `auto`        | Detects if HEAD is a merge commit and uses only the merged feature branch. |
| `always`      | Uses all commits since the last tag (`<tag>..HEAD`).                        |
| `merge_only`  | Always uses only the feature branch (HEAD must be a merge commit).         |

```toml
merge_strategy = "auto"
```

Recommended: keep `"auto"` for best coverage.

---

## 🚀 Bump Strategy via Commit Messages

Bump levels are auto-detected via commit message prefixes.

Declare them under:

```toml
[tool.gitag.bump_keywords]
```

Each key maps to a version level and accepts a list of match patterns.

---

### 🔼 Major

```toml
major = ["BREAKING CHANGE", "!:", "[MAJOR]"]
```

Triggers bump: `1.2.3` → `2.0.0`

---

### 🔼 Minor

```toml
minor = ["feat:", "feature:", "[MINOR]"]
```

Triggers bump: `1.2.3` → `1.3.0`

---

### 🔼 Patch

```toml
patch = [
  "fix:",
  "perf:",
  "refactor:",
  "docs:",
  "style:",
  "chore:",
  "test:",
  "ci:",
  "build:",
  "[PATCH]"
]
```

Triggers bump: `1.2.3` → `1.2.4`

---

## 📌 Default Configuration

Used if no config is found:

```toml
[tool.gitag]

# Strategy for collecting commits
# auto        – detect merge and use feature branch commits (default)
# always      – all commits since last tag
# merge_only  – only commits in the merged branch
merge_strategy = "auto"

# Optional prefix and suffix
prefix = ""
suffix = ""

# Regex for semantic versioning
version_pattern = "^v?(\\d+)\\.(\\d+)\\.(\\d+)$"

[tool.gitag.bump_keywords]
major = ["BREAKING CHANGE"]
minor = ["feat:"]
patch = [
  "fix:",
  "perf:",
  "refactor:",
  "docs:",
  "style:",
  "chore:",
  "test:",
  "ci:",
  "build:"
]
```

---

## ✅ Example Configuration

```toml
[tool.gitag]
prefix = "v"
suffix = "-rc"
merge_strategy = "merge_only"
version_pattern = "^v?(\\d+)\\.(\\d+)\\.(\\d+)(?:-([\\w\\.]+))?(?:\\+([\\w\\.]+))?$"

[tool.gitag.bump_keywords]
major = ["BREAKING CHANGE", "!:", "[MAJOR]"]
minor = ["feat:", "feature:", "[MINOR]"]
patch = ["fix:", "chore:", "docs:", "[PATCH]"]
```

---

## 🧪 Advanced

To override bump logic programmatically, see:

```python
VersionManager.load_config_from_pyproject()
```