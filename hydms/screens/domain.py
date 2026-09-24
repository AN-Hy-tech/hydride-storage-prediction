"""L4 -- how far from known chemistry a prediction may be trusted.

The card asked for a ceiling "derived from the leave-one-alloy-class-out result (#30): the
distance at which measured cross-family performance degrades past what the thesis is willing
to claim", and left one decision open -- whether that ceiling is **per-family** or **one
distance calibrated against the per-class curve**.

**It is neither, and the measurement is why.** Both options assume the degradation is
mediated by a composition distance. Measured over the ten classes, against
``reports/loco/loco-per-class.csv``, using each family's median nearest-neighbour distance to
the rest of the training corpus:

    Spearman rho, per-class isolation against per-class transfer R2 (n = 10)

        element-fraction L1 distance, median      -0.2727   (p 0.446)
        element-fraction L1 distance, mean        -0.0182   (p 0.960)
        the model's own 14-feature space, median  -0.2848   (p 0.425)

There is no curve to calibrate against. The two **least** isolated families -- ``A2B`` and
``LEA``, both at 0.1667 in element space -- score 0.7264 and 0.4995, among the best; the
**most** isolated, ``AB`` at 0.6521, scores 0.4214, near the middle. A scalar threshold fitted
to that ordering would reject the families the model handles best, and ten per-family
thresholds would each be set from a number that distance does not predict.

**The feature-space row is the one that closes the question**, because whatever a better
chemical metric would say, *the model cannot see it*. A CatBoost fit reads fourteen numbers.
If distance in the space it actually reads does not order its transfer failures, no distance
in a space it never reads can be the mechanism. ElMD (#49) is therefore real novelty evidence
for AC-7 and is **not** this ceiling; it is a separate screen, and its own threshold cannot be
derived from the LOCO curve either. That is boxed on #49.

What *does* order the failures
------------------------------

Of everything measured, one quantity reaches significance at n = 10, and it is a property of
the **target**, not of the composition: ``outside_rest``, the fraction of a family's
compositions whose capacity lies outside the range every other family spans.

    against per-class MAE                +0.7006   (p 0.024)
    against per-class interval coverage  -0.7006   (p 0.024)

It is carried by ``Mg``, and that is not a weakness of the finding -- it is the finding, and
it is arithmetically necessary rather than statistical. A gradient-boosted tree predicts leaf
averages of training targets, so it **cannot return a value outside the target range it was
trained on**. Hold ``Mg`` out and the model loses its only evidence of what high capacity
looks like; it then predicts the family it has never seen as though it were the families it
has, which is exactly the R2 of -0.3381 and the interval coverage of 0.1146 that #30 measured.

The ceiling, derived
--------------------

So the applicability domain has a ceiling in **capacity**, and the level is not chosen. Count
the families holding training rows above each level (893 training rows, reconciled classes):

    above 3.00 wt%   138 rows   8 families
    above 4.00 wt%    46 rows   5 families    (Mg 40 of 46)
    above 5.00 wt%    22 rows   2 families
    above 5.19 wt%    21 rows   **1 family**  (Mg)
    above 6.00 wt%     5 rows   1 family

At **5.19 wt%** -- the maximum capacity of every non-``Mg`` training row -- the model's
cross-family evidence stops existing. Above it there are 21 rows and they are all ``Mg``, and
LOCO is what tells us that ``Mg`` is the family the model cannot transfer into. That is the
sentence the card asked for: *the level at which measured cross-family performance degrades
past what the thesis is willing to claim*, read along the axis the evidence supports.

A prediction above it is :data:`OUT_OF_DOMAIN`. It is the primary structural mitigation for
risk R1, and it bites exactly where an optimiser pushes: toward high capacity.

The physical ceiling, and why the card's formula is not used as written
----------------------------------------------------------------------

The card prescribed ``wt%_max = H/M_max * 1.008 / mean atomic mass`` with ``H/M_max`` = 2 for
ordinary interstitial dihydrides and 2.5 for BCC HEAs. Measured against the 1,278 curated
rows, **that bound refuses real materials**:

    flat H/M = 2.0                    31 rows above their own ceiling, worst by 2.345 wt%
    flat H/M = 2.5                     9 rows,                         worst by 1.696 wt%
    element-wise max                  16 rows,                         worst by 1.600 wt%
    max(2.5, element-wise max)         4 rows,                         worst by 1.047 wt%

The constant is not a constant: the rare earths form **tri**\\ hydrides (``YH3``, ``LaH3``,
``CeH3``) and thorium reaches ``Th4H15`` at H/M 3.75, so ``Mg22Y3`` at 6.48 wt%, ``Mg4La1``,
``Th7Co3`` and every light-rare-earth ``MIC`` compound sit above a flat ceiling of 2. A screen
that calls its own training data unphysical is broken.

:data:`HM_MAX` therefore carries the richest known binary hydride stoichiometry per element,
and the rule is ``max(floor, element-wise max)`` with the floor at Sahlberg's 2.5 -- which is
still doing real work, since it is what admits the BCC solid solutions whose constituents are
all dihydride formers. Four curated rows remain above their ceiling and **none is absorbed**:

    Ce1Ni3Cr2   AB5   5.19 wt%   implies H/M 3.606
    Ce1Ni4Zr1   AB5   4.94 wt%   implies H/M 3.807
    Ce1Ni4Cr1   AB5   4.73 wt%   implies H/M 3.339
    Ti1.1Cr1Mn1V0.255Fe0.045   AB2   4.90 wt%   implies H/M 2.503

The three ``Ce-Ni`` rows are data defects -- ``LaNi5H6`` is H/M 1.0 and no AB5 intermetallic
holds three and a half hydrogens per metal atom -- and are boxed on #14. The fourth is over by
**0.006 wt%**: it is Sahlberg's BCC limit to within the rounding of a published table, and
loosening a physics bound to swallow it would be fitting the constant to the residue.

Both levels are config values (``domain.*`` in ``hydms/config/pipeline.yaml``), so an R1
iteration tightens them and re-runs without touching this module.

The other two signals
---------------------

**The bounding-box applicability domain** -- a feature outside the span the training rows
covered -- is exact, names the offending feature, and is included because it is the one signal
that is a statement about the model's *input*. It is also **nearly vacuous on this corpus**,
and saying so is part of the result: only **3 of 385** held-out rows fall outside any training
span. The curated chemistry is homogeneous; the domain problem here is not unusual chemistry,
it is unreachable capacity. It is kept because a candidate arriving from a search over the
composition simplex is not drawn from this corpus, and a range check costs one comparison.

**Alloy-class transfer** is the card's "second, independent domain signal". Where a candidate
carries a class, this screen attaches that class's measured LOCO transfer R2 as evidence and
refuses with :data:`UNTRUSTED_FAMILY` below ``domain.min_transfer_r2``. It is independent of
everything above: it reads neither the composition nor the prediction, only the label and a
number #30 measured.

**Uncertainty is reported, never substituted.** :data:`HIGH_UNCERTAINTY` and
:data:`OUT_OF_DOMAIN` are separate codes because #30 measured them coming apart in both
directions: ``Mg`` is the worst family *and* has the worst coverage (0.1146), but ``SS`` is the
**best** family by R2 (0.7626) with the second-worst coverage (0.1644), and ``HEA`` is the
second worst by R2 (-0.0723) with the **best** coverage (0.8824). A candidate can be out of
family and carry a narrow band, which is the failure this screen exists to catch.

Card #48.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import TextIO

import numpy as np
import pandas as pd

from hydms.config import Config
from hydms.config import load as load_config
from hydms.screens.protocol import (
    ADMITTED,
    INDETERMINATE,
    ScreenError,
    verdict_table,
)

__all__ = [
    "ABOVE_PHYSICAL_CEILING",
    "CEILING_COLUMN",
    "HIGH_UNCERTAINTY",
    "HM_COLUMN",
    "HM_MAX",
    "HYDROGEN_MASS",
    "OUTSIDE_FEATURE_RANGE",
    "OUT_OF_DOMAIN",
    "REFERENCE_FILE",
    "TRANSFER_COLUMN",
    "UNTRUSTED_FAMILY",
    "ApplicabilityDomain",
    "DomainReference",
    "applicability_domain",
    "capacity_ceiling",
]

# --------------------------------------------------------------------------------------
# The vocabulary
# --------------------------------------------------------------------------------------

#: The prediction sits in a capacity regime the training corpus covers with **one** family,
#: and #30 measured that family as the one the model cannot transfer into. Distinct from
#: :data:`HIGH_UNCERTAINTY`: a candidate can be here and carry a narrow band.
OUT_OF_DOMAIN = "out-of-domain"

#: The prediction is above what the composition can physically hold. Not a statement about
#: evidence -- a statement about hydrogen. See the module docstring for why the bound is
#: ``max(floor, element-wise max)`` and not the flat constant the card prescribed.
ABOVE_PHYSICAL_CEILING = "above-physical-ceiling"

#: A model input lies outside the span the training rows covered for it. The bounding-box
#: applicability domain, exact and loose; the reason names the feature and both bounds.
OUTSIDE_FEATURE_RANGE = "outside-feature-range"

#: The candidate's alloy class is one whose measured leave-one-class-out transfer is below
#: ``domain.min_transfer_r2``. Independent of composition and of the prediction.
UNTRUSTED_FAMILY = "untrusted-family"

#: The calibrated interval is wider than ``domain.max_interval_width_wt_pct``. A *report*
#: about the band, never a stand-in for :data:`OUT_OF_DOMAIN`.
HIGH_UNCERTAINTY = "high-uncertainty"

#: Evidence column: the composition's physical capacity ceiling, in weight percent.
CEILING_COLUMN = "ceiling"

#: Evidence column: the hydrogen-to-metal ratio that ceiling was computed at.
HM_COLUMN = "hm_max"

#: Evidence column: the candidate class's measured leave-one-class-out transfer R2, where the
#: batch carries a class. ``NaN`` where it does not.
TRANSFER_COLUMN = "transfer_r2"

#: Codes in the order they are reported when a candidate fails more than one. Most severe
#: first: "we could not judge you", then "impossible", then "no evidence", then the two
#: softer signals. The *reason* names every failure; the code names the worst.
_PRECEDENCE: tuple[str, ...] = (
    INDETERMINATE,
    ABOVE_PHYSICAL_CEILING,
    OUT_OF_DOMAIN,
    UNTRUSTED_FAMILY,
    OUTSIDE_FEATURE_RANGE,
    HIGH_UNCERTAINTY,
)

# --------------------------------------------------------------------------------------
# The physics
# --------------------------------------------------------------------------------------

#: Molar mass of atomic hydrogen, g/mol. The only constant in the ceiling that is not a
#: table lookup.
HYDROGEN_MASS = 1.008

#: Width of one temperature-support bin, kelvin. The support is a histogram of the training
#: rows' temperatures, served on ``GET /v1/model`` so a client can draw the rows behind each
#: part of a temperature sweep (card #82). 50 K because the corpus's resolution is coarser than
#: that nowhere it matters: 366 of the 893 training rows sit in 250-300 K and the next nine
#: bins thin to single digits by 650 K, and a finer bin would split that tail into bars of one.
#: The edges are aligned to multiples of it, so a bin reads as "300 to 350 K" rather than
#: "345 to 395 K".
SUPPORT_BIN_K = 50.0

#: The richest known binary hydride stoichiometry of each element, as H atoms per metal atom.
#:
#: The rule is ``max(floor, max over the constituents)`` -- an upper bound, so the most
#: hydride-forming constituent bounds the lattice's site occupancy. A composition-weighted
#: *average* was measured and rejected: it puts ``LaNi5`` at H/M 0.5 against a real 1.0, so it
#: is not a bound at all.
#:
#: An element absent from this mapping contributes 0.0. That is deliberate and is why the
#: floor exists: ``Cr``, ``Mn``, ``Fe``, ``Co``, ``Ni`` form no stable binary hydride at these
#: pressures, yet they host hydrogen in interstitial sites of the alloys that do.
#:
#: Sources: the trihydride set is the standard rare-earth ``RH2``/``RH3`` sequence (``Eu`` and
#: ``Yb`` are divalent and stop at 2); ``Th4H15`` gives thorium 3.75; the dihydride and
#: monohydride sets are the alkaline-earth, group-4/5 and alkali binaries.
HM_MAX: Mapping[str, float] = {
    **dict.fromkeys(
        (
            "Sc", "Y", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Gd", "Tb",
            "Dy", "Ho", "Er", "Tm", "Lu", "Ac", "U", "Np", "Pu",
        ),
        3.0,
    ),
    **dict.fromkeys(
        ("Mg", "Ca", "Sr", "Ba", "Ti", "Zr", "Hf", "V", "Nb", "Ta", "Eu", "Yb"), 2.0
    ),
    **dict.fromkeys(("Li", "Na", "K", "Rb", "Cs", "Pd"), 1.0),
    "Th": 3.75,
}

#: Where the measured reference lives, beside this module. Generated by
#: ``python -m hydms.screens.domain --emit``; a test asserts the committed file is what the
#: code produces from the curated data.
REFERENCE_FILE = Path(__file__).with_name("domain-reference.json")

_MASS_PROPERTY = "atomic_weight"
_MASS_TABLE = "oliynyk"


def _masses() -> Mapping[str, float]:
    """Atomic weights from the same table the featuriser reads. Imported lazily.

    :mod:`hydms.descriptors.element_data` pulls the packaged CSVs in; a screen that is only
    range-checking features should not pay for that at import time.
    """
    from hydms.descriptors.element_data import load_table

    table = load_table(_MASS_TABLE)
    return {
        element: table.value(element, _MASS_PROPERTY)
        for element in table.servable(_MASS_PROPERTY)
    }


def capacity_ceiling(
    formulas: Sequence[str] | pd.Series,
    *,
    floor: float,
    index: pd.Index | None = None,
) -> pd.DataFrame:
    """The physical capacity ceiling of each composition, in weight percent.

    ``wt%_max = H/M_max * 1.008 / mean atomic mass * 100``, with ``H/M_max`` the larger of
    ``floor`` and the richest binary hydride stoichiometry among the constituents
    (:data:`HM_MAX`). Every term is a pure function of the formula string, so this stays
    inside PRD 2.3's enabling fact -- no structure, no lookup of the candidate anywhere.

    Args:
        formulas: One composition per candidate.
        floor: The lower bound on ``H/M_max``, from ``domain.capacity_ceiling_hm_floor``.
            Sahlberg's 2.5 for the BCC lattice-strain case; see the module docstring.
        index: The candidates' index, taken from ``formulas`` when it is a ``Series``.

    Returns:
        A frame on that index with :data:`CEILING_COLUMN` and :data:`HM_COLUMN`. A formula
        this project cannot parse, or one naming an element the mass table does not carry,
        gets ``NaN`` in both -- the caller decides what an unjudgeable candidate means, and
        in this layer that decision is :data:`~hydms.screens.protocol.INDETERMINATE`.
    """
    from hydms.data.load import FormulaError, parse_formula

    if isinstance(formulas, pd.Series):
        labels = formulas.index if index is None else index
        strings = list(formulas)
    else:
        strings = list(formulas)
        labels = pd.RangeIndex(len(strings)) if index is None else index
    if len(strings) != len(labels):
        raise ScreenError(
            f"{len(strings)} formula(e) against {len(labels)} label(s); a ceiling is "
            f"addressed by the label of the candidate it bounds."
        )
    if not np.isfinite(floor) or floor <= 0.0:
        raise ScreenError(
            f"the H/M floor must be a positive number, got {floor}. A non-positive floor "
            f"would put every ceiling at or below zero and refuse every candidate."
        )

    masses = _masses()
    ceilings = np.full(len(strings), np.nan)
    ratios = np.full(len(strings), np.nan)
    for position, formula in enumerate(strings):
        if not isinstance(formula, str) or not formula.strip():
            continue
        try:
            parsed = parse_formula(formula)
        except FormulaError:
            continue
        if not parsed or any(symbol not in masses for symbol in parsed):
            continue
        amount = sum(parsed.values())
        if amount <= 0.0:
            continue
        mean_mass = sum(masses[symbol] * count for symbol, count in parsed.items()) / amount
        ratio = max(floor, max(HM_MAX.get(symbol, 0.0) for symbol in parsed))
        ratios[position] = ratio
        ceilings[position] = ratio * HYDROGEN_MASS / mean_mass * 100.0
    return pd.DataFrame(
        {CEILING_COLUMN: ceilings, HM_COLUMN: ratios}, index=pd.Index(labels)
    )


# --------------------------------------------------------------------------------------
# What the training rows say
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class DomainReference:
    """The measured facts the ceiling is read against -- small enough to commit.

    It is deliberately *not* part of the artifact bundle. The feature spans and the capacity
    levels are properties of the curated data rather than of any one fit, and the transfer
    numbers come from ``reports/loco/``, which is committed for the same reason
    (:mod:`hydms.gates.ac6_leave_one_class_out` reads it rather than refitting). Whether the
    delivery path should pin a copy into the bundle so a served version cannot drift from the
    data it was screened against is #76's decision, and is boxed there.

    Attributes:
        rows: How many training rows it was measured over.
        trained_min: The lowest capacity in those rows, weight percent.
        trained_max: The highest. A gradient-boosted tree cannot predict above it.
        cross_family_max: The highest capacity reached by more than one alloy class -- the
            ceiling. Above it the corpus holds one family, and #30 measured that family as
            untransferable.
        sole_family: The class holding every training row above ``cross_family_max``.
        rows_above: How many rows that is.
        feature_span: Feature name -> ``(min, max)`` over the training rows.
        transfer: Alloy class -> its leave-one-class-out R2, from
            ``reports/loco/loco-per-class.csv``.
        temperature_edges: Bin edges, kelvin, ascending, one more than there are counts. Empty
            when no support was measured -- a reference built for a test, or read from a file
            written before card #82 needed it -- and then the model card omits the support
            rather than reporting an empty histogram, which would read as "no rows anywhere".
        temperature_counts: Training rows per bin: half-open, the last one closed. They sum
            to ``rows``, because it is the same rows counted a second way.
    """

    rows: int
    trained_min: float
    trained_max: float
    cross_family_max: float
    sole_family: str
    rows_above: int
    feature_span: Mapping[str, tuple[float, float]]
    transfer: Mapping[str, float]
    temperature_edges: tuple[float, ...] = ()
    temperature_counts: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        edges = tuple(float(edge) for edge in self.temperature_edges)
        counts = tuple(int(count) for count in self.temperature_counts)
        object.__setattr__(self, "temperature_edges", edges)
        object.__setattr__(self, "temperature_counts", counts)
        if not edges and not counts:
            return
        if len(edges) != len(counts) + 1 or not counts:
            raise ScreenError(
                f"the temperature support has {len(edges)} edge(s) around {len(counts)} "
                f"bin(s); a bin is bounded on both sides."
            )
        if any(later <= earlier for earlier, later in pairwise(edges)):
            raise ScreenError(f"the temperature support edges are not ascending: {edges}.")
        if any(count < 0 for count in counts):
            raise ScreenError("a temperature support bin holds a negative number of rows.")
        if sum(counts) != self.rows:
            raise ScreenError(
                f"the temperature support counts {sum(counts)} row(s) and the reference was "
                f"measured over {self.rows}. It is the same rows counted by temperature, so a "
                f"difference means one of the two was measured on something else."
            )

    def to_json(self) -> str:
        """The committed form: sorted keys, two-space indent, one trailing newline."""
        payload: dict[str, object] = {
            "rows": self.rows,
            "trained_min": self.trained_min,
            "trained_max": self.trained_max,
            "cross_family_max": self.cross_family_max,
            "sole_family": self.sole_family,
            "rows_above": self.rows_above,
            "feature_span": {name: list(bounds) for name, bounds in self.feature_span.items()},
            "transfer": dict(self.transfer),
        }
        if self.temperature_counts:
            payload["temperature_support"] = {
                "edges": list(self.temperature_edges),
                "counts": list(self.temperature_counts),
            }
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"

    @classmethod
    def from_json(cls, text: str) -> DomainReference:
        """Read one back. Raises :class:`ScreenError` on anything it cannot use."""
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise ScreenError(f"the domain reference is not JSON: {error}") from error
        missing = sorted(
            {
                "rows", "trained_min", "trained_max", "cross_family_max",
                "sole_family", "rows_above", "feature_span", "transfer",
            }
            - set(payload)
        )
        if missing:
            raise ScreenError(f"the domain reference is missing {', '.join(missing)}.")
        support = payload.get("temperature_support") or {}
        if not isinstance(support, dict):
            raise ScreenError("the domain reference's temperature_support is not an object.")
        return cls(
            rows=int(payload["rows"]),
            trained_min=float(payload["trained_min"]),
            trained_max=float(payload["trained_max"]),
            cross_family_max=float(payload["cross_family_max"]),
            sole_family=str(payload["sole_family"]),
            rows_above=int(payload["rows_above"]),
            feature_span={
                str(name): (float(low), float(high))
                for name, (low, high) in payload["feature_span"].items()
            },
            transfer={str(name): float(value) for name, value in payload["transfer"].items()},
            temperature_edges=tuple(float(edge) for edge in support.get("edges", ())),
            temperature_counts=tuple(int(count) for count in support.get("counts", ())),
        )

    @classmethod
    def packaged(cls) -> DomainReference:
        """The committed reference. The default every caller gets."""
        try:
            text = REFERENCE_FILE.read_text(encoding="utf-8")
        except OSError as error:
            raise ScreenError(
                f"the domain reference is not readable at {REFERENCE_FILE}: {error}. "
                f"Regenerate it with `python -m hydms.screens.domain --emit`."
            ) from error
        return cls.from_json(text)

    @classmethod
    def measured(
        cls,
        training: pd.DataFrame,
        classes: pd.Series,
        *,
        target: str,
        features: Sequence[str],
        transfer: Mapping[str, float],
        temperature: str | None = None,
        temperature_edges: Sequence[float] = (),
    ) -> DomainReference:
        """Derive one from the training rows. See :func:`emit` for the caller that does.

        ``cross_family_max`` is the maximum capacity of the family holding the top row,
        excluded -- i.e. the highest level every *other* family reaches. That is the level at
        which cross-family evidence stops, computed rather than typed, so a change in the
        curated data moves it instead of silently invalidating a constant.

        ``temperature`` names the column to count into ``temperature_edges``; give both or
        neither. A row outside the edges is an error rather than a row left uncounted, since the
        support would then sum to less than ``rows`` and the sweep would under-report the
        evidence at exactly the end of the range where it is thinnest.
        """
        if (temperature is None) != (not temperature_edges):
            raise ScreenError(
                "the temperature support needs both the column to count and the edges to count "
                "it into; one without the other measures nothing."
            )
        counts: tuple[int, ...] = ()
        if temperature is not None:
            edges = np.asarray([float(edge) for edge in temperature_edges], dtype=float)
            kelvin = training[temperature].astype(float).to_numpy()
            outside = (kelvin < edges[0]) | (kelvin > edges[-1])
            if outside.any():
                raise ScreenError(
                    f"{int(outside.sum())} training row(s) lie outside the support edges "
                    f"{edges[0]:g} to {edges[-1]:g} K; widen the edges rather than drop them."
                )
            # `np.histogram` is half-open with the last bin closed -- the convention
            # `TemperatureSupport.measured` states, so the two cannot disagree on an edge.
            counts = tuple(int(n) for n in np.histogram(kelvin, bins=edges)[0])
        capacity = training[target].astype(float)
        if capacity.empty:
            raise ScreenError("the domain reference needs training rows; none were given.")
        if not classes.index.equals(training.index):
            raise ScreenError(
                f"{len(classes)} class label(s) against {len(training)} training row(s), on "
                f"a different index."
            )
        top = classes.loc[capacity.idxmax()]
        rest = capacity[classes != top]
        if rest.empty:
            raise ScreenError(
                f"every training row is class {top!r}, so there is no cross-family level to "
                f"measure. The ceiling cannot be derived from a single-family corpus."
            )
        cross_family_max = float(rest.max())
        return cls(
            rows=len(capacity),
            trained_min=float(capacity.min()),
            trained_max=float(capacity.max()),
            cross_family_max=cross_family_max,
            sole_family=str(top),
            rows_above=int((capacity > cross_family_max).sum()),
            feature_span={
                name: (float(training[name].min()), float(training[name].max()))
                for name in features
                if name in training.columns
            },
            transfer=dict(transfer),
            temperature_edges=tuple(float(edge) for edge in temperature_edges),
            temperature_counts=counts,
        )


# --------------------------------------------------------------------------------------
# The screen
# --------------------------------------------------------------------------------------


def _number(value: float) -> str:
    """A bound as it should read in a sentence: 5.19, not 5.190000000000001."""
    return f"{value:g}"


@dataclass(frozen=True)
class ApplicabilityDomain:
    """The applicability-domain ceiling, as a :class:`~hydms.screens.protocol.Screen`.

    Four signals, judged independently and reported together. Which of them *can* run depends
    on what the batch carries -- a caller screening raw candidates before predicting has no
    prediction column, and a caller screening a prediction frame has no class label -- so each
    signal fires where its input is present and is named in the reason where it is not. A
    batch carrying **no** judgeable column at all raises: that is the wrong frame, not a fact
    about any candidate in it.

    Attributes:
        name: The screen's name and its column prefix in the verdict table.
        reference: The measured facts, normally :meth:`DomainReference.packaged`.
        formula: The candidate column holding the composition. Required.
        prediction: The point estimate to bound, in weight percent -- the median head, not
            the lower confidence bound. The LCB is the *ranking* key and is deliberately
            conservative; bounding it instead would let a candidate whose band is wide and
            whose centre is unphysical through the one screen that exists to stop it.
        width: The calibrated interval width column, weight percent.
        alloy_class: The class label column.
        hm_floor: The lower bound on ``H/M_max``; ``domain.capacity_ceiling_hm_floor``.
        max_interval_width: Above this the band is :data:`HIGH_UNCERTAINTY`.
        min_transfer_r2: Below this a class is :data:`UNTRUSTED_FAMILY`.
    """

    reference: DomainReference
    formula: str
    prediction: str
    width: str
    alloy_class: str
    hm_floor: float
    max_interval_width: float
    min_transfer_r2: float
    name: str = "domain"

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ScreenError("a screen needs a name.")
        for label, value in (
            ("hm_floor", self.hm_floor),
            ("max_interval_width", self.max_interval_width),
            ("min_transfer_r2", self.min_transfer_r2),
        ):
            if not np.isfinite(value):
                raise ScreenError(
                    f"domain screen {self.name!r} has a non-finite {label} ({value}); a "
                    f"threshold that is not a number cannot reject anything."
                )
        if self.max_interval_width <= 0.0:
            raise ScreenError(
                f"domain screen {self.name!r} has max_interval_width="
                f"{self.max_interval_width}, which refuses every band including the "
                f"calibrated one."
            )

    @property
    def reasons(self) -> tuple[str, ...]:
        """Every code this screen can emit. Five rejections and the shared indeterminate."""
        return (
            OUT_OF_DOMAIN,
            ABOVE_PHYSICAL_CEILING,
            OUTSIDE_FEATURE_RANGE,
            UNTRUSTED_FAMILY,
            HIGH_UNCERTAINTY,
            INDETERMINATE,
        )

    @property
    def ceiling(self) -> float:
        """The capacity level above which the corpus holds one family. Weight percent."""
        return self.reference.cross_family_max

    def verdict(self, candidates: pd.DataFrame) -> pd.DataFrame:
        """Judge every candidate against every signal its columns support.

        Raises:
            ScreenError: if :attr:`formula` is absent, or if the batch carries none of the
                prediction, feature and class columns any signal reads.
        """
        if self.formula not in candidates.columns:
            raise ScreenError(
                f"domain screen {self.name!r} reads {self.formula!r}, which the candidates "
                f"do not have. They have: {', '.join(map(repr, candidates.columns))}."
            )

        index = candidates.index
        evidence = capacity_ceiling(
            candidates[self.formula], floor=self.hm_floor, index=index
        )
        ceilings = evidence[CEILING_COLUMN].to_numpy(dtype="float64")

        spans = [name for name in self.reference.feature_span if name in candidates.columns]
        has_prediction = self.prediction in candidates.columns
        has_class = self.alloy_class in candidates.columns
        if not (has_prediction or has_class or spans):
            raise ScreenError(
                f"domain screen {self.name!r} has nothing to judge: the batch carries no "
                f"{self.prediction!r}, no {self.alloy_class!r} and none of the "
                f"{len(self.reference.feature_span)} feature column(s) it range-checks. "
                f"Featurise or predict before screening -- admitting a batch nothing could "
                f"judge is the silent drop's mirror image."
            )

        # One boolean array per signal, plus the per-row sentence fragments they explain
        # themselves with. Nothing short-circuits: a candidate failing three rules is a
        # different finding from one failing one, and the reason has to say so.
        flags: dict[str, np.ndarray] = {}
        notes: dict[str, list[str]] = {code: [""] * len(index) for code in _PRECEDENCE}
        unreadable = np.zeros(len(index), dtype=bool)

        if has_prediction or spans:
            unreadable |= ~np.isfinite(ceilings)
        for position in np.flatnonzero(~np.isfinite(ceilings)):
            notes[INDETERMINATE][position] = (
                f"{candidates[self.formula].iloc[position]!r} could not be given a physical "
                f"capacity ceiling -- it does not parse, or it names an element the "
                f"{_MASS_TABLE!r} table has no mass for"
            )

        if has_prediction:
            values = candidates[self.prediction].to_numpy(dtype="float64", na_value=np.nan)
            readable = np.isfinite(values)
            unreadable |= ~readable
            for position in np.flatnonzero(~readable):
                if not notes[INDETERMINATE][position]:
                    notes[INDETERMINATE][position] = (
                        f"{self.prediction} is missing or not a finite number, so neither "
                        f"ceiling could be applied -- and a rule that could not run does "
                        f"not admit"
                    )
            usable = readable & np.isfinite(ceilings)
            above_physical = np.zeros(len(index), dtype=bool)
            above_physical[usable] = values[usable] > ceilings[usable]
            flags[ABOVE_PHYSICAL_CEILING] = above_physical
            for position in np.flatnonzero(above_physical):
                notes[ABOVE_PHYSICAL_CEILING][position] = (
                    f"{self.prediction} = {_number(values[position])} wt% is above the "
                    f"{_number(ceilings[position])} wt% this composition can hold at H/M "
                    f"{_number(evidence[HM_COLUMN].iloc[position])}"
                )
            out = np.zeros(len(index), dtype=bool)
            out[readable] = values[readable] > self.ceiling
            flags[OUT_OF_DOMAIN] = out
            for position in np.flatnonzero(out):
                notes[OUT_OF_DOMAIN][position] = (
                    f"{self.prediction} = {_number(values[position])} wt% is above "
                    f"{_number(self.ceiling)} wt%, the highest capacity more than one alloy "
                    f"class reaches in training: above it the corpus holds "
                    f"{self.reference.rows_above} row(s) and they are all "
                    f"{self.reference.sole_family}, whose measured transfer is "
                    f"{_number(self.reference.transfer.get(self.reference.sole_family, float('nan')))}"
                )

        if self.width in candidates.columns:
            widths = candidates[self.width].to_numpy(dtype="float64", na_value=np.nan)
            readable = np.isfinite(widths)
            unreadable |= ~readable
            for position in np.flatnonzero(~readable):
                if not notes[INDETERMINATE][position]:
                    notes[INDETERMINATE][position] = (
                        f"{self.width} is missing or not a finite number, so the band could "
                        f"not be judged -- and a rule that could not run does not admit"
                    )
            wide = np.zeros(len(index), dtype=bool)
            wide[readable] = widths[readable] > self.max_interval_width
            flags[HIGH_UNCERTAINTY] = wide
            for position in np.flatnonzero(wide):
                notes[HIGH_UNCERTAINTY][position] = (
                    f"the calibrated band is {_number(widths[position])} wt% wide, above the "
                    f"{_number(self.max_interval_width)} wt% this project will report"
                )

        transfers = np.full(len(index), np.nan)
        if has_class:
            labels = candidates[self.alloy_class].astype(object)
            known = np.array(
                [label in self.reference.transfer for label in labels], dtype=bool
            )
            transfers[known] = [
                self.reference.transfer[label] for label in labels[known]
            ]
            unreadable |= ~known
            for position in np.flatnonzero(~known):
                if not notes[INDETERMINATE][position]:
                    notes[INDETERMINATE][position] = (
                        f"{self.alloy_class} = {labels.iloc[position]!r} is not one of the "
                        f"{len(self.reference.transfer)} classes leave-one-class-out "
                        f"measured, so no transfer estimate exists for it"
                    )
            untrusted = np.zeros(len(index), dtype=bool)
            untrusted[known] = transfers[known] < self.min_transfer_r2
            flags[UNTRUSTED_FAMILY] = untrusted
            for position in np.flatnonzero(untrusted):
                notes[UNTRUSTED_FAMILY][position] = (
                    f"class {labels.iloc[position]} transfers at R2 "
                    f"{_number(transfers[position])}, below the "
                    f"{_number(self.min_transfer_r2)} this project will predict across"
                )

        if spans:
            outside = np.zeros(len(index), dtype=bool)
            for name in spans:
                low, high = self.reference.feature_span[name]
                values = candidates[name].to_numpy(dtype="float64", na_value=np.nan)
                readable = np.isfinite(values)
                unreadable |= ~readable
                for position in np.flatnonzero(~readable):
                    if not notes[INDETERMINATE][position]:
                        notes[INDETERMINATE][position] = (
                            f"{name} is missing or not a finite number, so the trained span "
                            f"could not be applied -- and a rule that could not run does "
                            f"not admit"
                        )
                beyond = np.zeros(len(index), dtype=bool)
                beyond[readable] = (values[readable] < low) | (values[readable] > high)
                outside |= beyond
                for position in np.flatnonzero(beyond):
                    fragment = (
                        f"{name} = {_number(values[position])} is outside the trained span "
                        f"{_number(low)} to {_number(high)}"
                    )
                    existing = notes[OUTSIDE_FEATURE_RANGE][position]
                    notes[OUTSIDE_FEATURE_RANGE][position] = (
                        f"{existing}; {fragment}" if existing else fragment
                    )
            flags[OUTSIDE_FEATURE_RANGE] = outside

        flags[INDETERMINATE] = unreadable
        return self._assemble(index, flags, notes, evidence, transfers)

    def _assemble(
        self,
        index: pd.Index,
        flags: Mapping[str, np.ndarray],
        notes: Mapping[str, Sequence[str]],
        evidence: pd.DataFrame,
        transfers: np.ndarray,
    ) -> pd.DataFrame:
        """One code and one sentence per candidate, plus the evidence columns."""
        rejected = np.zeros(len(index), dtype=bool)
        for flagged in flags.values():
            rejected |= flagged

        code = np.full(len(index), ADMITTED, dtype=object)
        for candidate in _PRECEDENCE:
            flagged = flags.get(candidate)
            if flagged is None:
                continue
            code[flagged & (code == ADMITTED)] = candidate

        admitted_sentence = (
            f"inside the applicability domain: at or below {_number(self.ceiling)} wt%, "
            f"within the composition's physical ceiling and the trained feature spans"
        )
        reason = [admitted_sentence] * len(index)
        for position in np.flatnonzero(rejected):
            said = [
                notes[candidate][position]
                for candidate in _PRECEDENCE
                if flags.get(candidate) is not None
                and flags[candidate][position]
                and notes[candidate][position]
            ]
            reason[position] = "; ".join(said) if said else "refused by the domain screen"

        table = verdict_table(~rejected, code, reason, index=index)
        table[CEILING_COLUMN] = evidence[CEILING_COLUMN].to_numpy()
        table[HM_COLUMN] = evidence[HM_COLUMN].to_numpy()
        table[TRANSFER_COLUMN] = transfers
        return table


def applicability_domain(
    cfg: Config | None = None, *, reference: DomainReference | None = None
) -> ApplicabilityDomain:
    """The ceiling, built from config and the committed reference.

    Every threshold is a ``domain.*`` key in ``hydms/config/pipeline.yaml``, which is the
    property the card requires so an R1 iteration can tighten the domain and re-run without a
    code change -- the same property :func:`~hydms.screens.window.temperature_window`
    demonstrates for the outer bound.
    """
    from hydms.surrogate.model import column_names

    config = cfg if cfg is not None else load_config()
    heads = column_names(config.model.quantiles)
    median = heads[len(heads) // 2]
    return ApplicabilityDomain(
        reference=reference if reference is not None else DomainReference.packaged(),
        formula=config.columns.formula,
        prediction=median,
        width="interval_width",
        alloy_class=config.columns.alloy_class,
        hm_floor=config.domain.capacity_ceiling_hm_floor,
        max_interval_width=config.domain.max_interval_width_wt_pct,
        min_transfer_r2=config.domain.min_transfer_r2,
    )


# --------------------------------------------------------------------------------------
# Regenerating the reference
# --------------------------------------------------------------------------------------


def transfer_table(cfg: Config | None = None) -> dict[str, float]:
    """Each alloy class's leave-one-class-out R2, read from #30's committed tables.

    Read, never recomputed -- the protocol behind these numbers costs four hours and
    :mod:`hydms.gates.ac6_leave_one_class_out` reads the same file for the same reason.
    """
    config = cfg if cfg is not None else load_config()
    path = config.paths.reports / "loco" / "loco-per-class.csv"
    if not path.exists():
        raise ScreenError(
            f"no leave-one-class-out table at {path}. The transfer signal is #30's "
            f"measurement; run `python -m hydms.surrogate.loco` or restore the committed "
            f"tables."
        )
    table = pd.read_csv(path)
    for column in ("alloy_class", "r2"):
        if column not in table.columns:
            raise ScreenError(f"{path} has no {column!r} column.")
    return {str(row.alloy_class): float(row.r2) for row in table.itertuples()}


def support_edges(low_k: float, high_k: float, width: float = SUPPORT_BIN_K) -> tuple[float, ...]:
    """Bin edges covering ``[low_k, high_k]``, aligned to multiples of ``width``.

    Read from the *configured* temperature window rather than from the training rows, so the
    histogram spans exactly the range the ``temperature`` screen admits: an empty end bin is then
    a finding about the data, where edges fitted to the rows could never show one.
    """
    if width <= 0 or high_k <= low_k:
        raise ScreenError(f"no support bins fit {low_k:g} to {high_k:g} K at width {width:g}.")
    start = float(np.floor(low_k / width) * width)
    stop = float(np.ceil(high_k / width) * width)
    count = round((stop - start) / width)
    return tuple(start + width * step for step in range(count + 1))


def emit(cfg: Config | None = None) -> DomainReference:
    """Measure the reference from the curated data. The slow half of this module.

    Featurises all 1,279 curated rows through :func:`~hydms.surrogate.model.capacity_matrix`,
    which is the one assembly every other stage uses, so the feature spans here are the spans
    of the matrix the model was actually fitted on rather than of a second reconstruction.
    """
    from hydms.data.canonical import alloy_classes
    from hydms.surrogate.model import ModelSettings, capacity_matrix
    from hydms.surrogate.scaler import TRAIN

    config = cfg if cfg is not None else load_config()
    settings = ModelSettings.from_config(config)
    frame, split = capacity_matrix(config, settings=settings)
    training = frame.loc[split == TRAIN]
    return DomainReference.measured(
        training,
        alloy_classes(training),
        target=config.columns.target,
        features=settings.features,
        transfer=transfer_table(config),
        temperature=config.columns.temperature,
        temperature_edges=support_edges(
            config.domain.temperature_min_k, config.domain.temperature_max_k
        ),
    )


def main(argv: list[str] | None = None, out: TextIO | None = None) -> int:
    """``--emit`` rewrites the committed reference; no argument prints what it holds."""
    stream = out if out is not None else sys.stdout
    parser = argparse.ArgumentParser(
        prog="python -m hydms.screens.domain",
        description="The applicability-domain reference: measure it, or show it.",
    )
    parser.add_argument(
        "--emit",
        action="store_true",
        help=f"re-measure from the curated data and rewrite {REFERENCE_FILE.name}",
    )
    args = parser.parse_args(argv)

    reference = emit() if args.emit else DomainReference.packaged()
    if args.emit:
        REFERENCE_FILE.write_text(reference.to_json(), encoding="utf-8")
        print(f"wrote {REFERENCE_FILE}", file=stream)
    print(
        f"{reference.rows} training row(s), capacity {_number(reference.trained_min)} to "
        f"{_number(reference.trained_max)} wt%.\n"
        f"Ceiling {_number(reference.cross_family_max)} wt%: above it the corpus holds "
        f"{reference.rows_above} row(s), all {reference.sole_family}, whose measured "
        f"transfer is "
        f"{_number(reference.transfer.get(reference.sole_family, float('nan')))}.\n"
        f"{len(reference.feature_span)} feature span(s), "
        f"{len(reference.transfer)} class transfer(s), "
        f"{len(reference.temperature_counts)} temperature support bin(s).",
        file=stream,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - the command line
    raise SystemExit(main())
