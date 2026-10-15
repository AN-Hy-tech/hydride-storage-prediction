"""Shared fixtures for the hydms test suite.

Two rules shape this file:

  - **Nothing heavy at import time.** Collection must succeed on a machine where the `Project`
    environment is not built, so pandas and the rest are imported inside fixtures, and a
    missing dependency skips rather than errors.
  - **Read-only on the raw data.** `data/raw/` is the committed source data the
    pipeline reads. Fixtures hand out copies; a test that mutates one must not affect the next.

Layout, one directory per layer, mirroring `hydms/`:

    tests/artifacts/  L0 — the version store, the manifest, the promotion pointer
    tests/data/       L1 — loaders, the canonical key, splits, screening
    tests/surrogate/  L3 — scaler, selection, validation protocol, calibration
    tests/screens/    L4 — the screen verdict, applicability domain, novelty
    tests/delivery/   L6 — the contract, predict_capacity(), the API, the app
    tests/leaks/      the HG-1 sentinels: one per named leak, marked `leak`

Card #69.

One hook lives here as well as the fixtures: `FailureRecorder`, below, which writes every red
run's tracebacks to `reports/test-failures/` whatever happened to the terminal. Card #100.
"""

from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
import time
from collections.abc import Iterable
from pathlib import Path

import pytest

pytest_plugins = ("pytester",)

REPO_ROOT = Path(__file__).resolve().parent.parent

# The source dataset. Facts asserted against it elsewhere in the suite:
# 1279 rows, 6 columns, 1149 distinct formula strings, 1115 distinct canonical compositions.
RAW_DATA = REPO_ROOT / "data" / "raw" / "hydride_data.csv"

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


# ── The failure record (card #100) ───────────────────────────────────────────────────────────


class FailureRecorder:
    """Write the tracebacks of a red run to a file, whatever happened to the terminal.

    Card #100's failure was seen once, in a 29-minute full run whose output went through
    `Select-Object -Last 15`: the summary survived, both tracebacks did not, and no subset or
    later run has reproduced it. The terminal was the only copy. This makes it not the only
    copy: when a session ends with any failed test or collection error, one file is written
    holding every failure's traceback and its captured output. The traceback is the one pytest
    built for the report, so it has the style the run asked for: `long` by default, which is
    what #100's lost run used, but a `--tb=line` or `--tb=no` run records only what that style
    keeps. Nothing a pipe does downstream of pytest can shorten it.

    It also records the two things #100 learned to check by hand and never could afterwards:
    which other Python processes were alive when the run started and when it ended, and which
    source files changed on disk while it ran. pytest imports test modules at collection and
    production modules on first use, so an edit mid-run gives a green or red that belongs to
    neither version. A run that passes writes nothing.

    It never changes a run's outcome. The probes are best-effort and say so in the record when
    they cannot run, and a record that cannot be written is reported in the terminal summary
    rather than raised.
    """

    def __init__(self, directory: Path, watched: Iterable[Path]) -> None:
        self.directory = directory
        self.watched = tuple(watched)
        self.failures: list[pytest.TestReport | pytest.CollectReport] = []
        self.written: Path | None = None
        self.write_error: str | None = None
        self._started = dt.datetime.now()
        self._started_epoch = time.time()
        self._processes_at_start = ""

    def pytest_sessionstart(self, session: pytest.Session) -> None:
        self._started = dt.datetime.now()
        self._started_epoch = time.time()
        self._processes_at_start = _other_pythons()

    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        if report.failed:
            self.failures.append(report)

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.failed:
            self.failures.append(report)

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        if not self.failures:
            return
        finished = dt.datetime.now()
        name = f"{self._started:%Y%m%d-%H%M%S}-pid{os.getpid()}.txt"
        header = [
            f"pytest failure record — {len(self.failures)} failure(s), exit status {int(exitstatus)}",
            f"started   {self._started:%Y-%m-%d %H:%M:%S}",
            f"finished  {finished:%Y-%m-%d %H:%M:%S}  ({(finished - self._started).total_seconds():.1f} s)",
            f"python    {sys.executable}",
            f"pytest    {pytest.__version__}",
            f"args      {' '.join(session.config.invocation_params.args) or '(none)'}",
            f"cwd       {session.config.invocation_params.dir}",
            f"collected {session.testscollected}",
            f"git       {_git_state(session.config.rootpath)}",
            "",
            "Other Python processes alive at the START of the run:",
            self._processes_at_start,
            "Other Python processes alive at the END of the run:",
            _other_pythons(),
            "Files under the watched directories modified WHILE the run was going:",
            _modified_since(self.watched, self._started_epoch, exclude=self.directory),
        ]
        body = []
        for report in self.failures:
            body += ["", "=" * 100, f"{report.nodeid or '<collection>'}  [{getattr(report, 'when', 'collect')}]", "=" * 100]
            body.append(report.longreprtext)
            for title, content in report.sections:
                body += ["", f"----- {title} -----", content]
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            path = self.directory / name
            path.write_text("\n".join(header + body) + "\n", encoding="utf-8")
        except OSError as exc:
            self.write_error = f"{type(exc).__name__}: {exc}"
        else:
            self.written = path

    def pytest_terminal_summary(self, terminalreporter: pytest.TerminalReporter) -> None:
        if self.written is not None:
            terminalreporter.write_line(f"failure record written: {self.written}", bold=True)
        elif self.write_error is not None:
            terminalreporter.write_line(
                f"failure record could NOT be written to {self.directory}: {self.write_error}",
                red=True,
            )


