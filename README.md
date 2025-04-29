# 🚀 gitag

<p align="center">
  <img src="https://raw.githubusercontent.com/henrymanke/gitag/main/assets/gitag.svg" alt="gitag logo" width="180"/>
</p>

**gitag** is a modern CLI tool that parses commit messages following [Conventional Commits](https://www.conventionalcommits.org/) and applies [Semantic Versioning](https://semver.org/) automatically — perfect for CI/CD pipelines.

| Commit Pattern                                                                                  | Bump Level | Version Change     |
|-------------------------------------------------------------------------------------------------|------------|--------------------|
| `!:`, `BREAKING CHANGE:`                                                                       | **major**  | `1.2.3` → `2.0.0`  |
| `feat(...)`, `feature(...)`                                                                    | **minor**  | `1.2.3` → `1.3.0`  |
| `fix(...)`, `perf(...)`, `refactor(...)`, `docs(...)`, `style(...)`, `chore(...)`, `test(...)`,<br>`ci(...)`, `build(...)` | **patch**  | `1.2.3` → `1.2.4`  |

---

## 📖 Table of Contents

- [⚡ Quickstart](https://github.com/henrymanke/gitag/blob/main/README.md#quickstart)
- [✨ Features](https://github.com/henrymanke/gitag/blob/main/README.md#features)
- [🛠️ Commit Mapping & Version Bumps](https://github.com/henrymanke/gitag/blob/main/README.md#commit-mapping--version-bumps)
- [📦 Installation](https://github.com/henrymanke/gitag/blob/main/README.md#installation)
- [🔧 CLI Reference](https://github.com/henrymanke/gitag/blob/main/README.md#cli-reference)
- [🤖 GitHub Actions Example](https://github.com/henrymanke/gitag/blob/main/README.md#github-actions-example)
- [⚙️ Configuration](https://github.com/henrymanke/gitag/blob/main/README.md#configuration)
- [📚 Deep Dive Documentation](https://github.com/henrymanke/gitag/blob/main/README.md#deep-dive-documentation)
- [🤝 Contributing & 📄 License](https://github.com/henrymanke/gitag/blob/main/README.md#contributing---license)

---

## Quickstart

1. **Install** 📦

   ```bash
   pip install gitag
   ```

2. **Preview tag** 🔍

   ```bash
   gitag --dry-run
   ```

3. **Tag & Changelog** 🔁

   ```bash
   gitag --ci --changelog
   ```

For development:

```bash
git clone https://github.com/henrymanke/gitag.git
cd gitag
pip install -e .[dev]
```

---

## Features

- ✅ Semantic Versioning (major, minor, patch)
- 🔍 Detect latest Git tag
- 🧠 Commit-based bump detection via Conventional Commits
- 📄 (BETA) Optional CHANGELOG.md generation
- 🔁 Dry-run & CI modes
- 🚀 Push tags via `GITHUB_TOKEN`
- ⚙️ Configurable via `pyproject.toml`
- 🔀 Flexible merge commit strategies
- 🧪 100% tested with pytest and mocks

---

## Commit Mapping & Version Bumps

| Commit Type          | Bump Level | Example                             | Spec Reference  |
|----------------------|------------|-------------------------------------|-----------------|
| `BREAKING CHANGE:`   | **major**  | `BREAKING CHANGE: update API method` | [SemVer](https://semver.org/#spec-item-4) |
| `feat:` / `feature:` | **minor**  | `feat: add new export feature`      | [Conventional Commits](https://www.conventionalcommits.org/) |
| `fix:` / `chore:`     | **patch**  | `fix: correct typo in docs`         | [Conventional Commits](https://www.conventionalcommits.org/) |

---

## Installation

Install from PyPI:

```bash
pip install gitag
```

Or install for development:

```bash
git clone https://github.com/henrymanke/gitag.git
cd gitag
pip install -e .[dev]
```

---

## CLI Reference

| Command            | Description                                         |
|--------------------|-----------------------------------------------------|
| `--dry-run`        | Preview the next tag without applying it            |
| `--changelog`      | Generate or update CHANGELOG.md                     |
| `--push`           | Push the new tag to the remote repository           |
| `--pre <label>`    | Add a pre-release label (e.g. `alpha.1`)            |
| `--build <meta>`   | Include build metadata (e.g. `123abc`)              |
| `--config <path>`  | Path to pyproject.toml (default: project root)      |
| `--merge-strategy` | Override bump strategy (`auto`, `always`, `merge_only`) |

See [Advanced CLI Options](<https://github.com/henrymanke/gitag/blob/main/docs/CONFIG.md#cli-options>) for full list.

---

## GitHub Actions Example

Save as `.github/workflows/auto-tag.yml`:

```yaml
name: Auto Tag

on:
  push:
    branches: [main]

jobs:
  tag:
    runs-on: ubuntu-latest

    # Allow this workflow to push tags and artifacts
    permissions:
      contents: write

    # GitHub token for pushing tags and uploading artifacts
    env:
      GH_TOKEN: ${{ secrets.GITHUB_TOKEN }} # or use a personal token for cross-repo support

    steps:
      # 1. Checkout the full repository (including all tags and history)
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0          # Needed to find the latest tag
          token: ${{ env.GH_TOKEN }}

      # 2. Set up Python 3.11 environment
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      # 3. Install the gitag CLI tool
      - name: Install gitag
        run: pip install gitag

      # 4. Run gitag in CI mode and generate the changelog
      - name: Run gitag (CI mode + changelog)
        run: gitag --ci --debug --changelog

      # 5. Upload the generated CHANGELOG.md as a build artifact
      - name: Upload generated changelog
        uses: actions/upload-artifact@v4
        with:
          name: changelog
          path: CHANGELOG.md
```

Commit and push — workflow runs on every push to `main`.

---

## Configuration

Add to `pyproject.toml`:

```toml
[tool.gitag]
prefix = "v"
merge_strategy = "auto"

[tool.gitag.bump_keywords]
major = ["BREAKING CHANGE"]
minor = ["feat:"]
patch = ["fix:"]
```

See [Config Reference](https://github.com/henrymanke/gitag/blob/main/docs/CONFIG.md) for details.

---

## Deep Dive Documentation

- [Config Reference](https://github.com/henrymanke/gitag/blob/main/docs/CONFIG.md)
- [CHANGELOG Guide](https://github.com/henrymanke/gitag/blob/main/docs/CHANGELOG.md)
- [Default Config](https://github.com/henrymanke/gitag/blob/main/default_pyproject.toml)
- [Architecture Overview](https://github.com/henrymanke/gitag/blob/main/docs/ARCHITECTURE.md)

---

## Contributing &  License

Contributions are welcome! Read [CONTRIBUTING.md](docs/CONTRIBUTING.md).  

Licensed under the MIT License — see [LICENSE](LICENSE) for details.
