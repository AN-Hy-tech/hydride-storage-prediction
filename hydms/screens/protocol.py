"""L4 -- what it means to admit or reject a candidate, and how that answer is carried.

Memo 4.2's requirement on this architecture is that its failure modes be *visible and
debuggable*: you should be able to print a candidate, its features, its prediction, its
uncertainty and its filter verdicts, and see why it is or is not on the shortlist. A screen
that quietly drops a row destroys exactly that -- the candidate is gone and nothing in the
output says which rule removed it or why.

So the contract here is one sentence: **a screen returns a verdict, never a subset.**
Filtering happens afterwards, once, explicitly, by a caller who asked for it
(:meth:`Verdicts.select`).

Three things follow from that, and each is enforced rather than requested:

``no screen drops, adds or reorders a row``
    :func:`apply_screens` compares the returned index to the one it handed over, label by
    label and in order, and refuses anything else. A verdict frame is not allowed to be
    *shorter* than its input even when every row failed.

``no screen mutates the candidates``
    The candidate frame is fingerprinted before and after each screen, so a screen that
    writes a column into its input -- the easy way to leak one screen's judgement into the
    next one's -- is named at the point it happens rather than found later as a result that
    depends on screen order.

``every verdict carries a declared code and a human-readable reason``
    ``passed`` says what happened, ``code`` says which rule it was, ``reason`` says it in a
    sentence. ``code`` must come from the vocabulary the screen *declares*, which is what
    lets the delivery layer enumerate every refusal it can ever emit (#75, #77, and
    ``docs/QA-PROTOCOL.md`` L6: "every refusal reason code is reachable and asserted")
    instead of discovering them from strings invented at the rejection site.

``passed`` is redundant beside ``code`` -- it is exactly ``code == ADMITTED`` -- and it is
carried anyway, for the same reason :class:`hydms.gates.GateResult` carries ``passed``
beside ``status``: a consumer reading one boolean should not have to know the vocabulary.
The runner checks the two agree, so the redundancy cannot drift.

**A screen that cannot judge does not admit.** :data:`INDETERMINATE` is the declared code
for "this rule could not be evaluated on this candidate" -- a missing value, an absent
feature, a distance that could not be computed -- and it is a *rejection*. Fail-closed is
the whole point of the guard-rail stage: the alternative is a candidate reaching the
shortlist because the screen meant to stop it broke.

**Screen a batch, never a candidate at a time.** :meth:`Screen.verdict` takes a frame and
:func:`apply_screens` calls it exactly once per run, whatever the batch size, because the
cost of the other shape is measured. ``featurize`` has a **5 ms per-call floor** that does
not depend on batch size (``require_self_consistent`` re-auditing both element tables'
composite columns, #18's guard, which is what stops a descriptor being silently zero for
caesium and gadolinium). That floor is 2% of a ten-thousand-candidate batch and **57% of a
batch of one**, so a screen written as ``for candidate in candidates: featurize([candidate])``
costs roughly **200x** the batched work before it has screened anything. The table is in
``docs/BENCHMARKS.md``; if a genuinely per-candidate path is ever needed, that audit is a
pure function of (table, properties) and can be memoised the way #22 memoised
``PropertyTable.servable``. Nobody should do that speculatively.

Usage::

    from hydms.screens import apply_screens, temperature_window

    verdicts = apply_screens(candidates, [temperature_window(), novelty_screen])
    verdicts.table            # admitted + one block of columns per screen
    verdicts.rejections()     # long form: one row per rejection, with its reason
    verdicts.counts()         # seen / admitted / rejected / seconds, per screen
    shortlist = verdicts.select(candidates)   # the filtering, explicit and afterwards

Card #44.
"""

from __future__ import annotations

import time
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

import numpy as np
import pandas as pd

__all__ = [
    "ADMITTED",
    "ADMITTED_COLUMN",
    "INDETERMINATE",
    "SEPARATOR",
    "VERDICT_COLUMNS",
    "Screen",
    "ScreenError",
    "Verdicts",
    "apply_screens",
    "verdict_table",
]

