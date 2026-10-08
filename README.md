<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/wordmark-dark.svg">
  <img src="docs/assets/wordmark.svg" alt="Sideword" width="352">
</picture>

A quiet place for words. Learn English without leaving your terminal.

[Website](https://sideword.vercel.app/) · [中文](README.zh-CN.md) · [Guide](docs/guide.md) · [Word books](docs/word-books.md) · [Contributing](CONTRIBUTING.md)

![Sideword's five-word learning view](docs/assets/preview.svg)

Read a few words. Listen to one. Come back when it's time.

Sideword pairs English words with IPA, Chinese meanings and bilingual examples.
It keeps your place, hides words you've remembered, and brings them back for
spaced review. No account, server, telemetry or network connection during study.

## Start here

**One-command Mac install** (Apple Silicon, macOS 14+; no Python or uv needed):

```sh
curl --proto '=https' --tlsv1.2 -fsSL https://github.com/shanezchang/sideword/releases/download/v0.4.0-beta.1/install.sh | /bin/bash
```

Open a new terminal and run `sideword`, or launch `~/.local/bin/sideword` immediately.
Prefer a download? [Get the ZIP](https://github.com/shanezchang/sideword/releases/tag/v0.4.0-beta.1),
extract it, then double-click `Install.command`.

This is an **unnotarized preview**. macOS may require explicit approval to open it;
do not disable system security. [Installation details and uninstall](docs/install-macos.md).

### Source install / Linux / developers

With [uv](https://docs.astral.sh/uv/getting-started/installation/) installed:

```sh
git clone https://github.com/shanezchang/sideword.git
cd sideword
uv run sideword
```

uv manages Python and the environment. The project defaults to Python 3.14 and
supports 3.12+. macOS and Linux are supported; pronunciation currently uses macOS
system voices. The interface is Chinese, for learners of English.

Want a command available anywhere?

```sh
uv tool install --python 3.14 git+https://github.com/shanezchang/sideword.git
sideword --page-size 10
```

Not published on PyPI. The command above installs this repository directly.

## A small, deliberate learning loop

- **Read first.** Choose any page size. Open a word for full context.
- **Listen with focus.** Only the selected word speaks; switch accents or turn sound off.
- **Recall later.** Mark a word remembered to remove it from daily learning, not from review.
- **Pick up where you left off.** Your order, preferences and progress stay on your machine.

`↑↓` select · `←→` change page · `Enter` details · `Space` pronounce<br>
`1 / 2` not yet / remembered · `M` page size · `R` review · `?` help

Start silently with `sideword --quiet`. Default autoplay is British English.
Reviews stay single-word and reveal the answer only when you ask.

## Bring your own words

The public edition includes **30 original example words**, not a complete IELTS
course. Drop compatible JSON books into `~/.local/share/sideword/books/`, then
run `sideword --list-books`. [Format and provenance →](docs/word-books.md)

Progress lives beside your books in SQLite. Updating the application does not
replace it. `--data-dir` and `XDG_DATA_HOME` support custom locations.

## Built to stay small

Python, curses and SQLite; no third-party runtime dependencies.
uv manages development, locking and builds. [Architecture](docs/architecture.md)
explains the boundaries; [Contributing](CONTRIBUTING.md) covers local checks.

MIT-licensed code and original demo content. Imported dictionaries retain their
own terms. Sideword is independent of IELTS and any commercial learning app.
