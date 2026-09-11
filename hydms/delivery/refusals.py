"""L6 -- every reason this system can give for declining to answer, on one page a human reads.

::

    python -m hydms.delivery.refusals              # what the catalogue holds
    python -m hydms.delivery.refusals --emit       # regenerate docs/REFUSALS.md

**The defect this exists for.** Card #49's QA pass found a bug no test could see: the screen
refused ``LaNi5Xx2`` correctly, with the correct code and no number, and explained itself with
a sentence written for a *different* defect. The verdict was right and the reason was false. A
green suite cannot tell those apart, because a reason is prose and prose has no assertion that
fits it. Gate HG-2 (#77) already requires that a refusal *carry* a code and a reason; nothing
asks whether the reason is *true*.

So this module does not try to make a stale sentence go red. It puts every sentence the
delivery path can produce on a **diff line, next to the input that produced it**, in Markdown
rather than JSON, because the whole value of the file is that a human reads it. That is the
strongest mechanism available for a defect whose only symptom is a false sentence, and the
honest framing is worth keeping: the rule "a refusal must name the offending input" would not
have caught #49 either -- the false sentence named it and then explained it wrongly. Every rule
statable about a reason's *shape* passes on that string. What survives is showing the pair.

Two things here are automatic, and neither depends on anybody reading anything
--------------------------------------------------------------------------------

``the emitted code set equals reason_codes() exactly``
    :func:`~hydms.delivery.contract.reason_codes` *derives* the declared vocabulary from the
    screens rather than listing it, so declared and reachable can be compared. A declared code
    no probe reaches is **dead vocabulary**; an emitted code nothing declares is a **contract
    violation** -- and that second half is enforced by the contract itself, because
    :class:`~hydms.delivery.contract.Refusal` runs every code through the same
    ``_code`` check any other consumer does. Neither is a copy of the rule; both are the rule.

``every probe declares the path it was chosen for``
    A probe that stops reaching its path raises :class:`CatalogueError` naming both codes,
    rather than being quietly re-labelled with whatever it reaches now. Tighten
    ``domain.max_interval_width_wt_pct`` below the baseline band and the *baseline* probe stops
    being admitted; that should be a loud failure, because the page would otherwise silently
    start documenting a different system.

The probe set is chosen, not sampled
-------------------------------------

Sampling reaches the paths that are easy to reach. Each probe here exists to reach exactly one
code, and it changes exactly one thing about :func:`baseline`, so the reason it collects is
attributable. Where a code has more than one cause -- ``indeterminate`` has two that a caller
can actually produce, and the section below says why the third is unreachable -- each cause gets
its own probe, because they produce *different sentences* and it is the sentences this page
exists to show.

What is stated rather than measured, and why the page says so
--------------------------------------------------------------

Nothing is trained: no model, scaler or split is on disk. The screens read a prediction, an
interval width, an alloy class and a feature value, so those are **stated inputs** here, not
model output, and every answer carries ``model_version = 'unfitted-probe'``. The generated page
says this in its own words; a catalogue that let a stated 6.0 wt% read as a prediction would be
committing the error it exists to catch.

The screens are ``delivery_screens()`` exactly
-----------------------------------------------

Not the screens that *exist* -- the ones the delivery path runs. **That sequence has now run
once, and it worked.** #49's ElMD novelty screen was outside the tuple when this page was
written; card #76 put it in, and nothing here was edited to let its code through:
:func:`~hydms.delivery.contract.reason_codes` widened on its own, ``check_vocabulary`` failed
naming ``beyond-known-chemistry`` as declared-and-unreached, a probe was added for it, the
byte-identity test went red, and ``--emit`` closed it. The page gained a row, three verdict
lines per probe, and a sharper sentence for ``unreadable-formula`` -- #49's cross-check names
the offending symbol, where the domain screen could only say the ceiling was uncomputable.

One path a probe cannot reach, and it is the contract's doing
--------------------------------------------------------------

:attr:`~hydms.screens.window.Window.reasons` declares
:data:`~hydms.screens.protocol.INDETERMINATE` for "there was no number to compare", and no probe
here reaches it: :class:`~hydms.delivery.contract.PredictionRequest` refuses a non-finite
``temperature_k`` with a :class:`~hydms.delivery.contract.ContractError`, so a caller cannot
express the question that would produce it. The vocabulary is still complete -- the
applicability screen reaches ``indeterminate`` two other ways -- but the *window's* sentence for
it is never shown here and a stale one would therefore never land on a diff. Whether a
malformed request should come back as a :class:`~hydms.delivery.contract.Refusal` rather than
raise is #77's call, and it is boxed there rather than assumed here.

Composing one answer out of several verdicts
---------------------------------------------

:func:`~hydms.delivery.contract.resolve` is the judgement, and it is deliberately small: the
code is the **first rejecting screen's**, in the order the screens ran, and the reason carries
*every* rejecting screen's sentence joined by ``"; "`` -- the same composition
:class:`~hydms.screens.domain.ApplicabilityDomain` already makes across its own signals. Screen
order is the only precedence declared across screens, which is why it is the tiebreak.

It was written here and card #76 **moved it to the contract**, along with
:func:`~hydms.delivery.predict.screen_verdicts`, which moved to the prediction path. The real
prediction path needs both, and the alternative to moving them was one of two defects: a second
composition rule, which is how the API's sentence and the app's come to differ, or a production
module importing this one -- a documentation generator, with twelve probes and a Markdown
writer in it -- to borrow two functions. This module imports *them* now, which is the direction
that makes the page a report on the delivery path rather than a thing beside it.

This module is not re-exported from :mod:`hydms.delivery`. It imports pandas and the screens;
:mod:`hydms.delivery.contract` deliberately imports neither, and a consumer that only needs the
answer types should not pay for the screening stack to get them.

Card #90.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

import numpy as np
import pandas as pd

from hydms.config import Config, repo_root
from hydms.config import load as load_config
from hydms.delivery.contract import (
    ADMITTED,
    Answer,
    DomainVerdict,
    Interval,
    Novelty,
    PredictionRequest,
    PredictionResult,
    Refusal,
    ScreenVerdict,
    delivery_screens,
    reason_codes,
    resolve,
)
from hydms.delivery.predict import novelty_from, screen_verdicts
from hydms.screens.protocol import Screen, apply_screens

__all__ = [
    "BASELINE_CLASS",
    "BASELINE_FEATURE",
    "BASELINE_FORMULA",
    "BASELINE_PREDICTION",
    "BASELINE_TEMPERATURE_K",
    "BASELINE_WIDTH",
    "DOCUMENT",
    "FEATURE",
    "PROBES",
    "PROBE_VERSION",
    "CatalogueError",
    "Probe",
    "answers",
    "baseline",
    "candidates",
    "check_vocabulary",
    "columns",
    "document",
    "emit",
    "reached",
    "resolve",
]

#: The published page, rebuilt by ``--emit`` and never written by hand. It lives in ``docs/``
#: rather than ``reports/``: ``.gitignore`` excludes ``/reports/*`` with per-directory
#: negations, so a new ``reports/refusals/`` would be invisible on a fresh clone and the
#: fast-lane check would read nothing -- the trap already found on ``artifacts/current.json``
#: (#34) and ``reports/loco/`` (#30). The file is cheap to regenerate, so it has no claim on
#: ``reports/`` anyway, and ``docs/**`` is an allowed path under the freeze.
DOCUMENT = repo_root() / "docs" / "REFUSALS.md"

#: The version string every answer on this page carries. Not a fit: no model, scaler or split
#: is on disk, and a probe's answer and a real one being the same shape is exactly why the
#: provenance has to be written down rather than inferred from the shape.
PROBE_VERSION = "unfitted-probe"

#: The one feature column the probes carry, so that ``outside-feature-range`` is reachable at
#: all. ``temperature(K)`` is itself in the reference's spans and cannot serve: its span is the
#: temperature window's own interval, so a value outside it is rejected by the window screen
#: first and the domain code never reaches a caller. Checked against the committed reference in
#: :func:`candidates` rather than assumed.
FEATURE = "range_Mendeleev_Number"

#: The composition every probe uses unless it is the thing being varied. A real AB5 alloy, the
#: one the forward model was built on, with a physical capacity ceiling of 4.196 wt%.
BASELINE_FORMULA = "LaNi5"

#: Room temperature, comfortably inside the trained window.
BASELINE_TEMPERATURE_K = 298.0

#: A stated median-head capacity, below both the composition's physical ceiling and the
#: cross-family level. Weight percent.
BASELINE_PREDICTION = 1.4

#: A stated calibrated band width, below ``domain.max_interval_width_wt_pct``. Weight percent.
BASELINE_WIDTH = 0.9

#: A class leave-one-class-out measured, whose transfer is at or above ``domain.min_transfer_r2``.
BASELINE_CLASS = "AB5"

#: A stated value for :data:`FEATURE`, inside its trained span.
BASELINE_FEATURE = 40.0

_MAX_NAMED = 8


class CatalogueError(ValueError):
    """A probe stopped reaching the path it was chosen for, or the batch cannot be probed.

    A ``ValueError``, like the other layer guards in this package, and it always names the
    probe, the code it was chosen for and the code it reached. The whole point of the probe set
    is that it is a *specification* of the vocabulary; a probe that silently starts documenting
    a different path is the page quietly describing a different system.
    """


def _named(items: Iterable[object]) -> str:
    listed = sorted(map(repr, items))
    if len(listed) <= _MAX_NAMED:
        return ", ".join(listed)
    return f"{', '.join(listed[:_MAX_NAMED])}, ... ({len(listed) - _MAX_NAMED} more)"


def _number(value: float) -> str:
    """A number as it should read in a table cell: 773, not 773.0; 1.12 stays."""
    return f"{value:g}"


def _value(value: float | str) -> str:
    """One stated input, rendered. A non-finite number is ``absent``, never ``nan``.

    A cell reading ``nan`` invites a reader to treat it as a measurement that came out strange,
    when what it records is that the caller gave no value -- which is the whole input of the
    probe that carries it.
    """
    if isinstance(value, str):
        return value
    return "absent" if not np.isfinite(value) else _number(value)


# --------------------------------------------------------------------------------------
# The probes
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Probe:
    """One input, chosen to reach one rejection path, with the path it was chosen for.

    Fields are named by *role* rather than by column, so a probe does not repeat the config's
    spelling of ``H2_W% (max)`` or ``temperature(K)`` and a renamed column moves in one place.
    Every field defaults to the baseline, so a probe's source line shows exactly what it varies
    -- which is the same thing its row in the catalogue shows.

    Attributes:
        name: The probe's label, and its row's first cell.
        purpose: What this probe is for, in a phrase. It is prose in the generated page and it
            is the only part of a row nothing checks, which is why it says *why the input was
            chosen* and never what the answer will be.
        expects: The code this probe must reach. :func:`answers` refuses the run otherwise.
        formula: The composition, as a caller would write it.
        temperature_k: Kelvin. ``float('nan')`` means the caller gave none.
        prediction: A **stated** median-head capacity, wt%. Not model output; see the module
            docstring.
        interval_width: A **stated** calibrated band width, wt%.
        alloy_class: A **stated** family label.
        feature: A **stated** value for :data:`FEATURE`.
    """

    name: str
    purpose: str
    expects: str
    formula: str = BASELINE_FORMULA
    temperature_k: float = BASELINE_TEMPERATURE_K
    prediction: float = BASELINE_PREDICTION
    interval_width: float = BASELINE_WIDTH
    alloy_class: str = BASELINE_CLASS
    feature: float = BASELINE_FEATURE

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.purpose.strip():
            raise CatalogueError("a probe needs a name and a stated purpose.")
        if not self.expects.strip():
            raise CatalogueError(
                f"probe {self.name!r} does not say which code it was chosen to reach. A probe "
                f"without an expectation cannot fail; it can only be re-labelled."
            )

    @property
    def request(self) -> PredictionRequest:
        """What a caller would have asked -- the #75 request, built from this probe."""
        return PredictionRequest(formula=self.formula, temperature_k=self.temperature_k)

    def varied(self) -> dict[str, float | str]:
        """The fields this probe changes from :func:`baseline`, by role name.

        Empty for the probe that *is* the baseline, which is how its row says so.
        """
        against: dict[str, tuple[float | str, float | str]] = {
            "formula": (self.formula, BASELINE_FORMULA),
            "temperature_k": (self.temperature_k, BASELINE_TEMPERATURE_K),
            "prediction": (self.prediction, BASELINE_PREDICTION),
            "interval_width": (self.interval_width, BASELINE_WIDTH),
            "alloy_class": (self.alloy_class, BASELINE_CLASS),
            "feature": (self.feature, BASELINE_FEATURE),
        }
        changed: dict[str, float | str] = {}
        for role, (mine, base) in against.items():
            # `nan != nan`, which is what makes an absent temperature a change rather than a
            # value that happens to compare unequal to everything including itself.
            same = mine == base or (
                isinstance(mine, float)
                and isinstance(base, float)
                and np.isnan(mine)
                and np.isnan(base)
            )
            if not same:
                changed[role] = mine
        return changed


