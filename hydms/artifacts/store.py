"""Where a trained artifact lives, and the only two doors into it.

Layout, under the configured artifacts directory (``paths.artifacts`` in ``pipeline.yaml``)::

    artifacts/
      current.json          the promotion pointer: which version is live
      gate-results.json     the standalone report `python -m hydms.gates run` writes
      v1/
        manifest.json       provenance, seeds, packages, feature contract, gate results
        model.joblib        one file per saved object, named by its payload key
        scaler.joblib
      v2/
        ...

Four properties hold, and each corresponds to a way the archival pipeline lost its own work.

**A version is written once and never edited.** :func:`save` refuses an existing version and
stages the whole directory under a dotted name before renaming it into place, so a run that dies
half-way leaves nothing that looks like a version. This is what makes "later phases pin the
version they consume" mean anything.

**Nothing enters or leaves except through here.** ``save`` and ``load`` are the doors. A stage
that reaches past them and pickles a scaler beside its script is the state this store exists to
end -- the audit found the fitted scaler, the model and the splits all unpersisted, which is why
Architecture A's "load the fitted scaler, do not refit" had nothing to load.

**A version whose gates are incomplete does not load.** Not as a warning: :func:`load` raises,
and so does :func:`promote`. A skip counts as incomplete -- see
:meth:`~hydms.artifacts.manifest.Manifest.unestablished` for why the harness's own lenient ``ok``
flag is not consulted. ``require_gates=False`` exists for the card that has just written a
version and wants it back, and for inspection; the delivery path never passes it.

**Promotion is a pointer.** ``current.json`` names a version, so rollback is one small write
rather than a retrain (card #7).

Card #4.
"""

from __future__ import annotations

import json
import re
import shutil
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .manifest import (
    ArtifactError,
    Manifest,
    ManifestError,
    PayloadRecord,
    describe_git,
    digest_file,
    environment,
    now,
    resolved_packages,
    validate_gate_report,
)

__all__ = [
    "Artifacts",
    "GatesIncomplete",
    "PayloadCorrupt",
    "VersionNotFound",
    "current",
    "load",
    "promote",
    "read_manifest",
    "save",
    "version_dir",
    "versions",
]

MANIFEST_NAME = "manifest.json"
CURRENT_POINTER = "current.json"

#: ``v`` followed by a decimal count. Sorting is numeric, never lexicographic: ``v10`` follows
#: ``v9``, and a string sort would quietly promote the wrong artifact on the tenth retrain.
_VERSION = re.compile(r"^v(\d+)$")

#: A payload key becomes a file name, so it is restricted rather than sanitised. Refusing
#: ``../model`` at the door is the whole of this store's path-traversal story.
_PAYLOAD_KEY = re.compile(r"^[a-z][a-z0-9_]*$")

_SUFFIX = ".joblib"


class VersionNotFound(ArtifactError, LookupError):
    """No such artifact version, or the promotion pointer names one that is gone."""


class GatesIncomplete(ArtifactError):
    """A version's recorded gate run did not establish every criterion.

    Raised by :func:`load` and :func:`promote`. It names the gates and their statuses, because
    "gates incomplete" without the list costs the reader the run again.
    """


class PayloadCorrupt(ArtifactError):
    """A stored file does not match the digest its manifest recorded for it."""


# --------------------------------------------------------------------------------------
# Locating the store
# --------------------------------------------------------------------------------------


def _store(store: Path | None) -> Path:
    """The artifacts directory: the caller's, or the configured one.

    The config import is deferred so that a caller who names a directory outright -- every test
    in ``tests/artifacts/``, and any tool inspecting a downloaded CI artifact -- needs neither
    ``pipeline.yaml`` nor a repository around it.
    """
    if store is not None:
        return Path(store)
    from hydms.config import load as load_config

    return load_config().paths.artifacts


def _version_dirs(store: Path) -> dict[int, Path]:
    """Every directory named ``v<N>``, by N. Includes ones with no manifest.

    Those are not versions -- :func:`versions` filters them out -- but they still hold a number,
    and handing that number to a second run would produce two different artifacts with one name.
    """
    if not store.is_dir():
        return {}
    found: dict[int, Path] = {}
    for entry in store.iterdir():
        match = _VERSION.match(entry.name)
        if match and entry.is_dir():
            found[int(match.group(1))] = entry
    return found


