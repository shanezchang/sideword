# Word books / 词库

The installed application contains a 30-word original demo. Your own books live
in the data directory, never inside the Python package:

```text
~/.local/share/sideword/books/work.json
```

The filename becomes the book ID. UTF-8 JSON format:

```json
[
  {
    "name": "prepare",
    "ukphone": "prɪˈpeə",
    "trans": ["v. 提前准备"],
    "example": {
      "en": "We prepare our notes before the meeting.",
      "zh": "我们在开会前准备笔记。",
      "phrase": "prepare notes — 准备笔记"
    }
  }
]
```

```sh
sideword --check
sideword --list-books
sideword --book work
```

`name` and a non-empty string list `trans` are required. `ukphone`, `usphone` and
`example` are optional. If provided, an example has string fields `en`, `zh`,
`phrase`. Duplicate normalized headwords merge definitions; the first entry's
other fields are retained. Matching words can use bundled original examples.

`sample` is reserved. Book IDs must be unique. Invalid data produces a readable
error, not a partially imported book. Each book has independent progress, so keep
the filename stable when updating it.

## Existing installations

The legacy filenames `IELTS_3_T.json` and `IELTSVocabularyBible.json` map to `ielts`
and `bible`, preserving the existing progress identifiers. Copy these files into
the user `books/` directory if you already have the right to use them. The old
SQLite database remains compatible and stays in place.

The public repository does not redistribute those dictionaries. An open-source
application license does not automatically license imported教材、例句或录音。
Only import material you have permission to use; do not commit private books.
See [provenance](sources.md) for the bundled content's origin.
