# Publishing checklist

This directory is a fresh, public-ready source repository. Do not push the older
private prototype: its history contains third-party dictionary files.

The public repository is https://github.com/shanezchang/sideword.
Before pushing updates:

1. Run `python3 -m unittest -v` and `python3 app.py --check`.
2. Review `git ls-files`; only original demo content belongs in `data/`.
3. Confirm the signed-in account with `gh api user --jq .login`.
4. Confirm `origin` points to the public repository, then push the reviewed commit:

```sh
git remote -v
git push origin main
```

GitHub Actions runs on pushes and pull requests. Check the run before making a release.
Audible playback also needs
manual verification in a normal macOS terminal. No PyPI package is published.
