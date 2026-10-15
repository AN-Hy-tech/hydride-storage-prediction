"""Tests for the configuration loader.

The card's information-hiding claim is that changing where data lives means editing one
YAML file and nothing else. That is only true if three things hold, and each has a test
here: paths resolve against a discovered root rather than the working directory, a typo in
a key is loud rather than silent, and an out-of-range value cannot reach a caller.

Card #3.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

# Aliased: conftest also provides a `repo_root` fixture, and a test taking that fixture
# would otherwise shadow the function under test.
from hydms.config import Config, ConfigError, load
from hydms.config import repo_root as discover_repo_root

# --------------------------------------------------------------------------------------
# Loading the real configuration
# --------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def cfg() -> Config:
    return load()


def test_the_packaged_config_loads(cfg: Config) -> None:
    assert isinstance(cfg, Config)
    assert cfg.seed == 42


def test_paths_are_absolute_and_under_the_repository_root(cfg: Config) -> None:
    for name in ("raw", "interim", "processed", "splits", "artifacts", "reports"):
        path = getattr(cfg.paths, name)
        assert path.is_absolute(), f"paths.{name} is not absolute: {path}"
        assert cfg.root in path.parents or path == cfg.root, (
            f"paths.{name} escapes the repository root: {path}"
        )


def test_the_raw_data_directory_actually_exists(cfg: Config) -> None:
    """The one path that must already be there — everything else is created on demand."""
    assert cfg.paths.raw.is_dir(), (
        f"configured raw data directory does not exist: {cfg.paths.raw}"
    )


def test_configured_columns_match_the_real_dataset(cfg: Config, hydride_raw) -> None:
    """A column name that does not exist is the failure this section exists to prevent."""
    actual = set(hydride_raw.columns)
    for field in ("formula", "alloy_class", "dataset", "target", "temperature", "citation"):
        name = getattr(cfg.columns, field)
        assert name in actual, (
            f"columns.{field} = {name!r} is not a column of the raw dataset. "
            f"Available: {sorted(actual)}"
        )


def test_the_configured_temperature_domain_matches_the_data(cfg: Config, hydride_raw) -> None:
    """The refusal bounds must not exclude rows the model was trained on."""
    temperatures = hydride_raw[cfg.columns.temperature]
    assert cfg.domain.temperature_min_k <= temperatures.min()
    assert cfg.domain.temperature_max_k >= temperatures.max()


def test_config_is_immutable(cfg: Config) -> None:
    """A stage that wants a different threshold takes a parameter; it does not edit config."""
    with pytest.raises(FrozenInstanceError):
        cfg.seed = 7  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        cfg.split.test_fraction = 0.5  # type: ignore[misc]


# --------------------------------------------------------------------------------------
# Root discovery — the property that makes a clone to another directory work
# --------------------------------------------------------------------------------------


def test_repo_root_finds_this_checkout(repo_root: Path) -> None:
    assert discover_repo_root() == repo_root


def test_paths_follow_an_overridden_root(tmp_path: Path) -> None:
    """The clone-to-a-different-directory property, tested rather than assumed."""
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    (tmp_path / "hydms").mkdir()

    cfg = load(root=tmp_path)

    assert cfg.root == tmp_path
    assert cfg.paths.processed == tmp_path / "data" / "processed"
    assert cfg.paths.raw == tmp_path / "data" / "raw"


def test_a_bogus_hydms_root_is_rejected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HYDMS_ROOT", str(tmp_path / "does-not-exist"))
    with pytest.raises(ConfigError, match="not a directory"):
        discover_repo_root()


def test_hydms_root_overrides_discovery(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HYDMS_ROOT", str(tmp_path))
    assert discover_repo_root() == tmp_path.resolve()


# --------------------------------------------------------------------------------------
# Rejection — a typo must be loud, and an invalid value must not reach a caller
# --------------------------------------------------------------------------------------


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "cfg.yaml"
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture()
def valid_text() -> str:
    return Path("hydms/config/pipeline.yaml").read_text(encoding="utf-8")


def test_a_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load(tmp_path / "absent.yaml")


def test_unparseable_yaml_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="YAML"):
        load(_write(tmp_path, "seed: [unclosed\n"))


def test_an_unknown_top_level_key_raises(tmp_path: Path, valid_text: str) -> None:
    with pytest.raises(ConfigError, match="unknown top-level key"):
        load(_write(tmp_path, valid_text + "\nlearning_rate: 0.1\n"))


def test_an_unknown_section_key_raises(tmp_path: Path, valid_text: str) -> None:
    """The typo case. Silently ignoring this leaves a default quietly in force."""
    text = valid_text.replace("  confidence_level: 0.80", "  confidence_levle: 0.80")
    with pytest.raises(ConfigError, match="unknown key"):
        load(_write(tmp_path, text))


def test_a_missing_section_key_raises(tmp_path: Path, valid_text: str) -> None:
    text = valid_text.replace("  confidence_level: 0.80", "")
    with pytest.raises(ConfigError, match="missing key"):
        load(_write(tmp_path, text))


@pytest.mark.parametrize(
    ("substitution", "message"),
    [
        (("  test_fraction: 0.20", "  test_fraction: 1.5"), "must be in"),
        (("  test_fraction: 0.20", "  test_fraction: 0.95"), "leave a training set"),
        (("  min_stratum_size: 5", "  min_stratum_size: 1"), "at least 2"),
        (("  vif_threshold: 30.0", "  vif_threshold: 0.5"), "exceed 1.0"),
        (("  temperature_min_k: 195.0", "  temperature_min_k: 900.0"), "below"),
        (("seed: 42", "seed: -1"), "non-negative"),
    ],
)
def test_out_of_range_values_are_rejected(
    tmp_path: Path, valid_text: str, substitution: tuple[str, str], message: str
) -> None:
    old, new = substitution
    assert old in valid_text, old
    with pytest.raises(ConfigError, match=message):
        load(_write(tmp_path, valid_text.replace(old, new, 1)))


def test_an_alpha_passed_as_a_confidence_level_is_caught(tmp_path: Path, valid_text: str) -> None:
    """MAPIE 0.x took alpha, 1.x takes confidence_level. Passing 0.2 by habit would give a
    20% interval that looks like a working 80% one.

    A range check alone cannot catch it -- 0.2 is a legal confidence level -- and this test
    used to assert exactly that, that the value was accepted and the reader warned. Card #27
    made it catchable: MAPIE's prefit CQR contract fixes the heads at `(1 - level) / 2` and
    `(1 + level) / 2`, so a level and a quantile list are two statements about one band and
    the loader can refuse a file where they disagree. 0.2 beside [0.1, 0.5, 0.9] does.
    """
    text = valid_text.replace("  confidence_level: 0.80", "  confidence_level: 0.20")
    with pytest.raises(ConfigError, match="prefit CQR contract"):
        load(_write(tmp_path, text))


@pytest.mark.parametrize(
    "quantiles",
    ["[0.9, 0.5, 0.1]", "[0.1, 0.1, 0.9]", "[]", "[0.1, 1.5]"],
)
def test_bad_quantile_lists_are_rejected(tmp_path: Path, valid_text: str, quantiles: str) -> None:
    """Order is a contract: CatBoost identifies quantiles by column position alone, so an
    unsorted list means the column the code calls P90 is not the one the model wrote."""
    text = valid_text.replace("  quantiles: [0.1, 0.5, 0.9]", f"  quantiles: {quantiles}")
    with pytest.raises(ConfigError, match="quantiles"):
        load(_write(tmp_path, text))


def test_empty_must_keep_is_rejected(tmp_path: Path, valid_text: str) -> None:
    text = valid_text.replace("  must_keep:\n    - temperature(K)", "  must_keep: []")
    with pytest.raises(ConfigError, match="must_keep"):
        load(_write(tmp_path, text))


# --------------------------------------------------------------------------------------
# The card's own claim
# --------------------------------------------------------------------------------------


def test_no_absolute_path_literal_survives_in_the_package(repo_root: Path) -> None:
    """`## Done when`: no absolute path literals remain in hydms/.

    The archival pipeline hard-coded `D:\\Hydride_Machine_learning_project\\...` in nine
    scripts. This asserts the new package never acquires one — including on POSIX, where a
    leading-slash literal is the same mistake wearing different shoes.
    """
    offenders: list[str] = []
    for path in sorted((repo_root / "hydms").rglob("*.py")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or "hard-coded" in line or "ROOT_MARKERS" in line:
                continue
            for marker in ('"D:\\', "'D:\\", '"C:\\', "'C:\\", '"/home/', '"/Users/', '"/mnt/'):
                if marker in line:
                    offenders.append(f"{path.relative_to(repo_root)}:{number}: {stripped}")
    assert not offenders, "absolute path literals found:\n  " + "\n  ".join(offenders)
