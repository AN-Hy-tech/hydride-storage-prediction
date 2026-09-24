# HydMS — Working Brain

**This file is a router, not a repository.** It holds no facts that live somewhere else. Its job is
to get you to the right document and the right skill in one hop, so a session spends its context on
the work instead of rediscovering the project.

**It is not a planning space.** The plan is [kanban/](kanban/). If you find yourself wanting to write
a plan here, write a card instead.

**How it stays true.** Every fact below has exactly one owner elsewhere, and this file names the
owner rather than copying the value. Card ids, ticket status, version pins, counts and metrics are
therefore absent by design — they are looked up, never restated, because a copy here drifts
silently and no test catches it. If you catch yourself pasting a number into this file, you have
found the wrong file.

---

## The project in five lines

A Master's thesis (Shiraz University, Metallurgy & Materials). A **forward** model exists: chemical
formula + temperature → max H₂ storage capacity (wt%). The thesis extends it to the **inverse**
problem — which alloys should we make? — via an uncertainty-calibrated surrogate, physics screens,
and NSGA-II on the composition simplex. The contribution is not the optimiser (the literature has
those) but the **guard rails**: conformal intervals, an explicit applicability domain, and honest
cross-family validation. Full statement: [docs/PRD-inverse-design.md](docs/PRD-inverse-design.md) §4.

---

## Authority order — who wins when documents disagree

Read top-down. A higher row overrides a lower one **within its own subject**.

> **Phase H is running.** An emergency hardening phase has the board and the repository frozen
> against everything outside it. Read [docs/FREEZE.md](docs/FREEZE.md) before you plan any work — CI
> will reject a change outside the allowed paths, and the active board is `kanban-hardening/`, not
> `kanban/`.

| # | Source | Authoritative for | Not authoritative for |
|---|---|---|---|
| 0 | [docs/FREEZE.md](docs/FREEZE.md) | What may be worked on at all right now, and the unfreeze condition | What the work is |
| 1 | `kanban-hardening/<card>.md`, `kanban/<card>.md` | What the work *is now* — status, blockers, done-criteria, `## Narrative` | Why the project exists |
| 2 | [docs/PHASE-H-RUNBOOK.md](docs/PHASE-H-RUNBOOK.md) | The current phase: the leak inventory, the stage order, the HG gates | Anything after the freeze lifts |
| 2 | [docs/PRD-inverse-design.md](docs/PRD-inverse-design.md) | Scope, the claim, acceptance criteria, risks, rejected alternatives — **of the frozen programme** | Day-to-day state; the current phase |
| 3 | [research/](research/) memos | Any cited fact — physics, methods, libraries, DOIs | Decisions (the PRD decides) |
| 4 | `.claude/skills/materials-science-specialist/` | Fast domain recall | Facts the memos corrected — see grounding memo §5 |
| 5 | [REPORT.md](REPORT.md), [README.md](README.md) | The archival record of the forward model **as published** | Whether those numbers are *valid* — PRD §2.2 names three leaks |
| 6 | `graphify-out/` | Where things are and how they connect | Ground truth; it is a derived index and goes stale |

The one that catches people: **row 5 is history, not status.** REPORT.md's numbers were produced by a
pipeline with known validation leaks and no artifacts on disk. Cite them as "as published", never as
current performance.

---

## Document map

