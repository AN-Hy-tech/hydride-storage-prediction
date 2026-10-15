"""How many candidate compositions this layer can featurise per second, and where the time goes.

Card #22, and PRD risk R6. The question is not vanity: NSGA-II makes far more surrogate calls
than enumeration does, so **the cost of one evaluation decides which paradigm is affordable**
and bounds how large Architecture A's grid can be. The inverse-design memo section 7 says to
measure it on day one rather than discover it at the end.

Run it::

    python -m hydms.descriptors.benchmark --sizes 1,100,10000,100000

Two things this module refuses to do, because both would report a number that is not the one
the design decision needs.

**It does not report the parser as though it were the arithmetic.** :func:`featurize` is one
Python pass that parses and interns element symbols, then nineteen fancy-indexes and nineteen
batched reductions in numpy. Those two halves scale differently -- the first is per formula and
stays in Python, the second is per *batch* and leaves it -- so they are timed separately and
reported separately. A single total would say "featurisation costs X" while X was almost
entirely :func:`hydms.data.load.parse_formula`.

**It does not featurise the same formula ten thousand times.** Tiling the curated set up to
100,000 rows would leave only 1,149 distinct formulae, and this layer memoises the
computability verdict per element *set* -- so the benchmark would measure the memo. The
synthetic candidates below are distinct by construction, drawn from the element universe the
shipped tables can fully serve and from the curated set's own arity distribution, which is
what a candidate generator on the composition simplex actually produces. The curated set is
reported too, as its own row, because it is the training-matrix workload rather than the search
workload and the two are different questions.

What is deliberately *not* optimised
------------------------------------

A batch of one does twice the arithmetic of the smallest possible call: #20 found that numpy
switches to an eight-accumulator unrolled sum at exactly eight contiguous elements, so a lone
composition is duplicated, reduced as a pair and the copy discarded, which is what makes a
single-formula prediction agree with the training matrix bit for bit. It is bounded and
intentional. The batch-of-one row measures per-*call* overhead, not per-formula cost.
"""

from __future__ import annotations

import argparse
import platform
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np

from hydms.config import Config, load
from hydms.data.load import load_hydride_data, parse_formula
from hydms.descriptors.contract import CONTRACT, FeatureContract
from hydms.descriptors.featurize import featurize

__all__ = ["Measurement", "candidates", "main", "measure", "render"]

#: The card's own batch sizes. 1 is the per-call overhead, 100 is a screen's page, 10,000 is
#: an NSGA-II run's whole evaluation budget, 100,000 is Architecture A's grid.
DEFAULT_SIZES: Final = (1, 100, 10_000, 100_000)

#: Best-of, not mean-of. A timing floor is the quantity that reproduces; the mean measures
#: whatever else the machine was doing.
DEFAULT_REPEATS: Final = 3

#: The temperature every synthetic candidate is evaluated at. It is one of the 22 features and
#: it is a passthrough, so its value cannot change the cost -- fixed so it cannot be suspected.
TEMPERATURE: Final = 298.0

#: Amounts are drawn from this range and rounded to three decimals, which is the resolution the
#: curated file writes and comfortably coarser than the canonical key's four significant digits
#: (``hydms.data.canonical``), so two draws that differ here are two different materials.
_AMOUNT = (0.05, 5.0)
_PLACES: Final = 3


@dataclass(frozen=True)
class Measurement:
    """One batch size, timed. Every derived figure is a property, so nothing can disagree."""

    label: str
    size: int
    #: Best of ``repeats``, in seconds: :func:`parse_formula` over the batch, alone.
    parse_s: float
    #: Best of ``repeats``, in seconds: the whole :func:`featurize` call, parsing included.
    total_s: float
    repeats: int
    #: Worst minus best over the repeats, so a reader can see whether the floor was reached.
    spread_s: float

    @property
    def arithmetic_s(self) -> float:
        """Everything that is not the parser: the verdict, the pack, and the reductions."""
        return max(self.total_s - self.parse_s, 0.0)

    @property
    def per_second(self) -> float:
        return self.size / self.total_s if self.total_s > 0 else float("inf")

    @property
    def us_per_formula(self) -> float:
        return 1e6 * self.total_s / self.size

    @property
    def parse_share(self) -> float:
        """The fraction of the wall clock spent in Python parsing formula strings."""
        return self.parse_s / self.total_s if self.total_s > 0 else 0.0


def _servable(contract: FeatureContract, elements: Sequence[str]) -> tuple[str, ...]:
    """The elements every feature in ``contract`` can be computed for, on their own.

    A candidate generator may only propose what the featuriser accepts, so the search
    workload is measured over these. Today that is the dataset's 55 elements less the 21 the
    citable Oliynyk edition leaves ``gordy_en`` blank for and less europium -- a fact this
    module reports rather than assumes, because #24 and #25 may drop the blocking feature and
    the universe would then widen without anything here changing.
    """
    return tuple(
        element
        for element in elements
        if contract.computability((element,)).complete
    )


