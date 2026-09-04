"""AC-2 -- the reimplemented featuriser matches CBFV to 1e-9 on the curated formulae.

PRD section 10.2, and the hard gate of stage S3. If it fails, the reimplementation is wrong,
not CBFV: every downstream model would otherwise be trained on subtly different features from
the ones ``REPORT.md`` describes, and nothing else in the project would notice.

Card #21 asks for three things a boolean cannot give. Each is a line of the result:

  - **the offending column and the formula it fails on**, because a red build that says only
    "parity failed" costs the next person a re-run over 1,279 rows to find out where;
  - **the exclusion, recorded rather than filtered**, because a row this layer refuses and
    CBFV answers anyway is not a disagreement -- it is two different questions;
  - **what a green AC-2 does not establish**, because this gate reads CBFV's copy of the
    Oliynyk table and that copy has no holes in it.

What "parity" means here
------------------------

Not "the numbers agree" -- **"the code agrees, given the same numbers"** (#16). The published
Oliynyk table was revised for its 2024 edition and eight of the thirteen properties the
selected features need disagree with CBFV's copy, by up to 10 in ``valence_d``. Comparing our
output against CBFV's while the tables differ would measure the tables. So the gate hands
:func:`~hydms.descriptors.featurize.featurize` **CBFV's own copy** through its ``tables=``
parameter, read from the installed package rather than from a fixture, so the table and the
expected numbers come from one CBFV and cannot drift apart.

The JARVIS half is not overridden, and that is #16's finding rather than an omission: CBFV's
``jarvis.csv`` *is* NIST's ``Elements.json``, the file this project ships, agreeing to 7.3e-12.
Measured here: supplying CBFV's copy of it as well changes the worst disagreement by **nothing
at all** -- 2.728e-12 either way, same column, same formula -- so the two copies are not what
this gate is sensitive to.

Why it is a tolerance and not an equality
-----------------------------------------

:func:`hydms.data.load.parse_formula` returns elements sorted by symbol and CBFV keeps its
parse order, so the statistics accumulate in a different order and round differently (#17).
That residue is the whole of the disagreement: measured over all 1,278 comparable rows, the
worst cell is **2.728e-12** on ``dev_atom_mass_mult_therm_cond`` -- a feature of magnitude
~4e3, so 6.8e-16 relative -- and seven of the 22 columns are bit-identical. **If this gate
ever fails by ~1e-12, suspect the element order before suspecting the arithmetic.**

Relative error is deliberately not reported. ``dev`` is exactly zero whenever every element in
a composition shares a property value, and 49 rows of
``dev_gilmor_number_of_valence_electron`` are such rows: CBFV lands on 4.44e-16 where this
layer lands on 0.0, which is a relative error of 1.0 and an absolute error of nothing. AC-2 is
an absolute criterion and the output stays absolute.

What this gate cannot see
-------------------------

Three things, all recorded in the result rather than left for a reader to know:

  - **The Gordy hole.** CBFV's copy of the Oliynyk table supplies ``gordy_en`` for all 21
    elements the citable 2024 revision leaves blank, so the *reference* table has no hole and
    this gate is green throughout. The shipped, cited tables cannot featurise 266 of the 1,279
    curated rows at all (#19, #20). The result says so, in rows.
  - **A wrong-axis reduction.** Reducing the composition batch over its fast axis costs up to
    2.274e-12 on these 22 columns -- which passes -- and 2.794e-09 on ``bp_mult_mp``, which
    would not, on a property no selected feature uses (#17). ``tests/descriptors/test_stats.py``
    guards the axis directly; that guard is not redundant with this gate and must not be
    deleted when this one goes green.
  - **Europium.** CBFV drops Eu from its JARVIS index and *still emits a row for it*, computed
    as though europium had zero mass -- it lists the formula in the ``skipped`` return value
    that ``extract_features_cbfv.py`` never read. A refusal and a fabricated number are not
    comparable, so ``Eu1Ni5`` is excluded. The exclusion is **derived, not hard-coded**: a row
    is excluded when this layer refuses it, or when CBFV lists it as skipped, and the result
    names the rows and says which side refused. Today those two sets are the same single row,
    and the gate says so rather than assuming it.

Card #21.
"""

from __future__ import annotations

import contextlib
import io
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import numpy as np
import pandas as pd

