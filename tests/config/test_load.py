"""Tests for the config loader (card #3).

These cover the four "Done when" criteria: the YAML holds paths/seeds/thresholds, `load()`
returns a validated typed object that rejects unknown keys, no absolute literals survive, and
paths resolve correctly when the repo is anchored at a different directory.
"""

from __future__ import annotations

import dataclasses
import textwrap
from pathlib import Path

import pytest

from hydms import config
from hydms.config import Config, ConfigError, load

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_load_returns_typed_config():
    cfg = load()
    assert isinstance(cfg, Config)
    assert cfg.seeds.global_ == 42
    assert cfg.splits.test_fraction == 0.20
    assert cfg.splits.val_fraction == 0.10
    assert cfg.thresholds.vif == 30.0


def test_paths_are_absolute_and_anchored_at_repo_root():
    cfg = load()
    assert cfg.paths.raw_capacity.is_absolute()
    assert cfg.paths.artifacts_root.is_absolute()
    assert cfg.paths.raw_capacity == (REPO_ROOT / "Machine_Model/data/raw/hydride_data.csv")


def test_input_paths_exist():
    cfg = load()
    assert cfg.paths.raw_capacity.exists()
    assert cfg.paths.raw_thermo.exists()


def test_train_fraction_is_the_remainder():
    cfg = load()
    assert cfg.splits.train_fraction == pytest.approx(0.70)


def test_paths_follow_the_root_when_repo_is_relocated(tmp_path):
    """Simulate a clone at a different directory: the same YAML resolves under the new root."""
    # Stage the raw inputs the packaged YAML expects, under the relocated root.
    for rel in ("Machine_Model/data/raw/hydride_data.csv", "Machine_Model/data/raw/ML-HYDPARK_v0.0.5.csv"):
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("stub", encoding="utf-8")

    cfg = load(root=tmp_path)
    assert cfg.paths.artifacts_root == (tmp_path / "artifacts")
    assert cfg.paths.raw_capacity == (tmp_path / "Machine_Model/data/raw/hydride_data.csv")
    assert str(cfg.paths.raw_capacity).startswith(str(tmp_path))


def _write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "pipeline.yaml"
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return p


VALID_BODY = """
    paths:
      raw_capacity: Machine_Model/data/raw/hydride_data.csv
      raw_thermo: Machine_Model/data/raw/ML-HYDPARK_v0.0.5.csv
      artifacts_root: artifacts
    seeds:
      global: 42
    splits:
      test_fraction: 0.20
      val_fraction: 0.10
    thresholds:
      variance: 0.001
      mutual_info: 0.001
      vif: 30.0
      outlier_residual_sigma: 3.0
"""


def test_unknown_top_level_key_raises(tmp_path):
    path = _write(tmp_path, VALID_BODY + "    surprise: 1\n")
    with pytest.raises(ConfigError, match="unknown config key 'surprise'"):
        load(config_path=path, root=REPO_ROOT)


def test_unknown_nested_key_raises(tmp_path):
    body = VALID_BODY.replace("      global: 42\n", "      global: 42\n      extra: 9\n")
    path = _write(tmp_path, body)
    with pytest.raises(ConfigError, match="unknown config key 'seeds.extra'"):
        load(config_path=path, root=REPO_ROOT)


def test_missing_required_key_raises(tmp_path):
    body = VALID_BODY.replace("      vif: 30.0\n", "")
    path = _write(tmp_path, body)
    with pytest.raises(ConfigError, match="missing required config key"):
        load(config_path=path, root=REPO_ROOT)


def test_missing_input_path_raises(tmp_path):
    """A raw input that does not exist under the given root fails loudly."""
    path = _write(tmp_path, VALID_BODY)
    with pytest.raises(ConfigError, match="does not exist"):
        load(config_path=path, root=tmp_path)


def test_missing_file_raises(tmp_path):
    with pytest.raises(ConfigError, match="config file not found"):
        load(config_path=tmp_path / "nope.yaml")


def test_empty_file_raises(tmp_path):
    path = tmp_path / "pipeline.yaml"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ConfigError, match="empty"):
        load(config_path=path)


def test_config_is_frozen():
    cfg = load()
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.seeds.global_ = 0  # type: ignore[misc]


def test_module_exposes_load():
    assert callable(config.load)
