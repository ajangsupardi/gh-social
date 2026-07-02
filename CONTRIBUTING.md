# Contributing to gh-social

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/ajangsupardi/gh-social.git
cd gh-social
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
```

## Coding Style

- Follow PEP 8
- Use type hints where practical
- Keep functions focused and small
- Write docstrings for public functions
- Use `rich` for terminal output (no raw `print` in CLI-facing code)

## Commit Messages

- Use clear, descriptive commit messages
- Start with a verb: "Add", "Fix", "Update", "Remove"
- Keep the subject line under 72 characters

## Pull Requests

1. Fork the repo and create a branch from `master`
2. Make your changes
3. Run `pytest` and make sure all tests pass
4. Write a clear PR description explaining what and why
5. Open a pull request

## Reporting Bugs

Open an issue with:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Your OS, Python version, and `gh` version

## Feature Requests

Open an issue describing:
- The problem you're trying to solve
- How you imagine the solution
- Any alternatives you considered

## Questions?

Open a [Discussion](https://github.com/ajangsupardi/gh-social/discussions) or an issue — whichever feels right.