def versions(*, store: Path | None = None) -> tuple[str, ...]:
    """Every complete artifact version, oldest first.

    A directory with no ``manifest.json`` is not reported: it is either a run that died before
    it finished or something copied in by hand, and in both cases the store knows nothing about
    what is in it.
    """
    root = _store(store)
    return tuple(
        f"v{number}"
        for number in sorted(_version_dirs(root))
        if (root / f"v{number}" / MANIFEST_NAME).is_file()
    )


def version_dir(version: str, *, store: Path | None = None) -> Path:
    """The directory holding ``version``, checked to exist.

    Public because CI uploads the directory wholesale (card #7) and a person occasionally needs
    to look inside one. It is a read path: writing into it by hand breaks the digests that make
    :func:`load` trustworthy.
    """
    root = _store(store)
    if not _VERSION.match(version):
        raise VersionNotFound(
            f"{version!r} is not an artifact version. Versions are 'v' followed by a number, "
            f"as save() assigns them: v1, v2, ..."
        )
    directory = root / version
    if not (directory / MANIFEST_NAME).is_file():
        known = ", ".join(versions(store=root)) or "none"
        raise VersionNotFound(
            f"no artifact version {version} under {root}. Versions present: {known}."
        )
    return directory


# --------------------------------------------------------------------------------------
# The promotion pointer
# --------------------------------------------------------------------------------------


