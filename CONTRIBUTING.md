# Contributing

Small, well-tested changes are welcome. Start a discussion in an issue for changes
to the learning model, runtime dependencies or supported platforms.

## Development

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```sh
uv sync --locked
uv run sideword --quiet
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv build
```

Python 3.14 is the development default; CI also checks 3.12 and 3.13. Runtime code
uses only the standard library. Developer dependencies are locked in `uv.lock`.
Do not edit the lockfile by hand.

## Where changes belong

- `vocabulary.py`: book discovery, validation and normalized words.
- `learning.py`: pure review policy. Supply time explicitly; do not read a database.
- `storage.py`: SQLite transactions and backward-compatible migrations.
- `audio.py`: subprocess lifecycle, cache validation and cancellation.
- `ui/app.py`: navigation and input; `ui/views.py`: rendering.
- `cli.py`: command parsing, application composition and exit codes.

See [architecture](docs/architecture.md) for the full dependency direction.
Prefer an explicit small module to a generic service layer or plugin framework.

## Tests and review

Use temporary directories and mocked audio. Add regression tests for migrations,
scheduling and keyboard changes. A window being displayed must never count as
successful recall. Preserve existing database keys when moving code.

For visual changes, regenerate the renderer preview with:

```sh
uv run python scripts/render_preview.py
```

Check small terminals and both light/dark themes. Keep content legible in
`NO_COLOR` mode. Screenshots are not a substitute for state-machine tests.

## Content and privacy

Never attach credentials, personal progress databases, private dictionaries or
audio caches. New vocabulary needs clear provenance and redistribution rights.
Do not copy textbook definitions, examples or recordings without permission.
AI-assisted examples must be labeled and checked for language quality.

Include OS, Python version, terminal dimensions and reproduction steps in bug
reports. Audio reports can include redacted `sideword --audio-check` output.

Contributions to code and original demo content are under the MIT license.
