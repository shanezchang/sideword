# Sideword

Learn English from your terminal. Local-first, keyboard-driven, no account required.

[中文说明](README.zh-CN.md)

Sideword started as a way to study English during short breaks without leaving
the terminal. Read words in context first, then review them on a simple schedule.
It is a small Python application with no third-party runtime dependencies.

## Quick start

Requires Python 3.9+ and a terminal with curses support (macOS or Linux).
Windows native terminals are not supported; try WSL.

Clone the repository and run it:

```sh
git clone https://github.com/shanezchang/sideword.git
cd sideword
python3 app.py --page-size 10
# Or:
./ielts --page-size 10
```

The public edition includes 30 independently authored demonstration words, with
British IPA, Chinese explanations, bilingual examples and collocations. It does
not bundle commercial IELTS textbooks or the full vocabulary used in the author's
private installation. This is not an official IELTS product or a certified course.

## Learning, not just spelling

- Randomized learning order, saved across restarts.
- Any positive number of words per page; small terminals scroll within the page.
- One selected word controls pronunciation, familiarity and favorites.
- Remembered words leave the everyday learning list, not the review schedule.
- Reviews ask you to recall before revealing the definition and example.
- Forgotten words return to learning. Spelling practice is optional and tracked separately.
- Local SQLite progress, preferences and audio cache. No network requests or telemetry.

| Key | Action |
| --- | --- |
| Up / Down or K / J | Select a word in a multiword page |
| Left / Right or H / L | Change page; in single-word mode, change word |
| Enter | Open/close full details; reveal an answer during review |
| M | Enter any positive page size, Enter to save, Esc to cancel |
| Space / S | Speak the selected word / example sentence |
| A / V / - / X | Toggle autoplay / accent / slow speech / stop audio |
| 1 / 2 | Not yet remembered / remembered, for the selected word only |
| F / T | Toggle favorite / translated example |
| R / P / U | Due reviews / schedule / unfamiliar words |
| Tab / ? / Esc | Home / help / save and quit |

Five words per page is the default. Definitions in the list are clipped to the
terminal width; Enter opens scrollable full details. Reviews always use one word
at a time. A 80×24 terminal is recommended; the minimum is 42×15.

## A transparent review schedule

"Forgot" schedules another review in 10 minutes. "Remembered" starts at one day;
successful due reviews extend the interval to 3, 7, 14, 30 and 60 days, then repeat
every 60 days. Early repeated clicks do not advance the stage or postpone reviews.
Browsing is not a successful review. There are no background notifications.
This is a simple heuristic, not a scientifically calibrated memory prediction.

## Pronunciation

On macOS, Sideword uses local `say` synthesis and `afplay` playback. British
autoplay is enabled by default; press A for silence. Switching selection cancels
the preceding utterance. Available system voices determine pronunciation quality.
Linux supports learning but currently has no audio backend.

```sh
python3 app.py --audio-check
```

The development sandbox blocked macOS speech services, so audible playback has
not been verified there. Errors are displayed, and empty audio is not cached as a
success. The diagnostic above attempts playback on your own machine.

## Local data and custom vocabulary

Progress lives in `$XDG_DATA_HOME/sideword/progress.sqlite3`, defaulting to
`~/.local/share/sideword/progress.sqlite3`; audio is cached beside it in `audio/`.
Back up the data directory while the app is closed. Use an isolated directory to
try the application without affecting an existing installation:

```sh
python3 app.py --data-dir /tmp/sideword-demo
python3 app.py --check
python3 app.py --stats  # Optional spelling-test statistics
```

See [data/README.md](data/README.md) for the vocabulary format and optional local
word books. You must have permission to use any data you import. No downloader
for third-party dictionaries is included.

## Development

```sh
python3 -m unittest -v
python3 -m compileall -q app.py core.py speech.py
```

`app.py` handles curses interaction; `core.py` handles books, SQLite transactions
and scheduling; `speech.py` handles cancellable audio processes and cache validation.
Tests use temporary databases and mock audio rather than altering user records.
See [CONTRIBUTING.md](CONTRIBUTING.md) and [SOURCES.md](SOURCES.md).

## License

MIT for this independent implementation and its original demonstration content.
Third-party vocabulary imported by users is not relicensed by this project.
