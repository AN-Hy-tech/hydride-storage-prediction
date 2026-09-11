"""HG-2 -- no prediction path returns a bare number, and every refusal says which door it came through.

``docs/PHASE-H-RUNBOOK.md`` section 4: this gate fails when any prediction path returns a
point estimate without an interval **and** a domain verdict.

It is the card the whole phase exists for. A tree ensemble extrapolates as a constant, so
outside the training hull the model returns a plausible flat number rather than an obvious
failure (risk R1) -- the interval and the domain verdict are what make that visible, and a
refusal with a stated reason is what makes it unmissable. "Contains Tc, which appears in no
training alloy" tells a user what to do next; "cannot predict" only sends them away.

Three claims, and only one of them needs an artifact
-----------------------------------------------------

**Structural.** :class:`~hydms.delivery.contract.PredictionResult` has no default for
``interval`` and none for ``domain`` and refuses ``None`` for either, and
:class:`~hydms.delivery.contract.Refusal` has no field a number could be spelled in. Card #75
made the bare number unrepresentable rather than discouraged; this half re-measures that,
because a default added later would put it back without touching a line this gate reads.

**Exhaustive over the path, by reading every exit rather than by sampling inputs.** The card
asks for "asserted exhaustively, not sampled", and no probe set can deliver that: passing a
thousand formulas establishes what a thousand formulas do. So the *source* of
:func:`~hydms.delivery.predict.predict_capacity` is parsed and every ``return`` in it is
required to return a call to one of the two contract types. A branch added later that returns
a float, a dict, or nothing at all is red the moment it is written, whatever it is given.

**Behavioural, against a real artifact.** The first two hold in an empty checkout; neither
says the assembled path answers. So a probe set goes through ``predict_capacity`` over the
version under certification -- the same ``_artifact.candidate`` door AC-3 and AC-4 use, for
the same reason: a gate cannot reach the artifact it exists to certify through the promoted
door, because the first thing recorded against a version is a gate run. See
:func:`~hydms.delivery.predict.bundle_from`, which is that split one layer up.

**So this gate can go red where it cannot go green.** CI's fast lane has no artifacts --
``.gitignore`` excludes ``/artifacts/`` -- so the behavioural half skips there and the first
two still run: a structural regression is caught on every push, and a ``SKIPPED`` says
honestly that the rest was not established.

Which door a code arrives through
----------------------------------

Card #76 left three findings here and they are one question. ``untrusted-family`` is declared
by the applicability screen, published in ``docs/REFUSALS.md``, and cannot be reached by
typing a formula: the rule judges a **family label** against that family's measured
leave-one-class-out transfer (#30), and a user who types ``LaNi5`` supplies no label. The
catalogue's ``unreadable-formula`` row carries the *screens'* sentence, which this path also
cannot produce, because :func:`~hydms.descriptors.featurize.featurize` raises before any
screen sees the candidate. And the temperature window declares ``indeterminate`` for "there
was no number to compare", which no request can express at all.

None of those is a defect and all three are the same fact: **there are two doors into the
screens, and they can state different things.** The *request* door
(:func:`~hydms.delivery.predict.predict_capacity`) accepts a formula and a temperature and
computes everything else; the *frame* door (:func:`~hydms.screens.protocol.apply_screens` over
a curated frame -- the training data, #84's uploaded CSV, and the probes behind
``docs/REFUSALS.md``) can state a prediction, a band, a class label and a feature value
directly. A code reachable only through the second is not dead vocabulary; a page that does
not say which is a page that over-claims. So this gate measures both doors and requires their
union to be the declared vocabulary exactly, and ``docs/REFUSALS.md`` now labels every row
with the door that reaches it.

What the request door cannot reach, and the two kinds of "cannot"
------------------------------------------------------------------

:data:`ABSENCES` is the difference between those two kinds, and it is the only part of this
gate that is declared rather than measured:

**Structural** -- no fit can reach it, because the input does not exist at this door.
``untrusted-family`` is the whole of this class. It must stay unreachable: supplying the
column with a guessed value would make the screen answer ``indeterminate`` for a class it has
no transfer estimate for, so every *novel* candidate -- the entire point of the exercise --
would be refused for the wrong reason (card #76). This gate goes **red** if it becomes
reachable.

**Contingent** -- reachable in principle, and this fit does not produce it. Both of the
capacity rules are here: ``above-physical-ceiling`` and ``out-of-domain`` need the model to
predict above a composition's physical ceiling or above the 5.19 wt% cross-family level, and a
well-behaved fit simply does not. A gate that demanded them would be red for the reason the
model is good. So they are reported, not required.

A code that is neither measured at this door nor listed in :data:`ABSENCES` is a failure: it
means reachability moved and nothing says why.

What the card asked for that turned out not to exist
------------------------------------------------------

Card #77 asks for "element absent from the training set -> refusal, naming the element", and
measured against the real artifact there is no such rule and cannot be one. ``Tc2Ni`` --
technetium appears in no training alloy -- is **answered**, at 4.17 on the ElMD scale against
a ceiling of 11.73. That is #49's design and not an oversight: novelty is a distance between
*compositions*, not a test of element membership, because the programme's whole purpose is
proposing alloys nobody has made. An element-membership rule would refuse every genuinely new
candidate and admit every re-proportioning of an old one.

Two real rules sit where the card expected one, and the probes below name both. An element the
**property tables** do not cover is refused with ``indeterminate``, and that sentence names
the element (``Blocking element(s): Rn, Xe``). A composition far from the corpus is refused
with ``beyond-known-chemistry``, and that sentence names the distance, the ceiling and the
nearest known alloy. Neither says "absent from the training set", because nothing judges that.

Owned by card #77.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import textwrap
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any, Final

from hydms.config import Config

from ._artifact import NoCandidate, candidate
from ._core import Gate, GateResult, Speed, Status

__all__ = ["GATE", "NOT_ALWAYS", "PROBES", "Probe", "Reachability"]

#: What a probe may require of the answer. A code requires that exact code; the other two are
#: for inputs whose outcome the *fit* decides, and demanding a code for those would make this
#: gate red whenever the model is well-behaved.
REFUSAL: Final = "<any refusal>"
EITHER: Final = "<the fit decides>"

#: A failure naming every probe is a failure nobody reads to the end.
_MAX_NAMED = 6


class Reachability(str, Enum):
    """How a declared code stands at the request door, where it is not simply reachable.

    ``NEVER`` means the input does not exist at that door, so no fit can produce it: the gate
    is **red** if it appears, because something started supplying an input a caller never
    gave. ``SOMETIMES`` means the fit decides -- it is reported either way and never required,
    since demanding it would make the gate red for the reason the model is well-behaved.

    A code in neither state is required: it is forced by a probe's input whatever the fit
    says, and its disappearance is a finding.
    """

    NEVER = "never"
    SOMETIMES = "sometimes"


def _not_always() -> dict[str, tuple[Reachability, str]]:
    """Built in a function so the codes are imported rather than spelled. See :data:`NOT_ALWAYS`."""
    from hydms.screens.domain import (
        ABOVE_PHYSICAL_CEILING,
        HIGH_UNCERTAINTY,
        OUT_OF_DOMAIN,
        OUTSIDE_FEATURE_RANGE,
        UNTRUSTED_FAMILY,
    )
    from hydms.screens.novelty import BEYOND_KNOWN_CHEMISTRY

    return {
        UNTRUSTED_FAMILY: (
            Reachability.NEVER,
            "the rule judges an alloy-class label against that family's measured transfer, "
            "and a caller who types a formula supplies no label. Supplying a guessed one is "
            "worse than omitting it: the screen answers `indeterminate` for a class it has no "
            "transfer estimate for, so every novel candidate would be refused for the wrong "
            "reason (card #76). It is reachable through the frame door, where a label is real",
        ),
        OUT_OF_DOMAIN: (
            Reachability.SOMETIMES,
            "the model has to predict above the 5.19 wt% level more than one alloy class "
            "reaches in training, which is a property of the fit and not of this path",
        ),
        ABOVE_PHYSICAL_CEILING: (
            Reachability.SOMETIMES,
            "the model has to predict more hydrogen than the composition can hold at H/M 3, "
            "which is a property of the fit and not of this path",
        ),
        HIGH_UNCERTAINTY: (
            Reachability.SOMETIMES,
            "the calibrated band has to come back wider than "
            "`domain.max_interval_width_wt_pct`, which is what the conformal correction and "
            "the candidate together decide",
        ),
        BEYOND_KNOWN_CHEMISTRY: (
            Reachability.SOMETIMES,
            "the novelty screen runs third, and `resolve` reports the *first* rejecting "
            "screen's code, so the applicability screen sitting between it and the window can "
            "take the code first on a fit that finds the same candidate implausible for a "
            "capacity reason. Measured both ways: the deployed v2 answers `K1Rb1` with this "
            "code, and the cheap fixture fit in tests/gates answers it with a domain code",
        ),
        OUTSIDE_FEATURE_RANGE: (
            Reachability.SOMETIMES,
            "the composition's features are committed reference data rather than fit output, "
            "but the rule sits below two capacity rules in the domain screen's own "
            "precedence, so a fit that rejected the same candidate higher up would take the "
            "code off this door without anything being wrong",
        ),
    }


#: Every declared code whose reachability through the request door is **not** required, with
#: the kind and the argument. The one declared thing in this module; everything else it
#: reports is measured in the call. A code absent from this mapping must be reachable by
#: typing a formula and a temperature, and the probe set is what reaches it.
NOT_ALWAYS: Final = _not_always()


# --------------------------------------------------------------------------------------
# The probes
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Probe:
    """One thing a caller can type, and what the answer must carry.

    Attributes:
        name: The probe's label in the result message.
        formula: The composition, as a caller would write it.
        temperature_k: Kelvin.
        expects: A reason code the input **forces** whatever the fit says, or :data:`REFUSAL`
            for an input that must be refused on some rule, or :data:`EITHER` where the fit
            decides and only the *shape* of the answer is this gate's business.
        names: Substrings the explanation must contain. This is the card's "naming the parse
            failure", "naming the element" and "naming the range" in the only form that can go
            red: a refusal whose sentence stopped naming what it is about still carries the
            right code, and #49 shipped exactly that defect.
        forbids: Codes the answer must **not** carry. One probe needs it and the reason is
            card #49's: ``"NaN"`` is sodium and nitrogen to both parsers, so the pin is not
            "it reaches this code" -- which fit and feature spans decide -- but "it is never
            refused as unreadable", which is what a null blocklist added here would do.
        names_the_window: Whether the explanation must name both trained temperature bounds.
            A flag rather than two literals, because the bounds are ``pipeline.yaml``'s and a
            gate that spelled them would be a second place for them to drift.
        why: What this probe is for. Prose, in the failure message, so a red gate says which
            guarantee moved rather than only which string did.
    """

    name: str
    formula: str
    temperature_k: float
    expects: str
    why: str
    names: tuple[str, ...] = ()
    forbids: tuple[str, ...] = ()
    names_the_window: bool = False


def _probes() -> tuple[Probe, ...]:
    from hydms.delivery.contract import INDETERMINATE
    from hydms.screens.window import OUTSIDE_WINDOW

    return (
        Probe(
            name="known-alloy",
            formula="LaNi5",
            temperature_k=298.0,
            expects=EITHER,
            why="the AB5 alloy the forward model was built on, at room temperature -- the "
            "probe that exercises the branch returning a number at all",
        ),
        Probe(
            name="window-lower-edge",
            formula="LaNi5",
            temperature_k=195.0,
            expects=EITHER,
            why="the coldest trained temperature: the window is closed, so it is inside",
        ),
        Probe(
            name="window-upper-edge",
            formula="LaNi5",
            temperature_k=773.0,
            expects=EITHER,
            why="the hottest trained temperature, for the same reason and the other side",
        ),
        Probe(
            name="too-cold",
            formula="LaNi5",
            temperature_k=100.0,
            expects=OUTSIDE_WINDOW,
            why="below the trained range. Forced, not contingent: the window reads the "
            "request's own temperature, so no fit can change this verdict",
            names_the_window=True,
        ),
        Probe(
            name="too-hot",
            formula="LaNi5",
            temperature_k=1000.0,
            expects=OUTSIDE_WINDOW,
            why="above the trained range, and the refusal must name the range rather than "
            "only decline -- 'cannot predict' sends a user away",
            names_the_window=True,
        ),
        Probe(
            name="unparseable-formula",
            formula="Xx2",
            temperature_k=298.0,
            expects=INDETERMINATE,
            why="a symbol that names no element. No screen declares a code for 'this does "
            "not parse', and inventing one here would be the second source of truth #75 "
            "exists to prevent, so the declared `indeterminate` carries it (card #76)",
            names=("Xx",),
        ),
        Probe(
            name="partially-parseable-formula",
            formula="LaNi5Xx2",
            temperature_k=298.0,
            expects=INDETERMINATE,
            why="card #49's own string: a real alloy with a symbol appended. ElMD reads it as "
            "LaNi5 at distance zero, so a path that did not refuse would answer confidently "
            "about a different material",
            names=("Xx",),
        ),
        Probe(
            name="element-absent-from-the-tables",
            formula="Xe1Rn1",
            temperature_k=298.0,
            expects=INDETERMINATE,
            why="the honest half of the card's 'unknown element' box: an element the property "
            "tables do not cover is refused and the sentence names it. The other half -- an "
            "element absent from the training set -- is not a rule this system has; see the "
            "module docstring",
            names=("Rn", "Xe"),
        ),
        Probe(
            name="beyond-known-chemistry",
            formula="K1Rb1",
            temperature_k=298.0,
            expects=REFUSAL,
            why="two alkali metals: real elements with real descriptors and no hydride "
            "chemistry anywhere near them. Refused on some rule whatever the fit says, "
            "because the novelty distance reads the formula and not the model",
        ),
        Probe(
            name="a-missing-value-that-is-chemistry",
            formula="NaN",
            temperature_k=298.0,
            expects=EITHER,
            why="the one spelling of a missing value that is a real material -- sodium and "
            "nitrogen, to this project's grammar and to ElMD both. It must be judged as "
            "chemistry. If it ever comes back `indeterminate`, a null blocklist was added to "
            "the delivery path and it is refusing a real composition (cards #49, #76); #84 "
            "owns the boundary where a missing value becomes text",
            forbids=(INDETERMINATE,),
        ),
        Probe(
            name="a-wide-band",
            formula="Mg2Ni",
            temperature_k=298.0,
            expects=EITHER,
            why="a real and famous hydride the corpus knows, whose band this fit returns "
            "wider than the project will report. It is here to reach `high-uncertainty` -- "
            "the one rule that judges the interval rather than the number -- and its outcome "
            "is the fit's to decide, which is why that code is in NOT_ALWAYS",
        ),
    )


#: The request-door probe set: one input per guarantee, chosen rather than sampled.
PROBES: Final = _probes()


# --------------------------------------------------------------------------------------
# The three claims
# --------------------------------------------------------------------------------------


def _structural() -> list[str]:
    """Findings about the contract types: a bare number must be unspellable.

    Returns:
        One sentence per defect, empty where the types still forbid it.
    """
    from hydms.delivery.contract import (
        ContractError,
        DomainVerdict,
        Interval,
        PredictionRequest,
        PredictionResult,
        Refusal,
    )

    found: list[str] = []
    required = {
        field.name: field
        for field in dataclasses.fields(PredictionResult)
        if field.name in ("interval", "domain")
    }
    for name in ("interval", "domain"):
        field = required.get(name)
        if field is None:
            found.append(
                f"PredictionResult has no {name!r} field at all, so an answer can be built "
                f"without one."
            )
            continue
        if (
            field.default is not dataclasses.MISSING
            or field.default_factory is not dataclasses.MISSING
        ):
            found.append(
                f"PredictionResult.{name} has a default, so an answer can be built without "
                f"saying what it is. Card #75's claim is that the bare number cannot be "
                f"*spelled*, and a default is how it comes back."
            )

    spelled = {field.name for field in dataclasses.fields(Refusal)}
    for forbidden in ("capacity", "interval"):
        if forbidden in spelled:
            found.append(
                f"Refusal carries a {forbidden!r} field. A refusal that carried a number "
                f"'for reference' is the bare number with a disclaimer, and every consumer "
                f"would eventually read it."
            )

    request = PredictionRequest(formula="LaNi5", temperature_k=298.0)
    interval = Interval(lower=0.9, upper=1.9, level=0.8)
    verdict = DomainVerdict.admitted_by(("temperature",))
    for name, payload in (
        ("interval", {"interval": None, "domain": verdict}),
        ("domain", {"interval": interval, "domain": None}),
    ):
        try:
            PredictionResult(
                request=request,
                capacity=1.4,
                model_version="hg2-probe",
                novelty=None,
                **payload,
            )
        except ContractError:
            continue
        found.append(
            f"PredictionResult accepted {name}=None. The type is the guarantee -- there is "
            f"meant to be no way to construct an answer that does not say it."
        )
    return found


def _exits() -> tuple[int, list[str]]:
    """How many exits ``predict_capacity`` has, and every finding about them.

    A probe set establishes what its probes do. This reads the function's own exits, so a
    branch that returns a float, a dict or nothing is a finding the moment it is written --
    which is what card #77 means by "asserted exhaustively, not sampled".
    """
    from hydms.delivery import predict as module

    source = inspect.getsource(module.predict_capacity)
    tree = ast.parse(textwrap.dedent(source))
    function = tree.body[0]
    if not isinstance(function, ast.FunctionDef):  # pragma: no cover - defensive
        return 0, [
            f"predict_capacity did not parse as a function definition: {type(function)}"
        ]

    allowed = {"Refusal", "PredictionResult"}
    found: list[str] = []
    inner = {
        node
        for parent in ast.walk(function)
        if parent is not function and isinstance(parent, ast.FunctionDef | ast.Lambda)
        for node in ast.walk(parent)
    }
    exits = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Return) and node not in inner
    ]
    if not exits:
        return 0, ["predict_capacity has no return statement; it cannot answer anything."]

    for node in exits:
        line = node.lineno + module.predict_capacity.__code__.co_firstlineno - 1
        if node.value is None:
            found.append(
                f"line {line}: a bare `return`, so this path answers None. A caller cannot "
                f"tell that from a refusal and will read it as an absent answer."
            )
            continue
        call = node.value
        name = (
            call.func.id
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
            else None
        )
        if name not in allowed:
            found.append(
                f"line {line}: returns {ast.unparse(node.value)[:60]!r}, which is not a "
                f"Refusal or a PredictionResult. Every exit from this function is one of the "
                f"two contract types, because that is the whole of how a number cannot leave "
                f"without an interval and a verdict."
            )
    return len(exits), found


@dataclass(frozen=True)
class Answered:
    """What one probe came back with, reduced to what this gate asserts about it."""

    probe: Probe
    code: str
    refused: bool
    explanation: str
    findings: tuple[str, ...]


def _run(probe: Probe, bundle: Any, cfg: Config) -> Answered:
    """One probe through the real path, with every claim the card makes about it checked."""
    from hydms.delivery.contract import ADMITTED, PredictionResult, Refusal
    from hydms.delivery.predict import predict_capacity
    from hydms.screens.window import OUTSIDE_WINDOW, temperature_window

    answer = predict_capacity(probe.formula, probe.temperature_k, bundle=bundle)
    refusal = answer if isinstance(answer, Refusal) else None
    refused = refusal is not None
    code = refusal.code if refusal is not None else ADMITTED
    explanation = (
        answer.explanation if isinstance(answer, Refusal) else answer.domain.reason
    )
    found: list[str] = []

    if probe.expects not in (REFUSAL, EITHER) and code != probe.expects:
        found.append(
            f"reached {code!r} where the input forces {probe.expects!r}: {explanation}"
        )
    elif probe.expects == REFUSAL and not refused:
        found.append("was answered with a number where every fit must refuse it")
    if code in probe.forbids:
        found.append(
            f"came back as {code!r}, which this input must never be refused as: "
            f"{explanation}"
        )

    if refusal is not None:
        if not explanation.strip():
            found.append("was refused with no sentence. 'Cannot predict' sends a user away")
        payload = refusal.to_dict()
        for field in ("capacity", "interval"):
            if field in payload:
                found.append(f"its serialised refusal carries a {field!r}")
        for wanted in probe.names:
            if wanted not in explanation:
                found.append(
                    f"its sentence never names {wanted!r}, which is what the refusal is "
                    f"about: {explanation[:160]}"
                )
        if probe.names_the_window:
            # The *window's own* sentence, not the composed explanation. Temperature is also a
            # model input, so the applicability screen rejects the same candidate with a note
            # that happens to name both bounds -- and a check on the joined string would be
            # satisfied by a neighbour while the window's own reason had gone to "cannot
            # predict". That is #49's defect exactly: a true sentence, written by a different
            # rule, standing in for the one that was asked. Found by staging it.
            window = temperature_window(cfg)
            owed = [v for v in refusal.screens if v.code == OUTSIDE_WINDOW]
            if not owed:
                found.append(
                    f"was refused as {code!r} and no screen's own verdict carries that code, "
                    f"so nothing on the answer explains the rule that rejected it"
                )
            for verdict in owed:
                missing = [
                    f"{bound:g}"
                    for bound in (
                        cfg.domain.temperature_min_k,
                        cfg.domain.temperature_max_k,
                    )
                    if f"{bound:g}" not in verdict.reason
                ]
                if missing:
                    found.append(
                        f"screen {verdict.screen!r} rejected it and its own sentence never "
                        f"names {', '.join(missing)} -- the trained range is {window.span}, "
                        f"and a refusal that does not say what the range is leaves the caller "
                        f"nothing to do next: {verdict.reason}"
                    )
    elif isinstance(answer, PredictionResult):
        if answer.interval is None or answer.domain is None:  # pragma: no cover - typed away
            found.append("came back with a number and no interval or no verdict")
        if answer.novelty is None:
            found.append(
                "came back with no novelty distance. The novelty screen is in "
                "delivery_screens() (card #76), so every admitted candidate was measured "
                "against the corpus to be admitted at all -- AC-7 is answered with a blank"
            )
        if not answer.model_version.strip():
            found.append("came back without naming the artifact version that answered")

    return Answered(probe, code, refused, explanation, tuple(found))


# --------------------------------------------------------------------------------------
# The gate
# --------------------------------------------------------------------------------------


def _lines(items: Sequence[str]) -> str:
    listed = list(items)
    shown = listed[:_MAX_NAMED]
    more = "" if len(listed) <= _MAX_NAMED else f"\n  ... ({len(listed) - _MAX_NAMED} more)"
    return "\n".join(f"  {line}" for line in shown) + more


@dataclass(frozen=True)
class RefusalPath:
    """The gate. Every number it reports is measured in this call."""

    name: str = "HG-2"
    title: str = "Never a bare number: every answer carries an interval and a domain verdict"
    card: int = 77
    speed: Speed = Speed.FAST

    def check(self, cfg: Config) -> GateResult:
        from hydms.delivery.contract import ADMITTED, reason_codes
        from hydms.delivery.predict import bundle_from
        from hydms.delivery.refusals import answers, reached

        # The two claims that need no artifact, so a structural regression is red on a push
        # even though the behavioural half cannot pass in a checkout with no version on disk.
        count, defects = _exits()
        structural = _structural() + defects
        if structural:
            return GateResult.fail(
                self.name,
                f"{len(structural)} way(s) exist to return a point estimate without an "
                f"interval and a domain verdict:\n{_lines(structural)}",
                measured=f"{len(structural)} structural defect(s)",
                threshold="0",
            )

        declared = set(reason_codes())
        frame = set(reached(answers(cfg=cfg)))

        try:
            scored = candidate(cfg)
        except NoCandidate as absent:
            return GateResult.skip(
                self.name,
                f"the contract still forbids a bare number and every exit from "
                f"predict_capacity() is a Refusal or a PredictionResult -- but the assembled "
                f"path was not run, so this criterion is not established. {absent}",
            )

        bundle = bundle_from(scored.surrogate, cfg=cfg)
        run = [_run(probe, bundle, cfg) for probe in PROBES]
        broken = [
            f"{result.probe.name} ({result.probe.formula} at "
            f"{result.probe.temperature_k:g} K) {finding}"
            for result in run
            for finding in result.findings
        ]
        if broken:
            return GateResult.fail(
                self.name,
                f"{len(broken)} probe finding(s) against {scored.provenance}:\n"
                f"{_lines(broken)}",
                measured=f"{len(broken)} finding(s) over {len(run)} probe(s)",
                threshold="0",
            )

        request = {result.code for result in run}
        answered = [result for result in run if not result.refused]
        if not answered:
            return GateResult.skip(
                self.name,
                f"every one of the {len(run)} probes was refused by {scored.provenance}, so "
                f"the branch that returns a number was never reached and this run establishes "
                f"nothing about it. A model that refuses everything satisfies 'never a bare "
                f"number' trivially. Check AC-3 and AC-4 first: the refusals were "
                f"{_named_codes(request)}.",
            )

        # Reachability, per door. A code in neither the measured set nor NOT_ALWAYS means
        # reachability moved and nothing in the repository says why -- which is the state the
        # `untrusted-family` finding on card #76 was found in.
        unexplained = sorted(declared - request - set(NOT_ALWAYS) - {ADMITTED})
        if unexplained:
            return GateResult.fail(
                self.name,
                f"{_named_codes(unexplained)} is declared by a screen on the delivery path "
                f"and no probe reaches it by typing a formula and a temperature, and nothing "
                f"says why. Either the probe set stopped covering it -- in which case add the "
                f"input that reaches it -- or its reachability now depends on the fit, in "
                f"which case say so in hydms.gates.hg2_refusal_path.NOT_ALWAYS. A code the "
                f"published catalogue documents and this door silently stopped producing is "
                f"exactly what this gate exists to surface.",
                measured=f"{len(request)} of {len(declared)} code(s) at the request door",
                threshold="every declared code reachable, or its absence stated",
            )

        wrong = sorted(
            code
            for code, (kind, _) in NOT_ALWAYS.items()
            if kind is Reachability.NEVER and code in request
        )
        if wrong:
            return GateResult.fail(
                self.name,
                f"{_named_codes(wrong)} became reachable by typing a formula and a "
                f"temperature, and it is recorded here as one no caller can reach. For "
                f"`untrusted-family` that means an alloy-class label is now being supplied "
                f"for a candidate that has none: the screen answers `indeterminate` for a "
                f"class it has no transfer estimate for, so every novel candidate -- the "
                f"entire point of the programme -- would be refused for the wrong reason "
                f"(card #76). Either the label is real, and this mapping is stale, or the "
                f"guess must go.",
                measured=_named_codes(wrong),
                threshold="a code with no input at this door stays unreachable",
            )

        dead = sorted(declared - request - frame - {ADMITTED})
        if dead:
            return GateResult.fail(
                self.name,
                f"{_named_codes(dead)} is declared by a screen and reachable through neither "
                f"door -- not by typing a formula and a temperature, and not by screening a "
                f"curated frame. The system publishes a reason it can never give, which is "
                f"dead vocabulary wherever `docs/REFUSALS.md` prints it.",
                measured=f"{len(request | frame)} of {len(declared)} code(s) over both doors",
                threshold=f"{len(declared)} of {len(declared)}",
            )

        never = sorted(
            code for code, (kind, _) in NOT_ALWAYS.items() if kind is Reachability.NEVER
        )
        quiet = sorted(declared - request - {ADMITTED} - set(never))
        return GateResult(
            self.name,
            Status.PASSED,
            f"no path through predict_capacity() returns a point estimate without an interval "
            f"and a domain verdict. The contract has no default for either and refuses None "
            f"for both; all {count} exits from the function return a Refusal or a "
            f"PredictionResult, read from its source rather than sampled; and "
            f"{len(run)} probe(s) against {scored.provenance} each came back with a code and "
            f"a sentence -- {len(answered)} answered with an interval, a verdict and an ElMD "
            f"distance, {len(run) - len(answered)} refused with no number anywhere in the "
            f"payload and each naming what it was about. Reachability by door: "
            f"{len(request)} code(s) by typing a formula and a temperature "
            f"({_named_codes(request)}); {len(frame)} by screening a curated frame; the union "
            f"is the declared vocabulary exactly. {_named_codes(never)} has no input at the "
            f"request door and must stay unreachable there. "
            f"{_named_codes(quiet) if quiet else 'Nothing else'} went unreached on this fit, "
            f"which NOT_ALWAYS records as the fit's to decide rather than this path's.",
            measured=f"{len(request | frame)}/{len(declared)} codes, 0 bare numbers",
            threshold=f"{len(declared)}/{len(declared)} codes, 0 bare numbers",
        )


def _named_codes(codes: Iterable[object]) -> str:
    listed = sorted(str(code) for code in codes)
    if not listed:
        return "none"
    if len(listed) <= _MAX_NAMED:
        return ", ".join(f"`{code}`" for code in listed)
    shown = ", ".join(f"`{code}`" for code in listed[:_MAX_NAMED])
    return f"{shown}, ... ({len(listed) - _MAX_NAMED} more)"



GATE: Gate = RefusalPath()
