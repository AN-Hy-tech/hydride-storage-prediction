---
id: 36
status: backlog
priority: High
blocked_by: [34]
assignee: "@amirhossein"
tags: [p1, l7, S7]
---

# Five architecture decision records

**Stage S8 — Evidence and close** · **L7 Evidence** · Estimate: 1 d

> **Owns (hidden behind this module):** Why the hardest-to-reverse choices were made, so they are not silently re-litigated.

## Why this exists

Five decisions that are hard to reverse, surprising without context, and the result of a
real trade-off:

1. Optimise in composition space; never invert descriptors
2. Reimplement the featuriser rather than depend on unlicensed CBFV
3. Rank by conformalised LCB, not predicted mean
4. New `hydms/` package; `Machine_Model/src/` archived rather than rewritten
5. pymoo with the element subset fixed per run, over mixed-integer encoding

## Done when

- [ ] `docs/adr/0001..0005-*.md` exist, one per decision
- [ ] Each states context, the alternatives genuinely considered, the decision and its consequences
- [ ] Each links to the PRD section and the research memo section that informed it
- [ ] ADR 2 records the CBFV licence finding explicitly, since a future reader will otherwise re-suggest depending on it
- [ ] **ADR 2 also records the ElMD licence, which is the same finding with the opposite sign**
      (added 2026-09-07 by #49). ElMD is **GPL-3.0** — `LICENSE.txt` in the sdist, and
      `setup.py` says `license='GPL3'`, though its own trove classifier says LGPLv3 and the
      licence file governs. That is compatible with this project's `GPL-3.0-or-later` and is
      *why* the project carries that licence; #49's card says in as many words that it is
      recorded "so the choice is not revisited by mistake". The pair is the point: CBFV is
      unlicensed and may never be a runtime dependency, ElMD is copyleft and may be, and a
      reader who sees only one of the two learns the wrong rule. `pyproject.toml`'s `novelty`
      extra carries both facts and the version evidence (0.5.15; `==0.5.0` is unsatisfiable
      because that sdist's metadata declares itself 0.4.25)

- [ ] **A sixth candidate arrived from #29 (2026-09-05): how the reported interval is
      constructed.** It meets all three tests. *Hard to reverse:* Chapter 1 quotes the number, and
      changing the estimator after publication changes every score in the thesis. *Surprising
      without context:* the bootstrap resamples **canonical groups rather than rows**, which costs
      only 13 % of the independent units (780 groups over 893 rows, 692 of them singletons) and
      looks like pedantry until you know `group_keys` is the seam #13, #87 and #88 all share.
      *A real trade-off:* the out-of-fold predictions come from five models with overlapping
      training sets, so no bootstrap over them is unbiased (Bengio & Grandvalet 2004) — the
      interval is knowingly too narrow, and the alternatives were either more compute than this
      phase has or a research project. The mitigation chosen was to state the caveat in the emitted
      table and carry the per-fold spread beside it as a second, cruder interval. Decide whether
      this displaces one of the five above or becomes a sixth

- [ ] **Three more decisions, and this card's list of five predates all of them** (added 2026-09-06,
      in review). Each meets every bar this card sets — hard to reverse, surprising without context,
      a real trade-off with alternatives that were genuinely considered and are written down. The
      card is not renamed: "five" was the count when it was cut, and the ADRs are numbered, not
      counted.

      6. **A waiver is an act, not a property.** Promotion demanded every registered criterion pass,
         `SKIPPED` counted, and three criteria belong to frozen phases — so the phase would have
         ended with a correct model that could never be promoted and a `predict()` that refused
         everything. Rejected: a phase-scoped subset computed at promotion time; a fourth gate
         status; loading with the gate check disabled in the delivery path. All three assume the fix
         belongs to the criterion or to the rule. It belongs to the **act**: a promotion is already
         a dated one-line decision, and all it lacked was the ability to say what it proceeded
         without. The consequence worth recording is the asymmetry — *the artifact says what was
         measured, the pointer says what was decided*, and neither is allowed to say the other's
         thing.

      7. **One definition of the deployed fit.** Two commands each built "the deployed fit" and the
         two were different models — 873 rows against 701 — so the committed explainability tables
         described a model with no band while the correction belonged to a model with no
         explanation. Rejected: making the two agree by convention, and documenting the difference.
         The decision was to put the sequence in one module both callers call, so it cannot be
         assembled three-quarters of the way. Hard to reverse because the L1 and L11 sentinels, the
         artifact payloads and the explainability tables are all now aimed at it.

      8. **`load_surrogate` splits into locating and assembling.** A gate needs a certified version;
         certification needs the gate. Three options were written on #33 and all three traded
         something away, because all three treated loading as one decision. It is two — *locating* a
         version has an opinion about gates, *assembling* a `Surrogate` from a bundle does not — so
         `surrogate_from(bundle)` is the second half and the gate uses it. **`load_surrogate` grew
         no parameter**, which is the whole point: the guarantee is intact for every other caller

## Runnable check

```bash
ls docs/adr/*.md | wc -l
```

## Traces to

`docs/PRD-inverse-design.md` — S7

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
