"""L0 — every path, RNG seed and threshold, in one place.

Paths resolve relative to the repository root, so a clone to a different directory
still runs. No absolute path literal belongs anywhere in this package.

The public interface is :func:`load`, which reads ``pipeline.yaml`` next to this module and
returns a validated, typed :class:`Config`. The schema *is* the contract: any key in the YAML
that is not a declared field raises :class:`ConfigError`, so a stray or misspelled key fails
loudly at load time instead of being silently ignored downstream.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any, cast, get_type_hints

import yaml  # type: ignore[import-untyped]

__all__ = ["Config", "ConfigError", "Paths", "Seeds", "Splits", "Thresholds", "load"]

# pipeline.yaml lives at hydms/config/pipeline.yaml; the repository root is two directories up
# (config -> hydms -> root). Deriving the root from this file's location — not from the current
# working directory — is what makes paths resolve after the repo is cloned somewhere else.
_CONFIG_PATH = Path(__file__).resolve().parent / "pipeline.yaml"
_REPO_ROOT = Path(__file__).resolve().parents[2]


class ConfigError(ValueError):
    """Raised when the config file does not match the declared schema."""


@dataclass(frozen=True)
class Paths:
    """Filesystem locations, all resolved to absolute paths by :func:`load`.

    ``raw_*`` name archival inputs that must already exist; ``load`` verifies they do.
    ``artifacts_root`` is a run *output* directory, so it need not exist yet.
    """

    raw_capacity: Path
    raw_thermo: Path
    artifacts_root: Path


@dataclass(frozen=True)
class Seeds:
    """Random seeds. One global seed threads through every stochastic pipeline step."""

    global_: int


@dataclass(frozen=True)
class Splits:
    """Train/val/test fractions for the stratified unique-formula split (card #13)."""

    test_fraction: float
    val_fraction: float

    @property
    def train_fraction(self) -> float:
        """The remainder after test and val are taken."""
        return 1.0 - self.test_fraction - self.val_fraction


@dataclass(frozen=True)
class Thresholds:
    """Numeric cut-offs for the data and selection layers."""

    variance: float
    mutual_info: float
    vif: float
    outlier_residual_sigma: float


@dataclass(frozen=True)
class Config:
    """The whole pipeline configuration. Obtain one with :func:`load`."""

    paths: Paths
    seeds: Seeds
    splits: Splits
    thresholds: Thresholds


# The YAML uses ``global`` (a Python keyword), so the dataclass field is ``global_``; this maps
# between them. Any other field name matches its YAML key exactly.
_KEY_ALIASES: dict[type, dict[str, str]] = {Seeds: {"global": "global_"}}


def _build(cls: type, raw: Any, context: str) -> Any:
    """Recursively construct a dataclass from a mapping, rejecting unknown keys.

    ``context`` is the dotted path to ``raw`` in the file, used only for error messages.
    """
    if not isinstance(raw, dict):
        raise ConfigError(f"{context or 'config'}: expected a mapping, got {type(raw).__name__}")

    aliases = _KEY_ALIASES.get(cls, {})
    # Resolve annotations to real types: `from __future__ import annotations` makes
    # `field.type` a string, which would defeat the nested-dataclass check below.
    hints = get_type_hints(cls)
    field_by_name = {f.name: f for f in fields(cls)}
    kwargs: dict[str, Any] = {}
    seen: set[str] = set()

    for raw_key, value in raw.items():
        yaml_key = str(raw_key)
        field_name = aliases.get(yaml_key, yaml_key)
        if field_name not in field_by_name:
            allowed = ", ".join(sorted(aliases.get(f.name, f.name) for f in fields(cls)))
            where = f"{context}." if context else ""
            raise ConfigError(f"unknown config key '{where}{yaml_key}'; allowed keys: {allowed}")
        child_context = f"{context}.{yaml_key}" if context else yaml_key
        field_type = hints[field_name]
        if is_dataclass(field_type):
            kwargs[field_name] = _build(cast(type, field_type), value, child_context)
        else:
            kwargs[field_name] = value
        seen.add(field_name)

    missing = [f.name for f in fields(cls) if f.name not in seen and not _has_default(f)]
    if missing:
        pretty = ", ".join(aliases.get(m, m) for m in missing)
        where = f" in '{context}'" if context else ""
        raise ConfigError(f"missing required config key(s){where}: {pretty}")

    return cls(**kwargs)


def _has_default(field: dataclasses.Field) -> bool:
    return (
        field.default is not dataclasses.MISSING
        or field.default_factory is not dataclasses.MISSING  # type: ignore[misc]
    )


def _resolve_paths(paths: Paths, root: Path) -> Paths:
    """Turn every repository-relative path into an absolute path under ``root``."""
    return Paths(
        raw_capacity=(root / paths.raw_capacity).resolve(),
        raw_thermo=(root / paths.raw_thermo).resolve(),
        artifacts_root=(root / paths.artifacts_root).resolve(),
    )


def load(config_path: Path | str | None = None, root: Path | str | None = None) -> Config:
    """Read and validate the pipeline configuration.

    Args:
        config_path: The YAML file to read. Defaults to ``pipeline.yaml`` beside this module.
        root: The repository root that relative paths resolve against. Defaults to the root
            derived from this file's location, which is what lets a clone in any directory
            resolve its paths correctly. Overridable so tests can point at a fixture tree.

    Returns:
        A validated :class:`Config` with all paths resolved to absolute paths.

    Raises:
        ConfigError: if the file has an unknown or missing key, or a required input path does
            not exist.
    """
    path = Path(config_path) if config_path is not None else _CONFIG_PATH
    base = Path(root).resolve() if root is not None else _REPO_ROOT

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"config file not found: {path}") from exc

    if raw is None:
        raise ConfigError(f"config file is empty: {path}")

    config = _build(Config, raw, context="")
    config = dataclasses.replace(config, paths=_resolve_paths(config.paths, base))

    for name in ("raw_capacity", "raw_thermo"):
        resolved = getattr(config.paths, name)
        if not resolved.exists():
            raise ConfigError(f"input path for '{name}' does not exist: {resolved}")

    return config