from hydms.config import Config
from hydms.data.load import load_hydride_data, parse_formula
from hydms.descriptors.contract import (
    CONTRACT,
    PASSTHROUGH,
    PUBLISHED_SPELLING,
    Computability,
    FeatureContract,
)
from hydms.descriptors.element_data import PropertyTable
from hydms.descriptors.featurize import featurize

from ._core import Gate, GateResult, Speed

__all__ = ["GATE"]

#: The acceptance criterion itself (PRD 10.2), so it lives beside the check rather than in
#: ``pipeline.yaml``. Every other threshold in this project is a modelling choice that a
#: re-measurement may move; this one is the definition of the gate, and a tolerance that can
#: be widened by editing a config file is not a gate.
TOLERANCE: Final = 1e-9

#: A failure naming two hundred rows is a failure nobody reads to the end. Same convention as
#: the descriptor layer it checks.
_MAX_NAMED = 8


def _named(items: Iterable[object]) -> str:
    listed = [str(item) for item in items]
    if len(listed) <= _MAX_NAMED:
        return ", ".join(listed)
    return f"{', '.join(listed[:_MAX_NAMED])}, ... ({len(listed) - _MAX_NAMED} more)"


@dataclass(frozen=True)
class Deviation:
    """The worst cell in one column: how far off, on which formula, and both numbers.

    Both values are carried rather than only their difference, because the two failure modes
    look completely different once you can see them -- a last-digit residue reads as
    ``4007.280600000002`` beside ``4007.280599999999``, and a wrong column or a wrong table
    reads as two unrelated magnitudes.
    """

    feature: str
    formula: str
    label: Any
    ours: float
    theirs: float

    @property
    def gap(self) -> float:
        return abs(self.ours - self.theirs)

    def __str__(self) -> str:
        return (
            f"{self.feature} at {self.formula} (row {self.label}): {self.gap:.4e} absolute "
            f"-- cbfv={self.theirs!r}, hydms={self.ours!r}"
        )


def _reference_table(contract: FeatureContract, name: str, root: Path) -> PropertyTable:
    """CBFV's own copy of one element property table, spelled the way the contract spells it.

    Read from the installed package, not from ``tests/descriptors/data/``. The card named the
    committed fixture, and the fixture is bit-identical to this file -- ``build_element_tables
    .py`` wrote it with ``repr(float)``, which round-trips exactly, and
    ``tests/descriptors/test_element_data.py`` pins that. But the gate has already imported
    CBFV in order to produce the expected *numbers*, so reading the table from anywhere else
    admits a version skew between the two halves of one comparison, and a stale fixture would
    surface as a parity failure rather than as what it is. The fixture stays what the tests
    use, since they cannot import CBFV; the gate reads the fixture's source.

    Only the properties this contract needs are extracted, so an unrelated non-numeric column
    of the published file is never coerced.
    """
    wanted = {
        PUBLISHED_SPELLING.get(spec.prop, spec.prop): spec.prop
        for spec in contract
        if spec.table == name and spec.prop is not None
    }
    path = root / f"{name}.csv"
    frame = pd.read_csv(path, index_col=0)
    absent = sorted(published for published in wanted if published not in frame.columns)
    if absent:
        raise RuntimeError(
            f"the installed CBFV's {name} table has no column(s) {_named(absent)}. The "
            f"contract's property names are checked against this file in "
            f"tests/descriptors/test_contract.py; a mismatch here means the installed CBFV is "
            f"not the 1.1.0 the parity extra pins."
        )
    values = {
        str(element): {
            ours: float(row[published])
            for published, ours in wanted.items()
            if pd.notna(row[published])
        }
        for element, row in frame.iterrows()
    }
    return PropertyTable.of(name, f"CBFV's copy of {name}, read from {path.name}", values)


