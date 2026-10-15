"""The delivery contract: what cannot be built, and what survives a round trip.

Card #75's boxes, each written to measure a consequence rather than to restate a docstring.

**"Cannot be constructed without an interval and a domain verdict"** is checked two ways,
because they fail differently and both matter. Omitting the argument is a ``TypeError`` from
the dataclass -- a caller who forgot; passing ``None`` is a
:class:`~hydms.delivery.contract.ContractError` -- a caller who had nothing and said so. The
second is the one a real prediction path hits, when the screens did not run.

**The reason codes are enumerated from the screens.** The assertion is not "these are the
codes" -- that would be the literal list the card forbids -- but that the set *equals* what
the screens declare, and that adding a screen widens it. A test that named the codes would be
the second source of truth arriving in the test file instead of the module.

**JSON round-trips losslessly** by equality of the reconstructed object, not by comparing
dicts. Two payloads can differ in key order and mean the same thing; two objects that compare
equal carry the same numbers, and float equality after a ``json`` round trip is exact because
``json`` writes ``repr``.

Card #75.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass

import pytest
from hydms.delivery.contract import (
    ADMITTED,
    INDETERMINATE,
    SCHEMA,
    SPACE,
    UNIT,
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

REQUEST = PredictionRequest(formula="LaNi5", temperature_k=298.0)
BAND = Interval(lower=0.98, upper=1.91, level=0.8)
ADMITTED_BY = ("temperature", "domain")


def _verdict() -> DomainVerdict:
    return DomainVerdict.admitted_by(ADMITTED_BY)


def _result(**overrides: object) -> PredictionResult:
    fields: dict[str, object] = {
        "request": REQUEST,
        "capacity": 1.42,
        "interval": BAND,
        "domain": _verdict(),
        "novelty": None,
        "model_version": "v2",
    }
    fields.update(overrides)
    return PredictionResult(**fields)  # type: ignore[arg-type]


def _rejecting_code() -> str:
    """A real rejection code from a real screen, chosen without naming one here."""
    return next(code for code in reason_codes() if code != ADMITTED)


# --------------------------------------------------------------------------------------
# The structural half of HG-2
# --------------------------------------------------------------------------------------


def test_a_result_cannot_be_constructed_without_an_interval() -> None:
    """The bare number is unspellable. Card #75's central claim, and HG-2's structural half."""
    with pytest.raises(TypeError):
        PredictionResult(  # type: ignore[call-arg]
            request=REQUEST, capacity=1.42, domain=_verdict(), novelty=None, model_version="v2"
        )
    with pytest.raises(ContractError, match="without an interval"):
        _result(interval=None)


def test_a_result_cannot_be_constructed_without_a_domain_verdict() -> None:
    with pytest.raises(TypeError):
        PredictionResult(  # type: ignore[call-arg]
            request=REQUEST, capacity=1.42, interval=BAND, novelty=None, model_version="v2"
        )
    with pytest.raises(ContractError, match="without a domain verdict"):
        _result(domain=None)


def test_novelty_has_no_default_so_an_absence_is_stated_rather_than_forgotten() -> None:
    """`None` is legal and means 'not measured'; leaving it out is not.

    #49 is unstarted, so `None` is the honest value today. The field is required so that the
    day it lands, every caller has already had to say what it knows.
    """
    with pytest.raises(TypeError):
        PredictionResult(  # type: ignore[call-arg]
            request=REQUEST,
            capacity=1.42,
            interval=BAND,
            domain=_verdict(),
            model_version="v2",
        )
    assert _result(novelty=None).novelty is None


def test_refused_is_a_property_on_both_answers_and_cannot_be_set() -> None:
    """A field could be set to False on a refusal; a property cannot."""
    result = _result()
    refusal = Refusal(request=REQUEST, code=_rejecting_code(), explanation="declined.")

    assert result.refused is False
    assert refusal.refused is True
    for answer in (result, refusal):
        with pytest.raises(AttributeError):
            answer.refused = not answer.refused  # type: ignore[misc]


def test_a_refusal_carries_no_number_at_all() -> None:
    """A refusal with a capacity 'for reference' is the bare number with a disclaimer."""
    refusal = Refusal(request=REQUEST, code=_rejecting_code(), explanation="declined.")

    assert not hasattr(refusal, "capacity")
    assert not hasattr(refusal, "interval")
    assert "capacity" not in refusal.to_dict()
    assert "interval" not in refusal.to_dict()


