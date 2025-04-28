# 🚀 gitag

<p align="center">
  <img src="https://raw.githubusercontent.com/henrymanke/gitag/main/assets/gitag.svg" alt="gitag logo" width="180"/>
</p>

**A modern CLI tool for automatic Git tagging based on commit messages.**  
Built for CI/CD pipelines. Powered by [Semantic Versioning](https://semver.org/). Tested. Flexible. Extendable.

---

## ✨ Features

- ✅ Semantic Versioning (`major`, `minor`, `patch`)
- 🔍 Detects latest Git tag (e.g. `v1.2.3`)
- 🧠 Commit-based version bump detection (configurable)
- 📄 Optional `CHANGELOG.md` generation
- 🔁 `--dry-run` mode support
- 🚀 Pushes tags via `GH_TOKEN` / `GITHUB_TOKEN`
- ⚙️ Configurable via `pyproject.toml`
- 🔀 Flexible merge commit strategies
- 🧪 100% tested (Pytest + Git mocks)

---

## 📦 Installation

```bash
git clone https://github.com/henrymanke/gitag.git
cd gitag
pip install -e .'[dev]'
```

Or symlink it globally:

```bash
ln -s $(pwd)/gitag/main.py /usr/local/bin/gitag
```

---

## 🔧 CLI Options

| Flag               | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| `--dry-run`        | Preview the next tag without applying it                                    |
| `--debug`          | Show verbose output                                                         |
| `--push`           | Push the tag to origin                                                      |
| `--since-tag`      | Compare commits since a specific tag                                        |
| `--changelog`      | Write changes to `CHANGELOG.md`                                             |
| `--pre`            | Add pre-release label (e.g. `--pre alpha.1`)                                |
| `--build`          | Add build metadata (e.g. `--build 123abc`)                                  |
| `--no-merges`      | Exclude merge commits from analysis                                         |
| `--ci`             | Enable CI mode (auto-detects push or dry-run)                               |
| `--config`         | Path to `pyproject.toml` (default: `pyproject.toml` in root)                |
| `--merge-strategy` | Override commit selection strategy (`auto`, `always`, `merge_only`)         |

💡 Alternatively, use `merge_strategy` via config – see below.

---

## 🧠 How It Works

1. Detects the latest Git tag
2. Collects commits since that tag (based on `merge_strategy`)
3. Determines bump level:
   - `feat:` → **minor**
   - `fix:` / `chore:` etc. → **patch**
   - `BREAKING CHANGE:` → **major**
4. Generates the next version
5. Optionally updates `CHANGELOG.md` and pushes the tag

If no tag is found, it starts from `0.0.0`.

---

## ⚙️ Configuration (`pyproject.toml`)

Define a `[tool.gitag]` section:

```toml
[tool.gitag]

# Optional prefix/suffix
prefix = "v"
suffix = "-rc"

# Optional regex for tag parsing
version_pattern = "^v?(\\d+)\\.(\\d+)\\.(\\d+)(?:-([\\w\\.]+))?(?:\\+([\\w\\.]+))?$"

# Merge strategy for collecting commits
merge_strategy = "auto"  # auto | always | merge_only

[tool.gitag.bump_keywords]
major = ["BREAKING CHANGE", "!:", "[MAJOR]"]
minor = ["feat:", "feature:", "[MINOR]"]
patch = ["fix:", "chore:", "docs:", "[PATCH]"]
```

📘 Full guide: [`Config.md`](./CONFIG.md)

---

## 📊 Exit Codes

| Code | Meaning                             |
|------|-------------------------------------|
| `0`  | Success                             |
| `1`  | Runtime or Git error                |
| `2`  | No commits found since last tag     |

---

## 🔁 Example GitHub Action

```yaml
name: Auto Tag

on:
  push:
    branches: [main]

jobs:
  tag:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    env:
      GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - uses: actions/setup-python@v5
        with:
          python-version: 3.11

      - name: Install tool
        run: pip install -e .[dev]

      - name: Run gitag
        run: gitag --ci --debug --changelog
```

---

## ✅ Testing

```bash
pytest
```

Tested components:

- 🔧 Version bumping
- 🧪 Commit parsing & changelog grouping
- ⚙️ CI token detection
- 🔁 Merge detection strategies
- 🛠 Config loading via `pyproject.toml`

---

## 📚 Related Files

- [`Config.md`](./Config.md) – Configuration guide
- [`default_pyproject.toml`](./default_pyproject.toml) – Example config fallback
- [`default_config.py`](./gitag/config.py) – Hardcoded defaults
- [`CHANGELOG.md`](./CHANGELOG.md) – Optional changelog output

---

## 🧠 Why?

Semantic versioning is great. But remembering to bump tags or changelogs manually? Not so much.  
This tool automates that process — reliably, consistently, and CI-friendly.

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Feedback, issues, and pull requests are welcome!  
Please read our [Contributing Guidelines](CONTRIBUTING.md) to learn how to get started. ✨