def _cbfv_features(
    generate_features: Any, formulas: pd.Series, kelvin: pd.Series, table: str
) -> tuple[pd.DataFrame, tuple[str, ...]]:
    """What CBFV emits for every curated row, on the caller's labels, plus what it skipped.

    ``extend_features=True`` because ``temperature(K)`` is one of the 22 and carrying it
    through CBFV is the only way to compare that column at all -- it is also what
    ``extract_features_cbfv.py`` did. ``drop_duplicates=False`` because the 1,279 rows carry
    only 1,149 distinct formula strings and a de-duplicated frame could not be laid back
    beside the input.

    CBFV returns its formulae in a separate array, so the alignment is checked rather than
    assumed and the frame is relabelled onto the input's index. Trusting a positional
    correspondence between two frames is leak L9 (``merge_datasets.py:46``), and this is the
    same shape in a different file.
    """
    request = pd.DataFrame(
        {
            "formula": formulas.to_numpy(),
            "target": 0.0,
            PASSTHROUGH: kelvin.to_numpy(dtype=np.float64),
        }
    )
    # CBFV prints a progress bar and a NOTE about "exotic elements" straight to the console.
    # That NOTE is real information and it is captured below as `skipped`, not discarded.
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        emitted, _, returned, skipped = generate_features(
            request, elem_prop=table, drop_duplicates=False, extend_features=True
        )

    got = list(returned)
    if got != list(formulas):
        raise RuntimeError(
            f"CBFV returned {len(got)} formula(e) for {len(formulas)} rows, or returned them "
            f"in a different order, so its output cannot be laid beside the input. Nothing is "
            f"aligned positionally here on purpose: that is leak L9's shape."
        )
    emitted.index = formulas.index
    return emitted, tuple(dict.fromkeys(skipped))


def _refusals(
    contract: FeatureContract,
    parsed: Sequence[Mapping[str, float]],
    tables: Mapping[str, PropertyTable] | None,
) -> dict[int, Computability]:
    """Which rows this layer will not featurise from ``tables``, by position, with the verdict.

    The verdict is per element *set*, so it is memoised -- 1,279 rows carry 464 of them.
    """
    verdicts: dict[tuple[str, ...], Computability] = {}
    refused: dict[int, Computability] = {}
    for position, composition in enumerate(parsed):
        elements = tuple(sorted(composition))
        verdict = verdicts.get(elements)
        if verdict is None:
            verdict = contract.computability(elements, tables=tables)
            verdicts[elements] = verdict
        if not verdict.complete:
            refused[position] = verdict
    return refused


def _blind_spot(contract: FeatureContract, parsed: Sequence[Mapping[str, float]]) -> str:
    """The line that keeps a green AC-2 from being read as more than it is.

    This gate runs against CBFV's copy of the Oliynyk table, which fills every cell the
    citable 2024 edition leaves blank. So the rows the *shipped* tables cannot featurise are
    invisible here, and the count is stated rather than left to be rediscovered downstream by
    whoever builds the training matrix (#24, #25).

    The rows are grouped by *which* features block them, not merely counted, because the two
    groups are different decisions: 265 rows lose one feature and one row loses seven.
    """
    refused = _refusals(contract, parsed, None)
    groups: Counter[tuple[str, ...]] = Counter(v.unavailable for v in refused.values())
    detail = "; ".join(
        f"{count} for {features[0]} alone"
        if len(features) == 1
        else f"{count} for {len(features)} features at once ({_named(features)})"
        for features, count in groups.most_common(_MAX_NAMED)
    )
    return (
        f"What this gate does not see: it reads CBFV's copy of the Oliynyk table, which "
        f"supplies gordy_en for all 21 elements the citable 2024 edition leaves blank. The "
        f"shipped, cited tables could not have featurised {len(refused)} of {len(parsed)} "
        f"curated rows at all -- {detail}. A green AC-2 is not 'the featuriser can produce "
        f"all {len(contract)} features for every row'."
    )