def candidates(
    size: int, universe: Sequence[str], arities: Sequence[int], *, seed: int
) -> list[str]:
    """``size`` distinct synthetic formulae, drawn the way a search proposes them.

    Distinctness is checked rather than hoped for: a repeated formula would be answered from
    the computability memo and the benchmark would report the cache.

    Args:
        size: How many formulae to generate.
        universe: The element symbols to draw from -- see :func:`_servable`.
        arities: The distinct-element counts to draw from, as an empirical population, so the
            batch has the curated set's shape rather than a uniform one.
        seed: The project seed, from ``pipeline.yaml``. The same seed gives the same batch.

    Returns:
        ``size`` formula strings, every one of them distinct and parseable.
    """
    rng = np.random.default_rng(seed)
    picked: dict[str, None] = {}
    while len(picked) < size:
        arity = min(int(rng.choice(arities)), len(universe))
        elements = rng.choice(len(universe), size=arity, replace=False)
        amounts = rng.uniform(*_AMOUNT, size=arity).round(_PLACES)
        formula = "".join(
            f"{universe[int(index)]}{amount:.{_PLACES}f}"
            for index, amount in zip(elements, amounts, strict=True)
        )
        picked[formula] = None
    return list(picked)


def _best(work: Callable[[], object], repeats: int) -> tuple[float, float]:
    """Run ``work`` ``repeats`` times; return its floor and the spread around it."""
    times = []
    for _ in range(repeats):
        clock = time.perf_counter()
        work()
        times.append(time.perf_counter() - clock)
    return min(times), max(times) - min(times)


def measure(
    sizes: Sequence[int] = DEFAULT_SIZES,
    *,
    repeats: int = DEFAULT_REPEATS,
    cfg: Config | None = None,
    contract: FeatureContract | None = None,
) -> tuple[Measurement, ...]:
    """Time :func:`featurize` at each batch size, plus the curated set as its own row.

    Returns:
        One :class:`Measurement` per size in the order given, followed by ``curated`` -- the
        real 1,279 rows less the ones the shipped tables refuse, which is the training-matrix
        workload rather than the search one.
    """
    settings = cfg if cfg is not None else load()
    declared = contract if contract is not None else CONTRACT

    raw = load_hydride_data()
    curated = [str(formula) for formula in raw[settings.columns.formula]]
    parsed = [parse_formula(formula) for formula in curated]
    universe = _servable(declared, sorted({e for row in parsed for e in row}))
    arities = [len(row) for row in parsed]

    def timed(label: str, batch: list[str], kelvin: float | np.ndarray) -> Measurement:
        parse_s, _ = _best(lambda: [parse_formula(f) for f in batch], repeats)
        total_s, spread = _best(
            lambda: featurize(batch, kelvin, contract=declared), repeats
        )
        return Measurement(
            label=label,
            size=len(batch),
            parse_s=parse_s,
            total_s=total_s,
            repeats=repeats,
            spread_s=spread,
        )

    results = [
        timed(
            f"synthetic {size:,}",
            candidates(size, universe, arities, seed=settings.seed),
            TEMPERATURE,
        )
        for size in sizes
    ]

    # The curated workload: the real rows, less the ones the shipped tables refuse. Which
    # ones those are is the contract's answer, not a list kept here (#19, #20).
    featurisable = [
        index
        for index, composition in enumerate(parsed)
        if declared.computability(composition).complete
    ]
    temperatures = raw[settings.columns.temperature].to_numpy(dtype=np.float64)
    results.append(
        timed(
            f"curated {len(featurisable):,}",
            [curated[index] for index in featurisable],
            temperatures[featurisable],
        )
    )
    return tuple(results)


def machine() -> str:
    """The machine this ran on, in one line, because a throughput without one is not a fact."""
    return (
        f"{platform.platform()} · {platform.processor() or platform.machine()} · "
        f"Python {platform.python_version()} · numpy {np.__version__}"
    )


def render(results: Sequence[Measurement], *, contract: FeatureContract | None = None) -> str:
    """The results as a Markdown table, ready to paste into ``docs/BENCHMARKS.md``."""
    if not results:
        raise ValueError("nothing was measured; render() has no empty table to draw")
    declared = contract if contract is not None else CONTRACT
    header = (
        "| batch | formulae/s | µs/formula | total (s) | parse (s) | arithmetic (s) | "
        "parse share | spread (s) |"
    )
    rule = "|---|---:|---:|---:|---:|---:|---:|---:|"
    rows = [
        f"| {m.label} | {m.per_second:,.0f} | {m.us_per_formula:,.1f} | {m.total_s:.4f} | "
        f"{m.parse_s:.4f} | {m.arithmetic_s:.4f} | {m.parse_share:.0%} | {m.spread_s:.4f} |"
        for m in results
    ]
    return "\n".join(
        [
            f"Machine: {machine()}",
            f"Features: {len(declared)} columns · best of {results[0].repeats} runs",
            "",
            header,
            rule,
            *rows,
        ]
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="How many candidate compositions this layer can featurise per second."
    )
    parser.add_argument(
        "--sizes",
        default=",".join(str(n) for n in DEFAULT_SIZES),
        help="comma-separated batch sizes (default: %(default)s)",
    )
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    args = parser.parse_args(argv)

    try:
        sizes = [int(part) for part in args.sizes.split(",") if part.strip()]
    except ValueError:
        parser.error(f"--sizes must be a comma-separated list of integers, got {args.sizes!r}")
    if not sizes or any(size < 1 for size in sizes):
        parser.error("--sizes must name at least one batch of at least one formula")
    if args.repeats < 1:
        parser.error("--repeats must be at least 1")

    print(render(measure(sizes, repeats=args.repeats)))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
