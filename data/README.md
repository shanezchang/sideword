# Vocabulary format

The public demo consists of `sample.json` and `examples.json`. Each word row has:

```json
{"name": "prepare", "ukphone": "prɪˈpeə", "trans": ["v. 提前准备"]}
```

Required: non-empty `name` and a non-empty list of Chinese meanings in `trans`.
Optional: `ukphone`, `usphone`. `examples.json` maps normalized lowercase headwords
to objects with `en`, `zh`, and `phrase`. Missing audio, IPA or examples do not prevent
learning. Demo mode selects the headwords present in both sample and example files.

The current loader recognizes two optional local books:

| Local filename | CLI selector |
| --- | --- |
| IELTS_3_T.json | `--book ielts` |
| IELTSVocabularyBible.json | `--book bible` |

Place compatible JSON arrays in this directory only if you have the right to use
them. They are ignored by Git and intentionally absent from public releases.
The UI book names describe the original private datasets; counts in the active
learning queue reflect the loaded data. Duplicate normalized headwords merge
definitions. Each book has separate learning records.

Run `python3 app.py --check` after adding a file. This is a prototype loader, not a
general import wizard. Do not commit private datasets, caches or progress records.
