# HydMS — Working Brain

**A router, not a repository.** Every fact below has one owner elsewhere; this file names the owner
and never copies the value. Card ids, status, versions, counts and metrics are therefore absent by
design. **Not a planning space** — the plan is the board; write a card. If you are pasting a number
into this file, you have found the wrong file.

## The project in five lines

A Master's thesis (Shiraz University, Metallurgy & Materials). A **forward** model exists: chemical
formula + temperature → max H₂ storage capacity (wt%). The thesis extends it to the **inverse**
problem — which alloys should we make? — via an uncertainty-calibrated surrogate, physics screens,
and NSGA-II on the composition simplex. The contribution is the **guard rails**, not the optimiser:
conformal intervals, an explicit applicability domain, honest cross-family validation.
Full statement: [docs/PRD-inverse-design.md](docs/PRD-inverse-design.md) §4.

## Authority order — who wins when documents disagree

> **Phase H is running.** The repository is frozen against everything outside it and the active
> board is `kanban-hardening/`, not `kanban/`. Read [docs/FREEZE.md](docs/FREEZE.md) first.

A higher row wins **within its own subject**.

| # | Source | Authoritative for | Not for |
|---|---|---|---|
| 0 | [docs/FREEZE.md](docs/FREEZE.md) | What may be worked on at all; the unfreeze condition | What the work is |
| 1 | `kanban-hardening/<card>.md`, `kanban/<card>.md` | What the work *is now*: status, priority band, blockers, done-criteria, `## Narrative` | Why the project exists |
| 2 | [docs/PHASE-H-RUNBOOK.md](docs/PHASE-H-RUNBOOK.md) | The phase: leak inventory, stage order, gates, verification | Anything after the freeze lifts |
| 2 | [docs/PRD-inverse-design.md](docs/PRD-inverse-design.md) | Scope, claim, acceptance criteria, risks, rejected alternatives — **of the frozen programme** | Day-to-day state |
| 3 | [research/](research/) memos | Any cited fact — physics, methods, libraries, DOIs | Decisions |
| 4 | `.claude/skills/materials-science-specialist/` | Fast domain recall | Facts the memos corrected (grounding memo §5) |
| 5 | [README.md](README.md); `REPORT.md` at git tag `machine-model-archive` | The forward model **as published** | Whether those numbers are *valid* |
| 6 | `graphify-out/` | Where things are and how they connect | Ground truth; it goes stale |

**Row 5 is history, not status.** Cite REPORT.md's numbers as "as published", never as current.

## Document map

| Document | Open it when |
|---|---|
| [docs/PHASE-H-FINDINGS.md](docs/PHASE-H-FINDINGS.md) | "What is still wrong, and what next?" — every open finding by priority band |
| [kanban-hardening/README.md](kanban-hardening/README.md) | Starting work: the `▶ Next action` block, the id space, stage map, gates, board rules |
| [docs/PHASE-H-RUNBOOK.md](docs/PHASE-H-RUNBOOK.md) | Before touching the pipeline, surrogate or app: the thirteen leaks (§1), gates (§4), verification commands (§5) |
| [docs/FREEZE.md](docs/FREEZE.md) | Planning work, or CI rejected a change |
| [docs/RUNNING-THE-FIT.md](docs/RUNNING-THE-FIT.md) | Before running `hydms.surrogate.train` / `evaluate` / `loco` — operator commands, in order |
| [CONTEXT.md](CONTEXT.md) | Before writing a number or noun for readers outside the room — the glossary |
| [docs/chapter1-revision.md](docs/chapter1-revision.md) | Quoting a current number in prose (hand-written; check its evidence table) |
| [docs/archive/REPORT-RECONCILIATION.md](docs/archive/REPORT-RECONCILIATION.md) | Why the old published numbers were wrong — **archived, frozen**, never edit |
| [docs/API.md](docs/API.md), [docs/REFUSALS.md](docs/REFUSALS.md) | The HTTP contract; every refusal sentence — **generated**, never edit |
| [docs/QA-PROTOCOL.md](docs/QA-PROTOCOL.md) | Writing a card's tests; the lint lane's no-install rule (§6) |
| [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) | Touching an environment file, or a rebuild fails |
| [docs/BENCHMARKS.md](docs/BENCHMARKS.md) | Quoting a throughput number |
| [docs/LIBRARY-APIS.md](docs/LIBRARY-APIS.md) | Calling MAPIE, pymoo or CatBoost quantiles |
| [docs/adr/](docs/adr/) | Why an architectural decision went the way it did |
| [research/inverse-design-methods.md](research/inverse-design-methods.md) | Choosing or defending a method or library |
| [research/hydride-domain-grounding.md](research/hydride-domain-grounding.md) | Any physics or chemistry claim for the thesis |
| [kanban/README.md](kanban/README.md) | The frozen inverse-design programme's board logic |
| [docs/archive/](docs/archive/) | *Intent* only — handoffs and closed stages, verbatim. **Never** for current state |
| [graphify-out/GRAPH_REPORT.md](graphify-out/GRAPH_REPORT.md) | Orienting in an unfamiliar corner |

