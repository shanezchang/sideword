# Sideword web fonts

Maple Mono v7.9 (internal version 7.900), licensed under `OFL-Maple.txt`.
The official license specifies no Reserved Font Name. Copyright, names and
license metadata are preserved when subsetting and converting CN to WOFF2.

- `maple-latin.woff2`: unmodified [official variable WOFF2](https://github.com/subframe7536/maple-font/blob/v7.9/woff2/var/MapleMono%5Bwght%5D-VF.woff2), upright weights 100–800.
- `maple-cn-{400,600,700}.woff2`: subsets of the corresponding upright
  Regular/SemiBold/Bold TTFs in the [official v7.9 CN archive](https://github.com/subframe7536/maple-font/releases/download/v7.9/MapleMono-CN-unhinted.zip).

`manifest.json` records exact input/output SHA-256, sizes and coverage. The CN
vocabulary comes from this site's bilingual content, demo states, no-JS/404 copy
and controls in the four listed source files, independently of other sites.
`maple-cn.css` restricts each face to that vocabulary. Unknown Chinese, symbols
or IPA absent from Maple retain the explicit platform fallbacks. No `local()`
source, font CDN, desktop TTF or Nerd Font is shipped.

Only the Latin face is preloaded. All faces use `font-display: swap`. The static
build copies committed assets; no Python or network font build is required.
After editing public text, regenerate from the original verified TTFs:

```sh
cd site
uv run scripts/subset-maple.py --source-dir /path/to/extracted-CN-fonts
npx prettier --write public/fonts/manifest.json
```

Regenerate the English share card with `node render-assets.mjs`. Its text uses
the same Latin file; the existing vector mark and icon are retained.