_MAX_NAMED = 8

#: The three columns every verdict frame carries, in this order. A screen may return more
#: (see :func:`apply_screens`) but never fewer.
VERDICT_COLUMNS: tuple[str, ...] = ("passed", "code", "reason")

#: The one code that means admitted. Every other code in a verdict is a rejection, which is
#: why a screen may not declare this one among its :attr:`Screen.reasons`.
ADMITTED = "admitted"

#: The declared code for "this screen could not judge this candidate". It is a **rejection**:
#: a guard rail that cannot evaluate a candidate must not pass it. A screen that can emit it
#: declares it like any other code.
INDETERMINATE = "indeterminate"

#: The composite table's overall column: ``True`` only where every screen admitted.
ADMITTED_COLUMN = "admitted"

#: Joins a screen's name to one of its verdict columns in the composite table:
#: ``domain.passed``, ``novelty.reason``, ``novelty.distance``.
SEPARATOR = "."


class ScreenError(ValueError):
    """A screen broke the contract, or the runner was given something it cannot screen.

    A ``ValueError``, like the other layer guards in this package. It always names the screen
    and the rows or codes at fault: the failure this module exists to prevent is an
    unexplained absence, so its own errors must never be one.
    """


@runtime_checkable
class Screen(Protocol):
    """One admissibility rule, applied to a batch of candidates.

    Implementations are typically frozen dataclasses -- a screen is a threshold plus the
    sentence that explains it, and neither should change under a caller's feet.
    """

    @property
    def name(self) -> str:
        """How this screen is addressed and how its columns are prefixed: ``'domain'``.

        Must be unique within one :func:`apply_screens` call and must not contain
        :data:`SEPARATOR`, because it becomes a column prefix in the composite table.
        """

    @property
    def reasons(self) -> tuple[str, ...]:
        """Every rejection code this screen can emit -- the declared vocabulary.

        Declared rather than discovered so that the refusal path above can enumerate what it
        might have to explain. :data:`ADMITTED` is not a member: it is not a reason to reject.
        """

    def verdict(self, candidates: pd.DataFrame) -> pd.DataFrame:
        """Judge every candidate, returning :data:`VERDICT_COLUMNS` on the same index.

        Same rows, same order, no exceptions -- a rejected candidate is a row with
        ``passed=False``, not an absent row. Extra columns are welcome and are carried into
        the composite table as evidence: #49's ElMD distance and its nearest known formula,
        #48's distance to the ceiling. Called once per batch; see the module docstring for
        what the per-candidate shape costs.
        """


def _named(items: Iterable[object]) -> str:
    listed = sorted(map(repr, items))
    if len(listed) <= _MAX_NAMED:
        return ", ".join(listed)
    return f"{', '.join(listed[:_MAX_NAMED])}, ... ({len(listed) - _MAX_NAMED} more)"


def _column(value: Any, index: pd.Index, dtype: Any, what: str) -> pd.Series:
    if isinstance(value, pd.Series):
        if not value.index.equals(index):
            raise ScreenError(
                f"the {what} Series is not on the candidates' index: {len(value)} label(s) "
                f"against {len(index)}. It would be aligned silently, which is how a verdict "
                f"ends up describing a different row than the one it judged."
            )
        return value.copy()
    if isinstance(value, str) or not isinstance(value, Iterable):
        return pd.Series([value] * len(index), index=index, dtype=dtype)
    values = list(value)
    if len(values) != len(index):
        raise ScreenError(
            f"the {what} sequence has {len(values)} entries for {len(index)} candidate(s)."
        )
    return pd.Series(values, index=index, dtype=dtype)


