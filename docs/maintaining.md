# Maintenance and release checks

Work from this public repository. The private prototype's history contains
third-party dictionaries and must never be merged or force-pushed here.

```sh
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv build --no-sources
```

Inspect the wheel and source archive before tagging a release: only original demo
data belongs under `src/sideword/data/`. User books, caches and SQLite files must
remain outside tracked source.

Push a reviewed commit to `main`, then check GitHub Actions on that exact commit.
CI installs the built wheel in an isolated environment and validates its resources.
Do not publish a release with failing checks. Update `CHANGELOG.md` and the
version in `pyproject.toml` together. Refresh the lockfile with `uv lock`.

```sh
git push origin main
gh run list --repo shanezchang/sideword
```

The repository is public; no PyPI package or automated PyPI publishing is configured.
A published source repository is not the same thing as a verified native binary.
Manual audible playback and visual acceptance still require a real terminal.

## macOS preview bundles

`macOS preview` builds on an Apple Silicon macOS 14 runner, verifies a user-local
install without Python on PATH, and exercises the frozen curses UI in a PTY.
It uploads artifacts; it **does not automatically publish** a release.

Local reproduction on Apple Silicon:

```sh
uv sync --locked --group bundle
uv run --frozen --group bundle python scripts/build_macos.py
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
