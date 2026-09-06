"""Certify a candidate artifact version and move the promotion pointer to it.

    python -m hydms.surrogate.promote                 # gate the newest version
    python -m hydms.surrogate.promote --version v1
    python -m hydms.surrogate.promote --dry-run       # run the gates, write nothing

**The circle this command closes, and the shape it has because of it.** An artifact version is
written once and never edited (:mod:`hydms.artifacts.store`), and a version may not be promoted
unless its *manifest* records a gate run in which every criterion passed. But the gates score a
model, so the run that certifies a version can only happen after that version exists -- by which
time its manifest is sealed. The three ways out were written up on card #33; card #34 takes
**(C)**, and this module is it: the gates run against the candidate, and the version that gets
promoted is a **new** one carrying the same payloads *and* the report.

The cost is stated rather than hidden: two version directories for one model. What is bought is
that the promoted version's manifest says, truthfully, "these gates passed against these
payloads", and that the candidate stays on disk with its own manifest recording the fit's own
git SHA and time -- so the chain from a promoted model back to the commit that fitted it is two
hops and neither is inferred.

**Nothing here fits anything.** The model comes from ``python -m hydms.surrogate.calibrate
--target capacity --save``, which is about two minutes from the committed
``reports/model/model-chosen.csv``. This command reads, certifies and points.

**Refusal is the common outcome while Phase H is running, and it is correct.** The registry
holds a criterion for everything this project has promised to check, including the ones nobody
has written yet, and those report ``SKIPPED`` -- which
:meth:`~hydms.artifacts.manifest.Manifest.unestablished` counts as *not established*, because a
manifest saying "AC-6 was not checked" is exactly as much evidence about cross-family transfer
as one saying "AC-6 failed". So a model cannot be promoted until the last gate is written. That
is the store's guarantee working, not this command failing, and the refusal names every
outstanding criterion and the card that owes it.

**``--waive`` is the exception, and it is narrow on purpose.** Three registered criteria --
AC-5, AC-7 and AC-8 -- belong to phases ``docs/FREEZE.md`` has frozen, so Phase H cannot make
them pass however much work it does; without a way through, the phase ends with a model that can
never be promoted and a delivery layer that can never load one. ``--waive AC-5`` names one such
criterion, and the reason recorded is **the gate's own skip message**, not prose typed at the
prompt: a ``Pending`` gate already states why it is pending and names the card and the freeze
document, and that sentence is reviewed code where a command-line string is not.

What it does not buy:

  - **A failed criterion is never waivable.** ``hydms.artifacts.promote`` refuses anything whose
    status is not ``SKIPPED``, so this flag cannot be used to ship past a gate that ran and said
    no.
  - **It is not "skip the ones that are hard".** AC-6, HG-2, HG-3 and HG-4 are skipped today and
    are *reachable* in this phase (cards #30, #77, #79, #86). Waiving one would be waiving work
    rather than scope. Nothing stops you at the prompt -- this command prints the owning card
    beside every waiver so the operator can see which board it is on -- but
    ``tests/artifacts/test_waiver_scope.py`` pins which criteria a frozen phase owns, derived
    from the board directories, so the set cannot drift without a red test.
  - **It does not touch the manifest.** The promoted version's embedded report still records
    AC-5 as ``SKIPPED``. The waiver lives in ``current.json``, dies when the pointer moves, and
    is what ``hydms.artifacts.waived()`` reads back for anything that reports what a prediction
    rests on.

The full argument, including the two shapes that were rejected, is in
:mod:`hydms.artifacts.store`'s docstring.

Exit codes:

    0   the version was certified and ``current`` now points at it (or ``--dry-run`` was green)
    1   a criterion is unestablished and not waived -- nothing was written, nothing promoted
    2   the invocation itself was wrong (unreadable config, unknown version, empty store, or a
        waiver naming a criterion a waiver may not cover)

Card #34.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TextIO

from hydms.config import ConfigError, load

EXIT_OK = 0
EXIT_UNESTABLISHED = 1
EXIT_BAD_INVOCATION = 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m hydms.surrogate.promote",
        description=(
            "Run every gate against a candidate artifact version, then write and promote a "
            "version carrying the report. Fits nothing."
        ),
    )
    parser.add_argument(
        "--version",
        default=None,
        help="the candidate to certify; defaults to the newest version in the store",
    )
    parser.add_argument(
        "--config", type=Path, default=None, help="a pipeline YAML; defaults to the packaged one"
    )
    parser.add_argument(
        "--store", type=Path, default=None, help="the artifacts directory; defaults to paths.artifacts"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="run the gates and report; write no version and move no pointer",
    )
    parser.add_argument(
        "--waive",
        action="append",
        default=[],
        metavar="GATE",
        help=(
            "proceed without this criterion, which must be SKIPPED in this run; repeatable, "
            "one name at a time. The reason recorded is the gate's own skip message. For "
            "criteria a frozen phase owns, never for work this phase can do."
        ),
    )
    return parser


def main(argv: list[str] | None = None, out: TextIO | None = None) -> int:
    args = _parser().parse_args(argv)
    stream = out if out is not None else sys.stdout

    try:
        cfg = load(args.config)
    except ConfigError as error:
        print(f"could not read the configuration: {error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION

    from hydms import artifacts
    from hydms.artifacts import ArtifactError
    from hydms.gates import render_report, run, select

    root = Path(args.store) if args.store is not None else cfg.paths.artifacts
    known = artifacts.versions(store=root)
    if not known:
        print(
            f"no artifact version in {root}. Build and persist the deployed fit first:\n"
            f"  conda run -n Project python -m hydms.surrogate.calibrate --target capacity "
            f"--save",
            file=sys.stderr,
        )
        return EXIT_BAD_INVOCATION

    candidate = args.version if args.version is not None else known[-1]
    if candidate not in known:
        print(
            f"no version {candidate!r} in {root}. Present: {', '.join(known)}.", file=sys.stderr
        )
        return EXIT_BAD_INVOCATION

    try:
        # `require_gates=False` on purpose: certifying a version is what gives it gates, so
        # requiring them here would be the circle this command exists to close. The load still
        # verifies every payload against its recorded digest.
        bundle = artifacts.load(candidate, store=root, require_gates=False)
    except ArtifactError as error:
        print(f"{candidate} could not be read: {error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION

    source = bundle.manifest
    # A store outside a work tree records no SHA at all (`describe_git` answers "unknown"
    # rather than raising), so both of these have to read as sentences when it is absent.
    sha = source.git.sha or ""
    fitted_at = f"{sha[:7]}{' with a modified tree' if source.git.code_modified else ''}" if sha else "an unknown commit"
    print(
        f"certifying {candidate}: {len(bundle.names)} payload(s) "
        f"({', '.join(bundle.names)}), fitted at {fitted_at} on {source.created_at}; "
        f"notes: {source.notes or '(none)'}",
        file=stream,
    )

    gates = select()
    report = run(gates, cfg, selection="--all", strict=True)
    print(render_report(report, gates), file=stream)

    by_name = {r.name: r for r in report.results}
    requested: dict[str, str] = {}
    for name in dict.fromkeys(args.waive):
        result = by_name.get(name)
        if result is None:
            print(
                f"--waive {name}: this run recorded no criterion by that name. Registered: "
                f"{', '.join(sorted(by_name))}.",
                file=sys.stderr,
            )
            return EXIT_BAD_INVOCATION
        if result.status.value != "SKIPPED":
            print(
                f"--waive {name}: it is {result.status.value} in this run, and a waiver covers "
                f"only a criterion that did not run at all. A waiver says why something was "
                f"not checked; it can never say a check was made and did not hold.",
                file=sys.stderr,
            )
            return EXIT_BAD_INVOCATION
        # The gate's own account, not the operator's. A `Pending` gate states why it is
        # pending and names its card and `docs/FREEZE.md`; that sentence is reviewed code,
        # and a reason typed at the prompt is not.
        requested[name] = result.message or f"skipped; card #{_card(name)}"

    if requested:
        listed = "\n".join(
            f"  {name} (card #{_card(name)}) -- {reason}" for name, reason in requested.items()
        )
        # Before the refusal below, not after it. An operator who waives three criteria and is
        # still refused for a fourth has to be able to see that the three were accepted --
        # otherwise the refusal reads as the flag having done nothing.
        print(
            f"\nWAIVED, and recorded in current.json as the promotion's own asterisk if this "
            f"promotion goes through:\n"
            f"{listed}\n"
            f"{candidate} therefore has {len(report.results) - len(requested)} of "
            f"{len(report.results)} criteria left to establish. The manifest still records "
            f"every waived one as SKIPPED: the decision to proceed lives in the pointer, not "
            f"in the artifact's account of what was measured.",
            file=stream,
        )

    outstanding = tuple(r for r in report.results if not r.passed and r.name not in requested)
    if outstanding:
        print(
            f"{candidate} is NOT promotable: {len(outstanding)} of {len(report.results)} "
            f"criteria are unestablished -- "
            + ", ".join(f"{r.name} {r.status.value} (card #{_card(r.name)})" for r in outstanding)
            + ".\nA SKIPPED gate is a criterion nobody checked, and hydms.artifacts.promote "
            "refuses it for the same reason it refuses a failure. Nothing was written and the "
            "promotion pointer did not move.",
            file=sys.stderr,
        )
        return EXIT_UNESTABLISHED

    if args.dry_run:
        established = (
            "every criterion passed"
            if not requested
            else f"every criterion passed or was waived ({', '.join(requested)})"
        )
        print(
            f"--dry-run: {established} against {candidate}. Re-run without --dry-run "
            f"to write the certified version and move the pointer.",
            file=stream,
        )
        return EXIT_OK

    notes = (
        f"certified copy of {candidate}, which was fitted at "
        f"{sha or 'an unknown commit'} on {source.created_at}"
        f"{' from a modified tree' if source.git.code_modified else ''}. "
        f"Payloads are that version's objects; the gate report is this command's run against "
        f"it."
        + (
            f" Promoted with {len(requested)} criteri{'on' if len(requested) == 1 else 'a'} "
            f"waived ({', '.join(requested)}); the report records each as SKIPPED and the "
            f"waiver itself is in current.json."
            if requested
            else ""
        )
    )
    manifest = artifacts.save(
        {name: bundle[name] for name in bundle.names},
        contract=source.contract,
        seeds=source.seeds,
        gates=report,
        notes=notes,
        store=root,
    )
    artifacts.promote(manifest.version, store=root, waive=requested)
    print(
        f"wrote {manifest.version} carrying the gate report and promoted it. "
        f"`current` now points at {manifest.version}; {candidate} stays on disk as the record "
        f"of the fit. Two directories for one model is the cost of a manifest that cannot be "
        f"edited after it is written.",
        file=stream,
    )
    return EXIT_OK


def _card(name: str) -> int:
    """Which card owes a criterion, so a refusal says who to go and see."""
    from hydms.gates import registry

    for gate in registry():
        if gate.name == name:
            return gate.card
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