def verdict_table(
    passed: Any,
    code: Any,
    reason: Any,
    *,
    index: pd.Index | None = None,
) -> pd.DataFrame:
    """Build the frame a :class:`Screen` returns, with the right columns and dtypes.

    Each of the three may be a scalar broadcast to every candidate, a sequence of the right
    length, or a ``Series`` already on the candidates' index -- a ``Series`` on a *different*
    index is refused rather than aligned, because a silently aligned verdict describes a row
    it never judged.

    Args:
        passed: ``True`` where the candidate is admitted by this screen.
        code: :data:`ADMITTED` where it passed, one of the screen's declared
            :attr:`Screen.reasons` where it did not.
        reason: The sentence a reader gets. Formatting one string per row is the expensive
            part of a large batch, so the idiom is a constant sentence for the admitted rows
            and per-row text only where a candidate was rejected.
        index: The candidates' index. Optional only when one of the three is a ``Series``,
            from which it is then taken.

    Returns:
        ``(len(index), 3)`` with columns :data:`VERDICT_COLUMNS`.

    Raises:
        ScreenError: if the index cannot be determined, or an argument does not line up
            with it.

    The helper is a convenience, not the enforcement point: :func:`apply_screens` validates
    every verdict frame identically whether or not it was built here.
    """
    if index is None:
        for candidate in (passed, code, reason):
            if isinstance(candidate, pd.Series):
                index = candidate.index
                break
    if index is None:
        raise ScreenError(
            "verdict_table needs an index: pass index=candidates.index, or one of passed, "
            "code and reason as a Series already on it."
        )
    return pd.DataFrame(
        {
            "passed": _column(passed, index, bool, "passed"),
            "code": _column(code, index, object, "code"),
            "reason": _column(reason, index, object, "reason"),
        },
        index=index,
    )