#: The committed probe set: one input per rejection path, plus the boundary cases the window's
#: closed interval turns on.
#:
#: Order is the reading order of the page and nothing else depends on it: the admitted rows
#: first, so a reader sees what an accepted answer looks like before every way of failing, then
#: the codes in the order a caller meets them -- the outer temperature bound, the three causes
#: that cannot be judged at all, then the applicability signals from "impossible" down to
#: "wide band".
PROBES: tuple[Probe, ...] = (
    Probe(
        name="baseline",
        purpose="a real AB5 alloy at room temperature, inside every rule that runs",
        expects=ADMITTED,
    ),
    Probe(
        name="window-lower-edge",
        purpose="the coldest trained temperature: the window is closed, so 195 K is inside it",
        expects=ADMITTED,
        temperature_k=195.0,
    ),
    Probe(
        name="window-upper-edge",
        purpose="the hottest trained temperature, for the same reason and the other side",
        expects=ADMITTED,
        temperature_k=773.0,
    ),
    Probe(
        name="too-cold",
        purpose="below the trained temperature range",
        expects="outside-window",
        temperature_k=100.0,
    ),
    Probe(
        name="too-hot",
        purpose="above the trained temperature range -- and outside its feature span too, "
        "which is why this row shows two screens rejecting and one code",
        expects="outside-window",
        temperature_k=1000.0,
    ),
    Probe(
        name="unreadable-formula",
        purpose="card #49's own string -- a real alloy with a symbol appended that names no "
        "element. The sentence this row carries is the one that was wrong",
        expects="indeterminate",
        formula="LaNi5Xx2",
    ),
    Probe(
        name="unmeasured-class",
        purpose="a family leave-one-class-out never measured, so no transfer estimate exists",
        expects="indeterminate",
        alloy_class="Perovskite",
    ),
    Probe(
        name="above-physical-ceiling",
        purpose="more hydrogen than this composition can hold -- physics, not evidence",
        expects="above-physical-ceiling",
        prediction=4.5,
    ),
    Probe(
        name="out-of-domain",
        purpose="above the capacity level more than one family reaches in training, on a "
        "composition whose physical ceiling is high enough that only this signal fires",
        expects="out-of-domain",
        formula="TiAl",
        alloy_class="AB",
        prediction=6.0,
    ),
    Probe(
        name="untrusted-family",
        purpose="a family whose measured transfer is below zero: the label alone rejects, "
        "whatever the composition and the prediction say",
        expects="untrusted-family",
        formula="Mg2Ni",
        alloy_class="Mg",
    ),
    Probe(
        name="outside-feature-range",
        purpose="a model input beyond the span the training rows covered for it",
        expects="outside-feature-range",
        feature=95.0,
    ),
    Probe(
        name="high-uncertainty",
        purpose="a band wider than the marginal spread of the target: the answer would tell "
        "the caller nothing they did not know before asking",
        expects="high-uncertainty",
        interval_width=1.6,
    ),
    Probe(
        name="beyond-known-chemistry",
        purpose="two alkali metals: real elements with real descriptors, and no hydride "
        "chemistry anywhere near them. This row is about the corpus, not the domain",
        expects="beyond-known-chemistry",
        formula="K1Rb1",
    ),
)


