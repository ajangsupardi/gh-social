# Changelog

All notable changes to gh-social will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [1.2.7] - 2026-07-02

### Changed
- Fixed PyPI classifiers: Production/Stable, Python 3.13, English, Utilities
- License handled via PEP 639 (pyproject.toml license field)

## [1.2.5] - 2026-07-02

### Changed
- Rewritten README as a casual intro book
- Added CI, PyPI, and license badges
- Added CONTRIBUTING.md, SECURITY.md, CHANGELOG.md, CODE_OF_CONDUCT.md
- Added issue and PR templates
- Updated PyPI description to match new README

## [1.2.4] - 2026-07-02

### Fixed
- `__version__` not updated in `__init__.py`

## [1.2.3] - 2026-07-02

### Changed
- Restore unfollow limit prompt in Interactive Mode
- Apply user-configured limit when fetching following list

## [1.2.2] - 2026-06-30

### Added
- Limit option for interactive mode
- Better error handling for API responses

## [1.2.1] - 2026-06-29

### Fixed
- Rate limit handling improvements

## [1.2.0] - 2026-06-28

### Added
- Follow stargazers feature
- Bot detection heuristics
- JSON output mode

### Changed
- Concurrent API calls with 16-thread worker pool
- Improved terminal output with `rich`

## [1.1.7] - 2026-06-25

### Fixed
- Pagination edge cases

## [1.1.6] - 2026-06-24

### Changed
- Better error messages

## [1.1.5] - 2026-06-23

### Added
- Dry-run mode

## [1.1.0] - 2026-06-20

### Added
- Interactive menu mode
- Follow back feature
- Unfollow feature

## [1.0.0] - 2026-06-15

### Added
- Initial release