| Document | Owns | Open it when |
|---|---|---|
| [docs/PRD-inverse-design.md](docs/PRD-inverse-design.md) | The whole proposal: audit findings (§2.2), the enabling fact (§2.3), the claim (§4), user stories S1–S12 (§5), rejected alternatives (§7), risks R1–R7 (§9), acceptance criteria AC-1–AC-8 (§10) | Before any design argument, and whenever a card's *Traces to* names an S or AC |
| [kanban-hardening/README.md](kanban-hardening/README.md) | The **active** board: the `▶ Next action` block, the two-directory id space, the stage→card map, the eight gates, how to start | Starting any work at all right now |
| [docs/PHASE-H-RUNBOOK.md](docs/PHASE-H-RUNBOOK.md) | The current phase end to end: why it exists, the thirteen leaks with their exact sites, the **live** stages (S7, S8), the gate table, the verification block | Before touching the pipeline, the surrogate, or the app |
| [docs/PHASE-H-FINDINGS.md](docs/PHASE-H-FINDINGS.md) | **Every open finding in priority order**, P1–P4, as one line and a pointer each — including the ones invisible to every tool here, the unticked boxes on `done` cards | Deciding what to work on, or asking "what is still wrong?" |
| [docs/archive/](docs/archive/) | The phase's history, verbatim and uncorrected: the full handoff log back to 2026-09-03, and stages S0–S6 in the detail the runbook used to carry | You need *intent* — why a decision went the way it did. **Never** for current state |
| [docs/FREEZE.md](docs/FREEZE.md) | What is frozen, the denied paths, the unfreeze condition | Before planning work, or when CI rejects a change |
| [docs/RUNNING-THE-FIT.md](docs/RUNNING-THE-FIT.md) | How to actually execute the training run and the evaluation: the commands, in order, with what each prints, the exit codes, and how to commit the result | Before running `hydms.surrogate.train` or `hydms.surrogate.evaluate` — it is written for an operator, not a reader |
| [CONTEXT.md](CONTEXT.md) | The project's **vocabulary**, glossary only. A term is in it because conflating it has already cost this project something: the three score readings, `Deployed fit`, `Sentinel subject`, `Probe`, the capacity levels | Before writing a number or a noun into prose somebody outside the room will read |
| [kanban/README.md](kanban/README.md) | The **frozen** board's logic: why tickets are cut by layer not phase, the 8 layers, the 5 phases, the gate→ticket map, the critical path | Understanding the inverse-design programme that resumes later |
| [research/inverse-design-methods.md](research/inverse-design-methods.md) | Method landscape (what the hydride literature actually does), why not generative models, UQ and novelty tooling, library survey with pinned versions, Architectures A/B/C | Choosing or defending a method, or picking a library |
| [research/hydride-domain-grounding.md](research/hydride-domain-grounding.md) | DOE targets and the system-vs-material distinction, hydride families, PCT and van 't Hoff, kinetics, ML validation pitfalls, databases, DFT limits | Any physics or chemistry claim that will appear in the thesis |
| [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) | Which interpreter, why 3.13 is excluded, the two-stage rebuild, and the export defects that bite on re-export | Before touching any environment file, or when a rebuild fails |
| [docs/BENCHMARKS.md](docs/BENCHMARKS.md) | Featurisation throughput: the batch-size curve with its machine, the parse-versus-arithmetic split, what it does and does not license about R6, and the 13x hot spot card #22 found | Before quoting a candidates-per-second number, or arguing about enumeration versus evolution |
| [docs/LIBRARY-APIS.md](docs/LIBRARY-APIS.md) | How the committed-to libraries are actually called — MAPIE, pymoo, CatBoost quantiles — with the version floors they imply | Before implementing against a library nobody here has run yet |
| [docs/REFUSALS.md](docs/REFUSALS.md) | Every sentence the delivery path can produce when it declines to answer — one row per probe, input → code → reason — plus the codes it declares but no request can reach | Before changing a screen's wording or adding a reason code. It is **generated** (`hydms.delivery.refusals --emit`), so regenerate it; never edit it |
| [docs/API.md](docs/API.md) | The published HTTP contract a client author reads: every route, the answer and refusal bodies, the batch limit, worked examples stamped with the artifact version that produced them | Before calling the service, or changing a route. It is **generated** (`hydms.delivery.apidoc --emit`, examples from `--probe`); never edit it |
| [docs/QA-PROTOCOL.md](docs/QA-PROTOCOL.md) | What must be tested at each layer, and the lint lane's no-install rule (§6) | Before writing a card's tests, or arguing about what `done` requires |
| [docs/REPORT-RECONCILIATION.md](docs/REPORT-RECONCILIATION.md) | Every place `REPORT.md` and a committed CSV disagree, which to believe and why, and the honest numbers beside the published ones. **Generated** (`hydms.evidence.reconciliation --emit`); never edit | Before quoting any REPORT.md number, and before writing Chapter 1 (#37 is written from it) |
| [REPORT.md](REPORT.md) | Full published methodology and results of the forward model | Writing Chapter 1, or comparing old-vs-new numbers |
| [Machine_Model/src/](Machine_Model/src/) | The 9-script pipeline that produced REPORT.md | Reading what the old pipeline did — **not** for new code |
| [graphify-out/GRAPH_REPORT.md](graphify-out/GRAPH_REPORT.md) | God nodes, communities, and surprising cross-document links | Orienting in an unfamiliar corner before reading files |

---

## Task router

| If the task is… | Read first | Use skill |
|---|---|---|
| **Anything at all, right now** | [docs/FREEZE.md](docs/FREEZE.md), then [docs/PHASE-H-RUNBOOK.md](docs/PHASE-H-RUNBOOK.md) | — |
| **"What is still broken, and what should I take?"** | [docs/PHASE-H-FINDINGS.md](docs/PHASE-H-FINDINGS.md), then the card | `kanban-ai` |
| Working a ticket | the card, then its *Traces to* section | `kanban-ai` |
| Board operations (list, move, unblock) | [kanban-hardening/README.md](kanban-hardening/README.md) § Using the board | `kanban-ai` |
| Training or fitting a model | [docs/PHASE-H-RUNBOOK.md](docs/PHASE-H-RUNBOOK.md) §1 — the leak inventory first | `ml-model-training`, but see the caveat below |
| The prediction API or the app | the card's *Owns* line | `backend-development`, `codebase-design`, `dataviz` |
| "How does the existing code work?" | ask the graph (below) before opening files | `graphify` |
| Shaping a module's interface or seam | the card's *Owns* line | `software-design-philosophy`, then `codebase-design` |
| Naming, glossary, or an ADR (the `l7` cards) | [CONTEXT.md](CONTEXT.md) first, then PRD §8 | `domain-modeling` |
| Hydride physics / thermodynamics / capacity | [research/hydride-domain-grounding.md](research/hydride-domain-grounding.md) | `materials-science-specialist` |
| Inverse-design method or library choice | [research/inverse-design-methods.md](research/inverse-design-methods.md) | `materials-science-specialist` |
| A fact we do not have yet | — | `research` (writes a cited memo into `research/`) |
| Stress-testing a plan or decision | — | `grill-with-docs` (leaves ADRs) or `grilling` |
| Surveying the codebase for structural debt | — | `improve-codebase-architecture` |
| Reviewing a diff | — | `/code-review` (built-in) |

**Full inventory:** `ls .claude/skills/` (project) and `ls ~/.claude/skills/` (global). The table
above covers the ones this project actually routes to; the rest are installed but idle here.

**Caveat on the three ML skills — `ml-model-training`, `ml-fundamentals`, `ml-model-trainer`.**
All three are installed and all three are fine for model-fitting *mechanics* and nothing more. Every
one of them is **silent** on group-aware splitting, nested cross-validation, and early stopping on
the scoring set. `ml-model-training`'s worked example is a plain `train_test_split` with no
`random_state` and no grouping; `ml-fundamentals` offers `train_test_split(stratify=y)` and
`cross_val_score(cv=5)`, and lists `GroupKFold` in a table without ever using it;
`ml-model-trainer` is prose about "selecting a suitable algorithm" with no code at all. Following
any of them here would reintroduce leaks L4, L7 and L8. Authority row 4 applies: on any validation
question the [research/](research/) memos and [docs/PHASE-H-RUNBOOK.md](docs/PHASE-H-RUNBOOK.md)
win. Audited 2026-09-05 against the live pipeline — they raised **no finding this repository had not
already guarded**, so treat them as a checklist to be exceeded, never as a source of method.

**Caveat on `/ask-matt`.** It routes over a skill set this repo does not have: `/to-spec`,
`/to-tickets`, `/implement`, `/tdd`, `/handoff`, `/wayfinder`, `/triage` and `/diagnosing-bugs` are
**not installed**. Its idea → spec → tickets stage has already happened here — the PRD is the spec
and `kanban/` is the tickets — so enter its flow at implementation, not at the top.

---

## Ask the graph before you grep

The corpus is far too large to sweep. A graph query costs a fraction of a search and surfaces
cross-document links a grep cannot; the corpus and community counts are in `GRAPH_REPORT.md`.

```bash
PY="C:/Python313/python.exe"                 # graphify's own interpreter — NOT the project env
"$PY" -m graphify query "how does feature selection choose the final descriptor set?"
"$PY" -m graphify path "22 Selected Features" "Constrained Multi-Objective EA (Architecture B)"
"$PY" -m graphify explain "22 Selected Features"
```

The graph is only as fresh as its last build — check `graphify-out/cost.json` for that date. If it
predates a directory you care about, the graph has never seen it. Treat a hit as a pointer to verify
in the file, never as the answer; refresh with `/graphify . --update`.

---

## Invariants

Things that are true across every session, and expensive to rediscover.

- **The enabling fact.** Every selected feature is a composition statistic or temperature — no
  structural descriptor survived selection. So a candidate is featurised by a *forward* function
  call and the descriptors are **never inverted**. The entire inverse-design plan rests on this
  (PRD §2.3). If it ever stops being true, the plan changes. (Re-running selection may change *how
  many* features there are; it must not change this property.)
- **Interpreter.** The published results were produced under the conda env `Project`, **not** the
  machine default `C:\Python313` — a different NumPy major that breaks on removed 2.0 aliases.
  Versions are pinned by the `l0` environment card into `docs/ENVIRONMENT.md`; until that lands,
  `conda env export -n Project` is the source of truth.
- **Two code trees.** New work goes in `hydms/` (not yet scaffolded). `Machine_Model/src/` is the
  archival record behind REPORT.md and is **not** rewritten — rewriting it orphans every published
  number (PRD §7.2).
- **Nothing is trained.** No model, scaler or split is on disk. Any instruction to "load the model"
  means "re-run the pipeline first".
- **Two rows describe the same material more often than the formula string admits.** 1,149 distinct
  formula strings collapse to 1,115 canonical compositions. Grouping — for splits, for folds, for
  anything — uses the canonical key, never the raw string, and the key is
  `hydms.data.canonical.group_keys`, called rather than re-derived. Reasoning and the measured
  collision count: [docs/PHASE-H-RUNBOOK.md](docs/PHASE-H-RUNBOOK.md) §1, leak L8; the resolution the
  key rounds to, and why, is that module's docstring.
- **A prediction without an interval and a domain verdict is not a deliverable.** Gate HG-2 makes that
  structural: the result type cannot be constructed without them.
- **The evaluator is the deep module; search is a seam.** Architectures A and B differ only in how
  candidates are *proposed* and *selected* — everything between is one shared evaluation path. Code
  that duplicates evaluation per architecture is the mistake the whole board is shaped to prevent.
  Reasoning: [kanban/README.md](kanban/README.md) § Why tickets are cut by layer.
- **Gates are executable.** AC-1 through AC-8 are cards run by CI, not remembered. Find the card for
  any criterion with `bash .claude/skills/kanban-ai/scripts/search_by_tag.sh kanban/ AC-3`; the full
  gate→card map is in [kanban/README.md](kanban/README.md).
- **Ranking uses the lower confidence bound, never the mean** — that is what stops the optimiser
  exploiting extrapolation (risk R1). No candidate is published without both an ElMD distance and an
  interval width (AC-7).
- **Narrative is the paper trail.** When a card teaches you something, append to its `## Narrative`.
  The ADRs and the Chapter 1 revision are written from those notes.

---

## Where to start when the board is cold

Ask the board. Do not trust a list written here — it goes stale the moment a card moves.

```bash
S=.claude/skills/kanban-ai/scripts
bash $S/show_blocked.sh kanban-hardening/     # what is waiting on what
bash $S/view_board.sh kanban-hardening/       # everything by status
bash $S/list_all_cards.sh kanban-hardening/   # id | status | blocked_by | title
```

`kanban-hardening/` is the active board. `kanban/` is frozen and every card in it must stay
`backlog` — `scripts/check_board.py` fails the build otherwise. The stage order is in
[docs/PHASE-H-RUNBOOK.md](docs/PHASE-H-RUNBOOK.md) §2; the opening move and the two hard gates are in
[kanban-hardening/README.md](kanban-hardening/README.md) § Start here.

---

## Session anti-patterns

- Quoting REPORT.md's scores as current performance. Thirteen leaks, and CSVs committed in this
  repository already contradict the headline numbers; they are expected to move down and that is a
  reported result, not a failure (risk R4). The evidence table is
  [docs/REPORT-RECONCILIATION.md](docs/REPORT-RECONCILIATION.md) (#89): every place the report and
  a committed CSV disagree, with the honest numbers beside the published ones. It is generated
  (`hydms.evidence.reconciliation --emit`), so it is regenerated, never edited.
- Working a card on the frozen board, or editing the PRD, `research/`, `REPORT.md` or
  `Machine_Model/` while the freeze holds. CI rejects it; [docs/FREEZE.md](docs/FREEZE.md) says why.
- Writing a plan into this file. Write a card.
- Reading twenty files to answer a question the graph would have routed in one query.
- Moving a card to `doing` while an id in `blocked_by` is unfinished.
- Re-opening a settled decision. Generative models, descriptor inversion, Optuna-instead-of-pymoo,
  patching the old pipeline in place — all rejected with reasons in PRD §7. Bring new evidence or
  move on.
- Comparing model output to DOE targets without stating the material-vs-system distinction. It is a
  two-step overstatement (PRD §4.4).
- Hand-editing a generated file. `docs/REFUSALS.md`, the LOCO write-up, the two screen reference
  JSONs and the smoke fixture are each rebuilt by an `--emit` flag, and a test asserts the committed
  bytes are what the code produces. Change the code and regenerate; an edit there fails the suite
  and, worse, is the exact drift those files exist to prevent.
- Believing `scripts/check_board.py` rejects a `done` card with an unticked box. **It does not** —
  it reads frontmatter and links, never a `- [ ]` (#68, 2026-09-13). The convention is real and
  worth keeping, but it is enforced by readers, which is why
  [docs/PHASE-H-FINDINGS.md](docs/PHASE-H-FINDINGS.md) exists. Two cards were filed on the belief
  that the checker would catch it.
- Landing a card without grepping [CONTEXT.md](CONTEXT.md) for its number. The glossary's *"State
  of the term"* blocks name cards by id, and **nothing reads that file** — no test, no gate, no
  `--emit`. When the card closes, the tense stays wrong and no diff goes red. Closing #76 left
  "the domain-verdict half is not built yet (cards #48, #49, #75, #76)" standing after all four
  were `done`.
- Quoting a suite count without saying which command produced it. The full run and the fast lane
  (`-m "not slow"`) differ by the four slow tests; the runbook §5 keeps both, labelled.
