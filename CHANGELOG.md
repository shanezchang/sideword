# Changelog

## 0.4.0b1 — macOS installation preview

- Standalone Apple Silicon bundle with Python and original demo data included.
- One-command user-local installer, download checksum verification, and double-click installation.
- Existing launchers backed up; learning data and custom books remain untouched.
- Frozen terminal smoke test and macOS 14 bundle CI.
- Ad-hoc signed only: Developer ID signing and Apple notarization are not yet available.

## 0.3.0

- Installable `src/sideword` package and `sideword` console command.
- Python 3.12+ support, Python 3.14 default, uv environment and lockfile.
- Separate CLI, vocabulary validation, review policy, storage, audio and UI modules.
- User-owned JSON books outside the package, with stable legacy book IDs.
- `--version`, `--list-books`, and session-only `--quiet`.
- Compact `[/]` terminal identity, light/dark SVG wordmarks and concise bilingual docs.
- Lint, formatting, package-build and Python/platform tests in CI.
- Existing learning records and review intervals preserved.

## 0.2.0

- First public prototype: local learning cards, pronunciation, random learning,
  configurable pages and spaced review.
- Original 30-word demonstration content and MIT license.
