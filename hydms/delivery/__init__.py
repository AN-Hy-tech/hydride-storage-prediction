"""L6 — the boundary users meet: one prediction path, and the vocabulary it answers in.

The design rule of stage S6 is that **one deep module owns prediction** and the API and the
interface are thin transports with no ML logic in them. Everything behind
``predict_capacity()`` — parsing, canonicalisation, featurisation, column order, scaling,
quantile assembly, conformal widening, the applicability check — is hidden, and what comes out
is a type that cannot represent a bare number.

``contract.py``
    The vocabulary every consumer speaks: :class:`~hydms.delivery.contract.PredictionRequest`,
    :class:`~hydms.delivery.contract.PredictionResult`,
    :class:`~hydms.delivery.contract.Refusal`, and the reason codes —
    **enumerated from the screens**, never written down here. It is also the structural half
    of gate HG-2: a result has no default for its interval and none for its domain verdict, so
    a point estimate on its own is unspellable. Card #75.

``predict.py``
    The path itself: :func:`~hydms.delivery.predict.predict_capacity`, over an immutable,
    version-stamped :class:`~hydms.delivery.predict.ArtifactBundle` that loads once. Null
    check, featurise, predict, screen, resolve, answer — and a formula that will not parse is
    caught where it raises and comes back as a refusal carrying the parse error's own
    sentence. Card #76. :func:`~hydms.delivery.predict.predict_many` is the same path over a
    whole batch at once, and ``predict_capacity`` is its one-row case (card #84).


``modelcard.py``
    What the deployment can honestly say about itself — the version, when it was fitted, what
    has been certified about it, and the ranges its screens enforce — assembled from the live
    bundle rather than from a document. ``GET /v1/model`` serialises it and #83's page renders
    it. Card #78.

``api/``
    The HTTP boundary: ``POST /v1/predict``, ``POST /v1/predict/batch``, ``GET /v1/health``,
    ``GET /v1/model``. A transport with no ML logic in it, holding one bundle for the life of
    the process. **Not imported here** — ``import hydms.delivery`` must not require FastAPI,
    because the library is what a notebook and the batch path use. Card #78.

Still to come: the Streamlit pages, which are HTTP clients of ``api/`` rather than in-process
callers of this package (#82-#84).

No candidate is published without both its distance to the nearest known alloy and its
prediction interval width (AC-7) — which is why
:attr:`~hydms.delivery.contract.PredictionResult.novelty` is a field a caller must fill in
rather than one it can forget, and why card #76 put the ElMD novelty screen into
:func:`~hydms.delivery.contract.delivery_screens` rather than leaving the distance optional.
"""

from .contract import (
    ADMITTED,
    INDETERMINATE,
    SCHEMA,
    SPACE,
    UNIT,
    Answer,
    ContractError,
    DomainVerdict,
    Interval,
    Novelty,
    PredictionRequest,
    PredictionResult,
    Refusal,
    ScreenVerdict,
    answer_from,
    delivery_screens,
    reason_codes,
    resolve,
)
from .predict import (
    ArtifactBundle,
    DeliveryError,
    clear_cache,
    load_bundle,
    predict_capacity,
    predict_many,
)

__all__ = [
    "ADMITTED",
    "INDETERMINATE",
    "SCHEMA",
    "SPACE",
    "UNIT",
    "Answer",
    "ArtifactBundle",
    "ContractError",
    "DeliveryError",
    "DomainVerdict",
    "Interval",
    "Novelty",
    "PredictionRequest",
    "PredictionResult",
    "Refusal",
    "ScreenVerdict",
    "answer_from",
    "clear_cache",
    "delivery_screens",
    "load_bundle",
    "predict_capacity",
    "predict_many",
    "reason_codes",
    "resolve",
]