## Task router

| Task | Read first | Skill |
|---|---|---|
| **Anything, right now** | [docs/PHASE-H-FINDINGS.md](docs/PHASE-H-FINDINGS.md), then the card | `kanban-ai` |
| Board operations | [kanban-hardening/README.md](kanban-hardening/README.md) § Using the board | `kanban-ai` |
| Training or fitting | runbook §1 (leaks), then RUNNING-THE-FIT | `ml-model-training` — see caveat |
| The API or the app | the card's *Owns* line | `backend-development`, `codebase-design`, `dataviz` |
| How existing code works | the graph (below) | `graphify` |
| A module's interface or seam | the card's *Owns* line | `software-design-philosophy`, `codebase-design` |
| Naming, glossary, ADRs | [CONTEXT.md](CONTEXT.md), PRD §8 | `domain-modeling` |
| Hydride physics, or inverse-design methods | the two `research/` memos | `materials-science-specialist` |
| A fact we do not have | — | `research` |
| Stress-testing a decision | — | `grilling`, `grill-with-docs` |
| Structural debt | — | `improve-codebase-architecture` |
| Reviewing a diff | — | `/code-review` |

**The three ML skills** (`ml-model-training`, `ml-fundamentals`, `ml-model-trainer`) are fine for
fitting mechanics only: all are silent on group-aware splits, nested CV and early stopping on the
scoring set, so following them reintroduces leaks L4, L7, L8. On validation, the runbook wins.
**`/ask-matt`** routes to skills not installed here; enter its flow at implementation.

## Ask the graph before you grep

```bash
PY="C:/Python313/python.exe"                 # graphify's own interpreter — NOT the project env
"$PY" -m graphify query "how does feature selection choose the final descriptor set?"
"$PY" -m graphify path "22 Selected Features" "Constrained Multi-Objective EA (Architecture B)"
"$PY" -m graphify explain "22 Selected Features"
```

A hit is a pointer to verify, never the answer. Freshness: `graphify-out/cost.json`; refresh with
`/graphify . --update`.

## Invariants

- **The enabling fact.** Every selected feature is a composition statistic or temperature, so a
  candidate is featurised by a *forward* call and descriptors are **never inverted** (PRD §2.3). If
  that stops being true, the plan changes.
- **Interpreter:** the conda env `Project`, **not** `C:\Python313` (a different NumPy major). Pins:
  [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md).
- **Two code trees.** New work is in `hydms/`. `Machine_Model/src/` is the archival record behind
  REPORT.md and is never rewritten (PRD §7.2).
- **The promoted model is on one machine.** `artifacts/` is gitignored, so a fresh clone has no
  model and the service refuses to start (#7).
- **Grouping uses the canonical composition key**, `hydms.data.canonical.group_keys`, called and
  never re-derived — formula strings collide (runbook §1, leak L8).
- **A prediction without an interval and a domain verdict is not a deliverable** — gate HG-2 makes
  the result type unconstructible without them.
- **The evaluator is the deep module; search is a seam.** Architectures A and B differ only in how
  candidates are proposed and selected; duplicated evaluation is the mistake
  ([kanban/README.md](kanban/README.md) § Why tickets are cut by layer).
- **Gates are executable:** `python -m hydms.gates list`; frozen AC cards via
  `bash .claude/skills/kanban-ai/scripts/search_by_tag.sh kanban/ AC-3`.
- **Rank on the lower confidence bound, never the mean** (risk R1); publish no candidate without an
  ElMD distance and an interval width (AC-7).
- **Narrative is the paper trail.** Append what a card teaches you to its `## Narrative`.

## Session anti-patterns

- Quoting REPORT.md's scores as current. They are expected to fall (risk R4); the evidence is
  [docs/archive/REPORT-RECONCILIATION.md](docs/archive/REPORT-RECONCILIATION.md).
- Working the frozen board, or editing the PRD, `research/`, `REPORT.md` or `Machine_Model/`.
- Moving a card to `doing` while a `blocked_by` id is unfinished.
- Re-opening a decision PRD §7 settled (generative models, descriptor inversion,
  Optuna-for-pymoo, patching the old pipeline) without new evidence.
- Comparing model output to a DOE target without stating material vs system (PRD §4.4).
- Hand-editing a generated file. Change the code and regenerate with its `--emit`; a test asserts
  the committed bytes.
- Believing `scripts/check_board.py` reads checkboxes. It does not (#68); the findings index exists
  because nothing does.
- Letting a document grow a log. The `▶` block holds one handoff, `CONTEXT.md` holds definitions
  only, and closed detail moves verbatim to `docs/archive/`.
- Quoting a suite count without its command: the full run and the fast lane (`-m "not slow"`)
  differ (runbook §5).
