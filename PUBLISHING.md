# Publishing checklist

This directory is a fresh, public-ready source repository. Do not push the older
private prototype: its history contains third-party dictionary files.

Before publishing:

1. Run `python3 -m unittest -v` and `python3 app.py --check`.
2. Review `git ls-files`; only original demo content belongs in `data/`.
3. Confirm the signed-in account with `gh api user --jq .login`.
4. Check whether `shanezchang/sideword` already exists. Do not overwrite it.
5. If it does not exist, create and push from this directory:

```sh
gh repo create shanezchang/sideword --public --source=. --remote=origin --push \
  --description "Offline, keyboard-first English learning in your terminal"
```

GitHub Actions is configured but has not run until the repository is actually
published. Check the run before making a release. Audible playback also needs
manual verification in a normal macOS terminal. No PyPI package is published.
