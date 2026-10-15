"""L6 -- what the deployment can honestly say about itself, as data.

``GET /v1/model`` (card #78) answers "what is answering me, and what is it worth?", and card
#83 renders the same payload as a page. Both need the *facts*, so the facts are assembled
here, in the delivery layer, and the route handler only serialises what this returns. An API
that assembled its own model card would be a second description of the deployment, free to
disagree with the first.

**Everything here is read off the objects that actually answer.** The version, the screens,
the band's nominal level and the reference digests come from the live
:class:`~hydms.delivery.predict.ArtifactBundle`; the training date and the gate record come
from that version's manifest. Nothing is read from a document, because a document is a copy
and a copy drifts -- the defect ``docs/REFUSALS.md`` is generated to avoid, one layer up.

**An absent record is reported as absent.** ``trained_at`` is ``None`` when no manifest was
read, ``gates`` is ``None`` for the same case and ``{"recorded": False, ...}`` when a manifest
was read and holds no gate run. The three are different states and a reader that collapses
them is the reader that calls an uncertified fit certified. The deployed ``v2`` is in the
third state today: it was saved before any gate could score it, which is why
:func:`~hydms.surrogate.predict.load_surrogate` refuses it and card #34 is still open.

**What "honest metrics" can mean for a running service.** It cannot mean R2: no metric is
stored beside an artifact, and inventing one here would be the exact over-claim this phase
exists to remove. What the deployment *does* hold is (a) the recorded gate run, which is the
only statement anybody has certified about this version, and (b) the per-family
leave-one-alloy-class-out transfer figures that the applicability screen already judges
against (card #30, via ``hydms/screens/domain-reference.json``). Both are reported, each
labelled with where it came from, and neither is computed here.

**It states everything, and that is a deployment assumption worth naming.** The payload carries
the git sha, the interpreter, the platform and every recorded package version, because a number
without the run that produced it is not evidence and this project says so everywhere else. That
is right for a research service on a trusted network, which is what this is. A deployment on a
public address would have to decide what to redact, and the decision belongs there rather than
here -- a model card that quietly dropped its provenance would be the worse default, since the
absence would read as "not recorded".

Card #78.
"""

from __future__ import annotations

from typing import Any

from hydms.delivery.contract import SPACE, UNIT

__all__ = ["SCHEMA", "model_card"]

#: The payload's own schema. Bumped when a field changes meaning, never when one is added:
#: a consumer that reads by key is unaffected by a new key and broken by a moved one.
SCHEMA = "hydms.delivery.model/1"

#: Numeric or short textual thresholds a screen may expose, read by the names the screens
#: themselves use. Duck-typed rather than dispatched on class, for the reason
#: :func:`~hydms.delivery.predict._digest` gives one module over: a fourth screen with a
#: ``ceiling`` is then reported without editing this layer, and a screen with none of these
#: reports an empty mapping rather than raising. The cost is stated because it is real -- a
#: new screen whose threshold has a *new* name is silently absent from ``limits``; its codes
#: are still listed under ``codes``, so the screen itself can never be invisible.
_LIMIT_ATTRS = (
    "quantity",
    "column",
    "low",
    "high",
    "units",
    "ceiling",
    "hm_floor",
    "max_interval_width",
    "min_transfer_r2",
)

#: Facts a screen's committed reference may carry about the *target*'s span in the training
#: rows, under the names the reference uses for them, and what they are called in the payload.
#:
#: Renamed rather than passed through, which is the one place this module stops duck-typing.
#: ``"trained_min": 0.1`` in a served payload is a number whose meaning has to be looked up, and
#: the delivery layer is exactly the layer that knows what it is the minimum *of*: the target is
#: a capacity in weight percent, which :data:`~hydms.delivery.contract.UNIT` and
#: :data:`~hydms.delivery.contract.SPACE` already say on every answer.
_CAPACITY_FACTS = (
    ("trained_min", "low"),
    ("trained_max", "high"),
    ("cross_family_max", "cross_family_max"),
    ("sole_family", "sole_family"),
    ("rows_above", "rows_above"),
    ("rows", "rows"),
)


