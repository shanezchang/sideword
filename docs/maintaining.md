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
