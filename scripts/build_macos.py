"""Build the Apple Silicon preview; run with `uv run --group bundle ...`."""

import hashlib
import importlib.metadata
import platform
import shutil
import subprocess
import sys
import sysconfig
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build() -> Path:
    if (platform.system(), platform.machine()) != ("Darwin", "arm64"):
        raise SystemExit("Build on an Apple Silicon Mac (not under Rosetta).")
    output = ROOT / "dist" / "macos"
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sideword-build-") as temp:
        work = Path(temp)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--noconfirm",
                "--clean",
                "--onedir",
                "--console",
                "--name=sideword",
                "--target-architecture=arm64",
                "--collect-data=sideword",
                "--copy-metadata=sideword",
                f"--distpath={work / 'Sideword'}",
                f"--workpath={work / 'build'}",
                f"--specpath={work}",
                str(ROOT / "packaging/macos/entry.py"),
            ],
            cwd=ROOT,
            check=True,
        )
        bundle = work / "Sideword"
        for name in ("Install.command", "Start.command"):
            shutil.copy2(ROOT / "packaging/macos" / name, bundle / name)
            (bundle / name).chmod(0o755)
        shutil.copy2(ROOT / "scripts/install.sh", bundle / "install.sh")
        shutil.copy2(ROOT / "LICENSE", bundle / "LICENSE")
        shutil.copy2(ROOT / "docs/install-macos.md", bundle / "README.md")
        # Runtime license notices travel with the executable, including after install.
        notices = bundle / "sideword" / "licenses"
        shutil.copytree(ROOT / "packaging/macos/licenses", notices)
        shutil.copy2(ROOT / "LICENSE", notices / "Sideword.txt")
        shutil.copy2(Path(sysconfig.get_path("stdlib")) / "LICENSE.txt", notices / "Python.txt")
        distribution = importlib.metadata.distribution("pyinstaller")
        for file in distribution.files or []:
            if str(file).endswith("licenses/COPYING.txt"):
                shutil.copy2(distribution.locate_file(file), notices / "PyInstaller.txt")
        # Do not distribute editable-install metadata containing developer paths.
        for metadata in bundle.glob("sideword/_internal/sideword-*.dist-info"):
            for name in ("direct_url.json", "uv_cache.json", "uv_build.json", "RECORD"):
                (metadata / name).unlink(missing_ok=True)
        for flag in ("--version", "--check"):
            subprocess.run(
                [str(bundle / "sideword/sideword"), "--data-dir", str(work / "data"), flag],
                cwd=work,
                check=True,
            )
        archive = output / "sideword-macos-arm64.zip"
        subprocess.run(
            [
                "ditto",
                "--norsrc",
                "--noextattr",
                "-c",
                "-k",
                "--keepParent",
                str(bundle),
                str(archive),
            ],
            check=True,
        )
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    (output / "SHA256SUMS").write_text(f"{digest}  {archive.name}\n")
    shutil.copy2(ROOT / "scripts/install.sh", output / "install.sh")
    return archive


if __name__ == "__main__":
    print(build())
