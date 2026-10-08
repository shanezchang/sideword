# Contributing

Keep the runtime standard-library-only and offline. Prefer small, focused changes.
Run `python3 -m unittest -v` before submitting a pull request. Add regression tests
for scheduling, data migration and keyboard behavior; use temporary databases and
mock audio. Never overwrite a user's learning history during a migration.

For bugs, include Python version, OS, terminal dimensions, reproduction steps and
the command you ran. Do not upload your progress database, credentials or private
vocabulary files. For audio problems, include redacted `--audio-check` output.

New dictionary content must include clear provenance and redistribution rights.
Do not copy textbook definitions, examples or recordings without permission.
Generated examples should be labeled and reviewed for language quality.

Changes to the code and original demo content are contributed under the MIT license.
