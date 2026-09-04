"""What is recorded alongside a trained artifact, and how it is read back.

The audit's first finding was that no trained artifact existed on disk: the model, the fitted
scaler and the splits were never persisted, so Architecture A's "load the fitted scaler, do not
refit" step had nothing to load. Persisting the objects is only half the fix. The other half is
this file: **an artifact that does not record what produced it cannot be reasoned about**, and a
model whose feature order is unknown returns plausible, wrong numbers rather than an error.

So a version directory carries a ``manifest.json`` recording five things, one per line of card
#4's contract:

  - the **git SHA** the run was made from, and whether the tree was dirty at the time;
  - **every seed** the run used;
  - the **resolved versions** of the packages that determine a fitted model;
  - the **feature contract** -- names, order and dtype, with the digest that refuses an edit;
  - the **gate results**, embedded verbatim as ``hydms.gates`` wrote them.

Two decisions here are load-bearing and are easy to get wrong the other way.

**The gate report is embedded, not re-formatted.** ``hydms/gates/_report.py`` already writes the
run as JSON behind a versioned ``schema`` key, precisely so this manifest could adopt it rather
than invent a second shape that drifts. :data:`GATE_SCHEMA` is the shape this module knows how to
read; ``tests/artifacts/test_manifest.py`` asserts it still equals the harness's own constant.

**A run's own ``ok`` flag is not consulted.** ``GateReport.ok`` tolerates a skip under a broad
selection, deliberately -- CI that is red for the length of the phase is CI nobody reads. That
leniency is right for a CI log and wrong for an artifact somebody is about to load into a
prediction path, so :meth:`Manifest.unestablished` recomputes the verdict from the per-gate
statuses and treats ``SKIPPED`` exactly as it treats ``FAILED``: a criterion nobody checked.

Card #4.
"""

from __future__ import annotations

import hashlib
import platform as _platform
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any, Final

__all__ = [
    "GATE_SCHEMA",
    "RECORDED_PACKAGES",
    "SCHEMA",
    "ArtifactError",
    "Git",
    "Manifest",
    "ManifestError",
    "PayloadRecord",
    "describe_git",
    "digest_file",
    "resolved_packages",
]

#: This manifest's own version. Written into every file so a reader can tell whether it is
#: looking at a shape it understands, and refuse rather than guess if it is not.
SCHEMA: Final = "hydms.artifacts/1"

#: The gate-report shape this module can read. It mirrors ``hydms.gates._core.SCHEMA``, and is
#: restated rather than imported: ``hydms.gates`` writes its report *into* the artifacts
#: directory, so importing it from here would close a cycle. A test asserts the two agree, which
#: is the check that actually matters -- it fails the moment the harness bumps its schema.
GATE_SCHEMA: Final = "hydms.gates/1"

#: The distributions whose versions change what a fitted model is. Recording a version is not
#: bookkeeping: a CatBoost or scikit-learn upgrade can change a fit from the same seed, which is
#: the failure AC-1 exists to detect, and without this list the only evidence would be "it used
#: to reproduce". Every core runtime dependency in ``pyproject.toml`` must appear here --
#: ``tests/artifacts/test_manifest.py`` reads the file and fails if one is missing -- plus
#: ``mapie``, whose calibration is part of the artifact and which is an optional extra.
#: Names are *distribution* names, not import names: ``scikit-learn``, not ``sklearn``.
RECORDED_PACKAGES: Final[tuple[str, ...]] = (
    "numpy",
    "pandas",
    "scipy",
    "scikit-learn",
    "catboost",
    "cleanlab",
    "PyYAML",
    "joblib",
    "mapie",
)

# Read in chunks rather than whole: a CatBoost model is not large, but a store whose integrity
# check needs the file in memory is one that stops being run on the day it matters.
_CHUNK = 1 << 20


class ArtifactError(Exception):
    """Base for every refusal from :mod:`hydms.artifacts`."""


class ManifestError(ArtifactError, ValueError):
    """A manifest is absent, malformed, or written in a schema this version cannot read."""


# --------------------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Git:
    """Where the code was when the artifact was made.

    ``dirty`` is recorded because it is the difference between "this SHA reproduces the run" and
    "this SHA plus some uncommitted edits nobody kept". Every field is optional: an installed
    package in a container has no work tree, and refusing to save an artifact for that reason
    would be worse than recording honestly that the provenance is unknown.
    """

    sha: str | None = None
    branch: str | None = None
    dirty: bool | None = None
    detail: str = ""

    @property
    def known(self) -> bool:
        return self.sha is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sha": self.sha,
            "branch": self.branch,
            "dirty": self.dirty,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> Git:
        return cls(
            sha=payload.get("sha"),
            branch=payload.get("branch"),
            dirty=payload.get("dirty"),
            detail=str(payload.get("detail", "")),
        )