@dataclass(frozen=True)
class Verdicts:
    """What every screen said about every candidate, and nothing removed.

    Attributes:
        table: One row per candidate, on the candidates' index. Column
            :data:`ADMITTED_COLUMN` is ``True`` only where every screen admitted; the rest
            are one block per screen -- ``<name>.passed``, ``<name>.code``, ``<name>.reason``
            and any evidence columns that screen returned -- in the order the screens ran.
        screens: The screen names, in the order they ran.
        durations: Wall-clock seconds each screen took. Carried because the batch rule this
            module is built around is a claim about cost, and a claim about cost should be
            inspectable in the result rather than only in a benchmark document.
    """

    table: pd.DataFrame
    screens: tuple[str, ...]
    durations: Mapping[str, float]

    @property
    def admitted(self) -> pd.Series:
        """``True`` where every screen admitted the candidate."""
        return self.table[ADMITTED_COLUMN]

    def verdict(self, screen: str) -> pd.DataFrame:
        """One screen's verdict, columns unprefixed, exactly as it returned them."""
        if screen not in self.screens:
            raise ScreenError(
                f"no screen named {screen!r} ran here; these did: {_named(self.screens)}."
            )
        prefix = f"{screen}{SEPARATOR}"
        columns = [name for name in self.table.columns if str(name).startswith(prefix)]
        frame = self.table[columns].copy()
        frame.columns = [str(name)[len(prefix) :] for name in columns]
        return frame

    def rejections(self) -> pd.DataFrame:
        """Every rejection, one row each: label, screen, code, reason.

        A candidate rejected by three screens appears three times, because "which rules
        rejected it" is a different question from "was it rejected" and the shortlist review
        needs both. In screen order within a candidate, candidates in frame order.

        Empty of rows but not of columns when everything was admitted, so a caller can write
        it out without special-casing the happy path.
        """
        columns = ["label", "screen", "code", "reason"]
        parts = []
        for position, screen in enumerate(self.screens):
            rejected = ~self.table[f"{screen}{SEPARATOR}passed"].to_numpy()
            if not rejected.any():
                continue
            parts.append(
                pd.DataFrame(
                    {
                        "label": self.table.index[rejected],
                        "screen": screen,
                        "code": self.table.loc[rejected, f"{screen}{SEPARATOR}code"].to_numpy(),
                        "reason": self.table.loc[
                            rejected, f"{screen}{SEPARATOR}reason"
                        ].to_numpy(),
                        "_row": np.flatnonzero(rejected),
                        "_screen": position,
                    }
                )
            )
        if not parts:
            return pd.DataFrame(columns=columns)
        found = pd.concat(parts, ignore_index=True).sort_values(["_row", "_screen"])
        return found[columns].reset_index(drop=True)

    def summary(self) -> pd.DataFrame:
        """Per candidate: admitted, which screens rejected it, and why -- as prose.

        The display and CSV view of :attr:`table` (PRD story S3: "a ranked CSV is produced
        with every filter verdict visible per candidate"). Built on demand rather than
        during the run because joining strings is per-row work, and the run is the part that
        has to stay cheap on a million candidates.
        """
        rejections = self.rejections()
        summary = pd.DataFrame({ADMITTED_COLUMN: self.admitted})
        for column, joiner in (("rejected_by", ", "), ("reasons", "; ")):
            source = "screen" if column == "rejected_by" else "reason"
            if rejections.empty:
                summary[column] = pd.Series("", index=self.table.index, dtype=object)
                continue
            joined = rejections.groupby("label", sort=False)[source].agg(joiner.join)
            summary[column] = joined.reindex(self.table.index).fillna("").astype(object)
        return summary

    def counts(self) -> pd.DataFrame:
        """Seen, admitted, rejected and seconds, per screen, plus an ``overall`` row.

        Per screen rather than as a total because the interesting property is *which* rule
        is doing the removing -- a shortlist that shrank by 90% because one screen rejected
        everything is a different finding from three screens each taking a third.
        """
        rows = len(self.table)
        records = []
        for screen in self.screens:
            admitted = int(self.table[f"{screen}{SEPARATOR}passed"].sum())
            records.append(
                {
                    "screen": screen,
                    "seen": rows,
                    "admitted": admitted,
                    "rejected": rows - admitted,
                    "seconds": round(float(self.durations.get(screen, float("nan"))), 6),
                }
            )
        admitted_all = int(self.admitted.sum())
        records.append(
            {
                "screen": "overall",
                "seen": rows,
                "admitted": admitted_all,
                "rejected": rows - admitted_all,
                "seconds": round(float(sum(self.durations.values())), 6),
            }
        )
        return pd.DataFrame.from_records(records).set_index("screen")

    def select(self, candidates: pd.DataFrame) -> pd.DataFrame:
        """The filtering step: the admitted rows of ``candidates``, in their original order.

        Explicit, afterwards, and by a caller who asked -- which is the whole shape of this
        module. Returns a copy, so a caller ranking or annotating the shortlist cannot reach
        back into the frame that was screened.

        Raises:
            ScreenError: if ``candidates`` is not the frame these verdicts describe. The
                labels must match exactly; a partial or reordered frame would silently
                admit rows nothing judged.
        """
        if not candidates.index.equals(self.table.index):
            raise ScreenError(
                f"these verdicts describe {len(self.table)} candidate(s) and the frame given "
                f"has {len(candidates)}, on a different index. Select from the frame that was "
                f"screened."
            )
        return candidates.loc[self.admitted.to_numpy()].copy()


def _fingerprint(frame: pd.DataFrame) -> tuple[Any, ...]:
    """A cheap, order-sensitive digest of a frame's structure and contents.

    Hashing costs O(rows x columns) per screen -- tens of milliseconds on a batch of a
    million, against the seconds that batch spends being featurised -- and it buys the one
    check that a structural comparison cannot make: a screen that overwrites a value in
    place. Row order is weighted in, so swapping two rows changes the digest; a plain sum of
    row hashes would not.

    ``hash_pandas_object`` raises on cells it cannot hash (a column of lists, say). The
    digest is then ``None`` and the structural half of the fingerprint stands alone, which is
    stated here rather than silently degraded.
    """
    digest: int | None
    try:
        hashes = pd.util.hash_pandas_object(frame, index=True).to_numpy(dtype="uint64")
        weights = np.arange(1, len(hashes) + 1, dtype="uint64")
        digest = int((hashes * weights).sum())
    except (TypeError, ValueError):
        digest = None
    return (
        frame.shape,
        tuple(frame.columns),
        tuple(str(dtype) for dtype in frame.dtypes),
        digest,
    )


