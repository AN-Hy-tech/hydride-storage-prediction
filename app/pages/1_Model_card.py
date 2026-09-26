"""The model-card page: what the model is, how well it does, and how it is most easily overstated.

    conda run -n Project uvicorn hydms.delivery.api:app --port 8000
    conda run -n Project streamlit run app/main.py      # this page is in the sidebar

An HTTP client of the prediction service, like the forward page. Every number comes from
``GET /v1/evidence``, ``GET /v1/evidence/parity`` and ``GET /v1/model``, so it is the snapshot
the service's refusals are judged against (ADR 0007). What to say is decided by
:mod:`hydms.delivery.modelcard_page`, which the test suite runs, and every chart is a
:mod:`hydms.figures` description drawn by :func:`hydms.figures.render.render`.
``tests/delivery/test_model_card.py`` reads this file's imports and fails if it acquires
anything else. Card #83.
"""

from __future__ import annotations

import os

import streamlit as st
from hydms.delivery.client import DEFAULT_URL, ServiceClient, ServiceUnreachable
from hydms.delivery.modelcard_page import CardPageError, model_card_view
from hydms.figures.render import render

st.set_page_config(page_title="HydMS -- model card", layout="wide")
st.title("Model card")
st.caption(
    "Three readings of one model, their intervals, the families it transfers to and the ones it "
    "does not, and the limits a reader should know before quoting a number."
)

client = ServiceClient(os.environ.get("HYDMS_API_URL", DEFAULT_URL))

try:
    view = model_card_view(client.evidence(), client.parity(), client.model())
except ServiceUnreachable as error:
    st.error("The prediction service is not reachable, so this page has nothing to show.")
    st.caption(str(error))
    st.stop()
except CardPageError as error:
    st.error("The service's evidence is incomplete, and the page will not guess the rest.")
    st.caption(str(error))
    st.stop()

theme = "dark" if st.get_option("theme.base") == "dark" else "light"
for section in view.sections:
    st.header(section.title)
    for paragraph in section.paragraphs:
        st.markdown(paragraph)
    if section.table is not None:
        st.table([dict(zip(section.table.columns, row, strict=True)) for row in section.table.rows])
    if section.figure is not None:
        st.pyplot(render(section.figure, theme=theme))
        st.caption(section.figure.caption)
    if section.caption:
        st.caption(section.caption)
