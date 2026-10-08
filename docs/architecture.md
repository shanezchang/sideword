# Architecture

Sideword is a local application, not a client for a hosted learning service.
The smallest useful boundaries are package resources, domain rules, persistence,
operating-system integration and presentation.

```text
src/sideword/
├── cli.py            Arguments, diagnostics, composition and exit status
├── config.py         User data paths and preference validation
├── vocabulary.py     Book discovery, validation and normalized entries
├── learning.py       Pure, time-injected review policy
├── storage.py        SQLite transactions, sessions and additive migrations
├── audio.py          Cancellable macOS synthesis, playback and cache
├── data/             Original demo resources included in the wheel
└── ui/
    ├── app.py        Keyboard state machine and screen lifecycle
    ├── views.py      Curses rendering, with no SQL or subprocess calls
    ├── text.py       Display-width-aware Chinese/IPA wrapping
    └── brand.py      ASCII mark and wordmark
```

`cli` composes the library, store and terminal controller. The controller calls
the store and audio adapter; views inspect its state and render. Storage applies
the pure review policy inside transactions. The policy knows nothing about the
terminal, SQLite or speech. Vocabulary reads bundled resources with
`importlib.resources`, so source checkouts and installed wheels behave alike.

## State and compatibility

SQLite keeps stable book/headword keys. A viewed word, a familiarity judgment and
a spelling result are distinct records. Reviewing saves both the new due date
and an event in one transaction. Saved learning queues reconcile with remembered
words without reshuffling the remaining order on every launch.

The v0.2 database is retained; schema changes are additive. Package installation
never writes into a user's data directory. Imported books and cached audio live
outside the installed code. The one-time legacy preference migration is retained
for compatibility; subsequent user choices are not overwritten.

## Why Python and uv?

The existing application is small, I/O-bound and built from the standard library.
Rewriting it in Rust or Go would add migration risk without addressing the current
problems: packaging, module ownership, validation and reproducible development.
uv manages the interpreter, project environment, lockfile and isolated command
installation. Python 3.14 is the default; 3.12–3.14 are tested in CI.

Reference projects: [Hatch](https://github.com/pypa/hatch) for explicit package and
test boundaries, [Textual](https://github.com/Textualize/textual) for separating
application code, examples and documentation, and [uv's project guide](https://docs.astral.sh/uv/guides/projects/)
for the environment workflow. We borrow conventions, not their implementation
or their framework complexity.

## Scope

No cloud sync, account layer, background reminder daemon or plugin framework.
The UI remains intentionally small; pronunciation is macOS-only. Scheduling is a
documented heuristic, not a fitted forgetting model. The public demo is not a
complete IELTS curriculum. These are explicit limits, not hidden dependencies.