def _check_screen(screen: Screen, seen: set[str]) -> None:
    name = getattr(screen, "name", None)
    if not isinstance(name, str) or not name.strip():
        raise ScreenError(f"{screen!r} has no usable name; a screen is addressed by name.")
    if SEPARATOR in name:
        raise ScreenError(
            f"screen name {name!r} contains {SEPARATOR!r}, which joins a screen to its "
            f"column in the composite table."
        )
    if name in seen:
        raise ScreenError(
            f"two screens are called {name!r}. Names address a screen and prefix its "
            f"columns, so a duplicate would overwrite one verdict with another."
        )
    reasons = getattr(screen, "reasons", None)
    if not isinstance(reasons, tuple) or not reasons:
        raise ScreenError(
            f"screen {name!r} declares no reason vocabulary. Every code it can emit must be "
            f"declared, so the refusal path above it can enumerate what it may have to "
            f"explain."
        )
    if any(not isinstance(reason, str) or not reason.strip() for reason in reasons):
        raise ScreenError(f"screen {name!r} declares a blank or non-string reason code.")
    if len(set(reasons)) != len(reasons):
        raise ScreenError(f"screen {name!r} declares a duplicate reason code.")
    if ADMITTED in reasons:
        raise ScreenError(
            f"screen {name!r} declares {ADMITTED!r} as a reason. That code means admitted; "
            f"reasons are the codes on which it rejects."
        )
    if not callable(getattr(screen, "verdict", None)):
        raise ScreenError(f"screen {name!r} has no verdict() to call.")


def _check_verdict(name: str, verdicts: Any, index: pd.Index, allowed: frozenset[str]) -> None:
    if not isinstance(verdicts, pd.DataFrame):
        raise ScreenError(
            f"screen {name!r} returned {type(verdicts).__name__}, not a DataFrame of verdicts."
        )
    if not verdicts.index.equals(index):
        missing = index.difference(verdicts.index)
        extra = verdicts.index.difference(index)
        if len(missing):
            detail = f"{len(missing)} candidate(s) have no verdict: {_named(missing)}"
        elif len(extra):
            detail = f"it invented {len(extra)} row(s): {_named(extra)}"
        elif len(verdicts) != len(index):
            detail = f"it returned {len(verdicts)} row(s) for {len(index)} candidate(s)"
        else:
            detail = "it returned the same labels in a different order"
        raise ScreenError(
            f"screen {name!r} did not judge the batch it was given -- {detail}. A screen "
            f"returns a verdict for every candidate; filtering happens afterwards, by the "
            f"caller."
        )
    if verdicts.columns.has_duplicates:
        raise ScreenError(f"screen {name!r} returned a duplicated column name.")
    absent = [column for column in VERDICT_COLUMNS if column not in verdicts.columns]
    if absent:
        raise ScreenError(
            f"screen {name!r} returned no {_named(absent)} column; a verdict is "
            f"{list(VERDICT_COLUMNS)}."
        )
    if not pd.api.types.is_bool_dtype(verdicts["passed"]):
        raise ScreenError(
            f"screen {name!r} returned 'passed' as {verdicts['passed'].dtype}, not bool. A "
            f"missing or non-boolean verdict is the silent drop wearing a different hat; "
            f"build the frame with verdict_table()."
        )
    for column in ("code", "reason"):
        kind = pd.api.types.infer_dtype(verdicts[column], skipna=False)
        if kind not in {"string", "empty"}:
            raise ScreenError(
                f"screen {name!r} returned {column!r} as {kind}, not strings. Every verdict "
                f"carries a code and a sentence, including the ones that passed."
            )
    if len(verdicts):
        blank = verdicts.index[verdicts["reason"].str.strip().eq("")]
        if len(blank):
            raise ScreenError(
                f"screen {name!r} left {len(blank)} verdict(s) without a reason: "
                f"{_named(blank)}."
            )
        undeclared = set(verdicts["code"].unique()) - allowed
        if undeclared:
            raise ScreenError(
                f"screen {name!r} emitted {_named(undeclared)}, which it does not declare. "
                f"Its vocabulary is {_named(allowed)}."
            )
        disagree = verdicts.index[verdicts["passed"].ne(verdicts["code"].eq(ADMITTED))]
        if len(disagree):
            raise ScreenError(
                f"screen {name!r} disagrees with itself on {len(disagree)} row(s): "
                f"{_named(disagree)}. 'passed' is true exactly where the code is "
                f"{ADMITTED!r}."
            )