def _git(root: Path, *args: str) -> str | None:
    """One ``git`` invocation, or ``None`` if git is absent, slow or unhappy.

    Never raises. Provenance that cannot be read is recorded as unknown; it does not stop a
    training run that has already cost an hour from writing its output.
    """
    try:
        # Fixed argv, no shell, and a timeout: provenance is worth a subprocess, not a
        # hang in the middle of a run that has already cost an hour.
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def describe_git(root: Path) -> Git:
    """Read the current commit, branch and cleanliness of the work tree at ``root``."""
    sha = _git(root, "rev-parse", "HEAD")
    if sha is None:
        return Git(detail=f"git reported nothing for {root}: not a work tree, or git is absent")

    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    status = _git(root, "status", "--porcelain")
    return Git(
        sha=sha,
        branch=branch or None,
        # `status` is "" for a clean tree and None only when the call itself failed, so the
        # two cases must not be collapsed: an unknown cleanliness is not a clean one.
        dirty=None if status is None else bool(status),
        detail="" if status is not None else "git status could not be read",
    )


def _distribution_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def resolved_packages() -> dict[str, str | None]:
    """The installed version of every distribution in :data:`RECORDED_PACKAGES`.

    A package that is not installed is recorded as ``null`` rather than omitted. The difference
    matters when reading an old manifest: an absent key means the store did not yet record that
    package, while ``null`` means it was recorded and genuinely was not there.
    """
    return {name: _distribution_version(name) for name in RECORDED_PACKAGES}


def digest_file(path: Path) -> tuple[str, int]:
    """The SHA-256 and byte length of one file.

    What makes a stored payload checkable. A truncated or edited ``model.joblib`` otherwise
    unpickles into something that predicts, which is the failure mode this store exists to
    remove.
    """
    hasher = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK):
            hasher.update(chunk)
            size += len(chunk)
    return hasher.hexdigest(), size


# --------------------------------------------------------------------------------------
# The manifest
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class PayloadRecord:
    """One stored object: what it is called, the file holding it, and its fingerprint."""

    name: str
    file: str
    sha256: str
    bytes: int

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "file": self.file, "sha256": self.sha256, "bytes": self.bytes}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> PayloadRecord:
        missing = [key for key in ("name", "file", "sha256", "bytes") if key not in payload]
        if missing:
            raise ManifestError(
                f"a payload record is missing {missing}; the entry reads {dict(payload)!r}"
            )
        return cls(
            name=str(payload["name"]),
            file=str(payload["file"]),
            sha256=str(payload["sha256"]),
            bytes=int(payload["bytes"]),
        )


