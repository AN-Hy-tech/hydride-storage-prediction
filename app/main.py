"""The forward-prediction page: a formula and a temperature in, an answer you can check out.

    conda run -n Project uvicorn hydms.delivery.api:app --port 8000
    conda run -n Project streamlit run app/main.py

An HTTP client of the prediction service and nothing else. It holds no model, no featuriser
and no plotting code: what to show is decided by :mod:`hydms.delivery.page`, which the test
suite runs, and every chart is a :mod:`hydms.figures` description drawn by
:func:`hydms.figures.render.render`. ``tests/delivery/test_app.py`` reads this file's imports
and fails if it acquires any of those things. Card #82.

``HYDMS_API_URL`` names the service; it defaults to the address ``docs/API.md`` starts it on.
"""

from __future__ import annotations

import os

import streamlit as st
from hydms.delivery.client import DEFAULT_URL, ServiceClient, ServiceUnreachable
from hydms.delivery.page import ANSWERED, REFUSED, UNREACHABLE, prediction_view, unreachable_view
from hydms.figures.render import render

st.set_page_config(page_title="HydMS -- hydrogen capacity", layout="centered")
st.title("Hydrogen storage capacity")
st.caption(
    "Maximum gravimetric capacity of a composition at a temperature, with a calibrated interval "
    "and a verdict on whether the model may answer at all."
)

client = ServiceClient(os.environ.get("HYDMS_API_URL", DEFAULT_URL))

try:
    card = client.model()
except ServiceUnreachable as error:
    view = unreachable_view(error)
    st.error(view.headline)
    for sentence in view.detail:
        st.caption(sentence)
    st.stop()

window = card["trained_ranges"]["temperature"]
with st.form("predict"):
    formula = st.text_input("Composition", value="LaNi5", help="For example LaNi5 or Ti1Fe0.9Mn0.1")
    kelvin = st.number_input(
        f"Temperature (K) -- trained on {window['low']:g} to {window['high']:g} K",
        value=298.0,
        step=25.0,
    )
    asked = st.form_submit_button("Predict")

if asked:
    try:
        view = prediction_view(client.predict(formula, float(kelvin)), card=card)
    except ServiceUnreachable as error:
        view = unreachable_view(error)

    if view.kind == ANSWERED:
        st.success(view.headline)
    elif view.kind in (REFUSED, UNREACHABLE):
        st.error(view.headline)
    else:
        st.warning(view.headline)
    for sentence in view.detail:
        st.write(sentence)

    if view.figure is not None:
        theme = "dark" if st.get_option("theme.base") == "dark" else "light"
        st.pyplot(render(view.figure, theme=theme))
        st.caption(view.figure.caption)

    if view.verdicts:
        st.subheader("Why it was answered" if view.kind == ANSWERED else "Why it was refused")
        for row in view.verdicts:
            mark = "passed" if row.passed else "**failed**"
            st.markdown(f"- `{row.screen}` {mark} (`{row.code}`): {row.reason}")

    if view.version is not None:
        st.caption(f"Answered by artifact version `{view.version}`.")
