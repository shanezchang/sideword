# Maintenance and release checks

Work from this public repository. The private prototype's history contains
third-party dictionaries and must never be merged or force-pushed here.

```sh
uv sync --locked --group build --no-install-project
uv sync --locked --group build --no-build-isolation --offline
uv run --frozen --group build python scripts/check_build_lock.py tests.yml
uv run --frozen --group build ruff check .
uv run --frozen --group build ruff format --check .
uv run --frozen --group build pytest
uv build --no-sources --no-build-isolation
```

Inspect the wheel and source archive before tagging a release: only original demo
data belongs under `src/sideword/data/`. User books, caches and SQLite files must
remain outside tracked source.

Merge a reviewed PR only after its required checks pass, then check GitHub Actions
on the exact `main` commit.
CI installs the built wheel in an isolated environment and validates its resources.
Do not publish a release with failing checks. Update `CHANGELOG.md` and the
version in `pyproject.toml` together. Refresh the lockfile with `uv lock`.

```sh
gh pr checks --repo shanezchang/sideword
gh run list --repo shanezchang/sideword
```

Required branch checks retain these names: `quality`, `verify`, and
`test (ubuntu-latest, 3.12/3.13/3.14)` / `test (macos-14, 3.12/3.13/3.14)`
(one job for each Python version). Release artifacts additionally require `bundle`.
All Actions are pinned to full commits; review upstream before changing a pin.
Use both sync steps, in order, in a fresh environment. The first installs the
locked `build` group without executing the project's backend. That group includes
Hatchling, its transitive dependencies and `editables`, requested dynamically by
Hatchling's editable hook. The second installs the project offline with isolation
disabled, using that prepared environment. A plain `uv sync --locked` does **not**
lock isolated backend resolution. Keep the build group installed for subsequent
wheel/sdist builds with `--no-build-isolation`.

`check_build_lock.py` replays the actual workflow sync steps in disposable homes
and virtual environments, offline using the wheels already in uv's cache. It
delegates to the real Hatch editable hooks and checks their complete dependency
closure, installed versions and loaded-module paths against the lock/environment.
This is an offline behavioral regression, not a cold-download or remote-runner test.

Main protection and the eight matching Vercel production Deployment Checks are
configured; the first end-to-end failing-check block still needs operator evidence.
Do not rename checks without updating both systems, bypass a failed check, force
promote, or treat a deployment build as proof that production checks passed.
Native releases remain manual: verify all jobs on the exact release SHA first.

The repository is public; no PyPI package or automated PyPI publishing is configured.
A published source repository is not the same thing as a verified native binary.
Manual audible playback and visual acceptance still require a real terminal.

## macOS preview bundles

`macOS preview` builds on an Apple Silicon macOS 14 runner, verifies a user-local
install without Python on PATH, and exercises the frozen curses UI in a PTY.
It uploads artifacts; it **does not automatically publish** a release.
The PTY check rates a sample word, saves page size/order, exits and resumes; it
is quiet by design and does not establish audible pronunciation quality.

Local reproduction on Apple Silicon:

```sh
uv sync --locked --group build --group bundle --no-install-project
uv sync --locked --group build --group bundle --no-build-isolation --offline
uv run --frozen --group build python scripts/check_build_lock.py macos-preview.yml
uv run --frozen --group build --group bundle python scripts/build_macos.py
```

Before publishing, wait for both CI and macOS preview on the exact commit. Download
the successful workflow's artifact, inspect its archive and SHA256SUMS, then create
a prerelease with `sideword-macos-arm64.zip`, `SHA256SUMS`, and `install.sh` attached.
Use the CI artifact, not a build made on a newer local macOS. Update the pinned tag
in `scripts/install.sh`, both READMEs and `docs/install-macos.md` for each release.
The package version uses PEP 440 (`0.4.0b1`); its Git tag is `v0.4.0-beta.1`.

The current bundle is ad-hoc signed, **not Developer ID signed or notarized**.
Do not claim frictionless Finder installation or publish a security-bypass command.
Keep that limitation prominent until signing, notarization and quarantined-download
acceptance have been verified. Do not put signing credentials in this repository.

The installer never edits the data directory. It preserves old binary versions and
backs up replaced launchers and shell settings under `~/.local/opt/sideword/backups/`.
The source/PyPI package and the standalone native bundle are separate products;
only the latter contains a Python interpreter and its license notices.

## Lifecycle acceptance before a new preview

Use a disposable HOME, XDG data/config/cache directories, TMPDIR and ZDOTDIR; never
point acceptance runs at your daily command, books or learning database. With the
30-word original sample, install the existing release, read/hear a selected word,
rate it, change a preference, exit and resume. Install the candidate into that same
isolated HOME, then restore the printed launcher backup using `docs/install-macos.md`.
At each step check the running binary/version, selected word, queue, preferences and
review row; a ZIP hash alone is insufficient. Check uninstall while retaining data.
Run `scripts/smoke_terminal.py <installed-command>` for repeatable quiet PTY coverage.
For pronunciation, verify real `say`/`afplay` calls and a nonempty AIFF; volume-zero
playback does not establish human-audible clarity. Record that separately.

There is currently one published preview, `v0.4.0-beta.1`. Reinstalling it or swapping
a locally rebuilt `0.4.0b1` is not evidence of a cross-version schema migration.
Do not manufacture a new version merely to label that test an upgrade. Runtime or
installer fixes need a newly reviewed preview; docs, website and CI changes alone
do not require replacing an existing immutable release asset. Publish before
pointing public install links at a new tag, and retain the previous asset for rollback.

Security reports go to the [private channel](../SECURITY.md), not public issue attachments.
