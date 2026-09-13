---
id: 81
status: done
priority: Normal
blocked_by: [29, 30, 76]
assignee: "@amirhossein"
tags: [ph, l6, S2, S10]
---

# App chart vocabulary: charts that resist false belief

**Stage S7 — Delivery: the interface** · **L6 Delivery** · Estimate: 1 d

> **Owns (hidden behind this module):** How uncertainty and applicability are drawn, so that every page in the app says the same thing the same way.

## Why this exists

A number rendered large and alone reads as certain, whatever the caveat beside it. The
charts are not decoration on the prediction — they are most of how the interval and the domain verdict
actually reach the user.

Five charts, each chosen because it makes a specific false belief harder to hold. They are built once,
here, so the prediction page and the model card cannot drift into drawing the same quantity two
different ways.

## Done when

- [x] **Prediction band** — the estimate drawn inside its conformal interval, with the width stated
      numerically. A wide interval must *look* wide; the axis may not rescale to hide it
- [x] **Domain strip** — where this composition sits against the training distribution and the AD ceiling
- [x] **Temperature sweep** — predicted wt% across the valid range with the interval as a band. ~~Only 39
      test rows sit above 500 K~~ — **130 of 893, measured**; see the narrative — the chart must not
      conceal that thinning
- [x] **Nearest neighbours** — the k closest training alloys by ElMD, with their *measured* capacities
- [x] **Parity plot** — predicted versus measured on the held-out test set, with the leave-one-alloy-class-out
      version beside it at the same scale. **Built and locked to one scale; the LOACO panel has no data
      on disk to fill it** — `reports/loco/` commits per-class metrics only, which is card **#98**
- [x] All five read correctly in both light and dark, and are colour-blind safe
- [x] Every axis carries units; no chart shows a point estimate without its interval

## Runnable check

