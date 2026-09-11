---
id: 35
status: done
priority: High
blocked_by: [20, 28]
assignee: "@amirhossein"
tags: [p1, l7, S7]
---

# CONTEXT.md domain glossary

**Stage S8 — Evidence and close** · **L7 Evidence** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The project's vocabulary, pinned so that easily-conflated terms stay distinct.

## Why this exists

Glossary only — no implementation detail. Terms that must be pinned because conflating
them causes real errors:

- **Candidate** vs **Composition** vs **Formula**
- **Capacity** — always *maximum material* gravimetric wt%; never usable, never system-level
- **Surrogate** (inside the optimiser) vs **production model** (reported in `REPORT.md`)
- **Novelty** (ElMD distance) vs **uncertainty** (interval width) vs **applicability domain** (in/out of scope)
- **LCB** — the ranking signal; never the mean
- **Alloy family** and **family stoichiometry**

## Done when

- [x] `CONTEXT.md` at repo root, glossary only — **26 terms in nine groups**
- [x] Each term has a one-line definition and, where useful, an explicit contrast with what it is
      *not*. Every term carries an `_Avoid_` line naming the words it is regularly confused with,
      because the contrast is the part that does the work
- [x] The capacity definition states the material/system and maximum/usable distinctions — three
      separate entries (`Capacity`, `Usable capacity`, `System capacity`) rather than one entry with
      caveats, so a reader cannot pick up the head term and leave the qualifications behind
- [x] No implementation detail, no decisions, no spec content. Checked term by term: no module name,
      no file path, no number, no threshold. The one place it came close is `Interval width`, which
      has to say the correction is not a constant — stated as a property of the transform rather than
      as an equation

- [x] **The inclusion rule turned out to be sharper than "the project's vocabulary", and it is
      worth stating.** A glossary of everything is a document nobody reads twice. So the file admits
      a term only if **conflating it with another has already cost this project something** — a
      wrong number quoted, a sentinel aimed at the wrong object, a caveat dropped. Every entry can
      name its incident. That is why `Deployed fit`, `Sentinel subject`, `Waiver` and `Probe` are in
      and why general ML vocabulary is not

- [x] **Three R² values needed three names, and that is why this card was opened out of order.**
      The maintainer asked, in review, why three scores exist and whether two should be deleted —
      which is the question this file exists to prevent, arriving from the person who owns the
      domain. They are not three attempts at one number: `Procedure score` is a claim about a
      *method*, `Artifact score` about *one model*, `Transfer score` about *extrapolation to an
      unseen family*. Deleting two would destroy two findings (a small procedure-to-artifact gap is
      evidence of stability; a large procedure-to-transfer gap is the argument for every guard rail),
      and choosing between them after seeing all three is leak L2's shape at the reporting layer

## Runnable check

```bash
test -f CONTEXT.md && grep -c '^\*\*' CONTEXT.md      # 26 terms
```

**The check was changed, and the reason is not "it did not pass".** It counted `^### `, which
assumed one heading per term. The format this file actually uses — the one
`.claude/skills/domain-modeling/CONTEXT-FORMAT.md` prescribes — is `**Term**:` for terms with `##`
for the groups they cluster into. With 26 terms, a heading each would have produced a table of
contents longer than several of the definitions and lost the grouping that makes the R² entries
legible side by side. The check's *intent* — the file exists and has terms in it — is unchanged and
is now counted in the notation the file uses. Recorded here rather than silently edited, per
`docs/QA-PROTOCOL.md` section 5.

## Traces to

`docs/PRD-inverse-design.md` — S7

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
- 2026-09-06: Opened out of order and closed the same session, during a review. The board had it in
  S8 behind #34; it was unblocked (#20 and #28 both done) and the vocabulary problem was live. Two
  things had already been paid for by the confusion this file pins: the maintainer asking in review
  why three R² values exist and whether two should be deleted, and the five hours in which the L11
  sentinel guarded `model.final_fit` — a real, wired, working fit that had quietly stopped being the
  one that ships. `Sentinel subject` is in the glossary because of the second, and the three score
  entries because of the first. Writing this in S8, from memory, would have been strictly worse than
  writing it while the incidents were a day old. (by @assistant)