#: What the temperature support counts, in the words a chart caption prints.
_SUPPORT_SOURCE = "training rows per temperature bin"


def _limits(screen: Any) -> dict[str, Any]:
    """Every threshold this screen names, under the screen's own name for it."""
    found: dict[str, Any] = {}
    for attribute in _LIMIT_ATTRS:
        value = getattr(screen, attribute, None)
        if isinstance(value, bool) or not isinstance(value, int | float | str):
            continue
        found[attribute] = value
    return found


def _screen_card(screen: Any, digests: dict[str, str]) -> dict[str, Any]:
    """One screen as a reader meets it: what it is called, what it can say, what it reads."""
    name = str(screen.name)
    return {
        "name": name,
        "codes": [str(code) for code in screen.reasons],
        "limits": _limits(screen),
        # The digest of the reference **as loaded**, so a bundle built over an overridden
        # reference reports the numbers that actually judged. `None` means this screen judges
        # against configuration rather than a committed file -- the temperature window -- and
        # not that its reference went unrecorded.
        "reference_sha256": digests.get(name),
    }


def _trained_ranges(screens: tuple[Any, ...]) -> dict[str, Any]:
    """The span of the data behind the fit, read off the screens that enforce it.

    Two sources, because they are two different claims. The temperature bounds are the
    *configured* window (``domain.temperature_min_k`` / ``_max_k``, measured over all 1,279
    rows), and the capacity and feature spans are the applicability screen's committed
    reference, measured over the training rows alone. A caller asking "is my candidate in
    range" is asking about both.
    """
    ranges: dict[str, Any] = {}
    for screen in screens:
        low = getattr(screen, "low", None)
        high = getattr(screen, "high", None)
        if isinstance(low, int | float) and isinstance(high, int | float):
            # Keyed by the screen's name, not by its ``quantity``: that attribute holds the
            # phrase the screen writes into a sentence -- "the trained temperature range" --
            # and a key is addressed by a client, so it must be short and must not change
            # when somebody improves the wording of a refusal.
            ranges[str(screen.name)] = {
                "low": float(low),
                "high": float(high),
                "units": str(getattr(screen, "units", "")),
                "quantity": str(getattr(screen, "quantity", "")),
            }

        reference = getattr(screen, "reference", None)
        if reference is None:
            continue
        formulas = getattr(reference, "formulas", None)
        if formulas:
            ranges["corpus"] = _corpus(tuple(str(formula) for formula in formulas))
        capacity: dict[str, Any] = {}
        for attribute, reported in _CAPACITY_FACTS:
            value = getattr(reference, attribute, None)
            if isinstance(value, int | float | str) and not isinstance(value, bool):
                capacity[reported] = value
        if capacity:
            ranges["capacity"] = {**capacity, "units": UNIT}
        span = getattr(reference, "feature_span", None)
        if span is not None:
            ranges["feature_span"] = {
                str(name): [float(bounds[0]), float(bounds[1])] for name, bounds in span.items()
            }
        counts = tuple(getattr(reference, "temperature_counts", ()) or ())
        if counts:
            # Per-bin, not the `low`/`high` of the temperature entry above: a sweep across the
            # window is only as good as the rows behind each part of it, and 250-350 K holds
            # most of them while 650-800 K holds six (card #82). Omitted rather than emptied
            # when the reference measured none -- an empty histogram reads as "no rows".
            ranges["temperature_support"] = {
                "edges": [float(edge) for edge in reference.temperature_edges],
                "counts": [int(count) for count in counts],
                "rows": int(sum(counts)),
                "units": "K",
                "source": _SUPPORT_SOURCE,
            }
    return ranges