def _other_pythons() -> str:
    """Every Python process except this one, its ancestors and its children, one per line."""
    try:
        import psutil
    except ImportError:
        return "  (not checked: psutil is not installed in this interpreter)"
    lines = []
    try:
        me = psutil.Process()
        ours = {me.pid} | {p.pid for p in me.parents()} | {p.pid for p in me.children(recursive=True)}
        for proc in psutil.process_iter(["pid", "name", "create_time", "cmdline"]):
            info = proc.info
            if info["pid"] in ours or not (info["name"] or "").lower().startswith("python"):
                continue
            since = f"since {dt.datetime.fromtimestamp(info['create_time']):%Y-%m-%d %H:%M:%S}  " if info["create_time"] else ""
            cmd = " ".join(info["cmdline"] or []) or "(command line not readable)"
            lines.append(f"  pid {info['pid']}  {since}{cmd}")
    except psutil.Error as exc:
        lines.append(f"  (listing stopped: {type(exc).__name__})")
    return "\n".join(lines) or "  none"


def _modified_since(roots: Iterable[Path], epoch: float, exclude: Path) -> str:
    """Files under `roots` whose mtime is after `epoch`, ignoring bytecode caches and the record."""
    hits = []
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d != "__pycache__" and Path(dirpath, d) != exclude]
            for filename in filenames:
                path = Path(dirpath, filename)
                try:
                    mtime = path.stat().st_mtime
                except OSError:
                    continue
                if mtime > epoch:
                    hits.append(f"  {dt.datetime.fromtimestamp(mtime):%H:%M:%S}  {path}")
    return "\n".join(sorted(hits)) or "  none"


def _git_state(root: Path) -> str:
    """HEAD and the number of uncommitted paths, or why they could not be read."""
    try:
        head = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True, timeout=10
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, timeout=10
        ).stdout.splitlines()
    except (OSError, subprocess.SubprocessError) as exc:
        return f"(not read: {type(exc).__name__})"
    return f"{head or '(no HEAD)'}, {len(dirty)} uncommitted path(s)"


FAILURE_RECORD_DIR = REPO_ROOT / "reports" / "test-failures"
FAILURE_RECORDER_NAME = "hydms-failure-record"


def pytest_configure(config: pytest.Config) -> None:
    watched = [REPO_ROOT / name for name in ("hydms", "tests", "app", "scripts", "kanban-hardening")]
    config.pluginmanager.register(FailureRecorder(FAILURE_RECORD_DIR, watched), FAILURE_RECORDER_NAME)
