# Contributing to drf-routes

Thank you for taking the time to contribute! Bug fixes, new features, documentation improvements, and test coverage are all welcome.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Running the Tests](#running-the-tests)
- [Writing Tests](#writing-tests)
- [Branch Naming](#branch-naming)
- [Commit Style](#commit-style)
- [Opening a Pull Request](#opening-a-pull-request)
- [Reporting a Bug](#reporting-a-bug)
- [Project Structure](#project-structure)

---

## Getting Started

### 1. Fork the repository

Click **Fork** on [github.com/shibinshibii/drf-routes](https://github.com/shibinshibii/drf-routes), then clone your fork:

```bash
git clone https://github.com/<your-username>/drf-routes.git
cd drf-routes
```

Add the upstream remote so you can pull in future changes:

```bash
git remote add upstream https://github.com/shibinshibii/drf-routes.git
```

---

## Development Setup

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install in editable mode with dev dependencies

```bash
pip install -e ".[dev]"
```

This installs the package itself plus `pytest`, `pytest-django`, and `rich`.

For the colored table formatter:

```bash
pip install -e ".[pretty]"
```

---

## Running the Tests

```bash
# Run the full suite
pytest

# Verbose output
pytest -v

# A specific file
pytest tests/test_resolver.py -v

# Stop on first failure
pytest -x
```

All tests must pass before opening a PR.

---

## Writing Tests

All new behaviour **must** have test coverage. Add your tests to the appropriate file in `tests/`:

```
tests/
  settings.py          ← minimal Django settings used by the test suite
  urls.py              ← URL patterns used in tests
  test_resolver.py     ← tests for the URL walker & RouteInfo building
  test_inspector.py    ← tests for view introspection (methods, serializer, etc.)
  test_formatter.py    ← tests for table / JSON / markdown output
```

If you're adding a large new feature, create a new `test_<feature>.py` file.

---

## Branch Naming

Create a new branch from `main` with a descriptive name:

```bash
git checkout -b feat/html-export
git checkout -b fix/infer-app-from-module
git checkout -b docs/improve-readme
```

| Prefix | Use for |
|--------|---------|
| `feat/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation only |
| `refactor/` | Internal cleanup, no behaviour change |
| `test/` | Adding or improving tests |
| `chore/` | Tooling, CI, dependencies |

---

## Commit Style

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<optional scope>): <short description>
```

Examples:

```bash
git commit -m "feat: add HTML export format"
git commit -m "fix: infer app name from module when namespace is missing"
git commit -m "docs: expand contributing guide"
git commit -m "test: add coverage for markdown formatter"
git commit -m "refactor(inspector): extract _get_path_params helper"
```

Keep the description under 72 characters. Use the body for anything longer.

---

## Opening a Pull Request

```bash
git push origin feat/your-branch-name
```

Then open a PR against the `main` branch on GitHub.

**PR checklist:**

- [ ] The test suite passes (`pytest`)
- [ ] New behaviour is covered by tests
- [ ] Docstrings updated if you changed a function's signature or behaviour
- [ ] `README.md` updated if you added a new flag or feature
- [ ] PR description explains **what** changed and **why**
- [ ] Related issues referenced with `Fixes #<issue-number>`

A maintainer will review your PR as soon as possible. Small, focused PRs are merged faster than large ones.

---

## Reporting a Bug

Open an issue at [github.com/shibinshibii/drf-routes/issues](https://github.com/shibinshibii/drf-routes/issues).

Please include:

- Your **Python version** (`python --version`)
- Your **Django version** (`python -m django --version`)
- Your **drf-routes version** (`pip show drf-routes`)
- The **full traceback** or unexpected output
- A **minimal reproduction** — a URL conf snippet is usually enough

---

## Project Structure

```
drf-routes/
├── drf_routes/
│   ├── apps.py                        ← AppConfig
│   ├── management/
│   │   └── commands/
│   │       └── routes.py              ← The management command
│   └── utils/
│       ├── resolver.py                ← URL tree walker, RouteInfo dataclass
│       ├── inspector.py               ← View introspection (methods, serializer, etc.)
│       ├── formatter.py               ← Rich table + plain ASCII + entry point
│       └── formatter_md.py            ← Markdown API doc generator
├── tests/
│   ├── settings.py                    ← Minimal Django settings for tests
│   ├── urls.py                        ← Test URL patterns
│   ├── test_resolver.py
│   ├── test_inspector.py
│   └── test_formatter.py
├── pyproject.toml
├── README.md
└── CONTRIBUTING.md                    ← You are here
```

---

## Questions?

Open a [GitHub Discussion](https://github.com/shibinshibii/drf-routes/discussions) or file an issue — happy to help.
