"""The refusal catalogue: what it publishes, and the two things it refuses to publish.

Card #90's boxes. The card is honest that its main mechanism is a human reading a diff, so
these tests are deliberately *not* written as though prose could be asserted. What they check is
everything around the prose:

  - the emitted code set equals the declared vocabulary, in **both** directions -- a declared
    code no probe reaches, and an emitted code no screen declares;
  - every probe still reaches the path it was chosen for, so the page cannot start documenting
    a different system under the same row labels;
  - the committed `docs/REFUSALS.md` is byte-for-byte what the code produces, which is what
    makes a stale sentence a diff line rather than a discovery.

The one thing not asserted anywhere is that a reason is *true*. That is the card's own finding:
every rule statable about a reason's shape passes on `LaNi5Xx2`, the string whose refusal was
correct and whose explanation was false. Adding such a test would buy false comfort, so none is
here; `docs/QA-PROTOCOL.md` section 4, question 8 carries the check that survives.

Card #90.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pandas", reason="the screens are pandas code")

from hydms.delivery.contract import (  # noqa: E402 -- after the pandas guard
    ADMITTED,
    ContractError,
    PredictionResult,
    Refusal,
    ScreenVerdict,
    delivery_screens,
    reason_codes,
)
from hydms.delivery.refusals import (  # noqa: E402
    DOCUMENT,
    FRAME,
    PROBES,
    REQUEST,
    CatalogueError,
    Probe,
    answers,
    candidates,
    check_vocabulary,
    delivery_refusal,
    document,
    emit,
    reached,
    resolve,
)
from hydms.screens.protocol import verdict_table  # noqa: E402


@pytest.fixture(scope="module")
def built() -> tuple[tuple[Probe, object], ...]:
    """The committed probe set, run once for the whole module."""
    return answers()


# --------------------------------------------------------------------------------------
# A screen that is not on the delivery path, for the two vocabulary directions
# --------------------------------------------------------------------------------------


class _Extra:
    """A screen declaring one code the delivery contract does not, admitting or rejecting.

    Not a `Screen` subclass: `hydms.screens.protocol.Screen` is a runtime-checkable Protocol,
    so structure is the whole membership test and a test double that satisfies it is exercising
    the same contract a real screen does.
    """

    name = "extra"
    #: A code no real screen declares. It read `beyond-known-chemistry` until card #76 put the
    #: novelty screen on the delivery path and made that code real -- at which point both
    #: tests below went green for the wrong reason, because a stand-in for "a code the
    #: contract does not declare" had quietly become a code the contract declares. A fictional
    #: rule is the right stand-in, and it cannot be overtaken by a fourth screen landing.
    reasons = ("smells-wrong",)

    def __init__(self, *, reject: bool) -> None:
        self._reject = reject

    def verdict(self, candidates):  # type: ignore[no-untyped-def]
        passed = not self._reject
        return verdict_table(
            passed,
            self.reasons[0] if self._reject else ADMITTED,
            "a sentence from a screen the delivery path does not run",
            index=candidates.index,
        )


# --------------------------------------------------------------------------------------
# The vocabulary, in both directions
# --------------------------------------------------------------------------------------


def test_the_emitted_codes_are_exactly_the_declared_vocabulary(built) -> None:
    """The card's red condition. Set equality, not containment, and not a literal list.

    Naming the codes here would be the second source of truth the contract module refuses to
    hold, arriving in the test file instead.
    """
    assert set(reached(built)) == set(reason_codes())


def test_a_declared_code_no_probe_reaches_is_named_as_dead_vocabulary(built) -> None:
    """A screen joining the delivery path without a probe must not publish quietly."""
    widened = (*delivery_screens(), _Extra(reject=False))
    assert "smells-wrong" in reason_codes(widened)
    with pytest.raises(CatalogueError, match="smells-wrong"):
        check_vocabulary(answers(screens=widened), widened)


def test_an_emitted_code_the_contract_does_not_declare_is_refused_by_the_contract() -> None:
    """And it is the contract that refuses it, one construction before the page exists.

    `_Extra` is not in `delivery_screens()`, so `reason_codes()` -- which the contract's own
    `_code` check reads -- does not carry its code, and `ScreenVerdict` rejects it.
    """
    with pytest.raises(ContractError, match="smells-wrong"):
        answers(screens=(*delivery_screens(), _Extra(reject=True)))


# --------------------------------------------------------------------------------------
# The probes
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("probe", PROBES, ids=lambda probe: probe.name)
def test_each_probe_reaches_the_path_it_was_chosen_for(probe: Probe, built) -> None:
    """Parametrised so a broken probe names itself, rather than one failure for the batch."""
    answer = next(found for chosen, found in built if chosen.name == probe.name)
    code = answer.code if isinstance(answer, Refusal) else ADMITTED
    assert code == probe.expects


def test_both_edges_of_the_temperature_window_are_inside_it(built) -> None:
    """The window is closed, and a boundary asserted on one side is half a test.

    195 K and 773 K are measured rows of `hydride_data.csv`; a half-open window would refuse a
    real training temperature. The probes document that, and this is the assertion under them.
    """
    edges = {
        probe.name: answer
        for probe, answer in built
        if probe.name in {"window-lower-edge", "window-upper-edge"}
    }
    assert set(edges) == {"window-lower-edge", "window-upper-edge"}
    for answer in edges.values():
        assert isinstance(answer, PredictionResult)


def test_a_probe_that_stops_reaching_its_path_fails_loudly() -> None:
    """The probe set is a specification, so a drifted probe is an error and not a re-label."""
    misaimed = Probe(
        name="claims-to-be-refused",
        purpose="the baseline, mislabelled -- this is the failure being demonstrated",
        expects="out-of-domain",
    )
    with pytest.raises(CatalogueError, match="was chosen to reach"):
        answers(probes=(misaimed,))


def test_the_admitted_answer_cannot_be_a_bare_number(built) -> None:
    """The catalogue runs through the real #75 contract, so HG-2's type check applies here."""
    admitted = [answer for _, answer in built if isinstance(answer, PredictionResult)]
    assert admitted
    for answer in admitted:
        assert answer.interval.width > 0.0
        assert answer.domain.admitted
        assert not answer.refused