def apply_screens(candidates: pd.DataFrame, screens: Sequence[Screen]) -> Verdicts:
    """Run every screen over the whole batch and collect one verdict table.

    Args:
        candidates: The candidates, one per row, on an index whose labels are unique. What
            columns it needs is each screen's business; this function does not read it.
        screens: The screens, in the order their columns should appear. All of them run --
            there is no short-circuit on the first rejection, because a candidate rejected
            by one rule and admitted by four is a different finding from one rejected by
            all five, and the point of this layer is that you can see which.

    Returns:
        :class:`Verdicts`, holding every screen's answer for every candidate. Nothing is
        filtered; :meth:`Verdicts.select` is how a caller asks for the shortlist.

    Raises:
        ScreenError: if a screen breaks the contract -- dropping, adding or reordering a
            row, mutating the candidates, returning a malformed verdict, or emitting a code
            it did not declare -- or if the batch itself cannot be screened. Whatever the
            screens raise is left to propagate: a screen that cannot run is not a verdict.

    Each screen is called **once**, whatever the batch size. That is the module's batch rule
    made structural rather than requested; see the module docstring for what the other shape
    costs and ``docs/BENCHMARKS.md`` for the measurement.
    """
    if not isinstance(candidates, pd.DataFrame):
        raise ScreenError(
            f"candidates must be a DataFrame, one row per candidate; got "
            f"{type(candidates).__name__}."
        )
    if candidates.index.has_duplicates:
        repeated = candidates.index[candidates.index.duplicated()].unique()
        raise ScreenError(
            f"the candidate index repeats {_named(repeated)}. A verdict is addressed by "
            f"label, so a repeated label makes 'which candidate was rejected' unanswerable."
        )
    ordered = list(screens)
    if not ordered:
        raise ScreenError(
            "no screens were given. An empty screen list admits every candidate, which is "
            "the silent drop's mirror image: a shortlist nothing judged. Pass the screens, "
            "even if that is one."
        )

    index = candidates.index
    seen: set[str] = set()
    before = _fingerprint(candidates)
    blocks: list[tuple[str, pd.DataFrame]] = []
    durations: dict[str, float] = {}

    for screen in ordered:
        _check_screen(screen, seen)
        name = screen.name
        seen.add(name)
        started = time.perf_counter()
        verdicts = screen.verdict(candidates)
        durations[name] = time.perf_counter() - started
        # Mutation first: a screen that wrote into the batch has usually broken its own
        # verdict too, and "you modified the input" is the diagnosis for both.
        if _fingerprint(candidates) != before:
            raise ScreenError(
                f"screen {name!r} modified the candidates it was given. A screen reads the "
                f"batch and returns a judgement about it; writing into the batch leaks one "
                f"screen's working into the next one's input and makes the result depend on "
                f"the order they ran in."
            )
        _check_verdict(name, verdicts, index, frozenset(screen.reasons) | {ADMITTED})
        blocks.append((name, verdicts))

    table = pd.DataFrame(index=index)
    passed = pd.DataFrame(
        {name: verdicts["passed"] for name, verdicts in blocks}, index=index
    )
    table[ADMITTED_COLUMN] = passed.all(axis=1)
    for name, verdicts in blocks:
        for column in verdicts.columns:
            table[f"{name}{SEPARATOR}{column}"] = verdicts[column]
    return Verdicts(table=table, screens=tuple(name for name, _ in blocks), durations=durations)