def test_a_result_may_carry_a_rejecting_verdict_and_still_carry_its_number() -> None:
    """The distinction #80 must answer: a refusal is not the same as a low prediction.

    Collapsing the two would mean the only way to see what the model said about an
    out-of-domain candidate is to remove the screen.
    """
    code = _rejecting_code()
    rejected = DomainVerdict(
        admitted=False,
        code=code,
        reason="above the level at which cross-family evidence stops.",
        screens=(
            ScreenVerdict(screen="temperature", passed=True, code=ADMITTED, reason="inside."),
            ScreenVerdict(screen="domain", passed=False, code=code, reason="above the level."),
        ),
    )
    result = _result(domain=rejected)

    assert result.refused is False
    assert result.domain.admitted is False
    assert result.capacity == 1.42


# --------------------------------------------------------------------------------------
# The vocabulary, derived rather than written
# --------------------------------------------------------------------------------------


def test_the_code_set_is_exactly_admitted_plus_the_screens_reasons_plus_indeterminate() -> None:
    """Card #75's box, measured against the screens themselves rather than against a list."""
    screens = delivery_screens()
    declared = {reason for screen in screens for reason in screen.reasons}

    assert set(reason_codes(screens)) == {ADMITTED, INDETERMINATE} | declared
    assert reason_codes(screens)[0] == ADMITTED


def test_the_default_vocabulary_is_the_delivery_screens_vocabulary() -> None:
    assert reason_codes() == reason_codes(delivery_screens())


def test_a_new_screen_widens_the_vocabulary_with_no_change_to_this_module() -> None:
    """The property that makes the derivation worth having: #49 lands and the codes grow.

    The screen here is a stand-in for #49's, declared the way #44 requires. If this ever
    stops widening the set, the module has grown a literal list somewhere.
    """

    @dataclass(frozen=True)
    class Novel:
        name: str = "novelty"
        reasons: tuple[str, ...] = ("too-novel",)

    widened = reason_codes((*delivery_screens(), Novel()))

    assert "too-novel" in widened
    assert set(reason_codes()) < set(widened)


def test_a_code_no_screen_declares_is_refused_everywhere_it_can_appear() -> None:
    """The code set is enforced on construction, not merely published."""
    for build in (
        lambda: ScreenVerdict(screen="domain", passed=False, code="made-up", reason="x."),
        lambda: DomainVerdict(admitted=False, code="made-up", reason="x."),
        lambda: Refusal(request=REQUEST, code="made-up", explanation="x."),
    ):
        with pytest.raises(ContractError, match="no screen on the delivery path declares"):
            build()


def test_indeterminate_is_available_for_a_cause_no_screen_can_judge() -> None:
    """#77 refuses an unparseable formula, and no screen declares a threshold for that.

    `INDETERMINATE` is the declared code for "this rule could not be evaluated", the
    applicability screen already emits it for a formula it cannot give a ceiling to, and the
    parse error's own sentence goes in the explanation.
    """
    refusal = Refusal(
        request=PredictionRequest(formula="lani5", temperature_k=298.0),
        code=INDETERMINATE,
        explanation="'lani5' has an unexpected character 'l' at position 0.",
    )

    assert refusal.code in reason_codes()
    assert "lani5" in refusal.explanation


def test_a_refusal_cannot_claim_the_admitted_code() -> None:
    with pytest.raises(ContractError, match="means the candidate was admitted"):
        Refusal(request=REQUEST, code=ADMITTED, explanation="x.")


# --------------------------------------------------------------------------------------
# Units and the target space
# --------------------------------------------------------------------------------------


def test_the_unit_and_the_space_are_fields_and_are_serialised() -> None:
    """Not implied by a field name: `capacity` is expm1 of a log1p head and says so."""
    payload = _result().to_dict()

    assert payload["unit"] == UNIT == "wt%"
    assert payload["space"] == SPACE
    assert payload["interval"]["unit"] == UNIT
    assert payload["interval"]["space"] == SPACE


@pytest.mark.parametrize(
    ("unit", "space"),
    [("wt%", "log1p(capacity)"), ("log wt%", "capacity"), ("g/L", "capacity")],
)
def test_an_answer_in_another_unit_or_space_cannot_be_built_at_all(unit: str, space: str) -> None:
    """The refusal is on `Interval`, which is why the result's own cross-check never fires.

    That guard is kept and is documented as unreached: it would be the thing that fires if
    the unit ever became per-instance, and a claim held true by one check in one place is
    cheaper than the same claim spread over two.
    """
    with pytest.raises(ContractError, match="this contract carries"):
        Interval(lower=0.5, upper=1.0, level=0.8, unit=unit, space=space)