# --------------------------------------------------------------------------------------
# Running them
# --------------------------------------------------------------------------------------


def baseline(cfg: Config | None = None) -> dict[str, float | str]:
    """The candidate row every probe varies exactly one field of, on the config's columns.

    The prediction column is the **median** head's name, taken from
    :func:`~hydms.surrogate.model.column_names` rather than spelled, because position is the
    only thing identifying P50 in a MultiQuantile result and a second spelling of it here would
    be a second place for that to drift.
    """
    from hydms.surrogate.model import column_names

    config = cfg if cfg is not None else load_config()
    heads = column_names(config.model.quantiles)
    return {
        config.columns.formula: BASELINE_FORMULA,
        config.columns.temperature: BASELINE_TEMPERATURE_K,
        heads[len(heads) // 2]: BASELINE_PREDICTION,
        "interval_width": BASELINE_WIDTH,
        config.columns.alloy_class: BASELINE_CLASS,
        FEATURE: BASELINE_FEATURE,
    }


def columns(cfg: Config | None = None) -> dict[str, str]:
    """Each probe field's role mapped to the column the screens read it as."""
    from hydms.surrogate.model import column_names

    config = cfg if cfg is not None else load_config()
    heads = column_names(config.model.quantiles)
    return {
        "formula": config.columns.formula,
        "temperature_k": config.columns.temperature,
        "prediction": heads[len(heads) // 2],
        "interval_width": "interval_width",
        "alloy_class": config.columns.alloy_class,
        "feature": FEATURE,
    }


def candidates(
    probes: Sequence[Probe] | None = None, cfg: Config | None = None
) -> pd.DataFrame:
    """The probes as a candidate frame, one row each, indexed by probe name.

    Raises:
        CatalogueError: if :data:`FEATURE` is not one of the spans the committed
            applicability-domain reference range-checks. A feature column the reference does
            not know is silently ignored by the screen, so ``outside-feature-range`` would
            become unreachable and the page would report it as dead vocabulary -- a true
            statement about a broken probe set, and a confusing one.
    """
    from hydms.screens.domain import DomainReference

    spans = DomainReference.packaged().feature_span
    if FEATURE not in spans:
        raise CatalogueError(
            f"the probes carry {FEATURE!r}, which the committed applicability-domain reference "
            f"does not range-check. Its spans are {_named(spans)}. Point FEATURE at one of "
            f"them, or `outside-feature-range` is unreachable and this page will call it dead "
            f"vocabulary."
        )

    chosen = PROBES if probes is None else tuple(probes)
    if not chosen:
        raise CatalogueError("no probes were given; a catalogue of nothing reaches no code.")
    role = columns(cfg)
    base = baseline(cfg)
    rows = []
    for probe in chosen:
        row = dict(base)
        for field_name, value in probe.varied().items():
            row[role[field_name]] = value
        rows.append(row)
    return pd.DataFrame(rows, index=pd.Index([probe.name for probe in chosen], name="probe"))


def answers(
    probes: Sequence[Probe] | None = None,
    cfg: Config | None = None,
    *,
    screens: Sequence[Screen] | None = None,
) -> tuple[tuple[Probe, Answer], ...]:
    """Run every probe through the real screens and build the real answer for each.

    Args:
        probes: Defaults to :data:`PROBES`.
        cfg: Defaults to the packaged configuration.
        screens: Defaults to :func:`~hydms.delivery.contract.delivery_screens`. A different
            list is what a test that widens the vocabulary passes; the *page* is always
            generated from the delivery path's own screens.

    Returns:
        Each probe beside its answer -- a :class:`~hydms.delivery.contract.Refusal` where a
        screen rejected, a :class:`~hydms.delivery.contract.PredictionResult` where none did.
        Both are built by the #75 contract, so every code passes the contract's own vocabulary
        check on the way in and an emitted code nothing declares raises there.

    Raises:
        CatalogueError: if a probe did not reach the code it was chosen for.
        ~hydms.delivery.contract.ContractError: if a screen emitted a code the delivery layer
            does not declare. That is the "contract violation" half of this card's red
            condition, and it is the contract that refuses it, not this module.
    """
    config = cfg if cfg is not None else load_config()
    chosen = PROBES if probes is None else tuple(probes)
    running = tuple(delivery_screens() if screens is None else screens)
    verdicts = apply_screens(candidates(chosen, config), running)
    names = tuple(str(screen.name) for screen in running)

    built: list[tuple[Probe, Answer]] = []
    for probe in chosen:
        judged = screen_verdicts(verdicts, probe.name)
        code, reason = resolve(judged)
        if code != probe.expects:
            raise CatalogueError(
                f"probe {probe.name!r} was chosen to reach {probe.expects!r} and reached "
                f"{code!r}: {reason} -- so the catalogue would document a path nobody chose. "
                f"Either a threshold moved under it (check hydms/config/pipeline.yaml and "
                f"hydms/screens/domain-reference.json) or the probe needs re-choosing; do not "
                f"change `expects` to match what it reaches now."
            )
        built.append(
            (
                probe,
                _answer(
                    probe,
                    code,
                    reason,
                    judged,
                    config,
                    novelty_from(verdicts, names, probe.name),
                ),
            )
        )
    return tuple(built)


def _answer(
    probe: Probe,
    code: str,
    reason: str,
    judged: Sequence[ScreenVerdict],
    cfg: Config,
    novelty: Novelty | None = None,
) -> Answer:
    """One probe's answer, in the contract's own types.

    The admitted branch builds a :class:`~hydms.delivery.contract.PredictionResult` from the
    probe's *stated* prediction and band, which is the point at which "an answer with a number
    in it cannot be spelled without an interval and a verdict" is exercised rather than
    described.
    """
    if code != ADMITTED:
        return Refusal(
            request=probe.request,
            code=code,
            explanation=reason,
            model_version=PROBE_VERSION,
            screens=tuple(judged),
        )
    half = probe.interval_width / 2.0
    return PredictionResult(
        request=probe.request,
        capacity=probe.prediction,
        interval=Interval(
            lower=probe.prediction - half,
            upper=probe.prediction + half,
            level=cfg.conformal.confidence_level,
        ),
        domain=DomainVerdict(
            admitted=True, code=ADMITTED, reason=reason, screens=tuple(judged)
        ),
        # Measured, not stated: the novelty screen reads the probe's own formula and
        # computes a real ElMD distance from it. Reporting `None` here would be this page
        # saying "not measured" about something it measured, which is the class of defect it
        # exists to catch.
        novelty=novelty,
        model_version=PROBE_VERSION,
    )


def reached(built: Sequence[tuple[Probe, Answer]]) -> dict[str, tuple[str, ...]]:
    """Each code that was reached, mapped to the probes that reached it, in page order."""
    found: dict[str, list[str]] = {}
    for probe, answer in built:
        code = answer.code if isinstance(answer, Refusal) else ADMITTED
        found.setdefault(code, []).append(probe.name)
    return {code: tuple(names) for code, names in found.items()}


def check_vocabulary(
    built: Sequence[tuple[Probe, Answer]], screens: Sequence[Screen] | None = None
) -> None:
    """Refuse a catalogue whose codes are not exactly the declared vocabulary.

    The card's red condition, and the half of it that depends on nobody reading anything. A
    declared code no probe reaches is dead vocabulary -- a sentence the system can never say,
    which is either a screen nobody can trigger or a probe set that has stopped covering one.
    The other direction is already refused by the contract, one construction earlier; it is
    checked again here so the failure names the probe rather than the field.

    Raises:
        CatalogueError: on either mismatch, naming the codes and what to do about each.
    """
    declared = set(reason_codes(screens))
    found = set(reached(built))
    dead = declared - found
    undeclared = found - declared
    if dead:
        raise CatalogueError(
            f"{_named(dead)} is declared by a screen on the delivery path and no probe reaches "
            f"it, so this page would publish a vocabulary the system cannot use. Add a probe "
            f"that reaches it, or -- if nothing can -- the screen declares a code it never "
            f"emits and that is the finding."
        )
    if undeclared:
        raise CatalogueError(
            f"{_named(undeclared)} was emitted and no screen on the delivery path declares it. "
            f"A code invented at the rejection site is unreachable from the screens and cannot "
            f"be asserted (docs/QA-PROTOCOL.md, L6)."
        )


# --------------------------------------------------------------------------------------
# The page
# --------------------------------------------------------------------------------------


def _cell(text: str) -> str:
    """One table cell: pipes escaped, so a reason containing ``|`` cannot break the row."""
    return text.replace("|", "\\|")


def _input_cell(probe: Probe, role: dict[str, str]) -> str:
    """What this probe changed, as ``column = value``, or a phrase where it changed nothing."""
    varied = probe.varied()
    if not varied:
        return "*the baseline, unchanged*"
    return "; ".join(
        f"`{role[name]}` = {_value(value)}" for name, value in varied.items()
    )


def document(
    built: Sequence[tuple[Probe, Answer]],
    cfg: Config | None = None,
    *,
    screens: Sequence[Screen] | None = None,
) -> str:
    """The published page, built from the answers and never typed.

    Generated rather than written for the reason #29 and #30 already established here: a
    sentence that lives only in prose is a sentence no test can contradict. What is new is
    which property the generation buys -- not that the numbers are right, but that the *words*
    on the page are the words the code produces, so a stale one is a diff and not a discovery.
    """
    config = cfg if cfg is not None else load_config()
    role = columns(config)
    base = baseline(config)
    codes = reason_codes(screens)
    running = tuple(delivery_screens() if screens is None else screens)
    by_code = reached(built)

    lines = [
        "# The refusal catalogue",
        "",
        "Generated by `python -m hydms.delivery.refusals --emit`. Do not edit: "
        "`tests/delivery/test_refusals.py` asserts this file is byte-for-byte what the code "
        "produces.",
        "",
        f"Every row below is a real run. Each probe goes through `apply_screens` over the "
        f"{len(running)} screen(s) the delivery path runs "
        f"(`{'`, `'.join(screen.name for screen in running)}`), and its answer is built with "
        f"the card #75 contract -- a `Refusal` where a screen rejected, a `PredictionResult` "
        f"where none did. Nothing here is a transcription of what the code is believed to say.",
        "",
        "## What this page is for",
        "",
        "A verdict can be right while the sentence explaining it is wrong, and a green suite "
        "cannot tell those apart, because a reason is prose and prose has no assertion that "
        "fits it. Card #49 shipped exactly that: the correct code, no number, and an "
        "explanation written for a different defect. So every sentence the delivery path can "
        "produce is put here, on a diff line, beside the input that produced it. **Read the "
        "sentences.** That is the mechanism; nothing automatic can replace it.",
        "",
        "Two things here *are* automatic, and neither depends on anybody reading anything:",
        "",
        "- **The set of codes reached below equals the declared vocabulary exactly.** A "
        "declared code no probe reaches is dead vocabulary; an emitted code nothing declares "
        "is refused by the contract itself, one construction before this page exists.",
        "- **Every probe declares the path it was chosen for.** A probe that stops reaching it "
        "fails loudly rather than being quietly re-labelled with whatever it reaches now.",
        "",
        "## The stated inputs",
        "",
        "Nothing is trained: no model, scaler or split is on disk. The screens read a "
        "prediction, a band width, a family label and a feature value, so those are **stated "
        "inputs** here and not model output -- every answer on this page carries "
        f"`model_version = {PROBE_VERSION!r}` for the same reason. A probe changes exactly one "
        "of the following and nothing else, which is what makes the sentence it collects "
        "attributable.",
        "",
        "| Column | Baseline | Stated or real | What reads it |",
        "|---|---|---|---|",
    ]
    described = {
        "formula": (
            "real",
            "the composition's physical capacity ceiling, and the temperature-independent "
            "half of the domain screen",
        ),
        "temperature_k": ("real", "the temperature window, and its own trained feature span"),
        "prediction": (
            "stated",
            "the physical ceiling and the cross-family capacity level",
        ),
        "interval_width": ("stated", "the band-width signal"),
        "alloy_class": ("stated", "the measured leave-one-class-out transfer of that family"),
        "feature": ("stated", "the trained span of one model input"),
    }
    for name, (kind, reads) in described.items():
        column = role[name]
        lines.append(
            f"| `{column}` | {_value(base[column])} | {kind} | {reads} |"
        )
    lines += [
        "",
        "## The vocabulary",
        "",
        f"`reason_codes()` derives these {len(codes)} code(s) from the screens rather than "
        f"listing them, so \"what the system can say\" and \"what a screen can emit\" are one "
        f"set by construction. Every one of them is reached below.",
        "",
        "| Code | Declared by | Reached by |",
        "|---|---|---|",
    ]
    for code in codes:
        if code == ADMITTED:
            declared_by = "the screen contract"
        else:
            declared_by = ", ".join(
                f"`{screen.name}`" for screen in running if code in screen.reasons
            )
        lines.append(
            f"| `{code}` | {declared_by} | "
            f"{', '.join(f'`{name}`' for name in by_code.get(code, ()))} |"
        )
    lines += [
        "",
        "### One sentence this page cannot show",
        "",
        "The temperature window declares `indeterminate` for *there was no number to compare*, "
        "and no probe reaches it: `PredictionRequest` refuses a non-finite `temperature_k` "
        "with a `ContractError`, so a caller cannot express the question that would produce "
        "it. The vocabulary above is still complete -- the applicability screen reaches "
        "`indeterminate` two other ways, and both are below -- but the window's own sentence "
        "for it is never rendered here, so a stale one would not land on a diff. Whether a "
        "malformed request should come back as a `Refusal` rather than raise is card #77's "
        "call.",
        "",
        "## The catalogue",
        "",
        "One row per probe: what was asked, the code the caller receives, and the sentence it "
        "arrives with. Where two screens rejected, the code is the first one's and the reason "
        "carries both -- a candidate rejected by two rules and explained by one is the partial "
        "truth this layer exists to remove.",
        "",
        "| Probe | Input | Code | Reason |",
        "|---|---|---|---|",
    ]
    for probe, answer in built:
        code = answer.code if isinstance(answer, Refusal) else ADMITTED
        reason = (
            answer.explanation
            if isinstance(answer, Refusal)
            else answer.domain.reason
        )
        lines.append(
            f"| `{probe.name}` | {_cell(_input_cell(probe, role))} | `{code}` | "
            f"{_cell(reason)} |"
        )
    lines += [
        "",
        "### Why each input was chosen",
        "",
    ]
    lines += [f"- **`{probe.name}`** -- {probe.purpose}." for probe, _ in built]
    lines += [
        "",
        "## Every screen's verdict",
        "",
        "The table above shows what one caller receives. This one shows what each screen "
        "actually said, including the screens whose rejection was not the one reported -- so a "
        "sentence that has gone stale still lands on a diff line even when another screen "
        "names the code.",
        "",
        "| Probe | Screen | Passed | Code | Reason |",
        "|---|---|---|---|---|",
    ]
    for probe, answer in built:
        judged = (
            answer.screens if isinstance(answer, Refusal) else answer.domain.screens
        )
        for verdict in judged:
            lines.append(
                f"| `{probe.name}` | `{verdict.screen}` | "
                f"{'yes' if verdict.passed else 'no'} | `{verdict.code}` | "
                f"{_cell(verdict.reason)} |"
            )
    lines += [
        "",
        "## How to read a change to this file",
        "",
        "A diff here is one of four things, and only the first needs a human.",
        "",
        "1. **A reason changed and its code did not.** The wording of an explanation moved. "
        "Read the new sentence against the input beside it and ask whether it is *true of that "
        "input* -- not whether it is well written, and not whether the code is right. This is "
        "the check no test performs and the reason this page is Markdown.",
        "2. **A code changed.** It cannot get here quietly: `--emit` refuses a probe that no "
        "longer reaches the path it was chosen for. Something moved a threshold, and the "
        "question is whether that was intended.",
        "3. **A row appeared or vanished.** The probe set moved. A vanished row is a path that "
        "is no longer covered.",
        "4. **The vocabulary table grew.** A screen joined the delivery path -- card #76 owns "
        "whether #49's ElMD novelty screen does -- or an existing one declared a new code. "
        "Every new code needs a probe, or `--emit` refuses it as dead vocabulary.",
        "",
        "Card #90. Registration of this check as a gate (HG-5) is boxed on #91, deliberately "
        "after the freeze lifts: `docs/FREEZE.md` fixes HG-1 through HG-4 as the unfreeze "
        "condition, and that list is the one thing that document exists to resist widening.",
        "",
    ]
    return "\n".join(lines)


def emit(path: Path | None = None, cfg: Config | None = None) -> Path:
    """Run the probes and rewrite the committed page. The whole of ``--emit``.

    Cheap -- the screens read a mass table and a committed JSON reference, and featurise
    nothing -- so this is a fast-lane operation and not a slow one, unlike ``loco --emit``
    which reads tables a four-hour run produced.
    """
    config = cfg if cfg is not None else load_config()
    built = answers(cfg=config)
    check_vocabulary(built)
    destination = DOCUMENT if path is None else Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # `newline` explicitly: the default translates "\n" to the platform terminator, so a page
    # emitted on Windows and one emitted on Linux would differ in every line and the
    # committed-bytes test would fail on whichever machine did not write it.
    destination.write_text(document(built, config), encoding="utf-8", newline="\n")
    return destination


def main(argv: list[str] | None = None, out: TextIO | None = None) -> int:
    """``--emit`` rewrites the committed page; no argument reports what the probes reach."""
    stream = out if out is not None else sys.stdout
    parser = argparse.ArgumentParser(
        prog="python -m hydms.delivery.refusals",
        description="The refusal catalogue: publish it, or show what it reaches.",
    )
    parser.add_argument(
        "--emit",
        action="store_true",
        help=f"re-run the probes and rewrite {DOCUMENT.name}",
    )
    args = parser.parse_args(argv)

    built = answers()
    check_vocabulary(built)
    if args.emit:
        print(f"wrote {emit()}", file=stream)
    by_code = reached(built)
    print(
        f"{len(built)} probe(s) reaching all {len(reason_codes())} declared code(s).",
        file=stream,
    )
    for code, names in sorted(by_code.items()):
        print(f"  {code}: {', '.join(names)}", file=stream)
    return 0


if __name__ == "__main__":  # pragma: no cover - the command line
    raise SystemExit(main())