@dataclass(frozen=True)
class FeaturiserParity:
    """The gate. Every number it reports is measured in this call."""

    name: str = "AC-2"
    title: str = "Featuriser parity with CBFV to 1e-9"
    card: int = 21
    speed: Speed = Speed.FAST

    def check(self, cfg: Config) -> GateResult:
        try:
            import CBFV
            from CBFV.composition import generate_features
        except ImportError as error:
            return GateResult.skip(
                self.name,
                f"CBFV is not installed in this interpreter ({error}). It is the featuriser "
                f"being replaced, it carries no licence, and it must never become a "
                f"dependency of a GPL-3.0 deliverable -- so it lives in the optional "
                f"`parity` extra and CI's suite job deliberately omits it. This criterion "
                f"can only be answered where it is installed: "
                f"`conda run -n Project python -m hydms.gates run AC-2`.",
            )

        contract = CONTRACT
        raw = load_hydride_data()
        formulas = raw[cfg.columns.formula]
        kelvin = raw[cfg.columns.temperature]
        parsed = [parse_formula(formula) for formula in formulas]

        sources = {
            name: _reference_table(
                contract, name, Path(CBFV.__file__).parent / "element_properties"
            )
            for name in ("oliynyk",)
        }

        theirs: dict[str, pd.DataFrame] = {}
        skipped: set[str] = set()
        for name in sorted({spec.table for spec in contract if spec.table is not None}):
            theirs[name], flagged = _cbfv_features(generate_features, formulas, kelvin, name)
            skipped.update(flagged)

        # The exclusion, derived from both sides rather than named. A row is comparable only
        # if this layer will produce all 22 features for it *and* CBFV was able to answer
        # honestly; the two sets are reported separately because their disagreeing is the
        # interesting case, not their coinciding.
        refused = _refusals(contract, parsed, sources)
        by_cbfv = {i for i, formula in enumerate(formulas) if formula in skipped}
        excluded = sorted(set(refused) | by_cbfv)
        kept = formulas.index[[i for i in range(len(formulas)) if i not in set(excluded)]]
        if not len(kept):
            # A gate that compares nothing reports a pass over nothing. The empty case is the
            # shape every vacuous check has, so it is a failure here rather than a green run.
            return GateResult.fail(
                self.name,
                f"every one of the {len(formulas)} curated rows was excluded from the "
                f"comparison, so this gate would have passed over nothing. {len(refused)} "
                f"were refused by this layer and {len(by_cbfv)} were skipped by CBFV.",
                measured="0 rows compared",
                threshold=f"{len(formulas)} rows",
            )

        ours = featurize(
            formulas.loc[kept], kelvin.loc[kept], contract=contract, tables=sources
        )

        deviations: list[Deviation] = []
        for spec in contract:
            source = theirs["oliynyk"] if spec.is_passthrough else theirs[str(spec.table)]
            column = spec.name if not spec.is_passthrough else PASSTHROUGH
            want = source.loc[kept, column].to_numpy(dtype=np.float64)
            got = ours[spec.name].to_numpy(dtype=np.float64)
            at = int(np.argmax(np.abs(got - want)))
            deviations.append(
                Deviation(
                    feature=spec.name,
                    formula=str(formulas.loc[kept[at]]),
                    label=kept[at],
                    ours=float(got[at]),
                    theirs=float(want[at]),
                )
            )

        worst = max(deviations, key=lambda d: d.gap)
        over = sorted((d for d in deviations if d.gap > TOLERANCE), key=lambda d: -d.gap)
        exact = sum(1 for d in deviations if d.gap == 0.0)
        version = getattr(CBFV, "__version__", "an unknown version")

        exclusion = (
            f"Excluded and not compared: {len(excluded)} of {len(formulas)} rows -- "
            f"{_named(f'{formulas.iloc[i]} (row {formulas.index[i]})' for i in excluded)}. "
            f"{len(refused)} refused by this layer, {len(by_cbfv)} listed as skipped by CBFV, "
            f"which emits a row for them anyway from an all-zero property vector. A refusal "
            f"and a fabricated number are not comparable."
        )
        blind = _blind_spot(contract, parsed)

        if over:
            return GateResult.fail(
                self.name,
                f"{len(over)} of {len(contract)} columns disagree with CBFV {version} by more "
                f"than {TOLERANCE:g} over {len(kept)} formulae:\n"
                + "\n".join(f"  {d}" for d in over[:_MAX_NAMED])
                + f"\nIf the gap is ~1e-12, suspect the element order before the arithmetic: "
                f"parse_formula sorts by symbol and CBFV does not (#17).\n{exclusion}\n{blind}",
                measured=worst.gap,
                threshold=TOLERANCE,
            )

        return GateResult.ok(
            self.name,
            f"all {len(contract)} columns reproduce CBFV {version} over {len(kept)} of the "
            f"{len(formulas)} curated formulae, given CBFV's own copy of the Oliynyk table. "
            f"Worst: {worst}. {exact} column(s) are bit-identical; the residue is element "
            f"order (#17), not arithmetic.\n{exclusion}\n{blind}",
            measured=worst.gap,
            threshold=TOLERANCE,
        )


GATE: Gate = FeaturiserParity()