def test_every_refusal_carries_a_code_and_a_sentence(built) -> None:
    """A refusal with no number in it still has to say what happened."""
    refusals = [answer for _, answer in built if isinstance(answer, Refusal)]
    assert refusals
    for answer in refusals:
        assert answer.code != ADMITTED
        assert answer.explanation.strip()
        assert answer.screens


def test_candidates_refuses_a_feature_the_reference_does_not_range_check(monkeypatch) -> None:
    """A feature column the domain reference does not know makes a code unreachable.

    Silently, too: the screen only range-checks the spans it recognises. The failure has to say
    so, or `outside-feature-range` would be reported as dead vocabulary and the finding would be
    aimed at the screen instead of at the probe set.
    """
    monkeypatch.setattr("hydms.delivery.refusals.FEATURE", "not_a_measured_span")
    with pytest.raises(CatalogueError, match="not_a_measured_span"):
        candidates()


def test_a_probe_varies_one_field_and_the_page_shows_which() -> None:
    """`varied()` is what the Input column renders; empty for the probe that is the baseline."""
    by_name = {probe.name: probe for probe in PROBES}
    assert by_name["baseline"].varied() == {}
    assert set(by_name["high-uncertainty"].varied()) == {"interval_width"}
    assert set(by_name["out-of-domain"].varied()) == {"formula", "prediction", "alloy_class"}


# --------------------------------------------------------------------------------------
# Which door reaches which row -- card #77, from #76's QA pass
# --------------------------------------------------------------------------------------


def test_a_probes_door_is_derived_from_what_it_varies_not_declared_beside_it() -> None:
    """A hand-maintained label is the thing that goes stale; this one cannot.

    A probe that states a prediction, a band, a class label or a feature value is describing
    something ``predict_capacity`` computes for itself, so no caller can ask for it.
    """
    by_name = {probe.name: probe for probe in PROBES}

    assert by_name["baseline"].door == REQUEST
    assert by_name["too-hot"].door == REQUEST
    assert by_name["unreadable-formula"].door == REQUEST
    assert by_name["untrusted-family"].door == FRAME
    assert by_name["high-uncertainty"].door == FRAME
    assert by_name["outside-feature-range"].door == FRAME


def test_untrusted_family_is_a_frame_row_and_the_page_says_so(built) -> None:
    """The page documented a code no caller can produce and did not say which door reaches it.

    Gate HG-2 owns the assertion that it stays unreachable by typing; this owns the assertion
    that the published page tells a reader so.
    """
    by_name = {probe.name: probe for probe in PROBES}
    assert by_name["untrusted-family"].door == FRAME

    page = document(built)
    assert "| `untrusted-family` | `frame` |" in page
    assert "no caller can reach it" in page


def test_the_typed_formulas_own_sentence_is_on_the_page_too(built) -> None:
    """The second of #76's two findings: same code, different words, and only one was shown.

    The catalogue's `unreadable-formula` row carries the *screens'* sentence, because the
    probes hand the screens a frame whose feature columns are already filled. A caller who
    types the same string never reaches a screen -- ``featurize`` raises first -- so the page
    now shows that sentence as well, on its own diff line.
    """
    by_name = {probe.name: probe for probe in PROBES}
    sentence = delivery_refusal(by_name["unreadable-formula"])

    assert sentence is not None
    assert "could not be parsed" in sentence
    assert "'Xx', which is not a chemical element" in sentence

    page = document(built)
    assert "refused before any screen runs" in page
    assert "could not be parsed" in page
    # And the screens' own sentence is still there: two true sentences, both shown.
    assert "could not be given a physical capacity ceiling" in page


