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

    Stored relative in YAML and exposed absolute here. `raw` points into `Machine_Model/`
    because that is where the archival dataset lives; it is read-only input, and the Phase H
    freeze denies writes there.
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


@dataclass(frozen=True)
class Conformal:
    """MAPIE 1.x takes `confidence_level`, not `alpha`. Card #27."""

    confidence_level: float


@dataclass(frozen=True)
class Domain:
    """The bounds outside which the surrogate refuses to answer (card #77).

    The temperature span is what the dataset actually covers, measured. Coverage inside it
    is not uniform — only 39 test rows sit above 500 K — which is why the applicability
    domain (card #48) is a separate, learned check rather than just this interval.
    """

    temperature_min_k: float
    temperature_max_k: float


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

    if not 0.0 < cfg.conformal.confidence_level < 1.0:
        problems.append(
            f"conformal.confidence_level must be in (0, 1), got {cfg.conformal.confidence_level}. "
            "MAPIE 1.x takes a confidence level, not an alpha — 0.9, not 0.1."
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
