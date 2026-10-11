"""Keep required checks unconditional and dependency sources immutable."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_actions_are_pinned_to_reviewable_commits():
    for workflow in (ROOT / ".github/workflows").glob("*.yml"):
        for action in re.findall(r"uses: (\S+)", workflow.read_text()):
            assert re.fullmatch(r"[\w-]+/[\w-]+@[0-9a-f]{40}", action), action


def test_required_workflows_do_not_skip_by_changed_path():
    for name in ("tests.yml", "website.yml", "macos-preview.yml"):
        workflow = (ROOT / ".github/workflows" / name).read_text()
        assert "paths:" not in workflow
        assert "paths-ignore:" not in workflow
        assert "contents: read" in workflow
        assert "contents: write" not in workflow
        assert "pull_request_target" not in workflow
        assert "continue-on-error" not in workflow


def test_build_backend_is_in_the_frozen_environment():
    import tomllib

    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    assert "build" in config["dependency-groups"]
    assert any(package["name"] == "hatchling" for package in lock["package"])
    workflow = (ROOT / ".github/workflows/tests.yml").read_text()
    assert "uv sync --locked --group build" in workflow
    assert "uv build --no-sources --no-build-isolation" in workflow


def test_editable_hook_requirements_are_in_the_lock():
    """Ask the real backend, including its dynamic PEP 660 requirements."""
    import tomllib
    from importlib.metadata import requires

    import hatchling.build
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name

    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    versions = {package["name"]: package["version"] for package in lock["package"]}
    pending = ["hatchling", *hatchling.build.get_requires_for_build_editable()]
    checked = set()
    while pending:
        requirement = Requirement(pending.pop())
        if requirement.marker and not requirement.marker.evaluate():
            continue
        name = canonicalize_name(requirement.name)
        assert name in versions, f"Backend requirement missing from uv.lock: {requirement}"
        assert versions[name] in requirement.specifier
        if name not in checked:
            checked.add(name)
            pending.extend(requires(name) or [])
