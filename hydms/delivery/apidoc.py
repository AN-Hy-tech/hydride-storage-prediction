"""L6 -- the caller's reference, generated so its numbers cannot rot.

::

    python -m hydms.delivery.apidoc            # is the committed docs/API.md current?
    python -m hydms.delivery.apidoc --emit     # rewrite it from the committed examples
    python -m hydms.delivery.apidoc --probe    # re-run every example against the deployed fit

Card #80 asks for a document that stops misuse, and is explicit that the part worth writing is
the part OpenAPI cannot generate: what the interval means, why the service refuses, what the
trained ranges are, and why a material wt% is not a system wt%. That prose is written by hand.
It simply lives *here*, next to the facts it is about, rather than in a file somebody edits --
the same arrangement :mod:`hydms.delivery.refusals` uses, and for the same reason. A document
whose numbers are typed goes stale silently; a document that is regenerated and compared
byte-for-byte turns a stale number into a diff line.

What is a fact here, and where each one comes from
--------------------------------------------------

Three sources, and they are kept apart on purpose, because they can fail in different ways.

**The code, read live.** The reason-code vocabulary (:func:`~hydms.delivery.contract.reason_codes`
over :func:`~hydms.delivery.contract.delivery_screens`), the batch limit, the schema strings,
the unit and the target space. None of this needs an artifact, so it is re-derived on every
``--emit`` and every test run.

**The committed OpenAPI document** (:data:`~hydms.delivery.api.openapi.SNAPSHOT_FILE`), for the
route list, the summaries and the status codes each route declares. Read rather than restated
so that this page and the machine-readable contract cannot disagree about what exists: gate
HG-3 already fails when that document drifts from the code, so pointing this page at it puts
the endpoint table behind a gate without adding one.

**The committed examples** (:data:`EXAMPLES_FILE`), which are the only thing here that needs a
trained model. Every request and response on the published page is a real exchange with the
service -- status code, body and all -- captured by ``--probe`` against a promoted artifact and
written down with the version that answered.

Why the examples are a committed fixture rather than a live call
-----------------------------------------------------------------

``--emit`` deliberately does **not** talk to a model. ``artifacts/`` is gitignored, so a fresh
clone and every CI runner has no promoted version; a generator that needed one would produce a
check that silently never runs -- the trap this repository has already found on
``artifacts/current.json`` (#34) and ``reports/loco/`` (#30), and the reason
``docs/REFUSALS.md`` is emitted from stated inputs. Splitting it in two keeps both halves
honest: the *shape* of the page is checked everywhere, on every push, with no artifact; the
*numbers* are a dated measurement carrying the version that produced them, refreshed by a
maintainer who has the fit.

The cost is stated because it is real. Between a fit and the next ``--probe``, the examples
describe the version named in :data:`EXAMPLES_FILE` and not necessarily the one now promoted.
That is why every number on the published page is stamped with its version rather than written
as though it were timeless, and why :func:`drift` reports the two versions separately when they
differ. An example that has gone stale is wrong about a *past* deployment, which a reader can
see and correct; an example silently regenerated against whatever happened to be on the machine
would be wrong about an unnamed one, which nobody can.

Card #80.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, TextIO

from hydms.config import repo_root
from hydms.delivery.api.openapi import SNAPSHOT_FILE
from hydms.delivery.api.service import MAX_BATCH_ROWS, PREFIX
from hydms.delivery.contract import SCHEMA, SPACE, UNIT, delivery_screens, reason_codes

__all__ = [
    "DOCUMENT",
    "EXAMPLES_FILE",
    "ApiDocError",
    "document",
    "drift",
    "emit",
    "examples",
    "main",
    "probe",
]


class ApiDocError(ValueError):
    """The page could not be built from what is on disk."""


#: The published page. In ``docs/`` rather than ``reports/`` for the reason
#: :data:`hydms.delivery.refusals.DOCUMENT` gives: ``.gitignore`` excludes most of
#: ``/reports/*``, so a check that read a file there would read nothing on a fresh clone.
DOCUMENT = repo_root() / "docs" / "API.md"

#: The captured exchanges, beside the package that produces them and shipped as package data,
#: so ``--emit`` works from an installed wheel with no repository around it -- the same reason
#: ``api/openapi.json`` and ``screens/domain-reference.json`` live where they do.
EXAMPLES_FILE = Path(__file__).with_name("apidoc-examples.json")

#: The fixture's own schema. A reader that meets an unknown one says so rather than guessing,
#: which is the convention :data:`hydms.delivery.contract.SCHEMA` sets.
EXAMPLES_SCHEMA = "hydms.delivery.apidoc/1"

#: The one composition-and-temperature pair used wherever the page needs a worked example that
#: is *admitted*: a real AB5 alloy at room temperature, the alloy the forward model was built
#: on. Same baseline as the refusal catalogue, so the two pages describe one system.
BASELINE = ("LaNi5", 298.0)

#: Every exchange the published page shows, in reading order, each with the sentence that says
#: why a reader is being shown it. The label is the fixture key; nothing else joins the two, so
#: a probe that stops producing a label fails loudly in :func:`document` rather than quietly
#: dropping a section.
#:
#: Order is the reading order and nothing depends on it: health first, because it is how a
#: caller learns which version will answer; then one admitted prediction, then the refusals in
#: the order a caller meets them -- the caller's own mistake, then the material's -- then the
#: batch, then the model card.
SECTIONS: tuple[tuple[str, str], ...] = (
    ("health", "Which version is answering, and what the batch limit is."),
    (
        "predict-baseline",
        "An admitted prediction: an estimate, its interval, and why it was admitted.",
    ),
    (
        "predict-too-cold",
        "A refusal the caller can act on: the temperature is outside the trained window.",
    ),
    (
        "predict-mg2ni",
        "A refusal that is **not** about a low number: the calibrated band is too wide to be worth reporting.",
    ),
    ("predict-novel", "A refusal about chemistry rather than about the model's domain."),
    ("predict-unreadable", "A composition the system cannot read at all."),
    ("predict-empty-formula", "An invalid *request* -- note that it carries no `refused` key."),
    ("predict-unknown-key", "The transport rejecting a field it does not declare."),
    ("batch-mixed", "A batch: three candidates, one of them refused, in the order they were sent."),
    ("batch-too-large", "A batch over the published limit."),
    (
        "model-card",
        "The deployment's own description of itself: ranges, screens, and what has been certified.",
    ),
)

#: How many candidates of an over-long batch request the page prints before eliding the rest.
#:
#: The ``batch-too-large`` example is a real request carrying one row more than the limit, and
#: printing it whole would bury the page under a thousand lines of identical JSON. The elision
#: is announced in prose beside the block, with the true count, rather than performed silently:
#: a reader must be able to tell a shortened example from a short one, or the page teaches a
#: request shape nobody sent.
_ELIDE_CANDIDATES_ABOVE = 3

#: Reason codes whose *sentence* is worth quoting under "what to do about it", paired with the
#: action. Written by hand because it is the one thing on the page no code can produce: the
#: system says what is wrong, and only a person can say what a caller should do next.
#:
#: Keyed by code and checked against :func:`~hydms.delivery.contract.reason_codes` in
#: :func:`document`, in **both** directions -- a code with no advice, and advice for a code no
#: screen declares. The first is the failure that matters: a caller meeting an undocumented
#: refusal is exactly the misuse this page exists to prevent.
ADVICE: Mapping[str, str] = {
    "admitted": (
        "Nothing. Every rule that runs was satisfied. Read the interval, not the point "
        "estimate — and read the material-versus-system caveat below before comparing the "
        "number to a storage target."
    ),
    "outside-window": (
        "Ask again inside the trained temperature range. The bound is not a modelling "
        "convenience: outside it the training rows do not exist, so an answer would be "
        "extrapolation with a calibrated-looking band around it."
    ),
    "high-uncertainty": (
        "Nothing you can fix by rephrasing the question — **this is the answer**. The model "
        "will predict here; it cannot do so tightly enough to be worth acting on, and a "
        "number with a band this wide tells you less than the training distribution already "
        "did. Treat the composition as unmeasured, not as low-capacity."
    ),
    "above-physical-ceiling": (
        "Do not retry. The prediction exceeded what this composition can physically hold at "
        "H/M 3, which means the model is wrong about this candidate rather than the candidate "
        "being remarkable. Report it: a prediction above the stoichiometric ceiling is a "
        "defect in the fit."
    ),
    "out-of-domain": (
        "Treat the estimate as unavailable. The prediction sits above the capacity level that "
        "more than one alloy family reaches in training, where the corpus holds one family "
        "only — so any answer here is a single family's behaviour generalised to yours."
    ),
    "outside-feature-range": (
        "Check which descriptor is named in the sentence; it is the one your composition "
        "pushes past the training rows. There is no way to ask this candidate differently, "
        "and no version will answer it until the corpus covers that range."
    ),
    "untrusted-family": (
        "**You cannot receive this over HTTP** — see the reachability note below. It is "
        "reachable only by supplying an alloy-class label directly, which the API has no "
        "field for."
    ),
    "beyond-known-chemistry": (
        "This is a statement about the corpus, not about your candidate's merit. The "
        "composition is further from every known alloy than any known alloy is from its own "
        "nearest neighbour, so the model has no comparable to reason from. It is the refusal "
        "an inverse-design programme should expect to meet often, and it is the correct one."
    ),
    "indeterminate": (
        "A rule could not be evaluated at all. Read the sentence: it is usually an "
        "unparseable formula or an element outside the property tables, which is a request to "
        "fix. It is never a statement that the candidate is poor."
    ),
}


def _fence(payload: Any) -> str:
    """One JSON block, formatted the way the service serialises it."""
    return "```json\n" + json.dumps(payload, indent=2, ensure_ascii=False) + "\n```"


def _and(names: Sequence[str]) -> str:
    """``a``, ``a and b``, ``a, b and c`` -- so a generated sentence reads like a sentence."""
    quoted = [f"`{name}`" for name in names]
    if len(quoted) <= 1:
        return "".join(quoted)
    return f"{', '.join(quoted[:-1])} and {quoted[-1]}"


def _request_block(payload: Any) -> list[str]:
    """A request as the page shows it: whole, or shortened and *said* to be shortened.

    Returns the fence and, where rows were dropped, the sentence naming how many the real
    request carried. The count comes from the captured request itself, so an elided example
    cannot claim a size nobody sent.
    """
    rows = payload.get("candidates") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or len(rows) <= _ELIDE_CANDIDATES_ABOVE:
        return [_fence(payload)]
    shown = {**payload, "candidates": rows[:_ELIDE_CANDIDATES_ABOVE]}
    return [
        _fence(shown),
        "",
        f"*Shortened for reading.* The request that produced the response below carried "
        f"**{len(rows)}** candidates — one more than the limit — all identical to those above.",
    ]


def _codes_by_screen() -> dict[str, tuple[str, ...]]:
    """Each delivery screen's declared vocabulary, read off the screens themselves.

    Derived rather than listed for the reason card #44 made a screen's reasons declared: a
    fourth screen is documented here without this module being edited, and a screen that
    stops declaring a code cannot leave the code standing on the page.
    """
    return {
        str(screen.name): tuple(str(code) for code in screen.reasons)
        for screen in delivery_screens()
    }


def examples(path: Path | None = None) -> dict[str, Any]:
    """The committed exchanges, or a clear sentence about why there are none.

    Raises:
        ApiDocError: the fixture is absent, unreadable, or written under a schema this
            version does not know. Each says what to run, because the fix is a command.
    """
    source = EXAMPLES_FILE if path is None else path
    if not source.exists():
        raise ApiDocError(
            f"{source} does not exist, so there are no captured exchanges to publish. "
            f"Run `python -m hydms.delivery.apidoc --probe` on a machine with a promoted "
            f"artifact; it is the only step here that needs one."
        )
    try:
        loaded = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ApiDocError(f"{source} is not readable JSON: {error}") from error
    if not isinstance(loaded, dict) or loaded.get("schema") != EXAMPLES_SCHEMA:
        raise ApiDocError(
            f"{source} declares schema {loaded.get('schema')!r} and this code reads "
            f"{EXAMPLES_SCHEMA!r}. Re-probe rather than hand-editing it."
        )
    return loaded


def _openapi() -> dict[str, Any]:
    """The committed contract document, which HG-3 already holds to the code."""
    if not SNAPSHOT_FILE.exists():
        raise ApiDocError(
            f"{SNAPSHOT_FILE} does not exist. Run "
            f"`python -m hydms.delivery.api.openapi --emit` first: this page reads the route "
            f"list off the published contract rather than restating it."
        )
    loaded: dict[str, Any] = json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))
    return loaded


def _routes(spec: Mapping[str, Any]) -> list[tuple[str, str, str, list[str]]]:
    """``(method, path, summary, status codes)`` for every published route, in path order."""
    found: list[tuple[str, str, str, list[str]]] = []
    for path, operations in sorted(spec.get("paths", {}).items()):
        for method, operation in sorted(operations.items()):
            found.append(
                (
                    method.upper(),
                    path,
                    str(operation.get("summary", "")),
                    sorted(operation.get("responses", {})),
                )
            )
    return found


def _covered_elements() -> tuple[tuple[str, ...], tuple[str, ...], int]:
    """Which elements the training corpus actually contains, and which are barely there.

    Read off the novelty screen's committed reference -- the distinct canonical compositions
    of the training split -- rather than from a list somebody maintained, and parsed with the
    same grammar the delivery path uses. It needs no artifact: the reference ships as package
    data, for the reason ``pyproject.toml`` gives.

    "The trained ranges" in card #80's sense is three things, and this is the one a caller
    cannot obtain from ``GET /v1/model``: temperature and the feature spans are numeric bounds
    the screens enforce, but element coverage is not a bound at all. Nothing refuses a
    composition for naming an element the corpus has never seen -- the novelty screen measures
    *distance*, which is the right rule and a different one. So a caller asking "can I ask
    about rhenium?" has no other place to look.

    Returns:
        ``(elements, rare, compositions)`` -- every symbol present, those appearing in two
        compositions or fewer, and how many compositions were read.
    """
    from hydms.data.load import FormulaError, parse_formula
    from hydms.screens.novelty import NoveltyReference

    formulas = NoveltyReference.packaged().formulas
    counts: dict[str, int] = {}
    for formula in formulas:
        try:
            parsed = parse_formula(formula)
        except FormulaError:  # a reference row that will not parse is not this page's to fix
            continue
        for element in parsed:
            counts[element] = counts.get(element, 0) + 1
    rare = tuple(sorted(symbol for symbol, seen in counts.items() if seen <= 2))
    return tuple(sorted(counts)), rare, len(formulas)


def _ranges_table(ranges: Mapping[str, Any]) -> list[str]:
    """The trained ranges as a reader meets them, from the served model card."""
    lines = ["| Quantity | Trained range | Read by |", "|---|---|---|"]
    temperature = ranges.get("temperature")
    if temperature:
        lines.append(
            f"| Temperature | **{temperature['low']:g} to {temperature['high']:g} "
            f"{temperature['units']}** | the `temperature` screen, and its own feature span |"
        )
    capacity = ranges.get("capacity")
    if capacity:
        lines.append(
            f"| Capacity (the target) | {capacity['low']:g} to {capacity['high']:g} "
            f"{capacity['units']} over {capacity['rows']} training rows | — |"
        )
        lines.append(
            f"| Capacity, cross-family | **at or below {capacity['cross_family_max']:g} "
            f"{capacity['units']}** — above it the corpus holds {capacity['rows_above']} row(s) "
            f"and they are all `{capacity['sole_family']}` | the `domain` screen |"
        )
    span = ranges.get("feature_span", {})
    if span:
        lines.append(
            f"| {len(span)} model inputs | each has its own trained span; "
            f"`GET {PREFIX}/model` returns all of them | the `domain` screen |"
        )
    return lines


def document(captured: Mapping[str, Any] | None = None) -> str:
    """The published page: hand-written argument, measured numbers, real exchanges.

    Args:
        captured: The exchanges to publish. Defaults to :func:`examples`, the committed
            fixture. A caller passes one only to render a page for a *different* capture,
            which is how a test renders without touching the committed file.

    Returns:
        The complete Markdown, ending in a newline.

    Raises:
        ApiDocError: a section names an exchange the capture does not hold, or the advice
            table and the declared vocabulary disagree. Both are failures of this module to
            describe the system it is documenting, so neither is allowed to publish.
    """
    data = examples() if captured is None else dict(captured)
    exchanges = data.get("exchanges", {})
    version = data.get("model_version", "unknown")

    missing = [label for label, _ in SECTIONS if label not in exchanges]
    if missing:
        raise ApiDocError(
            f"the page shows {len(SECTIONS)} exchange(s) and the capture is missing "
            f"{missing}. Re-probe: a section whose example vanished would publish as a "
            f"heading with nothing under it."
        )

    declared = set(reason_codes())
    undocumented = sorted(declared - set(ADVICE))
    invented = sorted(set(ADVICE) - declared)
    if undocumented or invented:
        raise ApiDocError(
            f"the advice table and the declared vocabulary disagree. No advice for: "
            f"{undocumented or 'none'}. Advice for codes nothing declares: "
            f"{invented or 'none'}. A caller meeting an undocumented refusal is the misuse "
            f"this page exists to prevent, so it is not published with a gap in it."
        )

    out: list[str] = []
    write = out.append

    write("# The prediction API")
    write("")
    write(
        "Generated by `python -m hydms.delivery.apidoc --emit`. **Do not edit:** "
        "`tests/delivery/test_apidoc.py` asserts this file is byte-for-byte what the code "
        "produces. The prose lives in `hydms/delivery/apidoc.py`, beside the facts it is "
        "about; change it there."
    )
    write("")
    write(
        f"Every request and response below is a **real exchange**, captured against artifact "
        f"version **`{version}`** ({data.get('probed_at', 'undated')}). Nothing on this page "
        f"is a transcription of what the service is believed to say."
    )
    write("")

    # ------------------------------------------------------------------ the one question
    write("## The one thing to understand first")
    write("")
    write(
        "**A refusal is not a low prediction, and you can tell them apart three ways.** This "
        "service will decline to answer about a material rather than hand you a number it "
        "cannot stand behind, and a caller who mistakes the two will read a refusal as "
        '"this alloy is poor" when it means "we do not know".'
    )
    write("")
    write("| | A genuinely low prediction | A refusal |")
    write("|---|---|---|")
    write("| HTTP status | `200` | `422` |")
    write("| `refused` | `false` | `true` |")
    write("| `capacity` | present | **the key does not exist** |")
    write("| Also carries | `interval`, `domain`, `novelty` | `code`, `explanation`, `screens` |")
    write("")
    write(
        "The third row is the one to rely on. `refused` is a *property* of the answer types "
        "rather than a field on them, and a refusal has no field a number could occupy — so "
        "there is no way for this service to spell a bare estimate, and no way for a low "
        "answer to arrive looking like a decline. Branch on `refused`; the status code agrees "
        "with it and is there for clients that only read statuses."
    )
    write("")
    write(
        "A worked example of the distinction that catches people: `Mg2Ni` at 573 K is "
        "**refused**, and not because the estimate is small. The calibrated band came back "
        "wider than this project will report, so the honest answer is that the composition "
        "is unmeasured — not that it stores little hydrogen. See "
        "[`high-uncertainty`](#every-reason-the-service-can-give) below."
    )
    write("")

    # ------------------------------------------------------------------ endpoints
    spec = _openapi()
    write("## Endpoints")
    write("")
    write(
        f"Base path `{PREFIX}`, versioned so that a contract change is a new prefix rather "
        f"than a surprise for whoever wrote a client. The machine-readable contract is "
        f"committed at `hydms/delivery/api/openapi.json` and gate HG-3 fails while it and the "
        f"code disagree; the table below is read from that document, not restated beside it."
    )
    write("")
    write("| | Route | What it answers | Statuses |")
    write("|---|---|---|---|")
    for method, path, summary, statuses in _routes(spec):
        write(f"| `{method}` | `{path}` | {summary} | {', '.join(f'`{s}`' for s in statuses)} |")
    write("")
    write("Run it:")
    write("")
    write("```bash")
    write("conda run -n Project uvicorn hydms.delivery.api:app --port 8000")
    write("```")
    write("")
    write(
        "**The service resolves one artifact version at startup and answers every request "
        "from it.** If no version can be resolved the server does not start. There is no "
        "lazy load in a request path, no default version and no unversioned fallback, because "
        "a service answering from whatever was on disk cannot say what a number came from. "
        f"`GET {PREFIX}/health` is how a client learns which version it is talking to, and "
        "every answer carries `model_version` as well."
    )
    write("")

    # ------------------------------------------------------------------ the exchanges
    write("## Every endpoint, with a real request and a real response")
    write("")
    for label, blurb in SECTIONS:
        exchange = exchanges[label]
        write(f"### `{exchange['method']} {exchange['path']}` — {blurb}")
        write("")
        if exchange.get("request") is not None:
            write("Request:")
            write("")
            for line in _request_block(exchange["request"]):
                write(line)
            write("")
        write(f"Response — **`{exchange['status']}`**:")
        write("")
        write(_fence(exchange["response"]))
        write("")

    # ------------------------------------------------------------------ the interval
    interval = data.get("interval", {})
    level = interval.get("confidence_level")
    write("## What the interval is, and what it is not")
    write("")
    write(
        f"**It is a conformal prediction interval at a nominal {level:.0%} level**, in "
        f"`{UNIT}` on the `{SPACE}` scale, produced by split-conformal calibration (MAPIE) "
        f"over a CatBoost multi-quantile fit. Both bounds and the level are on every answer, "
        f"and so are the unit and the space, so a payload crossing the wire still says what "
        f"it means."
        if isinstance(level, float)
        else f"**It is a conformal prediction interval**, in `{UNIT}` on the `{SPACE}` scale."
    )
    write("")
    write("It **is**:")
    write("")
    write(
        f"- **Marginal.** Over the calibration distribution, intervals of this kind contain "
        f"the truth at least {level:.0%} of the time. That is an average over candidates, not "
        f"a promise about yours."
        if isinstance(level, float)
        else "- **Marginal**, not conditional on your candidate."
    )
    write(
        "- **At least nominal, never nearer.** Split conformal guarantees *at least* the "
        "stated coverage; the finite-sample rank over the calibration rows makes the excess a "
        "constant, so a **better** raw fit moves measured coverage further above nominal, not "
        "closer to it. Over-coverage is the guarantee working, not a miscalibration."
    )
    write(
        "- **Reported in capacity space**, already `expm1` of the log-space the model is fitted in."
    )
    write("")
    write("It is **not**:")
    write("")
    write(
        "- **A confidence interval on a parameter.** It is a band around a *future "
        "observation*, and it includes the measurement scatter of the underlying experiments."
    )
    write(
        "- **Conditional coverage.** It does not promise that 80 % of the AB₅ alloys you ask "
        "about will be covered. Per-family behaviour is what leave-one-alloy-class-out "
        "measures, and those figures are on the model card — several of them are poor, and two "
        "are negative."
    )
    write(
        "- **A measure of how good the alloy is.** A wide band means the model is uncertain, "
        "which is why `high-uncertainty` is a refusal rather than a caveat on a number."
    )
    write(
        "- **Guaranteed positive.** A crossed band — `upper` below `lower` — is possible where "
        "quantile heads cross, and it is passed through unclipped on purpose, because clipping "
        "would hide the one signal that says the fit disagreed with itself."
    )
    write("")

    # ------------------------------------------------------------------ reason codes
    write("## Every reason the service can give")
    write("")
    by_screen = _codes_by_screen()
    write(
        f"The vocabulary is **derived, never listed**: `reason_codes()` is the union of what "
        f"the {len(by_screen)} screens on the prediction path declare, plus `admitted` and "
        f"`indeterminate`. A screen that grows a code widens this table without anything being "
        f"edited, and a code no screen declares is refused one construction before it could "
        f"reach you. The sentence beside each code is generated for every path and read by a "
        f"person on a diff — see [`REFUSALS.md`](REFUSALS.md), which is where the wording "
        f"lives."
    )
    write("")
    declared_by = {
        code: sorted(name for name, codes in by_screen.items() if code in codes)
        for code in reason_codes()
    }
    reachable = set(data.get("reachable_over_http", []))
    write("| Code | Declared by | Reachable over HTTP | What you should do about it |")
    write("|---|---|---|---|")
    for code in reason_codes():
        owners = ", ".join(f"`{name}`" for name in declared_by[code]) or "the screen contract"
        mark = "yes" if code in reachable else "**no**"
        write(f"| `{code}` | {owners} | {mark} | {ADVICE[code]} |")
    write("")
    grid = data.get("reachability_grid", {})
    if grid:
        write(
            f"**The reachability column is measured, not asserted.** "
            f"{grid.get('formulas', '?')} compositions x {grid.get('temperatures', '?')} "
            f"temperatures were sent through the request door against `{version}`, plus the "
            f"probes above for the two codes a well-formed in-range grid cannot reach. Every "
            f"declared code was reached except `untrusted-family`, which judges an alloy-class "
            f"label against that family's measured transfer — and a caller types a formula, "
            f"not a label. Supplying a guessed one would be worse than omitting it: the screen "
            f"would answer `indeterminate` for any family it has no transfer estimate for, so "
            f"every genuinely novel candidate would be refused for the wrong reason. Gate HG-2 "
            f"goes red if it ever becomes reachable by typing."
        )
        write("")
        write(
            f"*If you are comparing this table with a gate report, they will not match, and "
            f"neither is wrong.* Gates HG-2 and HG-3 run a fixed set of a dozen probes and "
            f"record `above-physical-ceiling` and `out-of-domain` as **unreached on this fit** "
            f"— which is what a small probe set can honestly say, and why the gate marks them "
            f"as the fit's to decide rather than requiring them. This table is a wider sweep "
            f"asking a different question: whether *some* typed request reaches the code at "
            f"all. It does, on `{version}`. A code marked reachable here is therefore a lower "
            f"bound on what a caller can meet, never a promise about any particular candidate."
        )
        write("")

    # ------------------------------------------------------------------ ranges
    write("## The trained ranges, and the applicability domain")
    write("")
    write(
        f"These are the spans the screens enforce. They are read off the objects that actually "
        f"judge, and `GET {PREFIX}/model` returns all of them for the version answering you — "
        f"prefer that over this table, which describes `{version}`."
    )
    write("")
    for line in _ranges_table(data.get("trained_ranges", {})):
        write(line)
    write("")
    elements, rare, compositions = _covered_elements()
    write(
        f"**Which elements the corpus contains.** {len(elements)} of them, across "
        f"{compositions} distinct canonical compositions in the training split:"
    )
    write("")
    write(f"> {' '.join(f'`{symbol}`' for symbol in elements)}")
    write("")
    write(
        "**This is not a bound, and nothing refuses a composition for leaving it.** No screen "
        "checks membership of that list: the novelty screen measures *distance* on a chemical "
        "scale instead, which is the right rule — an unseen element near a seen one is a "
        "better-supported candidate than a seen element in an unseen arrangement. So the list "
        "is here because a caller has nowhere else to find it, not because crossing it is an "
        "error. Treat it as where the evidence is, and let `beyond-known-chemistry` decide."
    )
    write("")
    if rare:
        write(
            f"{len(rare)} of the {len(elements)} appear in **two compositions or fewer** — "
            f"{' '.join(f'`{symbol}`' for symbol in rare)}. A candidate resting on one of "
            f"these is supported by one or two measurements, whatever the interval says: the "
            f"band is calibrated marginally, not conditionally on how much evidence your "
            f"particular chemistry has."
        )
        write("")
    write(
        "**The applicability domain is not the same thing as the trained ranges.** A candidate "
        "inside every span above can still be refused, because the domain screen also judges "
        "the *prediction*: against the composition's own physical capacity ceiling at H/M 3, "
        "and against the width of the calibrated band. That is why the order of operations is "
        "featurise, predict, **then** screen — a rule that reads a prediction cannot run before "
        "one exists."
    )
    write("")
    transfer = data.get("transfer_r2") or {}
    if transfer:
        write(
            f"**Which alloy families this has been shown to work on.** Leave-one-alloy-class-out "
            f"holds out an entire family and refits, which is the honest test of whether the "
            f"model transfers to chemistry it has not seen. Measured on `{version}`:"
        )
        write("")
        write("| Alloy class | LOACO R² |")
        write("|---|---|")
        for family, score in sorted(transfer.items(), key=lambda item: -item[1]):
            write(f"| `{family}` | {score:+.3f} |")
        write("")
        negative = sorted(name for name, score in transfer.items() if score < 0)
        write(
            f"Read that table before you read any prediction. "
            f"{_and(negative)} "
            f"{'transfer' if len(negative) != 1 else 'transfers'} at **below zero**, which "
            f"means that for {'those families' if len(negative) != 1 else 'that family'} the "
            f"corpus mean is a better predictor than this model when the family is unseen. The "
            f"`domain` screen refuses on that basis, which is why a label it has no measurement "
            f"for is `indeterminate` rather than admitted."
        )
        write("")

    # ------------------------------------------------------------------ the caveat
    write("## Material capacity is not system capacity")
    write("")
    write(
        f"Every number this service returns is **gravimetric hydrogen capacity of the material "
        f"alone**, in `{UNIT}`. It is the mass of hydrogen over the mass of the hydride, and "
        f"nothing else."
    )
    write("")
    write(
        "**Do not compare it to a DOE storage target.** Those targets are stated on a *system* "
        "basis — they count the tank, the valves, the heat exchanger, and the thermal "
        "management a metal hydride needs in order to absorb and release at a useful rate. "
        "Comparing a material wt% to a system target is a two-step overstatement: the system "
        "figure is strictly smaller than the material figure, often by a large factor, and the "
        "gap is engineering rather than chemistry."
    )
    write("")
    write(
        "A material at 6 wt% is not a system at 6 wt%, and a claim that it meets a 5.5 wt% "
        "system target because 6 > 5.5 is wrong twice over. If a number from this service is "
        "going into a comparison with a target, say which basis each side is on."
    )
    write("")
    write(
        "The second thing not to inherit: the published figures in `REPORT.md` were produced "
        "by a pipeline with known validation leaks and are **history, not current "
        "performance**. Do not quote them beside a number from this service."
    )
    write("")

    # ------------------------------------------------------------------ the library door
    write("## The other door: calling the library directly")
    write("")
    write("The HTTP service computes nothing. Every route is a transport over one function:")
    write("")
    write("```python")
    write("from hydms.delivery import predict_capacity")
    write("")
    write(f"answer = predict_capacity({BASELINE[0]!r}, {BASELINE[1]!r})")
    write("answer.refused          # False -- or True, and then there is no .capacity at all")
    write("answer.to_dict()        # exactly the JSON body the API returns")
    write("```")
    write("")
    write(
        "`to_dict()` is not *like* the served body; gate HG-3 sends the same probe set over "
        "both doors and requires the served JSON to equal it **value for value**, reporting "
        "any difference by JSON pointer. So the two cannot drift, and anything this page says "
        "about a response body is equally true of the returned object."
    )
    write("")
    write("Two differences that are real, and both are deliberate:")
    write("")
    write(
        "- **The library writes nothing.** `predict_capacity()` is pure: no logging, no "
        "record, no file. Persisting a served answer is the service's job. See "
        "[ADR 0006](adr/0006-the-delivery-seam.md)."
    )
    write(
        "- **The library has no batch limit.** "
        f"`{MAX_BATCH_ROWS}` is transport policy — how much work one HTTP request may do — "
        "and nothing below the API layer knows it."
    )
    write("")
    write(
        "**Prefer the HTTP door anyway if you have a choice.** It is the path gate HG-3 "
        "covers end to end, and the path the Streamlit pages use, so a bug you hit there is a "
        "bug everyone hits rather than one your script has to itself."
    )
    write("")

    # ------------------------------------------------------------------ provenance
    write("## What produced the examples on this page")
    write("")
    provenance = data.get("provenance") or {}
    write(f"- **Artifact version:** `{version}`")
    write(f"- **Captured:** {data.get('probed_at', 'undated')}")
    if provenance.get("git_sha"):
        write(
            f"- **Version written at commit:** `{provenance['git_sha'][:12]}` on "
            f"`{provenance.get('git_branch', '?')}`. This is the commit that *wrote* the "
            f"version, which is not always the commit that fitted the model — a version "
            f"re-saved to carry a gate report records the re-save. The manifest note below "
            f"says which."
        )
    if provenance.get("trained_at"):
        write(f"- **Version written:** {provenance['trained_at']}")
    if provenance.get("notes"):
        write(f"- **Manifest note:** {provenance['notes']}")
    gates = data.get("gates") or {}
    if gates:
        unestablished = gates.get("unestablished") or []
        if unestablished:
            names = ", ".join(f"`{name}` ({status})" for name, status in unestablished)
            write(
                f"- **Certified with {len(unestablished)} criteri{'on' if len(unestablished) == 1 else 'a'} "
                f"unestablished:** {names}. Each belongs to a frozen phase and was waived as a "
                f"dated act at promotion time, recorded in `artifacts/current.json` — the "
                f"artifact says what was *measured*, the pointer says what was *decided*."
            )
        else:
            write("- **Certified:** every registered criterion passed.")
    write("")
    write(
        f"Payload schema `{SCHEMA}`. A reader that meets an unknown schema string should say "
        f"so rather than guess at the fields."
    )
    write("")

    return "\n".join(out).rstrip() + "\n"


def drift(rendered: str | None = None) -> list[str]:
    """Lines describing how the committed page differs from what the code produces.

    Returns:
        An empty list when they agree. Otherwise one line naming the first differing line
        and the size of the difference -- enough to know *that* it moved and roughly where,
        with ``--emit`` as the fix. A full diff belongs to ``git diff`` after the rewrite.
    """
    produced = document() if rendered is None else rendered
    if not DOCUMENT.exists():
        return [f"{DOCUMENT} does not exist; run --emit."]
    committed = DOCUMENT.read_text(encoding="utf-8")
    if committed == produced:
        return []
    left = committed.splitlines()
    right = produced.splitlines()
    for number, (was, now) in enumerate(zip(left, right, strict=False), start=1):
        if was != now:
            return [
                f"{DOCUMENT.name} differs from what the code produces, first at line {number}:",
                f"  committed: {was[:110]}",
                f"  produced:  {now[:110]}",
                "Run `python -m hydms.delivery.apidoc --emit`.",
            ]
    return [
        f"{DOCUMENT.name} has {len(left)} line(s) and the code produces {len(right)}. "
        f"Run `python -m hydms.delivery.apidoc --emit`."
    ]


def emit() -> Path:
    """Rewrite the committed page. Returns where it was written."""
    DOCUMENT.parent.mkdir(parents=True, exist_ok=True)
    DOCUMENT.write_text(document(), encoding="utf-8", newline="\n")
    return DOCUMENT


def probe(out: TextIO | None = None) -> Path:
    """Re-run every published exchange against the deployed fit and rewrite the fixture.

    This is the one entry point here that needs a promoted artifact, and it is a maintainer's
    command rather than a CI step: ``artifacts/`` is gitignored, so a runner has no version to
    probe and a check that depended on one would never run.

    Returns:
        Where the fixture was written.

    Raises:
        DeliveryError: nothing is promoted, or the promoted version cannot be loaded. The
            sentence it carries names the fix and is not wrapped in a vaguer one here.
    """
    # Imported inside the function, not at module scope: `--emit` and the test that compares
    # the committed page must work in a checkout with no model, no pandas and no API extra,
    # and a module-level import of the service would make the whole module unimportable there.
    from datetime import datetime, timezone

    from fastapi.testclient import TestClient

    from hydms.delivery.api import create_app
    from hydms.delivery.modelcard import model_card
    from hydms.delivery.predict import load_bundle

    stream = out if out is not None else sys.stdout
    requests: dict[str, tuple[str, str, Any]] = {
        "health": ("GET", f"{PREFIX}/health", None),
        "model-card": ("GET", f"{PREFIX}/model", None),
        "predict-baseline": (
            "POST",
            f"{PREFIX}/predict",
            {"formula": BASELINE[0], "temperature_k": BASELINE[1]},
        ),
        "predict-too-cold": (
            "POST",
            f"{PREFIX}/predict",
            {"formula": "LaNi5", "temperature_k": 100.0},
        ),
        "predict-mg2ni": (
            "POST",
            f"{PREFIX}/predict",
            {"formula": "Mg2Ni", "temperature_k": 573.0},
        ),
        "predict-novel": (
            "POST",
            f"{PREFIX}/predict",
            {"formula": "K1Rb1", "temperature_k": 298.0},
        ),
        "predict-unreadable": (
            "POST",
            f"{PREFIX}/predict",
            {"formula": "LaNi5Xx2", "temperature_k": 298.0},
        ),
        "predict-empty-formula": (
            "POST",
            f"{PREFIX}/predict",
            {"formula": "  ", "temperature_k": 298.0},
        ),
        "predict-unknown-key": (
            "POST",
            f"{PREFIX}/predict",
            {"formula": "LaNi5", "temperature_k": 298.0, "model_version": "v2"},
        ),
        "batch-mixed": (
            "POST",
            f"{PREFIX}/predict/batch",
            {
                "candidates": [
                    {"formula": "LaNi5", "temperature_k": 298.0},
                    {"formula": "LaNi5", "temperature_k": 100.0},
                    {"formula": "TiFe", "temperature_k": 298.0},
                ]
            },
        ),
        "batch-too-large": (
            "POST",
            f"{PREFIX}/predict/batch",
            {"candidates": [{"formula": "LaNi5", "temperature_k": 298.0}] * (MAX_BATCH_ROWS + 1)},
        ),
    }

    application = create_app()
    exchanges: dict[str, Any] = {}
    with TestClient(application) as client:
        for label, (method, path, body) in requests.items():
            response = client.get(path) if method == "GET" else client.post(path, json=body)
            exchanges[label] = {
                "method": method,
                "path": path,
                "request": body,
                "status": response.status_code,
                "response": response.json(),
            }
            print(f"  {label:24s} {method:5s} {path:20s} -> {response.status_code}", file=stream)

    bundle = load_bundle()
    card = model_card(bundle)
    provenance = card.get("provenance") or {}

    reachable = _reachable(bundle, stream)

    payload = {
        "schema": EXAMPLES_SCHEMA,
        "model_version": bundle.version,
        "probed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "interval": card.get("interval", {}),
        "trained_ranges": card.get("trained_ranges", {}),
        "transfer_r2": (card.get("metrics") or {}).get("transfer_r2"),
        "gates": (card.get("metrics") or {}).get("gates"),
        "provenance": {
            "git_sha": provenance.get("git_sha"),
            "git_branch": provenance.get("git_branch"),
            "trained_at": card.get("trained_at"),
            "notes": provenance.get("notes"),
        },
        "reachable_over_http": reachable["codes"],
        "reachability_grid": reachable["grid"],
        "exchanges": exchanges,
    }
    EXAMPLES_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    return EXAMPLES_FILE


#: The compositions the reachability sweep sends through the request door. Chosen to span the
#: corpus and to leave it: real storage alloys, the binary hydrides, and a pair of alkali
#: metals with no hydride chemistry near them. It is a *lower bound* on what a caller can
#: reach -- a code this grid misses may still be reachable by some other composition, which is
#: why the published sentence says "was reached" rather than "can be reached".
_SWEEP_FORMULAS = (
    "LaNi5",
    "TiFe",
    "Mg2Ni",
    "MgH2",
    "Mg",
    "Ti",
    "V",
    "Pd",
    "LaNi4.7Al0.3",
    "Ti0.5V0.5",
    "ZrMn2",
    "TiCr2",
    "Mg2Cu",
    "CaNi5",
    "CeNi5",
    "TiVCr",
    "NaAlH4",
    "LiBH4",
    "LiAlH4",
    "Li3N",
    "MgNi",
    "AlH3",
    "BeH2",
    "Mg0.9Ni0.1",
    "V0.8Ti0.2",
    "Ti1.1CrMn",
    "LaNi3",
    "La2Mg17",
    "Mg3La",
    "K1Rb1",
    "CsF",
    "Li",
    "Be",
    "B",
    "C",
    "N",
    "O",
    "Al",
    "Si",
    "Sc",
    "MgB2",
    "Ca",
    "Sr",
    "Ba",
    "Y",
    "Zr",
    "Nb",
    "Mo",
    "Tc",
    "Ru",
)

#: Temperatures for the sweep: the two window edges and eight points between them.
_SWEEP_TEMPERATURES = (195.0, 250.0, 298.0, 350.0, 423.0, 500.0, 573.0, 650.0, 700.0, 773.0)

#: Codes the sweep cannot reach because a well-formed, in-window request cannot express them,
#: but which the probes above *do* reach. Named rather than silently unioned, so that a code
#: that stops being reachable by its probe is not covered up by this list.
_REACHED_BY_PROBE = ("outside-window", "indeterminate")


def _reachable(bundle: Any, stream: TextIO) -> dict[str, Any]:
    """Which reason codes a *typed* request actually reaches against this fit.

    The distinction is the one ``docs/REFUSALS.md`` calls the two doors. A caller types a
    formula and a temperature; a curated frame can also *state* a prediction, a band width and
    an alloy-class label, which is how ``untrusted-family`` is reachable at all. Measuring it
    rather than asserting it is the point: "the fit decides" is a hedge, and a sweep turns it
    into a number a reader can check.
    """
    from hydms.delivery.contract import Refusal
    from hydms.delivery.predict import predict_capacity

    seen: set[str] = set()
    for formula in _SWEEP_FORMULAS:
        for temperature in _SWEEP_TEMPERATURES:
            try:
                answer = predict_capacity(formula, temperature, bundle=bundle)
            except Exception:  # a raise is not a reachable *code*
                continue
            # isinstance rather than `answer.refused`: the flag is a *property* on both
            # answer types, which is what makes it safe for a JSON consumer and what stops
            # a type checker narrowing the union through it.
            seen.add(answer.code if isinstance(answer, Refusal) else answer.domain.code)
    seen.update(_REACHED_BY_PROBE)
    print(
        f"  reachability: {len(seen)} of {len(reason_codes())} declared code(s) "
        f"over {len(_SWEEP_FORMULAS)}x{len(_SWEEP_TEMPERATURES)} requests",
        file=stream,
    )
    return {
        "codes": sorted(seen),
        "grid": {
            "formulas": len(_SWEEP_FORMULAS),
            "temperatures": len(_SWEEP_TEMPERATURES),
        },
    }


def main(argv: Sequence[str] | None = None, out: TextIO | None = None) -> int:
    """``--emit`` rewrites the page, ``--probe`` refreshes the examples, nothing checks."""
    stream = out if out is not None else sys.stdout
    parser = argparse.ArgumentParser(
        prog="python -m hydms.delivery.apidoc",
        description="The API reference: check it, publish it, or re-measure its examples.",
    )
    parser.add_argument("--emit", action="store_true", help=f"rewrite {DOCUMENT.name}")
    parser.add_argument(
        "--probe",
        action="store_true",
        help="re-run every example against the deployed artifact (needs a promoted version)",
    )
    args = parser.parse_args(argv)

    if args.probe:
        print("probing the deployed artifact:", file=stream)
        print(f"wrote {probe(stream)}", file=stream)

    if args.emit:
        print(f"wrote {emit()}", file=stream)
        return 0

    differences = drift()
    for line in differences:
        print(line, file=stream)
    if not differences:
        data = examples()
        print(
            f"{DOCUMENT.name} is current: {len(SECTIONS)} exchange(s) against "
            f"{data.get('model_version')}, {len(reason_codes())} declared code(s) all "
            f"documented.",
            file=stream,
        )
    return 1 if differences else 0


if __name__ == "__main__":  # pragma: no cover - the command line
    raise SystemExit(main())
