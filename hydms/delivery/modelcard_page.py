"""L6 -- what the model-card page says, decided here and not in Streamlit.

The page is the counterweight to the optimistic number (card #83). A reader forms a belief about
how good this model is from whatever is on offer, and three overstatements are the likely ones:
the random-split score taken as *the* score, a material wt% compared with a DOE onboard-storage
target, and the published figures inherited as though nothing had changed. Every section below
exists to pre-empt one of them, or to state a limit a reader would otherwise have to discover.

**Everything is read from the service, never from a file.** The scores, intervals and scored
rows come from ``GET /v1/evidence`` and ``GET /v1/evidence/parity``. The version, training date,
ranges and screens come from ``GET /v1/model``. So the page shows the snapshot the refusals beside
it were judged against (ADR 0007). ``app/pages/1_Model_card.py`` renders what this returns and
decides nothing, and ``tests/delivery/test_model_card.py`` reads its imports to keep it so.

**What is typed here, and how it is kept honest.** A handful of limits are facts about the data
and the feature tables that no route serves: the Gordy filler, the gadolinium placeholder, the
selection's stability and the one impossible validation label. They are :data:`LIMIT_FACTS`, and
a test recomputes each one from its committed source. Everything else on the page is a value
copied from a payload, and no number on it is rounded before it is quoted with its interval.

**A score that is absent is shown as absent, with its reason.** The page never drops a row to
look tidier. A missing transfer score with the procedure score standing alone is exactly the
page this card exists to prevent.

Card #83.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from hydms.figures import Figure
from hydms.figures.charts import FigureError, ParityPoint, parity

__all__ = [
    "LIMIT_FACTS",
    "RECONCILIATION",
    "CardPageError",
    "ModelCardView",
    "Section",
    "Table",
    "model_card_view",
]

#: Where the previously published figures are reconciled against the committed evidence. A
#: repository path: the page is a client and does not serve the document itself.
RECONCILIATION: Final = "docs/REPORT-RECONCILIATION.md"

#: The limits no route serves, each recomputed from its source by the test suite.
LIMIT_FACTS: Final[Mapping[str, Any]] = {
    # reports/feature_selection/feature-row-cost.csv, dev_Gordy_electonegativity.
    "gordy_rows_blocked": 266,
    "curated_rows": 1279,
    # hydms.surrogate.comparison.placeholder_exposure(): voro_coord = 1.0 for Gd.
    "placeholder_element": "Gd",
    "placeholder_rows": 18,
    # reports/feature_selection/selection-stability.csv.
    "selection_candidates": 21,
    "selection_unanimous": 14,
    "selection_folds": 5,
    # The raw data and #13's split: the impossible label, and where it sits.
    "impossible_formula": "Ce1Ni4Cr1",
    "impossible_capacity": 4.73,
    "impossible_hm": 3.339,
    "impossible_split": "val",
}

#: The two parity panels, in the order they are read: the optimistic protocol first, so the
#: honest one is what the eye lands on second and stays on.
_PANELS: Final = (
    ("procedure", "random split, out-of-fold"),
    ("transfer", "leave one alloy family out"),
)

#: What each reading answers, in the words the page uses.
_ANSWERS: Final = {
    "procedure": (
        "How well the modelling method does, out-of-fold across five folds of the training "
        "rows. From five models, none of which is shipped."
    ),
    "artifact": (
        "How well the one promoted model does on the held-out test split, scored once."
    ),
    "transfer": (
        "How well the method does on an alloy family it never saw, averaged so every family "
        "counts once. The only one of the three that speaks to inverse design."
    ),
}


class CardPageError(ValueError):
    """A payload is missing something the page cannot state honestly without."""


@dataclass(frozen=True)
class Table:
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]

    def __post_init__(self) -> None:
        for row in self.rows:
            if len(row) != len(self.columns):
                raise CardPageError(f"a row of {len(row)} cells under {len(self.columns)} columns")


@dataclass(frozen=True)
class Section:
    """One block of the page: a heading, sentences, and at most one table and one figure."""

    key: str
    title: str
    paragraphs: tuple[str, ...] = ()
    table: Table | None = None
    figure: Figure | None = None
    caption: str = ""


@dataclass(frozen=True)
class ModelCardView:
    version: str
    digest: str
    sections: tuple[Section, ...]

    def section(self, key: str) -> Section:
        for found in self.sections:
            if found.key == key:
                return found
        raise KeyError(key)

    @property
    def text(self) -> str:
        """Every sentence and cell on the page, for tests that ask what the page says."""
        parts: list[str] = []
        for found in self.sections:
            parts += [found.title, *found.paragraphs, found.caption]
            if found.table is not None:
                parts += [" | ".join(found.table.columns)]
                parts += [" | ".join(row) for row in found.table.rows]
            if found.figure is not None:
                parts += [found.figure.title, found.figure.caption]
        return "\n".join(part for part in parts if part)


# --------------------------------------------------------------------------------------
# Reading the payloads
# --------------------------------------------------------------------------------------


def _scores(evidence: Mapping[str, Any]) -> dict[tuple[str, str, str], Mapping[str, Any]]:
    scores = evidence.get("scores")
    if not isinstance(scores, list) or not scores:
        raise CardPageError(
            "the evidence payload carries no scores. The page will not show a model card "
            "without the three readings, because a card with none reads as a card with no "
            "problems."
        )
    return {(s["reading"], s["quantity"], s["subject"]): s for s in scores}


def _get(scores: Mapping[tuple[str, str, str], Mapping[str, Any]], *key: str) -> Mapping[str, Any]:
    try:
        return scores[(key[0], key[1], key[2] if len(key) > 2 else "all")]
    except KeyError:
        raise CardPageError(f"the evidence payload has no {' '.join(key)} score") from None


def _figure(value: float, unit: str = "") -> str:
    """A number as the page prints it: four places, and the unit if it has one."""
    text = f"{value:.4f}"
    return f"{text} {unit}" if unit else text


def _value(score: Mapping[str, Any]) -> str:
    if score["value"] is None:
        return "absent"
    return _figure(float(score["value"]), "wt%" if score["unit"] == "wt%" else "")


def _interval(score: Mapping[str, Any]) -> str:
    if score["value"] is None:
        return f"absent: {score['absent_because']}"
    interval = score.get("interval")
    if interval is None:
        return f"none: {score['no_interval_because']}"
    return (
        f"[{interval['low']:.4f}, {interval['high']:.4f}] "
        f"({interval['confidence'] * 100:.0f} %, {interval['resampled']})"
    )


def run_text(run: Mapping[str, Any]) -> str:
    """Which run a score came from, with the run date and the commit kept apart."""
    parts = [f"run date {run['run_date_text']}"]
    if run.get("version"):
        parts.insert(0, f"artifact {run['version']}, {run['kind']}")
    if run.get("commit"):
        parts.append(f"ran at commit {str(run['commit'])[:7]}")
    if run.get("committed_in"):
        parts.append(f"tables committed in {run['committed_in']} (a commit, not a run date)")
    return "; ".join(parts)


# --------------------------------------------------------------------------------------
# The sections
# --------------------------------------------------------------------------------------


def _what(card: Mapping[str, Any], evidence: Mapping[str, Any]) -> Section:
    interval = card.get("interval", {})
    notes = str((card.get("provenance") or {}).get("notes") or "")
    return Section(
        key="what",
        title="What this model is",
        caption=(
            f"The manifest's own note on this version: {notes}" if notes else ""
        ),
        paragraphs=(
            f"Artifact version **{card['version']}**, trained "
            f"{card.get('trained_at') or 'on a date its manifest does not record'}. It predicts "
            f"the **maximum** gravimetric hydrogen capacity of a composition at a temperature, "
            f"in wt%, from {len(card.get('features', ()))} inputs that are all composition "
            f"statistics or the temperature. Every answer carries a band calibrated to a "
            f"nominal {float(interval.get('confidence_level', 0.8)) * 100:.0f} % and a verdict "
            f"from three screens on whether the model may answer at all.",
            f"Evidence digest `{str(evidence.get('digest', ''))[:12]}`: the tables this page is "
            f"read from, as the service read them when it started.",
        ),
    )


def _three_scores(
    scores: Mapping[tuple[str, str, str], Mapping[str, Any]], evidence: Mapping[str, Any]
) -> Section:
    readings = (
        ("procedure", "Procedure score", _get(scores, "procedure", "r2")),
        ("artifact", "Artifact score", _get(scores, "artifact", "r2")),
        ("transfer", "Transfer score", _get(scores, "transfer", "r2", "macro")),
    )
    rows = tuple(
        (name, _value(score), _interval(score), _ANSWERS[reading], run_text(score["run"]))
        for reading, name, score in readings
    )
    facts = evidence.get("artifact_facts") or {}
    procedure, artifact, transfer = (score for _, _, score in readings)
    paragraphs = [
        "Three R² values, all wt%, and they answer three different questions. Quoting one "
        "without the other two is how a model is overstated: the procedure and artifact "
        "scores are about rows like the training rows, and only the transfer score is about "
        "a family nobody has measured yet.",
    ]
    if procedure["value"] is not None and artifact["value"] is not None:
        grown = facts.get("rows_grown_on")
        paragraphs.append(
            f"The procedure score ({_figure(float(procedure['value']))}) comes from five models "
            f"scored out-of-fold over {procedure['rows']} training rows. The artifact score "
            f"({_figure(float(artifact['value']))}) is the one shipped model, scored once on "
            f"{artifact['rows']} test rows"
            + (
                f". That model grew on {int(grown)} rows, because the band's calibration rows "
                f"and the early-stopping rows were carved out first, while each cross-validation "
                f"fold was cut from all {procedure['rows']}"
                if grown is not None
                else ""
            )
            + ". The two are close, which is evidence the procedure is stable. They are not the "
            "same number."
        )
    if transfer["value"] is not None and procedure["value"] is not None:
        paragraphs.append(
            f"The transfer score is {_figure(float(transfer['value']))}, against "
            f"{_figure(float(procedure['value']))} for the procedure. That gap is the finding: "
            f"the model interpolates within families it has seen and transfers poorly to new "
            f"ones, as the hydride literature reports. It is why the service refuses rather "
            f"than guesses outside its domain."
        )
    paragraphs.append(
        "Transfer run: the leave-one-alloy-class-out protocol was run twice with seed 42 and "
        "the scores moved between the runs (card #104). The cause, a parallel forest in the "
        "label screen, has since been fixed, but the run shown is one draw from the old spread, "
        "and its interval prices the sampling of materials only."
    )
    return Section(
        key="scores",
        title="How well it does: three readings, side by side",
        paragraphs=tuple(paragraphs),
        table=Table(("score", "R²", "95 % interval", "what it answers", "run"), rows),
    )


def _other_quantities(scores: Mapping[tuple[str, str, str], Mapping[str, Any]]) -> Section:
    names = (
        ("rmse", "RMSE"),
        ("mae", "MAE"),
        ("interval_coverage", "band coverage"),
        ("interval_width", "band mean width"),
    )
    rows = []
    for quantity, label in names:
        for reading in ("procedure", "artifact"):
            score = _get(scores, reading, quantity)
            rows.append((label, reading, _value(score), _interval(score)))
    return Section(
        key="quantities",
        title="The other quantities, for the two readings that report them",
        paragraphs=(
            "The procedure's band is the raw 10th-90th percentile heads, out-of-fold, before "
            "calibration. The artifact's band is the calibrated one the service serves. Their "
            "coverages differ for that reason, not because either run was better.",
        ),
        table=Table(("quantity", "reading", "value", "95 % interval"), tuple(rows)),
    )


def _parity(parity_payload: Mapping[str, Any], coverage: Mapping[str, Any]) -> Section:
    readings = parity_payload.get("readings") or {}
    points: dict[str, list[ParityPoint]] = {}
    absent: list[str] = []
    for reading, label in _PANELS:
        entry = readings.get(reading) or {}
        rows = entry.get("rows") or []
        if not rows:
            absent.append(f"The {label} panel has no rows: {entry.get('absent_because')}")
            continue
        points[label] = [
            ParityPoint(
                measured=row["measured"],
                predicted=row["predicted"],
                lower=row["lower"],
                upper=row["upper"],
            )
            for row in rows
        ]
    transfer_run = (readings.get("transfer") or {}).get("run")
    run_line = (
        f"Leave-one-family-out rows: {run_text(transfer_run)}. They are one run's rows, and a "
        f"second seeded run gave different ones (card #104)."
        if transfer_run
        else ""
    )
    band = parity_payload.get("band", "")
    if absent:
        # parity() refuses a single panel, and that refusal is kept: one protocol alone is the
        # optimistic number on its own page. The page says what is missing instead.
        return Section(
            key="parity",
            title="Predicted against measured",
            paragraphs=(
                *absent,
                "The figure is not drawn with one panel: a parity plot of one protocol is the "
                "optimistic number presented alone.",
            ),
        )
    try:
        figure = parity(points, level=float(parity_payload.get("level", 0.8)))
    except FigureError as error:
        raise CardPageError(str(error)) from error
    return Section(
        key="parity",
        title="Predicted against measured",
        paragraphs=(
            "Each point is a training row, predicted by a model that never saw it. On the left "
            "the rows were held out at random, so the same family was always in training. On "
            "the right the whole family was held out.",
        ),
        figure=figure,
        caption=(
            f"The bands are {band}. Out-of-fold on the random split they cover "
            f"{_value(coverage)} of rows against the nominal "
            f"{float(parity_payload.get('level', 0.8)):g}, which is why the service calibrates "
            f"the band it serves. {run_line}"
        ),
    )


def _families(scores: Mapping[tuple[str, str, str], Mapping[str, Any]], card: Mapping[str, Any]) -> Section:
    families = sorted(
        (score for key, score in scores.items() if key[0] == "transfer" and key[2].startswith("family:")),
        key=lambda score: score["subject"],
    )
    floor = None
    for screen in card.get("screens", ()):
        limit = (screen.get("limits") or {}).get("min_transfer_r2")
        if limit is not None:
            floor = float(limit)
    rows = []
    for score in families:
        family = score["subject"].split(":", 1)[1]
        verdict = ""
        if floor is not None and score["value"] is not None:
            verdict = "refused (untrusted-family)" if float(score["value"]) < floor else "answered"
        rows.append((family, str(score.get("rows") or ""), _value(score), _interval(score), verdict))
    lead = [
        "Read every score against its support. An R² over 19 held-out rows and one over 260 are "
        "not the same claim, and the intervals say how much each would move with a different "
        "sample of materials from the same family.",
    ]
    if floor is not None:
        lead.append(
            f"The domain screen refuses a candidate from any family whose transfer score is "
            f"below {floor:g}: the model has shown it cannot predict that family better than "
            f"its mean."
        )
    return Section(
        key="families",
        title="Transfer, family by family",
        paragraphs=tuple(lead),
        table=Table(("family", "rows", "R²", "95 % interval", "the service"), tuple(rows)),
    )


def _data(card: Mapping[str, Any], families: int) -> Section:
    ranges = card.get("trained_ranges") or {}
    capacity = ranges.get("capacity") or {}
    temperature = ranges.get("temperature") or {}
    corpus = ranges.get("corpus") or {}
    if not capacity or not temperature or not corpus:
        raise CardPageError(
            "the model card lacks the training data's capacity, temperature or corpus facts, "
            "and the page does not describe the data from memory."
        )
    elements = corpus.get("elements") or []
    rare = corpus.get("rare_elements") or []
    return Section(
        key="data",
        title="What it was trained on",
        table=Table(
            ("fact", "value"),
            (
                ("training rows", str(capacity["rows"])),
                ("distinct canonical compositions", str(corpus["compositions"])),
                ("alloy families", str(families)),
                ("elements present", f"{len(elements)}: {' '.join(elements)}"),
                ("elements in two compositions or fewer", " ".join(rare) or "none"),
                (
                    "temperature",
                    f"{temperature['low']:g} to {temperature['high']:g} {temperature['units']}",
                ),
                ("capacity", f"{capacity['low']:g} to {capacity['high']:g} {capacity['units']}"),
            ),
        ),
        paragraphs=(
            "The same material often appears at several temperatures, so there are fewer "
            "independent materials than rows. Every split and every interval on this page is "
            "grouped by canonical composition for that reason.",
        ),
    )


def _domain(card: Mapping[str, Any]) -> Section:
    ranges = card.get("trained_ranges") or {}
    capacity = ranges.get("capacity") or {}
    temperature = ranges.get("temperature") or {}
    limits = {screen["name"]: screen.get("limits") or {} for screen in card.get("screens", ())}
    domain = limits.get("domain", {})
    novelty = limits.get("novelty", {})
    lines = []
    if temperature:
        lines.append(
            f"**Temperature.** Ask between {temperature['low']:g} and {temperature['high']:g} K. "
            f"Outside that the temperature screen refuses."
        )
    if capacity and "cross_family_max" in capacity:
        lines.append(
            f"**Capacity.** Only the {capacity.get('sole_family')} family has training rows above "
            f"{capacity['cross_family_max']:g} wt% ({capacity.get('rows_above')} rows). A "
            f"prediction above that for any other family is refused as out of domain."
        )
    if "max_interval_width" in domain:
        lines.append(
            f"**Certainty.** A band wider than {domain['max_interval_width']:g} wt% is refused "
            f"as high uncertainty: it would tell you less than the training data's own spread."
        )
    if "ceiling" in novelty:
        lines.append(
            f"**Novelty.** A composition further than {novelty['ceiling']:.2f} (ElMD) from every "
            f"known alloy is refused as beyond known chemistry. The model's nearest known alloys "
            f"are shown with every answer; if none is close, neither is the model's knowledge."
        )
    lines.append(
        "An answer is only as good as the family behind it: check the family's transfer score "
        "above before trusting a number for a composition unlike anything measured."
    )
    return Section(key="domain", title="Where it may be trusted", paragraphs=tuple(lines))


def _system() -> Section:
    return Section(
        key="system",
        title="A material number is not a tank number",
        paragraphs=(
            "Every capacity here is a **material** property: the maximum hydrogen the alloy "
            "absorbed, as a weight fraction of the alloy alone. The US DOE targets are "
            "**system** targets, for a whole onboard tank with its vessel, heat exchange and "
            "plumbing. A system carries a large mass penalty over its material.",
            "So comparing a predicted wt% with a DOE target overstates it twice: once by taking "
            "the maximum capacity for the usable one, and again by taking the material for the "
            "system. A material has to clear a DOE figure by a wide margin before the comparison "
            "means anything.",
        ),
    )


def _limits(
    scores: Mapping[tuple[str, str, str], Mapping[str, Any]], evidence: Mapping[str, Any]
) -> Section:
    facts = LIMIT_FACTS
    temperature = sorted(
        (score for key, score in scores.items() if key[0] == "procedure" and key[2].startswith("temperature:")),
        key=lambda score: float(score["subject"].split("(", 1)[1].split(",", 1)[0]),
    )
    lines = [
        "**No pressure data.** The dataset records a maximum capacity and no pressure, so the "
        "model cannot tell reversible (usable) capacity from maximum capacity. A material "
        "whose hydride is too stable to release its hydrogen at a useful pressure is predicted "
        "exactly as well as one that cycles. The dataset also cannot express a sloping plateau, "
        "which is one reason measured capacities disagree for similar compositions.",
        f"**Two descriptors rest on filler values.** `dev_Gordy_electonegativity` cannot be "
        f"computed from the citable Oliynyk table for {facts['gordy_rows_blocked']} of "
        f"{facts['curated_rows']:,} rows, so it was left out of the candidates. And "
        f"`dev_voro_coord_divi_mol_vol` rests on `voro_coord = 1.0` for "
        f"{facts['placeholder_element']}, a placeholder rather than a measurement (every other "
        f"element sits between 3 and 12; gadolinium is hcp with twelve nearest neighbours). "
        f"{facts['placeholder_element']} is in {facts['placeholder_rows']} of "
        f"{facts['curated_rows']:,} rows "
        f"({100 * facts['placeholder_rows'] / facts['curated_rows']:.1f} %). Neither moves the "
        f"scores; both are limits.",
        f"**The feature set is a consensus, not a discovery.** Of {facts['selection_candidates']} "
        f"candidates, every one was chosen by some fold and {facts['selection_unanimous']} by all "
        f"{facts['selection_folds']}. \"The model uses these {facts['selection_unanimous']} "
        f"features\" is a statement about agreement between folds, not about hydrogen storage.",
        f"**One validation label is physically impossible, and it stays.** "
        f"`{facts['impossible_formula']}` is recorded at {facts['impossible_capacity']} wt%, "
        f"which is H/M {facts['impossible_hm']} where no AB5 intermetallic exceeds about 1. It "
        f"sits in `{facts['impossible_split']}`, so it feeds early stopping and every "
        f"validation figure. It is not removed, because the rule that a held-out row is "
        f"reported and never touched is worth more than one row. The domain screen's capacity "
        f"ceiling catches this class of defect at serve time.",
    ]
    if temperature:
        coldest = temperature[0]
        lines.append(
            f"**The model is weakest where storage has to work.** In the coldest temperature "
            f"bin, {coldest['subject'].split(':', 1)[1]} K, the procedure R² is "
            f"{_value(coldest)} with interval {_interval(coldest)}. The warmer bins score "
            + ", ".join(_value(score) for score in temperature[1:])
            + ". Near-ambient operation is the practical regime, and it is where the model is "
            "worst."
        )
    width = _get(scores, "artifact", "interval_width")
    coverage = _get(scores, "artifact", "interval_coverage")
    art = evidence.get("artifact_facts") or {}
    if width["value"] is not None and coverage["value"] is not None:
        nominal = art.get("coverage_nominal")
        error = art.get("coverage_standard_error")
        shortfall = (
            f", which is {(float(nominal) - float(coverage['value'])) / float(error):.1f} "
            f"binomial standard errors under the nominal {float(nominal):g}"
            if nominal and error
            else ""
        )
        lines.append(
            f"**The band is wide relative to the physics.** The calibrated band averages "
            f"{_value(width)} on the test split, about ±{float(width['value']) / 2:.2f} wt%, at "
            f"coverage {_value(coverage)}{shortfall}. Intermetallics generally deliver under 2 "
            f"wt% usable, so the band is a large fraction of the signal: the model tells "
            f"families apart, not fine composition tweaks within one. The band is not a "
            f"constant either. Its correction is constant on a log scale, so it is wider at a "
            f"high prediction than at a low one."
        )
    return Section(key="limits", title="What it cannot do", paragraphs=tuple(lines))


def _published() -> Section:
    return Section(
        key="published",
        title="The previously published figures",
        paragraphs=(
            "The forward model's earlier results in `REPORT.md` were produced by a pipeline with "
            "thirteen named validation leaks, and committed tables contradict its headline "
            "numbers. They are history, not current performance, and this page does not "
            f"inherit them. Every disagreement, with the honest number beside the published "
            f"one, is in `{RECONCILIATION}` in the repository.",
        ),
    )


def model_card_view(
    evidence: Mapping[str, Any], parity_payload: Mapping[str, Any], card: Mapping[str, Any]
) -> ModelCardView:
    """The whole page, from the three payloads the service serves.

    Raises:
        CardPageError: a payload lacks the scores, the data facts or a reading the page cannot
            honestly be drawn without. An absent *score* is not this: it is shown as absent.
    """
    scores = _scores(evidence)
    families = sum(
        1 for key in scores if key[0] == "transfer" and key[2].startswith("family:")
    )
    return ModelCardView(
        version=str(card.get("version", "")),
        digest=str(evidence.get("digest", "")),
        sections=(
            _what(card, evidence),
            _three_scores(scores, evidence),
            _parity(parity_payload, _get(scores, "procedure", "interval_coverage")),
            _families(scores, card),
            _other_quantities(scores),
            _data(card, families),
            _domain(card),
            _system(),
            _limits(scores, evidence),
            _published(),
        ),
    )


def figures(view: ModelCardView) -> Sequence[Figure]:
    """Every figure on the page, in order."""
    return tuple(section.figure for section in view.sections if section.figure is not None)
