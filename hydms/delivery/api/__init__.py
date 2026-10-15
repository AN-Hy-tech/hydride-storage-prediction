"""L6 -- the prediction service. One path in, one contract out, no ML in the handler.

Run it::

    conda run -n Project uvicorn hydms.delivery.api:app --port 8000

``app`` is built at import and loads nothing; the artifact bundle is resolved when the server
starts, and if it cannot be resolved the server does not start. There is no unversioned
fallback and no per-request load, so every answer can name the version that produced it.

::

    POST /v1/predict         one composition and temperature -> an answer or a refusal
    POST /v1/predict/batch   many, in order, with per-row refusals
    GET  /v1/health          liveness, the loaded artifact version, the batch limit
    GET  /v1/model           the model card as data

The interesting design is one layer down, in :mod:`hydms.delivery.api.service`: why a refusal
and a malformed request are both 422 and what separates them, and why nothing here computes.
Card #78.
"""

from .schemas import BatchBody, BatchResponse, Candidate, Health, InvalidRequest, Problem
from .service import MAX_BATCH_ROWS, PREFIX, create_app

#: The application ``uvicorn hydms.delivery.api:app`` serves.
app = create_app()

__all__ = [
    "MAX_BATCH_ROWS",
    "PREFIX",
    "BatchBody",
    "BatchResponse",
    "Candidate",
    "Health",
    "InvalidRequest",
    "Problem",
    "app",
    "create_app",
]
