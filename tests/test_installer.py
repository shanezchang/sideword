"""Exercise the real installer with a fake bundle and a disposable home."""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def executable(path, text):
    path.write_text(text)
    path.chmod(0o755)


@pytest.fixture
def installation(tmp_path):
    home = tmp_path / "home with spaces"
    home.mkdir()
    bundle = tmp_path / "Sideword"
    (bundle / "sideword").mkdir(parents=True)
    executable(bundle / "sideword/sideword", '#!/bin/sh\necho "sideword test"\n')
    (bundle / "Start.command").write_text((ROOT / "packaging/macos/Start.command").read_text())
    commands = tmp_path / "commands"
    commands.mkdir()
    executable(commands / "uname", '#!/bin/sh\n[ "$1" = -s ] && echo Darwin || echo arm64\n')
    executable(commands / "id", "#!/bin/sh\necho 501\n")
    executable(commands / "sw_vers", "#!/bin/sh\necho 14.0\n")
    executable(commands / "ditto", '#!/bin/sh\ncp -R "$1/." "$2/"\n')
    env = {**os.environ, "HOME": str(home), "SHELL": "/bin/zsh", "TMPDIR": str(tmp_path)}
    env.pop("ZDOTDIR", None)
    env["PATH"] = f"{commands}:/usr/bin:/bin"

    def run(*args):
        return subprocess.run(
            ["/bin/bash", str(ROOT / "scripts/install.sh"), "--local", str(bundle), *args],
            env=env,
            capture_output=True,
            text=True,
        )

    return home, bundle, env, run


def test_install_and_upgrade_preserve_data_and_profile(installation):
    home, _, _, run = installation
    data = home / ".local/share/sideword"
    data.mkdir(parents=True)
    (data / "progress.sqlite3").write_bytes(b"untouched progress")
    (home / ".zshrc").write_text("# existing settings\n")
    first = run()
    assert first.returncode == 0, first.stderr
    link = home / ".local/bin/sideword"
    old_target = link.resolve()
    assert old_target.is_file()
    second = run()
    assert second.returncode == 0, second.stderr
    assert link.resolve() != old_target
    assert old_target.exists()
    assert (data / "progress.sqlite3").read_bytes() == b"untouched progress"
    assert (home / ".zshrc").read_text().count("# Sideword PATH") == 1
    assert (home / ".zshrc").read_text().startswith("# existing settings")
    assert os.access(home / "Applications/Sideword.command", os.X_OK)


def test_existing_uv_symlink_is_backed_up_not_followed(installation, tmp_path):
    home, _, _, run = installation
    original = tmp_path / "uv-sideword"
    original.write_text("original")
    link = home / ".local/bin/sideword"
    link.parent.mkdir(parents=True)
    link.symlink_to(original)
    result = run("--no-modify-path")
    assert result.returncode == 0, result.stderr
    assert original.read_text() == "original"
    backups = list((home / ".local/opt/sideword/backups").glob("*/sideword"))
    assert len(backups) == 1 and backups[0].is_symlink()
    assert backups[0].resolve() == original
    assert not (home / ".zshrc").exists()


def test_broken_bundle_never_replaces_installation(installation):
    home, bundle, _, run = installation
    assert run().returncode == 0
    link = home / ".local/bin/sideword"
    previous = link.resolve()
    executable(bundle / "sideword/sideword", "#!/bin/sh\nexit 1\n")
    assert run().returncode != 0
    assert link.resolve() == previous


def test_rejects_unsupported_architecture(installation):
    home, _, env, run = installation
    commands = Path(env["PATH"].split(":")[0])
    executable(commands / "uname", '#!/bin/sh\n[ "$1" = -s ] && echo Darwin || echo x86_64\n')
    result = run()
    assert result.returncode != 0
    assert "Apple Silicon" in result.stderr
    assert not (home / ".local").exists()


def test_respects_zdotdir(installation, tmp_path):
    _, _, env, run = installation
    config = tmp_path / "custom zsh"
    config.mkdir()
    env["ZDOTDIR"] = str(config)
    assert run().returncode == 0
    assert "# Sideword PATH" in (config / ".zshrc").read_text()


def test_checksum_mismatch_stops_before_install(installation):
    home, _, env, _ = installation
    commands = Path(env["PATH"].split(":")[0])
    # A fake transport supplies a validly shaped, but incorrect checksum.
    executable(
        commands / "curl",
        """#!/bin/bash
while [ "$#" -gt 0 ]; do
    case "$1" in
        *SHA256SUMS) manifest=1 ;;
        -o) shift; destination=$1 ;;
    esac
    shift
done
if [ "${manifest:-0}" = 1 ]; then
    printf '%064d  sideword-macos-arm64.zip\\n' 0 > "$destination"
else
    printf 'corrupt archive' > "$destination"
fi
""",
    )
    result = subprocess.run(
        ["/bin/bash", str(ROOT / "scripts/install.sh")],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Checksum mismatch" in result.stderr
    assert not (home / ".local").exists()


def test_old_macos_fails_before_install(installation):
    home, _, env, run = installation
    commands = Path(env["PATH"].split(":")[0])
    executable(commands / "sw_vers", "#!/bin/sh\necho 13.7\n")
    result = run()
    assert result.returncode != 0
    assert "macOS 14" in result.stderr
    assert not (home / ".local").exists()
