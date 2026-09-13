---
id: 102
status: backlog
priority: Normal
blocked_by: []
assignee: "@amirhossein"
tags: [ph, l7]
---

# One decision about refusal messages lives in twenty-two modules

**Stage S8 — Evidence and close** · **L7 Naming and evidence** · Estimate: 0.5 d

> **Owns (hidden behind this module):** How this project renders a list of offenders inside a refusal sentence.

**This card is NOT an unfreeze condition.** It was found by a duplication audit on 2026-09-13 and is
filed so it has an owner. The unfreeze condition is fixed and stays fixed.

## Why this exists

This project catches bugs by **refusing with a sentence**, not by logging — there is no logging, by
design, and `docs/REFUSALS.md` is generated from the code and asserted byte-for-byte. The sentence
*is* the product. So "how do we name the offending items inside that sentence" is a design decision
with a published consequence.

It is currently taken in **twenty-two modules independently**, and it has already drifted.

| | measured 2026-09-13 |
|---|---|
| modules defining `_MAX_NAMED` | **22** |
| modules defining `_named()` | **19** |
| distinct `_named` behaviours | **four** |
| distinct truncation limits | **two** |

**The truncation limit is not uniform.** `_MAX_NAMED = 8` in twenty modules and **`= 6`** in
`hydms/gates/ac4_known_alloy_round_trip.py` and `hydms/gates/hg2_refusal_path.py`. Nothing records
why those two are different, and nothing would fail if a third became 7.

**The rendering is not uniform either**, and the differences are visible in the output:

| variant | modules | what it does |
|---|---|---|
| `sorted(map(repr, items))` | 13, incl. `data/canonical.py`, `delivery/contract.py`, `delivery/refusals.py`, `surrogate/*` | sorts, and **quotes** — `'Xx'` |
| `[str(item) for item in items]` | 3 — `descriptors/contract.py`, `descriptors/featurize.py`, `gates/ac2_featuriser_parity.py` | preserves the caller's order, **no quotes** |
| `sorted(str(code) …)` + backticks + `"none"` | 1 — `gates/hg3_transport_parity.py` | Markdown-quoted, and has an empty case the others lack |
| `_named(pairs: list[tuple[Any, str]])` | 1 — `data/load.py` | a different signature entirely, same name |

So the same offender list is quoted in one guard and bare in another, sorted in one and
caller-ordered in another, truncated at six here and eight there. A reader comparing two refusals
cannot tell whether a difference in the sentence means a difference in the *input*. That is the
failure mode [[strike-the-input-out-before-asking-if-a-sentence-names-it]] describes from the other
side, and the reason [[enumerate-the-vocabulary-when-the-prose-cannot-go-red]] had to enumerate
rather than shape-match.

`_lines()` is duplicated **verbatim** in `gates/hg2_refusal_path.py:616` and
`gates/hg3_transport_parity.py:495` — byte-identical, no variation, no reason.

## Why it is not obviously a defect, and what the real decision is

The per-module private helper is defensible: it keeps every layer free of an import edge onto a
shared utility module, and this repository has deliberately avoided a junk-drawer `hydms/utils.py`
— `hydms/` has **no** top-level module but `__init__.py`. `repr` versus `str` is a real choice too:
`repr` quotes, which is what you want when the offender is a formula string that might be empty or
carry whitespace, and is noise when it is a column name.

So the decision is **not** "de-duplicate it" but **"is this one decision or twenty-two?"** — and
if it is one, where does it live so that no layer gains a dependency it should not have.

## Done when

- [ ] **Say whether this is one decision or several, and record it.** If the `repr`/`str` split is
      deliberate, it needs a name and a rule — something like *"identifiers the user typed are
      quoted; identifiers we chose are not"* — written where the next author will read it, not
      rediscovered. `CONTEXT.md` is the place for the term
- [ ] **Resolve the two `_MAX_NAMED = 6`s.** Either they have a reason, which goes in a comment
      beside each, or they are drift and become 8. Do not leave them unexplained
- [ ] **Take `_lines()` first, because it carries no decision at all.** Two byte-identical copies in
      two gate modules; whatever home is chosen for it is the home the rest can follow, and it is
      the cheapest possible test of that choice
- [ ] **If a shared home is chosen, it is a module with a name that says what it owns** — not
      `utils`. It renders evidence inside a refusal, so it belongs beside the thing that refuses;
      `hydms/qa/` already owns detection. Resist the top-level junk drawer
- [ ] **Regenerate `docs/REFUSALS.md` and `docs/API.md` and commit the diff deliberately.** Any
      change to the rendering changes published sentences. If the diff is empty, say so — that is
      the evidence that the consolidation preserved behaviour. If it is not empty, the diff is the
      review
- [ ] **A test that would have caught the drift.** Today nothing compares two guards' rendering of
      the same list. One parametrised test over the `_named` implementations, or over the reason
      rows `refusals --emit` already walks

## Runnable check

```bash
grep -rc '^_MAX_NAMED' hydms/ --include=*.py | grep -v ':0'      # 22 modules
grep -rn -A2 'def _named(' hydms/ --include=*.py | grep 'listed ='  # the four variants
grep -rn '^_MAX_NAMED = 6' hydms/ --include=*.py                  # the two outliers
```

## Traces to

`docs/PRD-inverse-design.md` — S12. Gate HG-2 owns "never a bare number"; this card owns the
*wording* beside it. #90 (the refusal catalogue) and #77 (HG-2) are the cards whose output this
changes, and both are `done` — which is why this is a new card rather than a box on either.

## Narrative

- 2026-09-13: Found by an `ast`-level duplicate-body scan during the documentation compaction, which
  reported `_named` as identical across seven modules; reading them showed the more interesting
  result — they are *not* all identical, there are four variants and two truncation limits, and no
  document records which is intended. Filed rather than fixed: consolidating it touches nineteen
  production modules on the refusal path and two byte-asserted generated documents, which is not a
  change to make as a side effect of a documentation pass. The duplication audit found exactly one
  other code duplication (`_lines`, two verbatim copies) and, across 126 markdown files, exactly one
  duplicated prose paragraph — the per-card creation note on the 2026-08-30 board cut, which is
  per-card provenance and correctly left alone. (by @assistant)
