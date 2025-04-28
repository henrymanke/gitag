# CONTRIBUTING.md

Thank you for your interest in contributing to **gitag**! To ensure a smooth review and integration process, please follow these steps:

## 1. Open an Issue

- Search the [Issue tracker](https://github.com/henrymanke/gitag/issues) to see if your bug report, feature request, or question already exists.
- If not, open a new issue and provide:
  - A concise title.
  - A clear description of the problem or suggestion.
  - Steps to reproduce (for bugs), expected vs. actual behavior.
  - Environment details (OS, Python version, logs, etc.).

## 2. Fork & Create a Branch

```bash
# Fork the repository via GitHub, then clone your fork:
git clone https://github.com/YOUR-USERNAME/gitag.git
cd gitag
# Create a descriptive branch name:
git checkout -b feature/awesome-feature
```

## 3. Code Style & Testing

- **Formatting:** Run `black .` to format your code.
- **Linting:** Run `flake8` and ensure there are no warnings.
- **Docstrings:** Follow PEP 257 conventions.
- **Type Hints:** Add PEP 484 type hints where appropriate.
- **Tests:** Add or update tests under `tests/` using `pytest`.
  - Aim for > 100% coverage (core functionality should be fully covered).

## 4. Commit Messages

- Use [Conventional Commits](https://www.conventionalcommits.org/) format:

  ```
  feat(parser): support prerelease tags
  fix(cli): handle missing Git token gracefully
  ```

- Reference issues in commit messages, e.g., `Closes #42`.

## 5. Push & Create a Pull Request

```bash
git push origin feature/awesome-feature
```  

- Open a Pull Request against the `main` branch of the upstream repo.
- Select the “Pull Request” template and describe your changes.
- Wait for at least one approval and all CI checks to pass.

## 6. Review Process

- A maintainer will review your PR. They may request changes.
- Once approved, your changes will be merged.

Thank you for helping make **gitag** better! 🎉