def test_a_parse_failure_says_the_same_thing_whatever_the_version_was_fitted_on() -> None:
    """Why the page can print a caller's sentence with no artifact on disk.

    A formula is parsed before any feature is reached, so the refusal does not depend on which
    contract the served version implies. Pinned rather than assumed: if it ever became
    contract-dependent, the page would be printing one version's sentence as though it were
    every version's.
    """
    import pandas as pd
    from hydms.delivery.predict import CANDIDATE
    from hydms.descriptors.contract import PASSTHROUGH, FeatureContract
    from hydms.descriptors.featurize import FeaturisationError, featurize

    formulas = pd.Series(["LaNi5Xx2"], index=pd.Index([CANDIDATE]))
    temperatures = pd.Series([298.0], index=pd.Index([CANDIDATE]))
    narrowed = FeatureContract.from_names(("avg_valence_d", PASSTHROUGH))

    said = []
    for contract in (None, narrowed):
        with pytest.raises(FeaturisationError) as raised:
            featurize(formulas, temperatures, contract=contract)
        said.append((str(raised.value), raised.value.rows[CANDIDATE]))

    assert said[0] == said[1], "a parse failure named a feature set it never reached"
    by_name = {probe.name: probe for probe in PROBES}
    assert delivery_refusal(by_name["unreadable-formula"]) == said[0][1]


def test_a_frame_only_probe_has_no_typed_sentence() -> None:
    """`delivery_refusal` is about the request door; a frame row has no caller to ask."""
    by_name = {probe.name: probe for probe in PROBES}

    assert delivery_refusal(by_name["untrusted-family"]) is None
    assert delivery_refusal(by_name["high-uncertainty"]) is None


# --------------------------------------------------------------------------------------
# Composing one answer from several verdicts
# --------------------------------------------------------------------------------------


def _verdict(screen: str, code: str, reason: str) -> ScreenVerdict:
    return ScreenVerdict(screen=screen, passed=code == ADMITTED, code=code, reason=reason)


def test_resolve_takes_the_first_rejecting_screens_code_and_every_reason() -> None:
    """Run order is the only precedence declared across screens, so it is the tiebreak."""
    code, reason = resolve(
        (
            _verdict("temperature", "outside-window", "too hot"),
            _verdict("domain", "outside-feature-range", "outside its span"),
        )
    )
    assert code == "outside-window"
    assert reason == "too hot; outside its span"


def test_resolve_carries_every_screens_sentence_when_nothing_rejected() -> None:
    code, reason = resolve(
        (
            _verdict("temperature", ADMITTED, "inside the window"),
            _verdict("domain", ADMITTED, "inside the domain"),
        )
    )
    assert code == ADMITTED
    assert reason == "inside the window; inside the domain"


def test_resolve_refuses_a_candidate_no_screen_judged() -> None:
    """Admitted *because* the rules did not run is the silent drop's mirror image.

    A `ContractError` rather than a `CatalogueError`: card #76 moved `resolve` into the
    contract, because the real prediction path needs the same rule and a production module
    must not import this one -- a document generator -- to borrow it.
    """
    with pytest.raises(ContractError, match="no screen judged"):
        resolve(())


def test_a_row_rejected_by_two_screens_reports_one_code_and_both_reasons(built) -> None:
    """`too-hot` is outside the window *and* outside that column's trained span."""
    answer = next(found for probe, found in built if probe.name == "too-hot")
    assert isinstance(answer, Refusal)
    assert answer.code == "outside-window"
    rejecting = [verdict for verdict in answer.screens if not verdict.passed]
    assert len(rejecting) == 2
    for verdict in rejecting:
        assert verdict.reason in answer.explanation
    # Only the rejecting sentences. The novelty screen admits this row, and an explanation
    # that also carried "within the corpus's own spread" would be telling a refused caller
    # what went right.
    admitted = [verdict for verdict in answer.screens if verdict.passed]
    assert admitted and all(v.reason not in answer.explanation for v in admitted)


# --------------------------------------------------------------------------------------
# The published page
# --------------------------------------------------------------------------------------


def test_the_committed_page_is_what_the_code_produces(built) -> None:
    """The byte-identity check, and the reason the page can be trusted as a diff.

    It inherits `loco.md`'s and `novelty-reference.json`'s lesson as well: this is the check
    that catches upstream nondeterminism nobody was testing for, because a screen whose sentence
    depends on dictionary order or on a float that moves will fail here and nowhere else.
    """
    assert DOCUMENT.is_file(), (
        f"{DOCUMENT} is missing. Publish it with "
        f"`python -m hydms.delivery.refusals --emit`; it is generated, never written."
    )
    assert DOCUMENT.read_text(encoding="utf-8") == document(built), (
        f"{DOCUMENT.name} is not what the code produces. Regenerate it with "
        f"`python -m hydms.delivery.refusals --emit` and read the diff: a changed sentence "
        f"beside an unchanged input is the defect this page exists to surface."
    )


def test_the_page_renders_every_probe_and_every_code(built) -> None:
    """A rendering bug that dropped rows would leave the byte-identity test perfectly green."""
    page = document(built)
    for probe, _ in built:
        assert f"`{probe.name}`" in page
    for code in reason_codes():
        assert f"`{code}`" in page


def test_emit_writes_the_same_bytes_somewhere_else(tmp_path, built) -> None:
    """`--emit` is the only writer, so it must produce exactly what the test compares against."""
    written = emit(tmp_path / "REFUSALS.md")
    assert written.read_text(encoding="utf-8") == document(built)
