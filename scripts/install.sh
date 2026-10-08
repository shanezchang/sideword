#!/bin/bash
# Sideword user-local macOS installer. No sudo; never touches learning data.
set -euo pipefail

main() {
    local source_dir='' modify_path=1
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --local) [ "$#" -ge 2 ] || die '--local needs a directory'; source_dir=$2; shift 2 ;;
            --no-modify-path) modify_path=0; shift ;;
            --help) printf 'Usage: install.sh [--local BUNDLE] [--no-modify-path]\n'; return ;;
            *) die "Unknown option: $1" ;;
        esac
    done
    [ "$(uname -s)" = Darwin ] || die 'This preview requires macOS.'
    [ "$(uname -m)" = arm64 ] || die 'This preview requires Apple Silicon. In a Rosetta terminal, open a native terminal first.'
    local macos_version
    macos_version=$(sw_vers -productVersion)
    [ "${macos_version%%.*}" -ge 14 ] || die 'This preview requires macOS 14 or newer.'
    [ "${HOME:-}" != / ] && [ -n "${HOME:-}" ] && [ -d "$HOME" ] || die 'A valid home directory is required.'
    [ "$(id -u)" -ne 0 ] || die 'Run as your own user, without sudo.'

    local tag='v0.4.0-beta.1' asset='sideword-macos-arm64.zip'
    local base="https://github.com/shanezchang/sideword/releases/download/$tag"
    local scratch
    scratch=$(mktemp -d "${TMPDIR:-/tmp}/sideword-download.XXXXXX")
    # Deliberately keep failed downloads for diagnosis; no broad recursive cleanup.
    if [ -z "$source_dir" ]; then
        printf 'Downloading Sideword %s (macOS Apple Silicon)…\n' "$tag"
        curl --proto '=https' --tlsv1.2 -fL --retry 3 "$base/$asset" -o "$scratch/$asset"
        curl --proto '=https' --tlsv1.2 -fsSL --retry 3 "$base/SHA256SUMS" -o "$scratch/SHA256SUMS"
        local expected actual
        expected=$(awk -v name="$asset" '$2 == name { print $1 }' "$scratch/SHA256SUMS")
        [[ "$expected" =~ ^[0-9a-f]{64}$ ]] || die 'Invalid checksum manifest.'
        actual=$(shasum -a 256 "$scratch/$asset" | awk '{print $1}')
        [ "$actual" = "$expected" ] || die 'Checksum mismatch; nothing installed.'
        ditto -x -k "$scratch/$asset" "$scratch/extracted"
        source_dir="$scratch/extracted/Sideword"
    fi
    [ -x "$source_dir/sideword/sideword" ] && [ -f "$source_dir/Start.command" ] || die 'Incomplete bundle.'
    printf 'Checking bundled program…\n'
    "$source_dir/sideword/sideword" --version
    "$source_dir/sideword/sideword" --data-dir "$scratch/check" --check

    local root="$HOME/.local/opt/sideword" bin="$HOME/.local/bin"
    local app="$HOME/Applications/Sideword.command" target backup
    [ ! -d "$bin/sideword" ] || die "$bin/sideword is a directory; leaving it untouched."
    [ ! -d "$app" ] || die "$app is a directory; leaving it untouched."
    mkdir -p "$root/versions" "$root/backups" "$bin" "$HOME/Applications"
    target=$(mktemp -d "$root/versions/$tag.XXXXXX")
    ditto "$source_dir/sideword" "$target"
    "$target/sideword" --data-dir "$scratch/check" --check >/dev/null

    # Preserve previous launchers, including uv-managed symlinks. Older binaries
    # are retained so a running session and manual rollback remain possible.
    backup=$(mktemp -d "$root/backups/launchers.XXXXXX")
    if [ -e "$bin/sideword" ] || [ -L "$bin/sideword" ]; then
        cp -P "$bin/sideword" "$backup/sideword"
    fi
    if [ -e "$app" ] || [ -L "$app" ]; then
        cp -P "$app" "$backup/Sideword.command"
    fi
    ln -s "$target/sideword" "$target/command-link"
    mv -f "$target/command-link" "$bin/sideword"
    cp "$source_dir/Start.command" "$target/Start.command"
    chmod +x "$target/Start.command"
    cp "$target/Start.command" "$backup/new-launcher"
    mv -f "$backup/new-launcher" "$app"

    if [ "$modify_path" -eq 1 ]; then
        local profile
        case "${SHELL:-/bin/zsh}" in
            */zsh) profile="${ZDOTDIR:-$HOME}/.zshrc" ;;
            */bash) profile="$HOME/.bash_profile" ;;
            *) profile='' ;;
        esac
        if [ -n "$profile" ]; then
            if ! grep -Fq '# Sideword PATH' "$profile" 2>/dev/null; then
                [ ! -f "$profile" ] || cp -p "$profile" "$backup/shell-profile"
                # shellcheck disable=SC2016 # Expand in the user's next shell, not now.
                printf '\n# Sideword PATH\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$profile"
            fi
        fi
    fi
    printf '\nInstalled. Open a new terminal and run: sideword\n'
    printf 'Start now: "%s/sideword"\n' "$bin"
    printf 'Or double-click: %s\n' "$app"
    printf 'Previous launchers: %s\nLearning records and books were not changed.\n' "$backup"
}

die() { printf 'sideword installer: %s\n' "$*" >&2; exit 1; }
main "$@"
