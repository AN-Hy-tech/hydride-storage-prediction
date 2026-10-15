"""L0 — every path, RNG seed and threshold, in one place.

Paths resolve relative to the repository root, so a clone to a different directory
still runs. No absolute path literal belongs anywhere in this package.

The archival pipeline hard-coded ``D:\\Hydride_Machine_learning_project\\...`` in nine
scripts and referred to six different data directory names, two of which nothing ever
wrote. The information-hiding test for this module is blunt: **changing where data lives
must mean editing one YAML file and nothing else.**

Usage::

    from hydms.config import load

    cfg = load()                      # the packaged pipeline.yaml
    cfg.paths.raw                     # an absolute Path, resolved for this checkout
    cfg.seed                          # the one RNG seed
    cfg.split.test_fraction

Two properties this module guarantees, both of which the archival code lacked:

  - **Unknown keys raise.** A typo in a YAML key is a loud failure, not a silently
    ignored setting that leaves a default in place. That is how a threshold ends up
    meaning something different from what the config says it means.
  - **The result is immutable.** Config is read once and cannot be mutated by a stage
    that wants a slightly different threshold. A stage that needs one takes a parameter.

Card #3.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any, TypeVar

import yaml

__all__ = ["Config", "ConfigError", "load", "repo_root"]

# Files that together identify the repository root. `pyproject.toml` alone is not enough:
# a parent directory could be another project entirely.
ROOT_MARKERS = ("pyproject.toml", "hydms")

DEFAULT_CONFIG = Path(__file__).with_name("pipeline.yaml")

#: How close a configured quantile must be to the level `conformal.confidence_level` implies.
#: `(1 - 0.8) / 2` is `0.09999999999999998` in binary floating point and the file says `0.1`,
#: so this comparison cannot be an equality. 1e-12 is the tolerance this project uses
#: throughout — see `tests/descriptors/test_contract.py` and the AC-2 gate.
_QUANTILE_TOLERANCE = 1e-12

T = TypeVar("T")


class ConfigError(ValueError):
    """Raised when configuration is missing, malformed, or contains an unknown key."""


def repo_root() -> Path:
    """Locate the repository root for this checkout.

    Resolution order, most explicit first:

      1. ``HYDMS_ROOT`` if set — the escape hatch for an installed (non-editable) package
         or a container where the source tree is somewhere unrelated.
      2. The nearest ancestor of this file containing every marker in ``ROOT_MARKERS``.

    Raises rather than falling back to the current working directory: a path silently
    resolved against whatever directory the user happened to be in is exactly the class
    of bug this module exists to remove.
    """
    override = os.environ.get("HYDMS_ROOT")
    if override:
        candidate = Path(override).expanduser().resolve()
        if not candidate.is_dir():
            raise ConfigError(f"HYDMS_ROOT is set to {candidate}, which is not a directory")
        return candidate

    here = Path(__file__).resolve()
    for parent in here.parents:
        if all((parent / marker).exists() for marker in ROOT_MARKERS):
            return parent

    raise ConfigError(
        f"could not locate the repository root above {here}: no ancestor contains "
        f"all of {ROOT_MARKERS}. Set HYDMS_ROOT to point at it explicitly."
    )


# --------------------------------------------------------------------------------------
# Sections
#
# Every section is a frozen dataclass. Adding a setting means adding a field here and a
# key to pipeline.yaml; the loader refuses anything present in one but not the other, in
# either direction, so the two cannot drift apart silently.
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Paths:
    """Every directory the pipeline reads or writes, relative to the repository root.

    Stored relative in YAML and exposed absolute here. `raw` is the committed dataset under
    `data/raw/`; it is read-only input. The other directories are written and gitignored.
    """

    raw: Path
    interim: Path
    processed: Path
    splits: Path
    artifacts: Path
    reports: Path

    def resolved(self, root: Path) -> Paths:
        return Paths(**{f.name: (root / getattr(self, f.name)) for f in fields(self)})


@dataclass(frozen=True)
class Columns:
    """The column names in the raw dataset, which are not identifiers and contain spaces,
    percent signs and parentheses. Naming them once stops nine spellings appearing."""

    formula: str
    alloy_class: str
    dataset: str
    target: str
    temperature: str
    citation: str


@dataclass(frozen=True)
class Split:
    """The train/val/test protocol.

    Fractions are 0.20 / 0.10 as `split_data.py` actually used, not the 70/15/15 that
    `REPORT.md` §2.6 and the README both claim. The documented target is 896/136/247, but
    that was produced by grouping on the raw formula string; grouping on the canonical
    composition key (card #87) moves it slightly, and that movement is the fix working.
    """

    test_fraction: float
    val_fraction: float
    target_bins: int
    temperature_bins: int
    min_stratum_size: int


@dataclass(frozen=True)
class Selection:
    """Feature-selection thresholds, ported from `Boruta_FeatEng.py`.

    `must_keep` is not a convenience: the archival selector force-re-adds `temperature(K)`
    after both the variance filter and VIF, because it is the only non-composition feature
    and the model is useless without it.
    """

    variance_threshold: float
    vif_threshold: float
    boruta_max_iter: int
    boruta_max_depth: int
    must_keep: tuple[str, ...]


@dataclass(frozen=True)
class Model:
    """The surrogate.

    `quantiles` order is a contract, not a preference: CatBoost's MultiQuantile returns one
    column per alpha **in the order given**, and position is the only thing identifying
    P10 / P50 / P90 (docs/LIBRARY-APIS.md).
    """

    quantiles: tuple[float, ...]
    early_stopping_rounds: int
    optuna_trials: int
    cv_folds: int
    inner_cv_folds: int
    stopping_folds: int
    calibration_folds: int


@dataclass(frozen=True)
class Conformal:
    """MAPIE 1.x takes `confidence_level`, not `alpha`. Card #27.

    Not independent of `model.quantiles`. MAPIE's conformalized quantile regression in
    `prefit` mode requires the heads it is handed to be exactly `(1 - confidence_level) / 2`,
    `(1 + confidence_level) / 2` and `0.5`, so this value and that list are two statements
    about one band. `_validate` refuses a configuration where they disagree.
    """

    confidence_level: float


@dataclass(frozen=True)
class Domain:
    """The bounds outside which the surrogate refuses to answer (card #77).

    The temperature span is what the dataset actually covers, measured. Coverage inside it
    is not uniform — 130 of the 893 scored out-of-fold rows sit above 500 K, measured by
    `TemperatureSupport.above()` over `reports/model/model-out-of-fold.csv` — which is why the applicability
    domain (card #48) is a separate check rather than just this interval.

    The three thresholds below are that check's, and card #48 measured every one of them.
    They are here rather than in `hydms.screens.domain` because the card requires the ceiling
    to be a config value: an R1 iteration tightens the domain and re-runs without a code
    change. The *derivation* of each stays in that module's docstring, because a number in a
    config file with no argument beside it is how a threshold comes to mean something nobody
    intended.
    """

    temperature_min_k: float
    temperature_max_k: float
    capacity_ceiling_hm_floor: float
    max_interval_width_wt_pct: float
    min_transfer_r2: float


@dataclass(frozen=True)
class Config:
    """The whole configuration. Immutable, validated, with absolute paths."""

    seed: int
    root: Path
    paths: Paths
    columns: Columns
    split: Split
    selection: Selection
    model: Model
    conformal: Conformal
    domain: Domain


# --------------------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------------------


def _build(cls: type[T], raw: Any, where: str) -> T:
    """Construct a frozen dataclass from a mapping, rejecting unknown and missing keys.

    Both directions matter. An unknown key is usually a typo, and ignoring it leaves a
    default silently in force. A missing key would otherwise become a TypeError from the
    constructor, naming the argument but not the file it should have come from.
    """
    # A section whose last key is deleted parses as None, not {}. Treating that as an empty
    # mapping lets the missing-key check below name what is actually absent, instead of
    # reporting "got NoneType" and leaving the reader to work out which key they removed.
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ConfigError(f"{where}: expected a mapping, got {type(raw).__name__}")

    assert is_dataclass(cls)
    expected = {f.name: f.type for f in fields(cls)}

    unknown = sorted(set(raw) - set(expected))
    if unknown:
        raise ConfigError(
            f"{where}: unknown key(s) {unknown}. Known keys: {sorted(expected)}"
        )

    missing = sorted(set(expected) - set(raw))
    if missing:
        raise ConfigError(f"{where}: missing key(s) {missing}")

    kwargs: dict[str, Any] = {}
    for name, annotation in expected.items():
        value = raw[name]
        text = annotation if isinstance(annotation, str) else getattr(annotation, "__name__", "")
        if "Path" in text:
            value = Path(str(value))
        elif text.startswith("tuple"):
            if not isinstance(value, list):
                raise ConfigError(f"{where}.{name}: expected a list, got {type(value).__name__}")
            value = tuple(value)
        kwargs[name] = value
    return cls(**kwargs)  # type: ignore[return-value]


def _validate(cfg: Config) -> None:
    """Range checks that a type cannot express.

    These are not defensive padding. Each one corresponds to a way the archival pipeline
    could be — or was — misconfigured without anything complaining.
    """
    problems: list[str] = []

    if cfg.seed < 0:
        problems.append(f"seed must be non-negative, got {cfg.seed}")

    total = cfg.split.test_fraction + cfg.split.val_fraction
    if not 0.0 < total < 1.0:
        problems.append(
            f"split.test_fraction + split.val_fraction must leave a training set: got {total}"
        )
    for name in ("test_fraction", "val_fraction"):
        value = getattr(cfg.split, name)
        if not 0.0 < value < 1.0:
            problems.append(f"split.{name} must be in (0, 1), got {value}")
    if cfg.split.min_stratum_size < 2:
        problems.append("split.min_stratum_size must be at least 2 for a stratified split")

    quantiles = cfg.model.quantiles
    if not quantiles:
        problems.append("model.quantiles must not be empty")
    if any(not 0.0 < q < 1.0 for q in quantiles):
        problems.append(f"model.quantiles must all lie in (0, 1), got {quantiles}")
    if list(quantiles) != sorted(quantiles):
        # Position identifies the quantile in CatBoost's output; an unsorted list means the
        # column the code calls P90 is not the one the model put there.
        problems.append(f"model.quantiles must be ascending, got {quantiles}")
    if len(set(quantiles)) != len(quantiles):
        problems.append(f"model.quantiles must not repeat, got {quantiles}")

    for name in ("cv_folds", "inner_cv_folds", "stopping_folds", "calibration_folds"):
        count = getattr(cfg.model, name)
        if count < 2:
            problems.append(
                f"model.{name} must be at least 2; one fold is not a partition and nothing "
                f"can be held out of it"
            )
    if cfg.model.stopping_folds > cfg.split.min_stratum_size:
        # Same reason as cv_folds below: the early-stopping slice is cut by the same
        # group-aware, stratified generator, so it inherits the same bound.
        problems.append(
            f"model.stopping_folds ({cfg.model.stopping_folds}) exceeds "
            f"split.min_stratum_size ({cfg.split.min_stratum_size}), so a stratum can hold "
            f"fewer compositions than there are folds to spread them over"
        )
    if cfg.model.cv_folds > cfg.split.min_stratum_size:
        # StratifiedGroupKFold cannot place a stratum holding fewer compositions than there
        # are folds, and split.min_stratum_size is exactly what bounds that from below.
        problems.append(
            f"model.cv_folds ({cfg.model.cv_folds}) exceeds split.min_stratum_size "
            f"({cfg.split.min_stratum_size}), so a stratum can hold fewer compositions than "
            f"there are folds to spread them over"
        )
    if cfg.model.calibration_folds > cfg.split.min_stratum_size:
        # The calibration slice is cut by that same generator, so it inherits the same bound.
        problems.append(
            f"model.calibration_folds ({cfg.model.calibration_folds}) exceeds "
            f"split.min_stratum_size ({cfg.split.min_stratum_size}), so a stratum can hold "
            f"fewer compositions than there are folds to spread them over"
        )

    level = cfg.conformal.confidence_level
    if not 0.0 < level < 1.0:
        problems.append(
            f"conformal.confidence_level must be in (0, 1), got {level}. "
            "MAPIE 1.x takes a confidence level, not an alpha — 0.8, not 0.2."
        )
    elif quantiles and list(quantiles) == sorted(set(quantiles)):
        # The band and the heads are two statements about one interval, and MAPIE's
        # conformalized quantile regression in `prefit` mode enforces the relation exactly:
        # the estimators it is handed must predict (1 - level) / 2, (1 + level) / 2 and 0.5.
        # This file shipped with 0.90 beside heads at [0.1, 0.5, 0.9] -- an 80% band told to
        # calibrate as a 90% one -- and nothing raised, because nothing read either key. The
        # check is here rather than in the calibrator so that the contradiction is refused at
        # load time, before a run has cost anything. Card #27.
        #
        # A tolerance, not equality: (1 - 0.8) / 2 is 0.09999999999999998 in binary floating
        # point and the file says 0.1. 1e-12 is this project's tolerance throughout.
        wanted = ((1.0 - level) / 2.0, (1.0 + level) / 2.0)
        got = (quantiles[0], quantiles[-1])
        if any(abs(a - b) > _QUANTILE_TOLERANCE for a, b in zip(wanted, got, strict=True)):
            problems.append(
                f"conformal.confidence_level {level} wants outer quantiles "
                f"({wanted[0]:g}, {wanted[1]:g}) and model.quantiles has "
                f"({got[0]:g}, {got[1]:g}). MAPIE's prefit CQR contract is exact: lower "
                f"(1 - level) / 2, upper (1 + level) / 2. Move whichever of the two is "
                f"wrong — they describe one band"
            )
        if not any(abs(q - 0.5) <= _QUANTILE_TOLERANCE for q in quantiles):
            problems.append(
                f"model.quantiles {list(quantiles)} has no median head. MAPIE's prefit CQR "
                f"takes three estimators — lower, upper and 0.5 — and the median is the "
                f"point prediction the interval is reported around"
            )

    if cfg.domain.temperature_min_k >= cfg.domain.temperature_max_k:
        problems.append("domain.temperature_min_k must be below domain.temperature_max_k")
    if cfg.domain.temperature_min_k <= 0:
        problems.append("domain.temperature_min_k must be above absolute zero")

    if cfg.selection.vif_threshold <= 1.0:
        problems.append("selection.vif_threshold must exceed 1.0 to admit any feature")
    if not cfg.selection.must_keep:
        problems.append(
            "selection.must_keep is empty; the archival selector force-keeps the temperature "
            "column through variance filtering and VIF, and the model is useless without it"
        )

    if problems:
        raise ConfigError("invalid configuration:\n  - " + "\n  - ".join(problems))


def load(path: str | Path | None = None, *, root: Path | None = None) -> Config:
    """Load, validate and return the configuration.

    Args:
        path: A YAML file. Defaults to the one packaged beside this module.
        root: The repository root paths resolve against. Defaults to :func:`repo_root`.

    Raises:
        ConfigError: The file is missing or malformed, a key is unknown or absent, or a
            value is out of range. Never returns a partially-valid config.
    """
    source = Path(path) if path is not None else DEFAULT_CONFIG
    if not source.is_file():
        raise ConfigError(f"configuration file not found: {source}")

    try:
        raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"{source}: could not be parsed as YAML: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError(f"{source}: expected a mapping at the top level")

    base = root if root is not None else repo_root()

    sections = {
        "paths": Paths,
        "columns": Columns,
        "split": Split,
        "selection": Selection,
        "model": Model,
        "conformal": Conformal,
        "domain": Domain,
    }

    known = {"seed", *sections}
    unknown = sorted(set(raw) - known)
    if unknown:
        raise ConfigError(f"{source}: unknown top-level key(s) {unknown}. Known: {sorted(known)}")
    missing = sorted(known - set(raw))
    if missing:
        raise ConfigError(f"{source}: missing top-level key(s) {missing}")

    built: dict[str, Any] = {
        name: _build(cls, raw[name], f"{source.name}:{name}") for name, cls in sections.items()
    }
    built["paths"] = built["paths"].resolved(base)

    cfg = Config(seed=int(raw["seed"]), root=base, **built)
    _validate(cfg)
    return cfg