# --------------------------------------------------------------------------------------
# The interval's own guarantees
# --------------------------------------------------------------------------------------


def test_the_width_is_derived_so_it_cannot_disagree_with_the_bounds() -> None:
    assert BAND.width == pytest.approx(BAND.upper - BAND.lower, abs=1e-12)
    assert Interval.from_dict({**BAND.to_dict(), "width": 999.0}) == BAND


def test_a_negative_lower_bound_survives_intact() -> None:
    """Cards #48 and #77 act on it; clipping here would hide what the band exists to show."""
    band = Interval(lower=-0.4, upper=1.2, level=0.8)

    assert band.lower == -0.4
    assert band.contains(0.0)


def test_an_inverted_interval_is_refused() -> None:
    with pytest.raises(ContractError, match="inverted"):
        Interval(lower=1.9, upper=0.9, level=0.8)


@pytest.mark.parametrize("level", [0.0, 1.0, -0.1, 1.2])
def test_a_level_outside_zero_to_one_is_refused(level: float) -> None:
    """MAPIE takes `confidence_level`, not `alpha`; 0.2 must not silently claim a 20 % band."""
    with pytest.raises(ContractError, match="probability"):
        Interval(lower=0.9, upper=1.9, level=level)


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_a_non_finite_number_is_refused_because_json_cannot_carry_it(value: float) -> None:
    with pytest.raises(ContractError, match="finite"):
        Interval(lower=value, upper=1.9, level=0.8)


# --------------------------------------------------------------------------------------
# The verdicts agree with themselves
# --------------------------------------------------------------------------------------


def test_a_verdict_that_disagrees_with_its_own_code_is_refused() -> None:
    with pytest.raises(ContractError, match="disagrees with itself"):
        ScreenVerdict(screen="domain", passed=True, code=_rejecting_code(), reason="x.")
    with pytest.raises(ContractError, match="disagrees with itself"):
        DomainVerdict(admitted=True, code=_rejecting_code(), reason="x.")


def test_an_admitted_verdict_over_a_rejecting_screen_is_refused() -> None:
    code = _rejecting_code()
    with pytest.raises(ContractError, match="rejected"):
        DomainVerdict(
            admitted=True,
            code=ADMITTED,
            reason="inside every rule.",
            screens=(ScreenVerdict(screen="domain", passed=False, code=code, reason="no."),),
        )


def test_a_rejection_with_no_rule_behind_it_is_refused() -> None:
    with pytest.raises(ContractError, match="rejection with no rule"):
        DomainVerdict(
            admitted=False,
            code=_rejecting_code(),
            reason="declined.",
            screens=(
                ScreenVerdict(screen="temperature", passed=True, code=ADMITTED, reason="ok."),
            ),
        )


def test_admitted_by_refuses_an_empty_screen_list() -> None:
    """A verdict nothing judged is the silent drop's mirror image."""
    with pytest.raises(ContractError, match="no screens"):
        DomainVerdict.admitted_by(())


def test_every_verdict_carries_a_sentence_including_the_ones_that_passed() -> None:
    with pytest.raises(ContractError, match="blank"):
        ScreenVerdict(screen="domain", passed=True, code=ADMITTED, reason="   ")


# --------------------------------------------------------------------------------------
# The request
# --------------------------------------------------------------------------------------


def test_a_request_keeps_the_formula_exactly_as_written() -> None:
    """`'Pr1Co5 '` and `'Pr1Co5'` are one material and the *pipeline* is what says so.

    Stripping here would hide the behaviour #74 measures, and would make the request no
    longer a record of what was asked.
    """
    assert PredictionRequest(formula="Pr1Co5 ", temperature_k=298.0).formula == "Pr1Co5 "


def test_a_temperature_outside_the_trained_range_is_a_verdict_not_a_construction_error() -> None:
    """Refusing it here would make the screen's verdict unobservable -- what #44 prevents."""
    assert PredictionRequest(formula="LaNi5", temperature_k=1200.0).temperature_k == 1200.0


def test_an_empty_formula_is_a_caller_error_rather_than_an_unparseable_material() -> None:
    with pytest.raises(ContractError, match="needs a composition"):
        PredictionRequest(formula="   ", temperature_k=298.0)


