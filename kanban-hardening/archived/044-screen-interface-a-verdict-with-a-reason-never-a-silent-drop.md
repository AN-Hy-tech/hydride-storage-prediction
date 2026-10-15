---
id: 44
status: done
priority: High
blocked_by: [3]
assignee: "@amirhossein"
tags: [pa, l4, S3]
---

# Screen interface: a verdict with a reason, never a silent drop

**Stage S5 — Guard rails** · **L4 Screens** · Estimate: 0.5 d

> **Owns (hidden behind this module):** What it means to admit or reject a candidate.

## Why this exists

Memo 4.2 says the failure modes of this architecture must be *visible and debuggable*: you
should be able to print a candidate, its features, its prediction, its uncertainty and its
filter verdicts.

So a screen never silently removes a row. It returns a verdict and a reason, and filtering
happens afterwards, explicitly.

```python
class Screen(Protocol):
    name: str
    def verdict(self, candidates: DataFrame) -> DataFrame: ...  # passed: bool, reason: str
```

## Done when

- [x] `Screen` protocol defined with `name`, `verdict()` and a declared reason vocabulary
- [x] Verdicts are returned as columns; no screen mutates or drops rows
- [x] A composite runner applies all screens and produces one verdict table
- [x] Every rejection carries a human-readable reason string

- [x] **Screen a batch, never a candidate at a time — and the cost is measured (from #22).**
      `featurize` has a **5 ms per-call floor** that does not depend on the batch size:
      `require_self_consistent` re-audits both element tables' composite columns on every call
      (#18's guard, and it is what stops a descriptor being silently zero for Cs and Gd). That
      is 2% of a ten-thousand-candidate batch and **57% of a batch of one**, so a runner that
      loops `for candidate in candidates: featurize([candidate], ...)` costs ~200× what the
      same work costs batched — before anything is screened. `docs/BENCHMARKS.md` has the
      table. If a genuinely per-candidate path is ever needed, the audit is a pure function of
      (table, properties) and can be memoised the way #22 memoised
      `PropertyTable.servable`; nobody should do that speculatively

## Runnable check

```bash
python -m pytest tests/screens/test_protocol.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S3

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-04: Landed, **out of stage order and legitimately so** — this card is blocked only by #3,
  and S5's other two are blocked on #30. `hydms/screens/protocol.py` is the contract;
  `hydms/screens/window.py` is the worked screen; 63 tests, suite 724 green, ruff and mypy clean,
  HG-1 unchanged at 5/13 (no sentinel names this package). Five things worth carrying forward.

  - **The protocol is a promise; the runner is the enforcement.** A `Protocol` cannot make a screen
    behave, so every check lives in `apply_screens` and none of it lives in `verdict_table`. A
    screen that never calls the helper is validated identically — which matters because #48 and #49
    will each have a reason to build their frame their own way. What is refused, by name: dropping,
    adding or reordering a row; writing into the batch; a missing verdict column; a non-boolean
    `passed`; a blank reason; a code the screen never declared; and `passed` disagreeing with
    `code == ADMITTED`.
  - **Catching a mutation needed a content fingerprint, not a structural check.** A screen that
    overwrites one cell in place, or sorts the batch in place, passes every comparison of shape,
    columns and dtypes — and an in-place sort is worse than a wrong answer, because the *next*
    screen then judges a differently ordered frame and the result depends on the order the screens
    ran in. `_fingerprint` hashes with `pd.util.hash_pandas_object` and weights each row hash by its
    position, so a permutation changes the digest where a plain sum would not. It costs one O(rows)
    pass per screen, against the seconds that batch spends being featurised.
  - **The batch rule is structural, not advisory.** `verdict()` takes a frame, there is no
    single-candidate entry point, and the runner calls each screen **exactly once** whatever the
    batch size — asserted at 1, 10 and 1,000 rows by a screen that counts its own calls, which is
    deterministic where a timing assertion would be flaky. What the runner *cannot* see is a screen
    looping internally; `Verdicts.durations` and `counts()['seconds']` exist so that shows up as a
    number rather than as a surprise in S7.
  - **`passed` is redundant beside `code` and is carried anyway**, for the reason `_core.py` already
    gives for `GateResult.passed` beside `status`: a consumer reading one boolean should not have to
    know the vocabulary. The runner asserts the two agree, so the redundancy cannot drift.
  - **A screen that cannot judge rejects.** `INDETERMINATE` is a declared code, not an exception and
    not a `None` — fail-closed, because the failure mode of the other choice is a candidate reaching
    the shortlist *because* the rule meant to stop it broke. `Window` uses it for a missing or
    non-finite value, and raises instead when the whole column is absent: that is the wrong frame,
    not a fact about any candidate in it.

  **Why a window shipped with the protocol.** The blocker is the tell — a bare `Protocol` needs no
  config loader, and this card is blocked by #3. `docs/QA-PROTOCOL.md` names the obligation for this
  layer as *boundary cases on each window, both sides*, and there was no window to put boundaries on.
  `temperature_window()` reads `domain.temperature_min_k/max_k` and `columns.temperature` from
  config, so tightening it is a config change — the property #48's ceiling is required to have, now
  demonstrated once. It admits all 1,279 curated rows, which is the arithmetic check that the bounds
  really are the measured span. It is an **outer bound only**: coverage inside is uneven (~~39 test
  rows above 500 K~~ — REPORT.md's archival split; 130 of 893 scored out-of-fold rows, #99) and the module docstring says so, because the way this screen fails the thesis
  is somebody quoting it as an applicability domain.

  Boxes left elsewhere: #48 and #49 (how to declare a vocabulary and where evidence columns go),
  #75 (the refusal schema is built from `Screen.reasons`, not a hand-written list) and #76 (the
  trained-temperature bound is this screen, not a comparison re-written in the delivery layer).
