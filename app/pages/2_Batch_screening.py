"""The batch screening page: a CSV of compositions in, every row's answer or refusal out.

    conda run -n Project uvicorn hydms.delivery.api:app --port 8000
    conda run -n Project streamlit run app/main.py      # this page is in the sidebar

An HTTP client of the prediction service, like the other two pages. What to read, what to show
and what to write is decided by :mod:`hydms.delivery.batch`, which the test suite runs; the
answers come from ``POST /v1/predict/batch`` through
:meth:`~hydms.delivery.client.ServiceClient.predict_many`, which chunks to the limit the service
reports. ``tests/delivery/test_batch.py`` reads this file's imports and fails if it acquires
anything else. Card #84.
"""

from __future__ import annotations

import hashlib
import os

import streamlit as st
from hydms.delivery.batch import (
    FORMULA_HEADERS,
    MAX_UPLOAD_ROWS,
    NAN_IS_FORMULA,
    NAN_IS_MISSING,
    TEMPERATURE_HEADERS,
    UploadError,
    read_upload,
    screening,
)
from hydms.delivery.client import (
    DEFAULT_URL,
    InvalidRequest,
    ServiceClient,
    ServiceError,
    ServiceUnreachable,
)

st.set_page_config(page_title="HydMS -- batch screening", layout="wide")
st.title("Batch screening")
st.caption(
    "Upload a CSV of compositions and temperatures. Every row comes back -- answered with an "
    "estimate, its interval, a domain verdict and a novelty distance, or refused with a reason. "
    "No row is dropped and no refusal is left blank."
)

client = ServiceClient(os.environ.get("HYDMS_API_URL", DEFAULT_URL))
try:
    version = str(client.health()["model_version"])
except ServiceUnreachable as error:
    st.error("The prediction service is not reachable, so nothing can be screened.")
    st.caption(str(error))
    st.stop()

st.markdown(
    f"Two columns are read: a formula column named one of "
    f"{', '.join(f'`{name}`' for name in FORMULA_HEADERS)}, and a temperature column in kelvin "
    f"named one of {', '.join(f'`{name}`' for name in TEMPERATURE_HEADERS)} (any case). Other "
    f"columns are ignored. At most {MAX_UPLOAD_ROWS:,} rows. Answered by model **{version}**."
)
uploaded = st.file_uploader("Candidates (CSV)", type=["csv"])
if uploaded is None:
    st.stop()
data = uploaded.getvalue()

try:
    upload = read_upload(data)
    if upload.needs_decision:
        st.warning(
            f"{len(upload.literal_nan)} formula cell(s) read exactly `NaN`. That is sodium "
            f"nitride to the parser, and it is also how pandas writes a missing value. The page "
            f"will not guess which you meant."
        )
        meaning = st.radio(
            "What does `NaN` in the formula column mean in this file?",
            options=[NAN_IS_MISSING, NAN_IS_FORMULA],
            format_func=lambda option: (
                "A missing value -- do not ask about those rows"
                if option == NAN_IS_MISSING
                else "Sodium nitride (Na1N1) -- ask about them"
            ),
            index=None,
        )
        if meaning is None:
            st.stop()
        upload = read_upload(data, nan_means=meaning)
except UploadError as error:
    st.error("The file cannot be read as a whole.")
    st.caption(str(error))
    st.stop()

# The answers are kept per file and per NaN decision, so changing the ordering below does not
# ask the service again.
key = hashlib.sha256(data + str(upload.nan_means).encode()).hexdigest()
if st.session_state.get("batch-key") != key:
    st.session_state.pop("batch-screening", None)
    st.session_state["batch-key"] = key

asked = upload.requests()
if "batch-screening" not in st.session_state:
    if not st.button(f"Screen {len(asked):,} row(s)", type="primary", disabled=not asked):
        st.caption(f"{len(upload.rows) - len(asked):,} row(s) cannot be read and will be listed.")
        st.stop()
    try:
        with st.spinner(f"Asking model {version} about {len(asked):,} row(s)..."):
            outcome = client.predict_many(asked) if asked else []
    except ServiceUnreachable as error:
        st.error("The prediction service stopped answering part-way; nothing is shown.")
        st.caption(str(error))
        st.stop()
    except ServiceError as error:
        # A batch the service failed on as a whole -- today, one row whose band came back
        # crossed (card #94) -- is said, never shown as the rows either side of it.
        st.error("The service failed on this batch, and no row of it is shown.")
        st.caption(str(error))
        st.stop()
    if isinstance(outcome, InvalidRequest):
        st.error("The service rejected the batch whole.")
        st.caption(outcome.message)
        for problem in outcome.problems:
            st.caption(problem)
        st.stop()
    st.session_state["batch-screening"] = screening(upload, outcome, version=version)

result = st.session_state["batch-screening"]
for sentence in result.summary():
    st.info(sentence)

widest = st.toggle("Widest interval first -- the least certain answers at the top")
st.dataframe(result.shown(by_width=widest), hide_index=True, use_container_width=True)
st.download_button(
    f"Download all {len(result.records):,} rows (model {result.version})",
    data=result.to_csv(by_width=widest),
    file_name=result.file_name,
    mime="text/csv",
)