```bash
conda run -n Project python -m pytest tests/test_figures.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S7; `docs/PRD-inverse-design.md` — S2, S10

## Narrative

- 2026-09-02: Created for Phase H. The parity plot showing random-split and LOACO at the same
  scale is the one that matters most: it puts the optimistic number and the honest number on one page (by @assistant)

- 2026-09-12: **Done.** `hydms/figures/` is three modules and `tests/test_figures.py` is 55 tests,
  4.4 s, no `slow` marker — **55 passed alone and in the fast lane (`-m "not slow"`: 1526 passed),
  and two of them fail in a full run.** `test_every_figure_renders_in_both_themes` is
  order-dependent, and the obvious explanation — one of the four `slow` tests, all of which sort
  before this file — was tested and **refuted**: those four beside the figures tests give 134
  passed. Both halves of the suite are green and only the whole is red. That is **#100**, filed
  rather than left as a box here because
  `check_board.py` refuses a `done` card with an unticked one. The five builders and every
  guarantee they carry are unaffected — the failing pair is the smoke test, and the split this
  card is built on is what makes that sentence true rather than hopeful. (by @assistant)

  **A chart here is a description before it is an image, and that split is the whole design.**
  `charts.py` builds `Figure` objects and imports no plotting library; `render.py` turns one into
  matplotlib and is thin. The reason is not taste: **every box above is a property of the
  description, not of the pixels.** An estimate never drawn without its interval, an axis that
  always names its unit, panels locked to one scale, a threshold labelled rather than merely
  coloured — each is a construction error in `charts.py`, checkable by a test that installs
  nothing. Had they lived in the renderer, every one of them would have been a guarantee that runs
  only where a plotting library is installed, and the CI lane's install list would decide which
  guarantees this project has.

  **Four of the seven boxes are types rather than assertions.** `Series` cannot be constructed with
  `origin=PREDICTED` and no band. A quantitative `Axis` cannot be constructed without a unit — and
  a categorical one cannot be constructed *with* one, because "this candidate" is not in weight
  percent and a unit printed beside it would be read as the series'. `Panel` refuses a series or a
  marker its axis cannot hold, so **nothing clips**: a builder that finds a band running past its
  axis widens the axis, which is the mechanism behind "a wide interval must look wide". `Figure`'s
  `shared=('x', 'y')` makes every panel's axis *equal*, checked — which is how "at the same scale"
  stopped being a review note.

  **The wide-looks-wide claim is measured, not asserted.** `test_a_wide_interval_occupies_more_of
  _the_axis_than_a_narrow_one` builds two answers, one with a 0.14 wt% band and one with a 4.70 wt%
  band, and asserts the second covers more than ten times the fraction of its frame. That comparison
  only means anything because both axes are anchored to the trained capacity range; an axis fitted
  to its own band would make the two figures identical, which is precisely the chart this card
  exists to prevent.

  **"Only 39 test rows sit above 500 K" is REPORT.md's number and it does not describe this
  project's evidence.** It traces to `REPORT.md:394` — *"n = 39"* — over the archival pipeline's
  247-row test split, and that split no longer exists: the group-aware nested protocol scores every
  row out of fold. Measured against `reports/model/model-out-of-fold.csv`: **893 rows, 130 of them
  above 500 K.** The *claim* survives untouched — 15.8% then, 14.6% now — and only the number was
  inherited, which is exactly why `TemperatureSupport` takes counts rather than carrying a
  constant. A chart whose thinning claim is typed in is a chart that keeps being right about the
  wrong split. The string `39` still stands in **three** production docstrings, two test
  docstrings and two card paragraphs; retiring it is **#99**, not this card.

  **The parity plot found a gap in the evidence and reports it at the point of use.** `parity()`
  requires at least two readings — a single-panel parity plot is the optimistic number on its own
  page, which is what this card's own first narrative entry names — and there is no second reading
  on disk. `hydms.surrogate.train` writes `evaluation.out_of_fold`; `hydms.surrogate.loco` writes
  four tables and that is not one of them, so LOACO leaves ten class averages and no scored rows.
  The refusal's message says so and names **#98**. The alternative — relaxing the builder to accept
  one reading — would have shipped the optimistic panel alone under a caption explaining the
  absence, and captions are what readers skip.

  **The palette is computed, not chosen.** Three slots, validated with the `dataviz` skill's Node
  validator on the **all-pairs** list in both modes (worst CVD ΔE 9.2 light / 9.4 dark against a
  gate of 8; worst normal-vision ΔE 24.0 / 20.9 against a floor of 15). Three, not eight, because
  the reference palette's full set clears only the *adjacent* pairlist and these are scatter and
  dot plots. The light aqua raised the one contrast WARN, so slot 3 carries the relief rule: a
  series in it must have a visible direct label, `Figure.relief()` reports any that does not, and
  the renderer **refuses** such a figure. The committed test pins every hex and every reported
  number — which cannot prove the palette is safe, since the simulation that decides that runs in
  another language outside this repository, but does force the command to be re-run rather than the
  reasoning re-done.

  **Two things the rendered figures changed, that reading the spec would not have.** The sweep was
  first drawn as two side-by-side panels sharing an x axis, and a support histogram *beside* the
  curve it supports is not the claim the card makes — `Figure.layout='column'` stacks it under, and
  a column is required to share x because stacking is itself the claim that the panels line up.
  And the support bins are unequal (55 K up to 100 K), so a uniform bar width was overstating the
  density of the narrow bins by up to 2×; `Series.widths` carries the bin extent. Both were only
  visible by opening the PNG, which is the last step of the skill's procedure and the one easiest
  to skip.

  **matplotlib got its own extra and CI installs it.** `figures = ["matplotlib>=3.8"]`, with
  `app = ["hydms[figures]", "streamlit>=1.30"]`, and `.github/workflows/ci.yml` now installs
  `.[dev,uq,novelty,api,figures]`. Both lock files already carry matplotlib as a leftover of the
  archival pipeline — `matplotlib-base=3.9.2` and `matplotlib==3.10.1` — so the floor names a
  version `Project` already satisfies and nothing was re-solved. Naming it in CI is the point: an
  extra CI skips is a guarantee nobody checks. It stays a *separate* extra from `app` because
  `hydms.figures.render` is its only importer and the description tests must run with no plotting
  library at all.

  **What #82 gets.** Five builders taking the delivery contract's own types — `PredictionResult`,
  `Interval`, `DomainVerdict`, `Novelty` — so Streamlit stays an HTTP client: it reads a JSON
  answer through `answer_from()` and hands the result to a builder. No chart function loads a
  model, reads an artifact, or touches the surrogate.

- 2026-09-13 (correction, appended not rewritten): the note above gives the wrong *reason* for
  filing #100. `check_board.py` does **not** refuse a `done` card with an unticked box — it has no
  checkbox rule at all, and nothing in `scripts/` or `tests/` reads a `- [ ]` (#68). The decision to
  file #100 as its own card was still right, for the reason #94 gives: an unticked box on a closed
  card is a finding nobody is going to see. Only the mechanism was imagined. The correction is
  appended rather than edited in, because a narrative records what a session believed at the time
  and that is the whole of its value. Open findings are indexed in
  [../docs/PHASE-H-FINDINGS.md](../docs/PHASE-H-FINDINGS.md). (by @assistant)
