"""Replay CI bootstrap offline in fresh homes/venvs; audit the real Hatch hooks.

Run after the selected workflow's sync has cached its locked wheels. The artifact
cache is reused, not the environment or user configuration. No network is used.
Only a disposable project's backend is wrapped; every hook delegates to Hatch.
"""

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def audit(hook):
    """Called inside the backend subprocess, not merely in the test's parent."""
    from importlib.metadata import distributions, requires, version

    import hatchling.build
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name

    root = Path.cwd()
    lock = tomllib.loads((root / "uv.lock").read_text())
    locked = {p["name"]: p["version"] for p in lock["package"]}
    config = tomllib.loads((root / "pyproject.toml").read_text())
    # no-isolation frontends may omit get_requires; still exercise the actual
    # dynamic hook and prove its full dependency closure is already installed.
    dynamic = hatchling.build.get_requires_for_build_editable()
    pending = [*config["build-system"]["requires"], *dynamic]
    closure = {}
    while pending:
        req = Requirement(pending.pop())
        if req.marker and not req.marker.evaluate():
            continue
        name = canonicalize_name(req.name)
        assert name in locked, f"Untracked backend dependency: {req}"
        installed = version(name)
        assert installed == locked[name] and installed in req.specifier, (req, installed)
        if name not in closure:
            closure[name] = installed
            pending.extend(requires(name) or [])
    installed = {canonicalize_name(d.name): d.version for d in distributions()}
    assert all(locked.get(name) == value for name, value in installed.items()), installed
    expected = root / ".venv"
    assert Path(sys.prefix) == expected, f"Backend escaped locked environment: {sys.prefix}"
    modules = {}
    for name, module in list(sys.modules.items()):
        file = getattr(module, "__file__", None)
        if file and ("site-packages" in file or "dist-packages" in file):
            assert Path(file).is_relative_to(expected), (name, file)
            modules[name] = file
    with Path(os.environ["SIDEWORD_BUILD_AUDIT"]).open("a") as stream:
        stream.write(
            json.dumps(
                {
                    "hook": hook,
                    "prefix": sys.prefix,
                    "dynamic": dynamic,
                    "closure": closure,
                    "installed": installed,
                    "loaded_modules": modules,
                }
            )
            + "\n"
        )


def get_requires_for_build_editable(config_settings=None):
    import hatchling.build

    result = hatchling.build.get_requires_for_build_editable(config_settings)
    audit("get_requires_for_build_editable")
    return result


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    import hatchling.build

    audit("before_build_editable")
    result = hatchling.build.build_editable(wheel_directory, config_settings, metadata_directory)
    audit("after_build_editable")
    return result


def bootstrap_jobs(workflow):
    """Read the literal sync steps actually run by our two workflows."""
    jobs = {}
    job = None
    for line in workflow.read_text().splitlines():
        match = re.fullmatch(r"  (\w+):", line)
        if match:
            job = match[1]
        match = re.fullmatch(r"      - run: (uv sync .+)", line)
        if match:
            jobs.setdefault(job, []).append(shlex.split(match[1]))
    expected = {"test", "quality"} if workflow.name == "tests.yml" else {"bundle"}
    assert set(jobs) == expected, f"Update the behavioral harness for changed sync steps: {jobs}"
    return jobs


def check(workflow):
    uv = shutil.which("uv")
    assert uv, "uv must be on PATH"
    cache = subprocess.check_output([uv, "cache", "dir"], text=True).strip()
    for job, commands in bootstrap_jobs(workflow).items():
        with tempfile.TemporaryDirectory(prefix="sideword-build-lock-") as directory:
            base = Path(directory)
            project = base / "project"
            project.mkdir()
            for name in ("pyproject.toml", "uv.lock", "README.md"):
                shutil.copy2(ROOT / name, project / name)
            shutil.copytree(ROOT / "src", project / "src")
            probe = project / "probe"
            probe.mkdir()
            shutil.copy2(__file__, probe / "audit_backend.py")
            config = project / "pyproject.toml"
            original = config.read_text()
            assert original.count('build-backend = "hatchling.build"') == 1
            config.write_text(
                original.replace(
                    'build-backend = "hatchling.build"',
                    'build-backend = "audit_backend"\nbackend-path = ["probe"]',
                )
            )
            audit_log = base / "hooks.jsonl"
            env = {
                "PATH": os.path.dirname(uv) + os.pathsep + os.defpath,
                "UV_CACHE_DIR": cache,
                "UV_OFFLINE": "true",
                "UV_PYTHON_DOWNLOADS": "never",
                "UV_PYTHON": sys.executable,
                "UV_PROJECT_ENVIRONMENT": str(project / ".venv"),
                "SIDEWORD_BUILD_AUDIT": str(audit_log),
                "PYTHONNOUSERSITE": "1",
            }
            for key in ("HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "TMPDIR"):
                path = base / key.lower()
                path.mkdir()
                env[key] = str(path)
            before = (project / "uv.lock").read_bytes()
            for command in commands:
                result = subprocess.run(
                    [uv, *command[1:], "-v"],
                    cwd=project,
                    env=env,
                    text=True,
                    capture_output=True,
                    timeout=180,
                )
                print(f"{workflow.name}/{job}: {shlex.join(command)}", flush=True)
                print(result.stdout + result.stderr, flush=True)
                assert result.returncode == 0, "Workflow bootstrap failed offline"
                if "--no-install-project" in command:
                    assert not audit_log.exists(), "Bootstrap executed the project backend"
            assert (project / "uv.lock").read_bytes() == before
            records = [json.loads(line) for line in audit_log.read_text().splitlines()]
            assert any(r["hook"] == "after_build_editable" for r in records)
            last = records[-1]
            assert any(name.startswith("editables") for name in last["loaded_modules"]), last
            print(json.dumps({"workflow": workflow.name, "job": job, "hooks": records}), flush=True)
            subprocess.run(
                [str(project / ".venv/bin/sideword"), "--check"],
                cwd=base,
                env=env,
                check=True,
                timeout=30,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow", choices=("tests.yml", "macos-preview.yml"))
    args = parser.parse_args()
    check(ROOT / ".github/workflows" / args.workflow)
