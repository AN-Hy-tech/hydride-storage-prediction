"""Regression tests for the test tooling itself.

These exist because the collection guarantees card #69 set up are invisible: nothing about a
green run tells you that `testpaths` still limits collection to tests/, or that
`norecursedirs` still carries pytest's own defaults. The legacy-script interlock those
guarantees were first written for went with `Machine_Model/` (card #107).

Card #69.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

# tomllib is 3.11+; the pinned interpreter is 3.10.13 (docs/ENVIRONMENT.md), so fall back to
# tomli, which the Project environment already carries.
try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - depends on the interpreter, not the code
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent

@pytest.fixture(scope="module")
def pytest_config() -> dict:
    raw = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    return tomllib.loads(raw)["tool"]["pytest"]["ini_options"]


def test_testpaths_is_limited_to_the_tests_directory(pytest_config: dict) -> None:
    assert pytest_config["testpaths"] == ["tests"], (
        "testpaths must stay ['tests']. Widening it lets pytest collect files that are "
        "not part of the suite."
    )


def test_pytest_defaults_were_not_dropped_from_norecursedirs(pytest_config: dict) -> None:
    """Setting `norecursedirs` replaces pytest's defaults rather than extending them.

    Found the hard way while writing card #69: an earlier version of this config listed only
    the project's own additions, which silently dropped `.*` and made `pytest .` collect the
    vendored skill suites under `.claude/`. The defaults are re-listed in pyproject.toml and
    this asserts they stay there.
    """
    configured = set(pytest_config["norecursedirs"])
    pytest_defaults = {"*.egg", ".*", "_darcs", "build", "CVS", "dist", "node_modules", "venv", "{arch}"}
    missing = pytest_defaults - configured
    assert not missing, (
        f"norecursedirs dropped pytest's own defaults: {sorted(missing)}. "
        "The key replaces the defaults; it does not extend them."
    )


def test_collected_tests_come_only_from_this_directory(pytest_config: dict) -> None:
    """No collected module may live outside tests/ — the interlock's observable consequence."""
    tests_dir = REPO_ROOT / "tests"
    for name, module in list(sys.modules.items()):
        origin = getattr(module, "__file__", None)
        looks_like_a_test = name.startswith("test") or ".test" in name
        if not origin or not looks_like_a_test:
            continue
        path = Path(origin).resolve()
        if REPO_ROOT not in path.parents:
            continue  # site-packages and the like
        assert tests_dir in path.parents or path.parent == tests_dir, (
            f"collected test module {name} lives outside tests/: {path}"
        )


@pytest.fixture(scope="module")
def dev_extra() -> dict[str, str]:
    """The `dev` optional-dependency group, as ``{name: specifier}``."""
    raw = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    parsed = tomllib.loads(raw)["project"]["optional-dependencies"]["dev"]
    out: dict[str, str] = {}
    for entry in parsed:
        name = re.split(r"[<>=!;\[ ]", entry, maxsplit=1)[0].strip()
        out[name] = entry
    return out


@pytest.mark.parametrize("tool", ["ruff", "mypy"])
def test_the_lint_tools_are_pinned_exactly_and_agree_with_ci(dev_extra: dict, tool: str) -> None:
    """The `dev` extra and the workflow must name the same ruff and the same mypy.

    Two places install these. `.github/workflows/ci.yml`'s `hygiene` job pins them by hand,
    because the first run of that workflow failed when a floor resolved to a newer ruff that
    raised RUF100 on a `# noqa` the older one needs — the two versions are mutually
    unsatisfiable, so a floor makes the lane "a check plus whatever was released this week".
    The `suite` job installs the `dev` extra, and it runs gate HG-4, which shells out to ruff
    and mypy itself. While this extra carried floors, HG-4 could have gone red in CI against a
    version the hygiene job never runs, for a reason nobody could reproduce.

    Card #86. Bumping a version is a deliberate commit that changes both sites together.
    """
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    in_workflow = re.findall(rf'"{tool}==([0-9][^"]*)"', workflow)
    assert in_workflow, f"the ci.yml hygiene job no longer pins {tool} exactly"

    spec = dev_extra.get(tool)
    assert spec is not None, f"{tool} is no longer in the dev extra"
    assert "==" in spec, (
        f"the dev extra floors {tool} ({spec!r}) instead of pinning it. CI's suite job "
        f"installs this extra and runs gate HG-4, which runs {tool}; a floor there means the "
        f"gate is checked against whatever was released this week."
    )

    pinned = spec.split("==", 1)[1].strip()
    assert {pinned} == set(in_workflow), (
        f"the dev extra pins {tool}=={pinned} but ci.yml installs {sorted(set(in_workflow))}. "
        f"Both sites must name the same version."
    )


def test_leak_marker_is_registered(pytest_config: dict) -> None:
    """Gate HG-1's sentinels are selected by marker; an unregistered marker errors under
    --strict-markers, which is exactly how a typo would silently deselect the whole gate."""
    markers = " ".join(pytest_config["markers"])
    assert "leak:" in markers
    assert "--strict-markers" in pytest_config["addopts"]
