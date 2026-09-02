"""Shared fixtures for the hydms test suite.

Two rules shape this file:

  - **Nothing heavy at import time.** Collection must succeed on a machine where the `Project`
    environment is not built, so pandas and the rest are imported inside fixtures, and a
    missing dependency skips rather than errors.
  - **Read-only on the raw data.** `Machine_Model/data/raw/` is the archival input behind
    REPORT.md. Fixtures hand out copies; a test that mutates one must not affect the next.

Layout, one directory per layer, mirroring `hydms/`:

    tests/data/       L1 — loaders, the canonical key, splits, screening
    tests/surrogate/  L3 — scaler, selection, validation protocol, calibration
    tests/screens/    L4 — the screen verdict, applicability domain, novelty
    tests/delivery/   L6 — the contract, predict_capacity(), the API, the app
    tests/leaks/      the HG-1 sentinels: one per named leak, marked `leak`

Card #69.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# The archival dataset behind REPORT.md. Facts asserted against it elsewhere in the suite:
# 1279 rows, 6 columns, 1149 distinct formula strings, 1115 distinct canonical compositions.
RAW_DATA = REPO_ROOT / "Machine_Model" / "data" / "raw" / "hydride_data.csv"

TARGET_COLUMN = "H2_W% (max)"
FORMULA_COLUMN = "Composition"
CLASS_COLUMN = "Alloy_class"
TEMPERATURE_COLUMN = "temperature(K)"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """The repository root, so no test needs a relative path or a `cwd` assumption."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def raw_data_path() -> Path:
    """Path to the raw dataset, skipping the test if it is not in this checkout."""
    if not RAW_DATA.is_file():
        pytest.skip(f"raw dataset not present: {RAW_DATA}")
    return RAW_DATA


@pytest.fixture(scope="session")
def _raw_frame(raw_data_path: Path):
    """The raw dataset, read once per session. Private: use `hydride_raw` for a safe copy."""
    pd = pytest.importorskip("pandas", reason="pandas is not installed in this interpreter")
    return pd.read_csv(raw_data_path)


@pytest.fixture()
def hydride_raw(_raw_frame):
    """A fresh copy of the raw dataset (1279 x 6), safe to mutate.

    Columns: Composition, Alloy_class, Dataset, H2_W% (max), temperature(K), Citation.
    """
    return _raw_frame.copy(deep=True)


@pytest.fixture()
def known_collisions() -> list[tuple[str, str]]:
    """Formula-string pairs that name the same material and must share a canonical key.

    Measured against the real data during the Phase H audit. Each pair currently receives two
    independent identities under the raw-string key, which is leak L8: 1149 formula strings
    collapse to 1115 canonical compositions, and 16 of those span two splits. `Pr1Co5 ` differs
    from `Pr1Co5` by a trailing space alone.

    Used by the L8 sentinel (#71), the canonical-key tests (#87) and the metamorphic tests (#74).
    """
    return [
        ("Ce1Mg12", "Mg12Ce1"),                      # element order
        ("Ti1Co0.5Fe0.5", "Ti1Fe0.5Co0.5"),          # element order
        ("Ce0.5La0.5Ni5", "La0.5Ce0.5Ni5"),          # element order
        ("Mg1Al1", "Mg0.5Al0.5"),                    # scaling
        ("Pr1Co5", "Pr1Co5 "),                       # trailing whitespace
        ("Mg2Al3", "Mg2Al3 "),                       # trailing whitespace
    ]


@pytest.fixture()
def trained_temperature_range() -> tuple[float, float]:
    """The temperature span the dataset actually covers, in kelvin.

    The refusal path (#77) declines anything outside it. Note the coverage is not uniform:
    only 39 test rows sit above 500 K, which the temperature-sweep chart (#81) must not hide.
    """
    return (195.0, 773.0)
