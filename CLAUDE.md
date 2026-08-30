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

| # | Source | Authoritative for | Not authoritative for |
|---|---|---|---|
| 1 | `kanban/<card>.md` | What the work *is now* — status, blockers, done-criteria, `## Narrative` | Why the project exists |
| 2 | [docs/PRD-inverse-design.md](docs/PRD-inverse-design.md) | Scope, the claim, acceptance criteria, risks, rejected alternatives | Day-to-day state |
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
| [kanban/README.md](kanban/README.md) | The board's own logic: why tickets are cut by layer not phase, the 8 layers, the 5 phases, the gate→ticket map, the critical path, the two hard gates | Starting work, picking a ticket, or wondering where a change belongs |
| [research/inverse-design-methods.md](research/inverse-design-methods.md) | Method landscape (what the hydride literature actually does), why not generative models, UQ and novelty tooling, library survey with pinned versions, Architectures A/B/C | Choosing or defending a method, or picking a library |
| [research/hydride-domain-grounding.md](research/hydride-domain-grounding.md) | DOE targets and the system-vs-material distinction, hydride families, PCT and van 't Hoff, kinetics, ML validation pitfalls, databases, DFT limits | Any physics or chemistry claim that will appear in the thesis |
| [REPORT.md](REPORT.md) | Full published methodology and results of the forward model | Writing Chapter 1, or comparing old-vs-new numbers |
| [Machine_Model/src/](Machine_Model/src/) | The 9-script pipeline that produced REPORT.md | Reading what the old pipeline did — **not** for new code |
| [graphify-out/GRAPH_REPORT.md](graphify-out/GRAPH_REPORT.md) | God nodes, communities, and surprising cross-document links | Orienting in an unfamiliar corner before reading files |

---

## Task router

| If the task is… | Read first | Use skill |
|---|---|---|
| Working a ticket | the card, then its *Traces to* PRD section | `kanban-ai` |
| Board operations (list, move, unblock) | [kanban/README.md](kanban/README.md) § Using the board | `kanban-ai` |
| "How does the existing code work?" | ask the graph (below) before opening files | `graphify` |
| Shaping a module's interface or seam | the card's *Owns* line | `software-design-philosophy`, then `codebase-design` |
| Naming, glossary, or an ADR (the `l7` cards) | PRD §8 (documentation) | `domain-modeling` |
| Hydride physics / thermodynamics / capacity | [research/hydride-domain-grounding.md](research/hydride-domain-grounding.md) | `materials-science-specialist` |
| Inverse-design method or library choice | [research/inverse-design-methods.md](research/inverse-design-methods.md) | `materials-science-specialist` |
| A fact we do not have yet | — | `research` (writes a cited memo into `research/`) |
| Stress-testing a plan or decision | — | `grill-with-docs` (leaves ADRs) or `grilling` |
| Surveying the codebase for structural debt | — | `improve-codebase-architecture` |
| Reviewing a diff | — | `/code-review` (built-in) |

**Full inventory:** `ls .claude/skills/` (project) and `ls ~/.claude/skills/` (global). The table
above covers the ones this project actually routes to; the rest are installed but idle here.

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
bash $S/show_blocked.sh kanban/          # what is waiting on what
bash $S/view_board.sh kanban/            # everything by status
bash $S/list_all_cards.sh kanban/        # id | status | blocked_by | title
```

The opening move, the two hard gates that block everything behind them, and the critical path are
in [kanban/README.md](kanban/README.md) § Start here.

---

## Session anti-patterns

- Quoting REPORT.md's scores as current performance. Three leaks; the numbers are expected to move
  down and that is a reported result, not a failure (risk R4).
- Writing a plan into this file. Write a card.
- Reading twenty files to answer a question the graph would have routed in one query.
- Moving a card to `doing` while an id in `blocked_by` is unfinished.
- Re-opening a settled decision. Generative models, descriptor inversion, Optuna-instead-of-pymoo,
  patching the old pipeline in place — all rejected with reasons in PRD §7. Bring new evidence or
  move on.
- Comparing model output to DOE targets without stating the material-vs-system distinction. It is a
  two-step overstatement (PRD §4.4).
