"""L0 — the versioned artifact store and its manifest.

The only way a model, scaler or split reaches disk or comes back. Promotion is a
manifest pointer, which is what makes rollback a one-line change rather than a retrain.

Two doors::

    from hydms import artifacts

    artifacts.save({"model": model, "scaler": scaler}, contract=CONTRACT, gates=report)
    bundle = artifacts.load()          # the promoted version, gates checked
    bundle["scaler"].transform(X)      # never .fit

:mod:`~hydms.artifacts.store` owns the layout, the immutability rule and the gate check;
:mod:`~hydms.artifacts.manifest` owns what is recorded and how it is read back. Card #4.
"""

from .manifest import (
    GATE_SCHEMA,
    RECORDED_PACKAGES,
    SCHEMA,
    ArtifactError,
    Git,
    Manifest,
    ManifestError,
    PayloadRecord,
)
from .store import (
    Artifacts,
    GatesIncomplete,
    PayloadCorrupt,
    VersionNotFound,
    WaiverRefused,
    current,
    load,
    promote,
    read_manifest,
    save,
    version_dir,
    versions,
    waived,
)

__all__ = [
    "GATE_SCHEMA",
    "RECORDED_PACKAGES",
    "SCHEMA",
    "ArtifactError",
    "Artifacts",
    "GatesIncomplete",
    "Git",
    "Manifest",
    "ManifestError",
    "PayloadCorrupt",
    "PayloadRecord",
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