@pytest.mark.parametrize("wrong", [5, ["La1Ni5"], {"formula": "La1Ni5"}, 2.5])
def test_a_formula_that_is_not_a_string_names_the_type_and_not_emptiness(
    wrong: object,
) -> None:
    """Card #77, from #76's QA pass: the guard must name the cause it observed.

    One sentence covered both arms, so ``predict_capacity(5, 298.0)`` was told "a request
    needs a composition; the formula is empty" -- every clause of it about a case that did
    not happen. It is reachable across a real boundary: ``from_dict`` checks only that the
    key is *present*, so a JSON body or a CSV column of part numbers arrives here, and #78
    and #84 would both hand a user the wrong explanation of what they did wrong. The
    temperature field one line below already distinguished its two arms, so the asymmetry
    was visible by reading one method.
    """
    with pytest.raises(ContractError) as raised:
        PredictionRequest(formula=wrong, temperature_k=298.0)  # type: ignore[arg-type]

    assert type(wrong).__name__ in str(raised.value)
    assert "empty" not in str(raised.value)


def test_a_non_string_formula_arrives_through_from_dict_which_only_checks_presence() -> None:
    """The boundary the finding crosses: JSON delivers this without complaint."""
    with pytest.raises(ContractError, match="must be a string"):
        PredictionRequest.from_dict({"formula": 5, "temperature_k": 298.0})


def test_a_malformed_request_raises_rather_than_becoming_a_refusal() -> None:
    """#77's decision, and the type had already made it.

    A refusal is a statement about a *material*: it carries the request it declines, so an
    input that cannot build a ``PredictionRequest`` cannot be carried by the ``Refusal`` that
    would describe it. The choice is closed by construction rather than by preference, which
    is why this test asserts the *type* rather than a policy.
    """
    fields = {f.name: f.type for f in dataclasses.fields(Refusal)}

    assert "request" in fields
    with pytest.raises(ContractError):
        Refusal(
            request="LaNi5",  # type: ignore[arg-type]
            code=INDETERMINATE,
            explanation="the formula was an integer",
        )


def test_a_request_carries_nothing_a_caller_could_widen_its_own_band_with() -> None:
    """The whole of the input is a composition and a temperature (card #75's design note)."""
    assert set(REQUEST.to_dict()) == {"formula", "temperature_k"}


# --------------------------------------------------------------------------------------
# Serialisation
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("novelty", [None, Novelty(distance=0.31, nearest="La1Ni5")])
def test_a_result_round_trips_through_json_without_loss(novelty: Novelty | None) -> None:
    result = _result(novelty=novelty)

    assert answer_from(json.loads(json.dumps(result.to_dict()))) == result


def test_a_refusal_round_trips_through_json_without_loss() -> None:
    code = _rejecting_code()
    refusal = Refusal(
        request=REQUEST,
        code=code,
        explanation="declined by the applicability rule.",
        model_version="v2",
        screens=(ScreenVerdict(screen="domain", passed=False, code=code, reason="above."),),
    )

    assert answer_from(json.loads(json.dumps(refusal.to_dict()))) == refusal


def test_answer_from_dispatches_on_refused_alone() -> None:
    """#79 compares the API's answer to the library's; both must come back one door."""
    assert isinstance(answer_from(_result().to_dict()), PredictionResult)
    refusal = Refusal(request=REQUEST, code=_rejecting_code(), explanation="declined.")
    assert isinstance(answer_from(refusal.to_dict()), Refusal)


def test_a_payload_that_does_not_say_whether_it_was_refused_is_refused() -> None:
    payload = _result().to_dict()
    payload.pop("refused")

    with pytest.raises(ContractError, match="whether it was refused"):
        answer_from(payload)


def test_a_payload_from_a_future_schema_is_refused_rather_than_guessed_at() -> None:
    payload = {**_result().to_dict(), "schema": "hydms.delivery/2"}

    with pytest.raises(ContractError, match="schema"):
        answer_from(payload)


def test_every_serialised_answer_carries_the_schema() -> None:
    refusal = Refusal(request=REQUEST, code=_rejecting_code(), explanation="declined.")

    assert _result().to_dict()["schema"] == SCHEMA
    assert refusal.to_dict()["schema"] == SCHEMA


def test_a_result_payload_missing_its_interval_is_refused_on_the_way_back_in() -> None:
    """The bare number must not be able to arrive by the transport door either."""
    payload = _result().to_dict()
    payload.pop("interval")

    with pytest.raises(ContractError, match="arriving by another door"):
        answer_from(payload)