def _corpus(formulas: tuple[str, ...]) -> dict[str, Any]:
    """How many distinct canonical compositions the training split holds, and which elements.

    Read off the novelty screen's reference, which is one formula per canonical composition of
    the training split (card #49). Element coverage is **not a bound**: nothing refuses a
    composition for naming an element the corpus lacks, because the novelty screen measures
    distance, which is the right rule and a different one. It is here because a reader deciding
    whether to trust an answer about rhenium has nowhere else to look (card #83). A formula the
    grammar will not read is counted and not parsed, and ``unparsed`` says how many.
    """
    from hydms.data.load import FormulaError, parse_formula

    seen: dict[str, int] = {}
    unparsed = 0
    for formula in formulas:
        try:
            parsed = parse_formula(formula)
        except FormulaError:
            unparsed += 1
            continue
        for element in parsed:
            seen[element] = seen.get(element, 0) + 1
    return {
        "compositions": len(formulas),
        "elements": sorted(seen),
        "rare_elements": sorted(symbol for symbol, count in seen.items() if count <= 2),
        "unparsed": unparsed,
        "source": "the novelty screen's reference: one formula per canonical composition",
    }


def _transfer(screens: tuple[Any, ...]) -> dict[str, float] | None:
    """Per-family leave-one-alloy-class-out R2, if a screen judges against it."""
    for screen in screens:
        table = getattr(getattr(screen, "reference", None), "transfer", None)
        if table:
            return {str(family): float(score) for family, score in table.items()}
    return None


def _gates(manifest: Any) -> dict[str, Any] | None:
    """What has been certified about this version -- or ``None`` for "no record was read".

    The two absences are different and are kept different. ``None`` means this deployment
    never saw a manifest, so nothing is known either way. ``{"recorded": False}`` means the
    manifest was read and no gate has ever scored this version, which is a statement, and the
    one that is true of ``v2`` today.
    """
    if manifest is None:
        return None
    return {
        "recorded": bool(manifest.gate_run_recorded),
        "unestablished": [[name, status] for name, status in manifest.unestablished()],
    }


def model_card(bundle: Any) -> dict[str, Any]:
    """The deployment's own description of itself, as JSON-ready primitives.

    Args:
        bundle: The :class:`~hydms.delivery.predict.ArtifactBundle` that is answering. Not a
            version string: the point of the card is that it describes the object serving
            predictions right now, including screens a deployment narrowed and a reference it
            overrode.

    Returns:
        A mapping under :data:`SCHEMA`. ``trained_at``, ``provenance`` and ``gates`` are
        ``None`` when the bundle carries no manifest -- which is every bundle assembled by
        :func:`~hydms.delivery.predict.bundle_from` rather than loaded from a store, the door
        the gates use. The service always has one.

    It raises nothing and reaches for nothing on disk. A model card that could fail is a
    ``GET /v1/model`` that can 500 while ``/v1/predict`` is answering perfectly well, which
    tells an operator the opposite of the truth.
    """
    manifest = bundle.manifest
    screens = bundle._screens
    digests = bundle.reference_digests

    return {
        "schema": SCHEMA,
        "version": bundle.version,
        "trained_at": None if manifest is None else manifest.created_at,
        "provenance": None
        if manifest is None
        else {
            "git_sha": manifest.git.sha,
            "git_branch": manifest.git.branch,
            # True means the fit ran from a tree with uncommitted changes, so the sha above
            # does not fully describe what produced this model.
            "code_modified": manifest.git.code_modified,
            "python": manifest.python,
            "platform": manifest.platform,
            "seeds": dict(manifest.seeds),
            "packages": dict(manifest.packages),
            "notes": manifest.notes,
        },
        "features": list(bundle.feature_names),
        "interval": {
            "confidence_level": bundle.confidence_level,
            # Nominal, and said so in the payload rather than in a comment a client never
            # reads: what the band is worth on held-out data is gate AC-3's to establish
            # (card #31), and until it has, this number is a target rather than a measurement.
            "basis": "nominal",
            "unit": UNIT,
            "space": SPACE,
        },
        "screens": [_screen_card(screen, digests) for screen in screens],
        "trained_ranges": _trained_ranges(screens),
        "metrics": {
            "gates": _gates(manifest),
            "transfer_r2": _transfer(screens),
            "transfer_protocol": "leave-one-alloy-class-out (card #30), from the "
            "applicability screen's committed reference",
        },
    }
