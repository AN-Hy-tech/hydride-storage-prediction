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

**What git carries, and how** (card #7). ``current.json`` and every ``v<N>/`` are tracked;
``gate-results.json`` and a ``.v<N>.partial`` staging directory are not. A ``.joblib`` payload
travels through Git LFS, while ``manifest.json`` and ``current.json`` stay plain text, so a
clone that never ran ``git lfs pull`` can still read what a version is and whether it passed.
It cannot load one: :func:`load` finds an LFS pointer where a pickle should be and raises
:class:`PayloadNotFetched`, which says what to run. ``tests/artifacts/test_portability.py``
pins those four routing rules against ``.gitignore`` and ``.gitattributes``.

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

**Promotion is a pointer, and it is the only place a criterion may be set aside.**
``current.json`` names a version, so rollback is one small write rather than a retrain (card
#7). It may also name **waivers**: criteria that this promotion is knowingly proceeding without.
The reason that mechanism is here, and not in the manifest or in the gate harness, is card #34's
wall and is worth stating in full, because the shape of the answer is the argument for it.

Phase H fits a forward surrogate. Three registered criteria -- AC-5, AC-7 and AC-8 -- belong to
phases ``docs/FREEZE.md`` has frozen: there is no entropy model, no candidate list and no search
in this phase, and no amount of Phase H work makes them green. On the rule as first written, the
phase therefore ends with a correct model that can never be promoted, and because :func:`load`
refuses an unpromoted version, ``predict()`` cannot answer at all. Three shapes were considered
and two rejected:

  - **A phase-scoped subset computed at promotion time** -- rejected. It makes "in scope" a
    thing a session derives, and a derived scope is one that widens quietly.
  - **A fourth gate status, ``NOT APPLICABLE``** -- rejected, and this is the one the gate
    harness makes cheapest, which is why it was looked at hardest. It would put the judgement
    inside the criterion, where it is invisible at the moment of promotion and one edit away
    from being applied to a criterion that *is* applicable. It also corrupts the manifest: the
    embedded report would stop being a record of what was measured.

What is implemented instead is narrower than either. **A waiver is an act, not a property.** It
is named at promotion, one criterion at a time, never by pattern; it is written into
``current.json`` where a reviewer reads it in a diff; it carries the *gate's own* statement of
why it did not run rather than prose invented at the prompt; and it dies with the promotion --
:func:`load` honours a waiver only for the version ``current.json`` actually points at, so a
waiver cannot be smuggled onto a version by naming it.

Three properties hold it shut:

  - **A failure is never waivable.** :func:`promote` refuses a waiver naming a criterion whose
    recorded status is anything but ``SKIPPED``. A waiver may say "this was not checked, and
    here is the check's own account of why it could not be"; it can never say "this was checked
    and did not hold".
  - **A stale waiver is refused too.** Naming a criterion that passed, or one the report does
    not record at all, is an error rather than a no-op -- otherwise the list rots into
    decoration and stops being read.
  - **The manifest never learns about waivers.** ``Manifest.unestablished()`` is unchanged and
    still counts ``SKIPPED`` as unestablished; the embedded report still says AC-5 was skipped.
    The artifact's record of what was *measured* stays exactly as truthful as it was, and the
    decision to ship anyway is recorded somewhere else, under someone's name, in a file that is
    one line long.

Whether a waiver is *legitimate* -- whether the criterion really does belong to a frozen phase
rather than to work somebody skipped -- is a question about the board, and this module has no
business knowing what a board is. It is not answered here and it is not answered by inspecting
``current.json`` either: when this was written ``artifacts/`` was gitignored, so a pointer file
never reached CI. Card #7 now commits it, but the answer below derives the waivable set from the
repository and does not depend on one.

It is answered instead by ``tests/artifacts/test_waiver_scope.py``, which derives the waivable
set from the repository rather than from anyone's memory: it reads each registered gate's card
number, asks which board directory holds that card, and pins the answer. Today exactly three
criteria have their card on the frozen board, and those three are the only ones a Phase H
promotion may waive. A card that crosses between boards, or a newly registered criterion owned
by a frozen phase, turns that test red and forces the question to be asked again out loud.

Card #4; the waiver is card #34.
"""

from __future__ import annotations

import json
import re
import shutil
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
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
    "PayloadNotFetched",
    "VersionNotFound",
    "WaiverRefused",
    "current",
    "load",
    "promote",
    "read_manifest",
    "save",
    "version_dir",
    "versions",
    "waived",
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


def staging_name(version: str) -> str:
    """The directory :func:`save` writes ``version`` into before renaming it into place.

    Named here, not inline, because ``.gitignore`` must keep it out of git while admitting
    ``v<N>/`` itself, and the test that pins that rule asks this function rather than
    repeating the spelling (card #7).
    """
    return f".{version}.partial"


class VersionNotFound(ArtifactError, LookupError):
    """No such artifact version, or the promotion pointer names one that is gone."""


class GatesIncomplete(ArtifactError):
    """A version's recorded gate run did not establish every criterion.

    Raised by :func:`load` and :func:`promote`. It names the gates and their statuses, because
    "gates incomplete" without the list costs the reader the run again.
    """


class WaiverRefused(ArtifactError, ValueError):
    """A promotion asked to waive a criterion a waiver is not allowed to cover.

    Separate from :class:`GatesIncomplete` because it is a different mistake with a different
    fix: the version is not necessarily unpromotable, the *waiver list* is wrong.
    """


class PayloadCorrupt(ArtifactError):
    """A stored file does not match the digest its manifest recorded for it."""


class PayloadNotFetched(ArtifactError):
    """A payload is a Git LFS pointer: the clone has the version's record but not its bytes.

    Not a :class:`PayloadCorrupt`, because the fix is the opposite one. A corrupt payload says
    "re-run the pipeline, do not trust this"; an unfetched one says "run ``git lfs pull``" --
    the bytes exist and the manifest's digest will verify them once they arrive. A caller that
    treats an absent model as absent rather than broken (the gates' :class:`NoCandidate`) can
    catch this one alone.
    """


#: Every Git LFS pointer opens with this line (the LFS spec, v1). ``hawser`` is the spec's
#: pre-release name, and git-lfs still accepts pointers written with it.
_LFS_POINTER_HEADS = (
    b"version https://git-lfs.github.com/spec/v1",
    b"version https://hawser.github.com/spec/v1",
)

#: The spec caps a pointer at 1024 bytes, so anything larger is a real payload and is not read.
_LFS_POINTER_MAX_BYTES = 1024


def _is_lfs_pointer(path: Path) -> bool:
    if path.stat().st_size > _LFS_POINTER_MAX_BYTES:
        return False
    head = path.read_bytes()
    return head.startswith(_LFS_POINTER_HEADS)


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


def waived(*, store: Path | None = None) -> Mapping[str, str]:
    """The criteria the standing promotion set aside, by name, with the reason recorded.

    Empty for a promotion that waived nothing, which is every promotion the rule as originally
    written could make. Read it before quoting what an artifact has established: a version whose
    ``current.json`` waives AC-7 has not established AC-7, and says so.
    """
    pointer = _store(store) / CURRENT_POINTER
    if not pointer.is_file():
        return {}
    try:
        payload = json.loads(pointer.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactError(f"{pointer} could not be read: {exc}") from exc
    recorded = payload.get("waived") if isinstance(payload, Mapping) else None
    if not isinstance(recorded, Mapping):
        return {}
    return {str(name): str(reason) for name, reason in recorded.items()}


def promote(
    version: str,
    *,
    store: Path | None = None,
    waive: Mapping[str, str] | None = None,
) -> str:
    """Point ``current`` at ``version``, refusing anything its gates did not establish.

    This is the promotion half of card #7: a full run produces ``v{N+1}``, the gates run against
    it, and only a complete pass moves the pointer. Rolling back is the same call with the older
    version -- one small write, no retrain.

    Args:
        version: The version to promote.
        store: The artifacts directory.
        waive: Criteria this promotion proceeds without, as ``{name: reason}``. Every name must
            be recorded ``SKIPPED`` in the version's own gate report -- a failed criterion is
            never waivable, and a criterion that passed or that the report does not mention is a
            stale entry and is refused rather than ignored. The mapping is written into
            ``current.json`` and is what :func:`load` and :func:`waived` read back. This
            module's docstring argues why the mechanism lives here and nowhere else; whether a
            given waiver is legitimate is ``scripts/check_board.py``'s question, not this one's.

    Raises:
        VersionNotFound: no such version.
        GatesIncomplete: its manifest records no gate run, or a gate that did not pass and was
            not waived.
        WaiverRefused: a waiver names a criterion that failed, passed, or was never recorded.
    """
    root = _store(store)
    directory = version_dir(version, store=root)
    manifest = read_manifest(directory)
    requested = dict(waive or {})
    _check_waivers(manifest, directory, requested)
    _require_established(manifest, directory, waived=frozenset(requested))

    pointer = root / CURRENT_POINTER
    record: dict[str, Any] = {"version": version, "promoted_at": now()}
    if requested:
        record["waived"] = requested
    pointer.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
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


def _standing_waivers(root: Path, version: str) -> Mapping[str, str]:
    """The waivers that apply to ``version``, which is none unless it is the promoted one.

    A waiver belongs to the **promotion**, not to the store and not to the version: naming an
    older version explicitly gets the unwaived rule, which is what stops a waiver from being
    inherited by an artifact nobody promoted under it.

    A pointer that cannot be read yields no waivers rather than raising. That leniency is safe
    in one direction only, and that is why it is allowed: with no waivers :func:`load` applies
    the *full* rule, so a broken pointer can make this function refuse more and never less. The
    loud reading of a bad pointer stays where it belongs -- :func:`current`, which is what a
    caller asking "what is promoted?" goes through, and what ``load(version=None)`` calls.
    """
    try:
        if current(store=root) != version:
            return {}
        return waived(store=root)
    except ArtifactError:
        return {}


def _check_waivers(manifest: Manifest, directory: Path, requested: Mapping[str, str]) -> None:
    """Refuse a waiver that is not what a waiver is allowed to be.

    Three refusals, and each closes a different way the list could stop meaning anything: a
    failure waived away, a criterion waived that in fact passed, and a name that matches nothing
    in the report at all -- a typo, or a criterion that has since been renamed, either of which
    would otherwise present as a silently narrower promotion.
    """
    if not requested:
        return
    recorded = {
        str(entry.get("name", "?")): str(entry.get("status", "?"))
        for entry in (manifest.gates or {}).get("gates", ())
    }
    for name, reason in requested.items():
        status = recorded.get(name)
        if status is None:
            known = ", ".join(sorted(recorded)) or "none"
            raise WaiverRefused(
                f"{directory.name}'s gate report records no criterion named {name!r}, so "
                f"waiving it would narrow the promotion by a name nothing answers to. "
                f"Recorded: {known}."
            )
        if status == "PASSED":
            raise WaiverRefused(
                f"{name} PASSED against {directory.name}; waiving it claims less than the "
                f"artifact has established. Remove it from the waiver list."
            )
        if status != "SKIPPED":
            raise WaiverRefused(
                f"{name} is {status} against {directory.name} and a waiver cannot cover it. A "
                f"waiver says a criterion was not checked and why; it can never say a criterion "
                f"was checked and did not hold."
            )
        if not reason.strip():
            raise WaiverRefused(
                f"{name} is waived with no reason. The reason is the gate's own account of why "
                f"it did not run, and a waiver nobody can read is one nobody will revisit."
            )


def _require_established(
    manifest: Manifest, directory: Path, *, waived: frozenset[str] = frozenset()
) -> None:
    if not manifest.gate_run_recorded:
        raise GatesIncomplete(
            f"{directory.name} records no gate run, so nothing about it has been established. "
            f"Run `python -m hydms.gates run --all` and save the version with its report, or "
            f"pass require_gates=False if you are inspecting an unpromoted artifact."
        )
    outstanding = tuple(
        (name, status) for name, status in manifest.unestablished() if name not in waived
    )
    if outstanding:
        recorded = len(manifest.gates["gates"]) if manifest.gates else 0
        listed = ", ".join(f"{name} {status}" for name, status in outstanding)
        note = (
            f" {len(waived)} other(s) are waived by the standing promotion: "
            f"{', '.join(sorted(waived))}."
            if waived
            else ""
        )
        raise GatesIncomplete(
            f"{directory.name} did not establish {len(outstanding)} of {recorded} recorded "
            f"gates: {listed}. A SKIPPED gate is a criterion nobody checked, which is why it "
            f"counts here even though the harness tolerates it in a CI log.{note}"
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
    #: Criteria the standing promotion set aside, by name, with the reason. Empty unless this
    #: version is the promoted one *and* its promotion waived something. A delivery path that
    #: reports what a prediction rests on reads this, because the manifest deliberately does
    #: not know about it -- see this module's docstring.
    waived: Mapping[str, str] = field(default_factory=dict)

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
        PayloadNotFetched: a payload is a Git LFS pointer, not yet pulled.
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
    standing = _standing_waivers(root, version)
    if require_gates:
        _require_established(manifest, directory, waived=frozenset(standing))

    import joblib

    unfetched = [
        record.file
        for record in manifest.payloads
        if (directory / record.file).is_file() and _is_lfs_pointer(directory / record.file)
    ]
    if unfetched:
        raise PayloadNotFetched(
            f"{version} is checked out but its payloads are not: {', '.join(unfetched)} "
            f"{'is a Git LFS pointer' if len(unfetched) == 1 else 'are Git LFS pointers'}, "
            f"not the pickled object. Run `git lfs install` once, then `git lfs pull`; the "
            f"manifest's digests verify the bytes when they arrive."
        )

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
        version=version,
        directory=directory,
        manifest=manifest,
        objects=objects,
        waived=standing,
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
    staging = root / staging_name(version)
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