@dataclass(frozen=True)
class Manifest:
    """Everything recorded beside one artifact version.

    Constructed by :func:`hydms.artifacts.save` and read by :func:`hydms.artifacts.load`; it is
    a snapshot of a run, so nothing here is edited after the fact. Editing the file on disk is
    detectable for the two things where it would be dangerous -- the feature contract carries
    its own digest, and every payload carries a SHA-256.
    """

    version: str
    created_at: str
    git: Git
    seeds: Mapping[str, int]
    packages: Mapping[str, str | None]
    python: str
    platform: str
    contract: Mapping[str, Any]
    payloads: tuple[PayloadRecord, ...]
    gates: Mapping[str, Any] | None = None
    notes: str = ""
    schema: str = SCHEMA

    # -- the feature contract ------------------------------------------------------------

    @property
    def feature_names(self) -> tuple[str, ...]:
        """The columns this artifact's model was fitted on, in fitting order."""
        entries = self.contract.get("features", ())
        return tuple(str(entry["name"]) for entry in entries)

    def feature_contract(self) -> Any:
        """Rebuild the :class:`~hydms.descriptors.contract.FeatureContract`, digest checked.

        Imported here rather than at module scope: ``hydms.descriptors.contract`` pulls in
        pandas, and reading a manifest -- which CI does on a bare interpreter -- must not
        require the scientific stack.

        Raises:
            ContractError: the recorded names, their order or their dtype were edited after
                the model was fitted.
        """
        from hydms.descriptors.contract import FeatureContract

        return FeatureContract.from_manifest(self.contract)

    # -- the gate verdict ----------------------------------------------------------------

    @property
    def gate_run_recorded(self) -> bool:
        """Whether any gate run at all is recorded against this version."""
        return self.gates is not None and bool(self.gates.get("gates"))

    def unestablished(self) -> tuple[tuple[str, str], ...]:
        """Every recorded gate that did **not** pass, as ``(name, status)`` pairs.

        ``SKIPPED`` counts. The harness reports it for a criterion nobody has written yet, and
        an artifact whose manifest says "AC-3 was not checked" has exactly as much evidence for
        its conformal coverage as one that says "AC-3 failed" -- none. See this module's
        docstring for why the run's own ``ok`` flag is not consulted.
        """
        if not self.gates:
            return ()
        results = self.gates.get("gates", ())
        if not isinstance(results, Sequence):
            return ()
        return tuple(
            (str(entry.get("name", "?")), str(entry.get("status", "?")))
            for entry in results
            if str(entry.get("status", "")) != "PASSED"
        )

    # -- serialisation -------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "version": self.version,
            "created_at": self.created_at,
            "git": self.git.to_dict(),
            "seeds": dict(self.seeds),
            "packages": dict(self.packages),
            "python": self.python,
            "platform": self.platform,
            "contract": dict(self.contract),
            "gates": dict(self.gates) if self.gates is not None else None,
            "payloads": [record.to_dict() for record in self.payloads],
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> Manifest:
        """Rebuild a manifest read from disk, refusing a shape this version cannot read.

        Raises:
            ManifestError: the schema is absent or unknown, or a required key is missing. A
                partially-understood manifest is never returned: the whole value of the file is
                that the reader can trust what it says.
        """
        schema = payload.get("schema")
        if schema != SCHEMA:
            raise ManifestError(
                f"manifest schema is {schema!r}, and this version of hydms reads {SCHEMA!r}. "
                f"An artifact written by a different schema is not read on a guess."
            )

        required = ("version", "created_at", "git", "seeds", "packages", "contract", "payloads")
        missing = [key for key in required if key not in payload]
        if missing:
            raise ManifestError(f"manifest is missing required key(s) {missing}")

        gates = payload.get("gates")
        if gates is not None:
            validate_gate_report(gates)

        return cls(
            version=str(payload["version"]),
            created_at=str(payload["created_at"]),
            git=Git.from_dict(payload["git"]),
            seeds=dict(payload["seeds"]),
            packages=dict(payload["packages"]),
            python=str(payload.get("python", "")),
            platform=str(payload.get("platform", "")),
            contract=dict(payload["contract"]),
            payloads=tuple(PayloadRecord.from_dict(entry) for entry in payload["payloads"]),
            gates=dict(gates) if gates is not None else None,
            notes=str(payload.get("notes", "")),
            schema=str(schema),
        )


def validate_gate_report(payload: Any) -> Mapping[str, Any]:
    """Refuse a gate report this store cannot honestly interpret.

    The completeness rule reads per-gate statuses, so a report whose shape is unrecognised is
    not "no gates" and not "all fine" -- it is unreadable, and the only safe answer is to say
    so at save time rather than store a green-looking file nobody can check.

    Raises:
        ManifestError: the payload is not a mapping, or its ``schema`` is not
            :data:`GATE_SCHEMA`, or it carries no ``gates`` list.
    """
    if not isinstance(payload, Mapping):
        raise ManifestError(
            f"gate results must be the mapping hydms.gates writes (GateReport.to_dict()); "
            f"got {type(payload).__name__}"
        )
    schema = payload.get("schema")
    if schema != GATE_SCHEMA:
        raise ManifestError(
            f"gate results carry schema {schema!r}, and this store embeds {GATE_SCHEMA!r}. "
            f"Pass what `python -m hydms.gates run` produced, unmodified."
        )
    results = payload.get("gates")
    if not isinstance(results, Sequence) or isinstance(results, str | bytes):
        raise ManifestError(
            f"gate results must carry a 'gates' list of per-gate results; got "
            f"{type(results).__name__}"
        )
    for index, entry in enumerate(results):
        if not isinstance(entry, Mapping) or "name" not in entry or "status" not in entry:
            raise ManifestError(
                f"gate result {index} is not a per-gate result: every entry needs 'name' and "
                f"'status'. Got {entry!r}."
            )
    return payload


def now() -> str:
    """A UTC timestamp, to the second. One spelling, so two manifests sort by string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def environment() -> tuple[str, str]:
    """The interpreter and the machine, as a manifest records them."""
    return _platform.python_version(), _platform.platform()
