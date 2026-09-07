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

Still to come: ``predict.py`` over an immutable artifact bundle (#76), ``api/`` (#78), and the
Streamlit pages that are HTTP clients of it (#82-#84).

No candidate is published without both its distance to the nearest known alloy and its
prediction interval width (AC-7) — which is why
:attr:`~hydms.delivery.contract.PredictionResult.novelty` is a field a caller must fill in
rather than one it can forget.
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
)

__all__ = [
    "ADMITTED",
    "INDETERMINATE",
    "SCHEMA",
    "SPACE",
    "UNIT",
    "Answer",
    "ContractError",
    "DomainVerdict",
    "Interval",
    "Novelty",
    "PredictionRequest",
    "PredictionResult",
    "Refusal",
    "ScreenVerdict",
    "answer_from",
    "delivery_screens",
    "reason_codes",
]