def current(*, store: Path | None = None) -> str | None:
    """The promoted version, or ``None`` if nothing has been promoted yet."""
    pointer = _store(store) / CURRENT_POINTER
    if not pointer.is_file():
        return None
    try:
        payload = json.loads(pointer.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactError(f"{pointer} could not be read: {exc}") from exc
    version = payload.get("version") if isinstance(payload, Mapping) else None
    if not isinstance(version, str):
        raise ArtifactError(f"{pointer} records no version; it reads {payload!r}")
    return version


def promote(version: str, *, store: Path | None = None) -> str:
    """Point ``current`` at ``version``, refusing anything its gates did not establish.

    This is the promotion half of card #7: a full run produces ``v{N+1}``, the gates run against
    it, and only a complete pass moves the pointer. Rolling back is the same call with the older
    version -- one small write, no retrain.

    Raises:
        VersionNotFound: no such version.
        GatesIncomplete: its manifest records no gate run, or a gate that did not pass.
    """
    root = _store(store)
    directory = version_dir(version, store=root)
    manifest = read_manifest(directory)
    _require_established(manifest, directory)

    pointer = root / CURRENT_POINTER
    pointer.write_text(
        json.dumps({"version": version, "promoted_at": now()}, indent=2) + "\n",
        encoding="utf-8",
    )
    return version


# --------------------------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------------------------


def read_manifest(directory: Path) -> Manifest:
    """Read one version's manifest without loading anything it points at.

    Separate from :func:`load` on purpose. Answering "what produced this artifact, and did its
    gates pass?" is a question CI asks on a bare interpreter, and it must not require joblib,
    CatBoost, or the memory to hold a model.
    """
    path = directory / MANIFEST_NAME
    if not path.is_file():
        raise VersionNotFound(f"no {MANIFEST_NAME} in {directory}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"{path} could not be read: {exc}") from exc
    return Manifest.from_dict(payload)


def _require_established(manifest: Manifest, directory: Path) -> None:
    if not manifest.gate_run_recorded:
        raise GatesIncomplete(
            f"{directory.name} records no gate run, so nothing about it has been established. "
            f"Run `python -m hydms.gates run --all` and save the version with its report, or "
            f"pass require_gates=False if you are inspecting an unpromoted artifact."
        )
    outstanding = manifest.unestablished()
    if outstanding:
        recorded = len(manifest.gates["gates"]) if manifest.gates else 0
        listed = ", ".join(f"{name} {status}" for name, status in outstanding)
        raise GatesIncomplete(
            f"{directory.name} did not establish {len(outstanding)} of {recorded} recorded "
            f"gates: {listed}. A SKIPPED gate is a criterion nobody checked, which is why it "
            f"counts here even though the harness tolerates it in a CI log."
        )


@dataclass(frozen=True)
class Artifacts:
    """One loaded artifact version: the objects, and the manifest that vouches for them.

    Immutable and version-stamped. Card #76's ``ArtifactBundle`` is this, held for the life of
    the process: a prediction path that can silently pick up a different model between two calls
    cannot honour AC-4 and cannot be reasoned about at all.
    """

    version: str
    directory: Path
    manifest: Manifest
    objects: Mapping[str, Any]

    def __getitem__(self, name: str) -> Any:
        try:
            return self.objects[name]
        except KeyError:
            raise KeyError(
                f"{self.version} holds no payload named {name!r}. It holds: "
                f"{', '.join(self.names) or 'nothing'}."
            ) from None

    def get(self, name: str, default: Any = None) -> Any:
        return self.objects.get(name, default)

    def __contains__(self, name: object) -> bool:
        return name in self.objects

    def __iter__(self) -> Iterator[str]:
        return iter(self.objects)

    def __len__(self) -> int:
        return len(self.objects)

    @property
    def names(self) -> tuple[str, ...]:
        """The payload keys this version holds, in the order they were saved."""
        return tuple(self.objects)

    @property
    def feature_names(self) -> tuple[str, ...]:
        """The columns the stored model was fitted on, in fitting order."""
        return self.manifest.feature_names

    def contract(self) -> Any:
        """The stored :class:`~hydms.descriptors.contract.FeatureContract`, digest checked."""
        return self.manifest.feature_contract()


def load(
    version: str | None = None,
    *,
    store: Path | None = None,
    require_gates: bool = True,
) -> Artifacts:
    """Load an artifact version, with everything it recorded about itself.

    Args:
        version: Which version. Defaults to the promoted one (``current.json``).
        store: The artifacts directory. Defaults to the configured ``paths.artifacts``.
        require_gates: Refuse a version whose recorded gate run did not establish every
            criterion. **Leave this true on any path that returns a prediction.** It is false
            only for the card that has just written a version and wants it back, and for
            inspecting an artifact you already know is unpromoted.

    Raises:
        VersionNotFound: no such version, or nothing has been promoted and none was named.
        GatesIncomplete: ``require_gates`` and the version's gates are not all passing.
        PayloadCorrupt: a stored file no longer matches its recorded digest.
        ManifestError: the manifest is unreadable or written in an unknown schema.
    """
    root = _store(store)

    if version is None:
        promoted = current(store=root)
        if promoted is None:
            known = ", ".join(versions(store=root)) or "none"
            raise VersionNotFound(
                f"nothing is promoted in {root}, and no version was named. Versions present: "
                f"{known}. Promote one with hydms.artifacts.promote(), or name it explicitly."
            )
        version = promoted

    directory = version_dir(version, store=root)
    manifest = read_manifest(directory)
    if require_gates:
        _require_established(manifest, directory)

    import joblib

    objects: dict[str, Any] = {}
    for record in manifest.payloads:
        path = directory / record.file
        if not path.is_file():
            raise PayloadCorrupt(
                f"{version} records a payload {record.name!r} in {record.file}, which is not "
                f"in {directory}."
            )
        digest, size = digest_file(path)
        if digest != record.sha256 or size != record.bytes:
            raise PayloadCorrupt(
                f"{version}/{record.file} does not match the manifest: recorded "
                f"sha256 {record.sha256[:12]}... at {record.bytes} bytes, found "
                f"{digest[:12]}... at {size}. An artifact directory is written once and never "
                f"edited; re-run the pipeline rather than trusting this one."
            )
        objects[record.name] = joblib.load(path)

    return Artifacts(
        version=version, directory=directory, manifest=manifest, objects=objects
    )


# --------------------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------------------


def save(
    payloads: Mapping[str, Any],
    *,
    contract: Any,
    seeds: Mapping[str, int] | None = None,
    gates: Any = None,
    notes: str = "",
    version: str | None = None,
    store: Path | None = None,
) -> Manifest:
    """Write a new artifact version and return the manifest recorded beside it.

    Args:
        payloads: The objects to store, by name -- ``{"model": ..., "scaler": ...}``. Each name
            becomes ``<name>.joblib``, so names are lowercase identifiers and nothing else.
        contract: The feature contract the model was fitted against: a
            :class:`~hydms.descriptors.contract.FeatureContract`, or what its ``as_manifest()``
            returned. Not optional -- a model whose column order is unrecorded returns
            plausible, wrong numbers instead of an error, which is what AC-4 exists to catch.
        seeds: Every seed the run used, by name. Defaults to the one configured seed.
        gates: The gate run to embed, either a ``GateReport`` or the mapping its ``to_dict()``
            produced. ``None`` records no run, which is honest and means the version will not
            load without ``require_gates=False`` and cannot be promoted.
        notes: One line for a human reading the promotion history.
        version: Override the assigned version. Defaults to the next free ``v<N>``.
        store: The artifacts directory. Defaults to the configured ``paths.artifacts``.

    Raises:
        ArtifactError: the version already exists, a payload name is not a plain lowercase
            identifier, or ``payloads`` is empty.
        ManifestError: ``gates`` is not a gate report this store can read.
    """
    root = _store(store)
    root.mkdir(parents=True, exist_ok=True)

    if not payloads:
        raise ArtifactError(
            "an artifact version with no payloads records provenance for nothing. Save the "
            "model, the scaler and whatever else the prediction path needs."
        )
    bad = sorted(name for name in payloads if not _PAYLOAD_KEY.match(name))
    if bad:
        raise ArtifactError(
            f"payload name(s) {bad} are not usable as file names. A name is lowercase letters, "
            f"digits and underscores, starting with a letter -- it becomes <name>{_SUFFIX} "
            f"inside the version directory."
        )

    existing = _version_dirs(root)
    if version is None:
        version = f"v{max(existing) + 1 if existing else 1}"
    elif not _VERSION.match(version):
        raise ArtifactError(
            f"{version!r} is not a usable version name. Versions are 'v' followed by a number."
        )
    destination = root / version
    if destination.exists():
        raise ArtifactError(
            f"{destination} already exists. An artifact version is written once: later phases "
            f"pin the version they consume, so overwriting one changes what they pinned. Save "
            f"a new version instead."
        )

    contract_payload = contract.as_manifest() if hasattr(contract, "as_manifest") else contract
    if not isinstance(contract_payload, Mapping) or "features" not in contract_payload:
        raise ArtifactError(
            "contract must be a FeatureContract or what its as_manifest() returned "
            "(a mapping with a 'features' list); got "
            f"{type(contract_payload).__name__}"
        )

    gate_payload = gates.to_dict() if hasattr(gates, "to_dict") else gates
    if gate_payload is not None:
        validate_gate_report(gate_payload)

    if seeds is None:
        from hydms.config import load as load_config

        seeds = {"pipeline": load_config().seed}
    wrong = sorted(name for name, value in seeds.items() if not isinstance(value, int))
    if wrong:
        raise ArtifactError(f"seed(s) {wrong} are not integers; a seed that is not an int is a bug")

    # Staged under a dotted name and renamed into place, so a run that dies part-way through
    # leaves nothing that `versions()` will offer and nothing a later run can half-read.
    staging = root / f".{version}.partial"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    try:
        import joblib

        records: list[PayloadRecord] = []
        for name, obj in payloads.items():
            file_name = f"{name}{_SUFFIX}"
            joblib.dump(obj, staging / file_name)
            digest, size = digest_file(staging / file_name)
            records.append(
                PayloadRecord(name=name, file=file_name, sha256=digest, bytes=size)
            )

        python_version, machine = environment()
        manifest = Manifest(
            version=version,
            created_at=now(),
            # git discovers the work tree from any directory inside it, so the artifacts
            # directory is a fine place to ask from -- and a store outside a repository
            # answers "unknown" rather than raising.
            git=describe_git(root),
            seeds=dict(seeds),
            packages=resolved_packages(),
            python=python_version,
            platform=machine,
            contract=dict(contract_payload),
            payloads=tuple(records),
            gates=dict(gate_payload) if gate_payload is not None else None,
            notes=notes,
        )
        (staging / MANIFEST_NAME).write_text(
            json.dumps(manifest.to_dict(), indent=2) + "\n", encoding="utf-8"
        )
        staging.rename(destination)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    return manifest
