# The hardening board — Phase H

**This is the active board.** [../kanban/](../kanban/) is frozen; see [../docs/FREEZE.md](../docs/FREEZE.md).

> ## ▶ Next action — as of 2026-09-25 evening (#98 `done`; #104 filed)
>
> **Handoff, one line: #98 is `done`: the full LOACO run landed and `reports/loco/loco-out-of-fold.csv`
> is committed. Next, in the maintainer's order, are #83 and #84. The run also filed #104, and
> whether #104 jumps that queue is OPEN.**
>
> **What landed.** The run took 288.4 min (4 h 48 m, so budget five hours). It exited 0 with
> five `wrote` lines and 893 scored rows. AC-6 passes at macro **0.2559** against the random
> split's 0.7459. The figures test on the committed rows now **runs** instead of skipping. #83's
> parity panel has its data, so nothing blocks it but the page itself.
>
> **What it found: #104.** The seeded tables did not come back unchanged. Seven families are
> identical to every digit, and three moved: Mg −0.3381 → **−0.5084**, MEA 0.1135 → 0.0933,
> SS 0.7626 → 0.7780. The macro average went 0.2734 → 0.2559. Nothing in the fit path changed
> between the two runs. Mg's search picked a different configuration; MEA and SS picked the
> *same* one and still scored differently. AC-1 covers only the deployed fit, so no gate could
> see this. The run was committed as it came back, per #98's box. Every generated consumer was
> regenerated from it: the domain reference, `docs/REFUSALS.md`, `docs/REPORT-RECONCILIATION.md`,
> and `docs/API.md` (`--probe` against `v3`, where only the three transfers, the reference digest
> and the capture time moved). The hand-written text was updated too: the Chapter 1 transfer
> table, plus a new paragraph stating both runs that **the author owes a read**. **No refusal
> verdict moved:** Mg and HEA are below `min_transfer_r2` in both runs.
>
> **Restart the service** before demonstrating it. The uvicorn process running on port 80
> loaded the old domain reference, so it still quotes Mg at −0.338.
>
> **OPEN, the maintainer's call: does #104 go before #83/#84?** It is P1 by
> [../docs/PHASE-H-FINDINGS.md](../docs/PHASE-H-FINDINGS.md)'s rule, because it makes a published
> number (the thesis's transfer score) a single draw from a spread nobody has sized. Its first
> step is cheap: two `loco --trials 1 --no-screening --report <scratch>` probes (~12 min each),
> diffed, then the same pair with screening on. That fits beside either card and is not a
> heavy fit. If the fix changes the numbers, the maintainer reruns LOACO and the regeneration
> chain in `docs/RUNNING-THE-FIT.md` Step 10 follows.
>
> **For #83:** caption the LOACO parity panel with its run date. It shows one run's rows, and
> #104 says a second run gives different ones.
>
> *Below: the block from when #98's review fixes landed. Carried out.*
>
> **(2026-09-25, #98's review fixes landed)** **Handoff, one line: #98's four review fixes are committed and its fixes box is ticked, so the
> maintainer starts the full LOACO run with the command in #98's last box (~4 h; the last took
> 4 h 07 m), then commits `reports/loco/` by name. #84 is startable meanwhile; #83 builds but its
> parity box waits on the file.**
>
> **How to read the run's exit, corrected by one.** Exit 0 with **five** `wrote` lines is
> success. Exit 1 with **four** `wrote` lines and no traceback is a withheld per-row table (the
> earlier block below said "five"; a withheld run writes only the four AC-6 tables, and a test now
> pins the count). Exit 1 with a traceback is a crash. A withheld run also **deletes** any
> `loco-out-of-fold.csv` already in the destination, and says so. The committed-evidence test
> now refuses the file when `loco-run.csv` records `probe` true, so **do not commit a probe's
> rows** — a `--trials` run without `--report` writes into `reports/loco/`.
>
> *Below: the block that asked for the fixes. Carried out; its wording "five `wrote` lines" is
> superseded above.*
>
> **(2026-09-25, #98 reviewed)** **Handoff: land #98's four review fixes first; the maintainer runs LOACO only after they are
> committed.** (1) **A withheld write leaves a stale per-row file** — confirmed by running it: a
> complete run then a short-record run into one directory exits 1 and leaves the first run's
> `loco-out-of-fold.csv` byte-identical beside the new per-class tables, and the committed-evidence
> test still passes because both score 893 rows; on withholding, `main` must unlink
> `<destination>/loco-out-of-fold.csv` and say so on stderr (`hydms/surrogate/loco.py`, the
> `try`/`except` before `_write`), with a test that seeds a stale file first. (2) **Exit 1 is
> ambiguous** — an uncaught traceback is also 1, so reword #98's run box and
> `docs/RUNNING-THE-FIT.md` Step 10 to "exit 1 with five `wrote` lines and no traceback"; keep the
> code, it matches `gates` and `smoke`. (3) **A probe's rows pass as a result** — a `--trials 1`
> run without `--report` writes `reports/loco/loco-out-of-fold.csv` with no probe mark, so
> `tests/test_figures.py::test_the_committed_loco_run_keeps_every_scored_row` must also assert
> `loco-run.csv` has `probe` false, and `parity()`'s message in `hydms/figures/charts.py` must stop
> saying "only a full run writes" it. (4) **Count per fold, not per model** in `loco.out_of_fold()`
> — group `table` by `fold` against `kept["fold"]`, so a fold kept twice cannot mask one never kept;
> a test for exactly that. Then the fast lane, commit, push, tick #98's fixes box, and hand the
> maintainer the run command already in #98's last box; #84 is startable meanwhile.
>
> *Below: the earlier block, written when #98's code landed. Its facts stand; its run instruction
> now waits on the fixes above.*
>
> **(2026-09-25, #98's code landed)** **Handoff, one line: #98 is `doing` with its code landed and verified at probe budget; its
> last box is the full LOACO run (~4 h, the last took 4 h 07 m), which the maintainer runs with
> the command in #98's last box — then commit `reports/loco/` by name. #83 and #84 next.**
>
> **What landed.** `hydms.surrogate.loco` now writes `loco-out-of-fold.csv`, one row per scored
> training row — the same columns and the same 893 row labels as `model-out-of-fold.csv` — so
> `parity()` can draw both protocols. It stays outside the four tables `--emit` reads, so
> `loco.md` does not move. A short record is refused with exit 1, and the four AC-6 tables are
> written anyway, so a four-hour run is never lost to it. The probe (1 trial, no screening) ran
> 12.3 min and built both parity panels, 893 beside 893. **The rerun overwrites the four
> committed tables; being seeded, they should come back unchanged** — if `git diff --stat
> reports/loco/` shows any of them moved, that is an AC-1 finding to record on #98, not a
> reason to discard the run.
>
> **While the run is out, #84 is startable** (it does not read `reports/loco/`). #83 can be
> built, but its parity box stays open until the file is committed.
>
> *Below: the earlier block from after the #100 full run. Its pointer to #98 is now carried out.*
>
> **(2026-09-25, after the #100 full run)** **Handoff, one line: the full run #100 asked for is green — 1650 passed, 0 failed, 1 h 15 m 4 s,
> quiet machine, no failure record — so #100 stays `doing` with nothing to fix; (2) #98 is next when
> the maintainer assigns it.** Budget well over an hour for any future full run, not the ~29 min the
> older blocks quote.
>
> *Below: the earlier block from after the #100 session. Its instruction has now been carried out.*
>
> **(2026-09-25, #100 session)** **Handoff, one line: #100 stays `doing` (maintainer's ruling) — run
> the full `pytest` (no `-m`) on a quiet machine, and if it goes red, fix the render test from the
> traceback now saved in `reports/test-failures/`; otherwise go on to (2) #98.**
>
> *Below: the earlier 2026-09-25 block, written when #82 closed. Its pointer to #98 still holds.*
>
> **(2026-09-25, #82)**
>
> **Handoff, one line: #82 is `done` — the Streamlit page ran end to end under `Project` — so
> (2) #98's code is next, then its ~4.7 h LOACO run, which the maintainer runs; #83 and #84 are
> unblocked behind it.**
>
> **How #82 closed.** Streamlit 1.56.0 is installed in `Project` and nothing locked moved.
> `tests/delivery/test_app_script.py` drives the real `app/main.py` through Streamlit's `AppTest`
> against a live service: 40 passed with `test_app.py`, 0 skipped, on Python 3.10.13. **Two
> things to know.** CI does not install the `app` extra, so that file runs only where the pin is
> installed. And **any command you hand over names `Project`'s `python.exe` in full**: a bare
> `PY` is the Windows `py` launcher (Python 3.13), which is where the first install went.
>
> **#84 is unblocked outright.** #83 is unblocked, but its parity panel still needs #98's
> out-of-fold rows. That is why the maintainer's order puts #98 first.
>
> *Below: the 2026-09-24 night block, superseded on #82.*
>
> **(2026-09-24 night)**
>
> **Handoff, one line: #82's two API additions and its Streamlit pin have landed; the card
> closes when the maintainer runs `app/main.py` once against `v3` (the commands are in #82's
> last box), then it is (2) #98.**
>
> **What landed.** `GET /v1/neighbours?formula=…&k=…` serves the k nearest known alloys with
> every training row measured on them. It is a lookup, not a prediction: `"basis": "measured"`,
> no interval, and a bad query is an *invalid request*, never a refusal. `GET /v1/model` now
> carries `trained_ranges.temperature_support`: training rows per 50 K bin, the same 893 rows as
> the capacity range. Both come from the committed screen references (`novelty-reference.json`,
> `domain-reference.json`), not the artifact, so `v3` serves them unchanged. `openapi.json` gained
> 94 pointers, all additions. `docs/API.md` was re-probed against `v3`: every earlier exchange is
> byte-identical, and the model card's two reference digests moved. The page model draws both
> (`page.neighbours_figure`, `page.sweep_view`). **Streamlit is pinned at 1.56.0** (`app` extra
> `>=1.40,<1.57`). 1.57 is the first release that needs `starlette>=0.40`, and installing 1.56.0
> changes no locked package. The screen is in `docs/ENVIRONMENT.md`.
>
> **The order the maintainer set is unchanged past step 1:** (2) #98's code, then its ~4.7 h
> LOACO run. (3) #83 and #84, which #82 unblocks. (4) Triage, then lift.
>
> *Below: the 2026-09-24 close-of-day block, superseded on #82.*
>
> **(2026-09-24 close of day)**
>
> **Handoff, one line: #37 is `done` and the freeze is held by the maintainer until S7 is finished,
> so start #82's two API contract changes (a nearest-measured-alloys route, and per-bin temperature
> support on `GET /v1/model`; each needs `openapi.json`, `docs/API.md --probe` against v3, and
> HG-3), then ask the maintainer for the Streamlit pin.**
>
> **The order the maintainer set:** (1) #82: the nearest-alloys route and per-bin temperature
> support, then the Streamlit pin (the maintainer's lock decision). (2) #98's code, then its
> ~4.7 h LOACO run, which the maintainer runs. (3) #83 and #84. (4) Triage the remaining findings
> (#91, #92, #94–#96, #99–#102, #36, #7) as must fix, carry over, or drop, then lift. **After
> Phase H,** the maintainer wants to work on the width of the uncertainty band and re-test the
> Miedema descriptors (#37's future-work list, items 1 onward). That is a new artifact version,
> v4, reported beside v3 and never in its place.
>
> *Below: the 2026-09-24 late-night block, superseded on #37.*
>
> **(2026-09-24 late night)**
>
> **Handoff, one line: #37 has every box ticked and waits only on the author's read of
> [../docs/chapter1-revision.md](../docs/chapter1-revision.md). After that, #37 → `done`, lift the
> freeze per [../docs/FREEZE.md](../docs/FREEZE.md), then the two API additions for #82.**
>
> **#103 is `done`**, filed by the maintainer's decision. It is a card of its own, not #83's box
> and not #37's. `hydms/evidence/artifact_score.py` copies the AC-1/AC-3 records out of the sealed
> `v3` manifest into `reports/model/artifact-gates.json` (`--probe`, which needs `artifacts/`) and
> tabulates them in `reports/model/artifact-score.csv` (`--emit`, byte-checked in CI). It
> **re-scores nothing**, because AC-3 is the only reader of the test split. It refuses unless AC-1's
> refit coverage matches AC-3's stored-model coverage. #83's box now only *shows* the number. The
> chapter's † markers are gone. **After any future promotion, run `--probe --emit`**; a local-only
> test goes red until you do.
>
> *Below: the 2026-09-24 night block, superseded on #37.*
>
> **(2026-09-24 night)**
>
> **Handoff, one line: #37 is drafted ([../docs/chapter1-revision.md](../docs/chapter1-revision.md))
> and `doing` on one box: three numbers trace only to the gitignored `artifacts/`. Committing them
> is a few minutes and no fit. The only question is which card owns it.**
>
> **What is open on #37, exactly.** The draft cites committed files for everything except the
> **artifact score** (R² 0.7071, RMSE 0.5420, MAE 0.3117 on 254 test rows, gate AC-1) and the
> **test coverage** (0.7795, width 0.8630 wt%, gate AC-3). Those live in
> `artifacts/v3/manifest.json` and are marked † in the chapter. Publishing them is already a box on
> **#83**, but #83 is blocked behind #82's Streamlit pin. That would chain the last unfreeze bullet
> to a lock decision it has nothing to do with. **OPEN, the maintainer's call:** file a small card
> that writes the AC-1/AC-3 metrics to a committed `reports/model/` table, move #83's box to it,
> then tick #37's box 5. Do **not** tick it by rewording the criterion. The author also owes the
> prose a read: it is thesis text, and the `1.R.x` numbering is a placeholder.
>
> **Watch for:** `reports/model/conformal-coverage.csv` reports R² 0.8255 and coverage 0.8081. Those
> are over the 172 **calibration** rows, not the test rows. They are not the artifact score.
>
> **After that, unchanged from the block below:** the two API additions for #82, then the Streamlit
> pin once the maintainer picks one.
>
> *Below: the 2026-09-24 evening block, superseded on #37.*
>
> **(2026-09-24 evening) Handoff, one line: #89 is `done`, so #37 is unblocked and is the last unfreeze condition.
> #82 is `doing` with its guarantees landed, and waits on two things that are not the page: a
> Streamlit pin (the maintainer's, because it fights the lock) and two API additions.**
>
> **#89 closed as a generated page:
> [../docs/REPORT-RECONCILIATION.md](../docs/REPORT-RECONCILIATION.md).** It lists twelve
> disagreements, not eight, because the audit's "eight" were never written down and had to be
> re-measured. Every quotation is tested to occur in `REPORT.md` verbatim, and every refuting value
> is read from its CSV at emit time. The headline: **two committed CSVs describe two different
> ensembles** (0.939/0.892 in one, 0.377/0.376 in the other), and the report quoted one of them.
> **Cite this page, not `REPORT.md`, for any published number.**
>
> **#82 landed its guarantees and not its script.** What the page shows is decided in
> `hydms/delivery/page.py`, and it talks to the service through `hydms/delivery/client.py`
> (stdlib `urllib`). Both are tested against uvicorn on a real socket (24 tests), so the fast lane
> checks them. `app/main.py` is a thin Streamlit layer that **has never run**. Streamlit is not in
> `Project`, and `pip install streamlit` would move `starlette` 0.38.6 → 1.7.0, past what the
> locked `fastapi` 0.115.0 accepts (`<0.39`), and `protobuf` 3.20 → 7. **Choosing a pin is a lock
> decision and the maintainer's.** Two boxes also need the *service* to grow: the k nearest
> alloys with measured capacities (no route serves them), and per-bin temperature support for the
> sweep (`GET /v1/model` has only `rows` / `rows_above`). Each is an API contract change:
> `openapi.json`, `docs/API.md --probe`, HG-3.
>
> **Next, in order of what it unblocks:** **#37**, the Chapter 1 revision (the last unfreeze
> bullet; it needs no fit and no decision). Then the two API additions for #82, which also serve
> #83's neighbours chart. Then the streamlit pin, once the maintainer picks one.
>
> **Every red CI run on this branch has now been read, and the 2026-09-13 block below is wrong
> about CI.** The job-logs API returns logs to this machine today:
> `gh api repos/AN-Hy-tech/hydride-storage-prediction/actions/jobs/<job-id>/logs`. There were six
> reds. One was #86's missing mypy stubs, two were #93's tests, and three (`34709161104`,
> `34716528657`, `34750680910`) were **#97's sort tie**, now fixed. **None was #100's render test.**
> So the paragraphs below saying "CI was red from #81", "the pyplot removal fixed something real",
> and that the #100 traceback "is probably sitting in CI run `34716528657`" are superseded.
> Corrected on #100, #101 and #97.
>
> *Below: the 2026-09-24 morning block, then the 2026-09-13 block. Both are superseded where the block above says so.*
>
> **(2026-09-24 morning)** Handoff, one line: #97 is done and CI is green on `411c721`; start #82, run #89 beside it, and open CI run `34750680910` in a browser once to learn why a markdown-only commit went red.
>
> **The documentation set was compacted today and nothing about the work changed.** This file went
> from **3,925 lines to ~310** and the runbook from **1,511 to 497**; everything removed is in
> [../docs/archive/](../docs/archive/), verbatim. Two new entry points:
> **[../docs/PHASE-H-FINDINGS.md](../docs/PHASE-H-FINDINGS.md)** is every open finding in priority
> order — including the eleven unticked boxes on `done` cards that no tool here can see — and
> **#101** is a new card holding three CI findings measured against the GitHub API. The opening
> move is unchanged: **#82**.
>
> **Handoff, one line: the full suite is green again — 1531 passed in 26 m 45 s on a quiet machine
> — #100's renderer no longer touches `pyplot` or a global backend, and S7's opening move is still
> #82.**
>
> **#100 is repaired but stays `doing`, and the reason is the interesting part.** Five full-length
> runs since it was filed are green and none reproduced the failure, so **there is no traceback and
> the card's second box cannot be ticked** — left unticked deliberately, because a criterion edited
> until it passes is not a criterion. What was removed is the *mechanism*: `hydms/figures/render.py`
> no longer calls `matplotlib.use()` or imports `pyplot`, so the rendering path holds no
> process-wide state for one test's result to depend on, and a subprocess test holds it that way.
> Not claimed as a fix. **Do not spend a sixth run looking for the traceback** — spend one only if
> a run goes red on its own, and redirect it to a file when it does.
>
> **CI was red from #81 until this commit, and the lane that was failing is the one this card said
> passes.** #81's own run was `cancelled` by the next push before reporting, so the first run to
> *complete* after it went red — on a commit that changed four markdown files and no code. The
> failing step is the fast lane, which passes on this machine (`pytest -m "not slow" --cov` re-run
> at that commit: **1527 passed, coverage 89.34 %, exit 0**), so it is a CI-only failure of the kind
> [../docs/ENVIRONMENT.md](../docs/ENVIRONMENT.md) and #93 already describe — the runner resolves `matplotlib>=3.8` to its own
> version and has no GUI toolkit where this machine has PyQt5. **The repair turned it green.** One
> red and one green is evidence, not proof, but it means the pyplot removal fixed something real
> rather than only removing a mechanism. **The practical lesson: a `cancelled` CI run is not a
> passing one** — `gh run list` before believing a workflow is fine, and treat a cancel as a gap.
>
> **The traceback this card has wanted for three sessions is probably sitting in CI run
> `34716528657`.** It could not be fetched from this machine — the log endpoints all redirect to a
> blob host that refuses the connection — but a browser can read it, and it costs minutes rather
> than another 29-minute run.
>
> **Before you quote any suite number, check the machine is yours.** On 2026-09-13 two sessions ran
> this 29-minute command concurrently without knowing, ~18 minutes overlapping, and one landed a
> source edit *while the other's run was still going* — producing a green that tested the old test
> body against the new renderer. Contention costs only a minute or two of wall clock, so the
> misleading number is the **pass**, not the duration. `docs/PHASE-H-RUNBOOK.md` §5 carries the
> two commands that check it.
>
> **#81 is `done`. S7 has started, and `hydms/figures/` is the vocabulary the rest of it draws
> with.** Five chart builders over the delivery contract's own types, 55 tests, 4.4 s, none `slow`.
>
> **The opening move is #82** — unblocked, with 78 and 81 both `done`. It is `app/main.py`: an HTTP
> client of the service, handing each `PredictionResult` to a builder. It must not acquire a
> matplotlib call of its own; a chart it needs that `hydms.figures` does not have is a builder
> added *there*, with its guards.
>
> | Goal | Path | Why it is not the other one |
> |---|---|---|
> | **Deliver Phase H's objective** — a user-facing predictor | **#82 → #84**, then #83 | `docs/FREEZE.md` §Why: *"The stated objective for this phase is a user-facing interface that predicts gravimetric capacity."* The freeze exists so it can be built on defensible numbers, **not instead of it** |
> | **Lift the freeze** — let PA/PB resume | **#89 → #37** | The four unfreeze bullets gate the *frozen* board reopening. They are not a to-do list for this phase |
>
> Three of the four unfreeze conditions hold (gates green; `current` → `v3`; `docs/API.md`
> published). The fourth is **#37**, waiting on **#89 alone**, and #89 is independent of S7 — no
> shared files, no shared blockers — so it runs beside it. **#83 needs both**, which is where the
> two paths converge.
>
> **#81 filed two cards by measuring its own instructions. Neither is an unfreeze condition.**
>
> | Card | What it is | Who it blocks |
> |---|---|---|
> | **#98** | `loco.py:595` writes four tables and not `evaluation.out_of_fold`, so LOACO leaves ten class averages and no scored rows. `parity()` refuses fewer than two readings, so **#83's parity figure cannot be built from committed evidence** | #83's second panel. Needs a **LOACO run** — the maintainer's |
> | **#99** | *"Only 39 test rows sit above 500 K"* is `REPORT.md`'s count over the archival 247-row test split. Measured now: **130 of 893**. The claim is unchanged; the number was inherited. Three production docstrings and two tests still carry it | nothing |
>
> **#36** (the five ADRs) is unblocked and has a directory to land into: `docs/adr/README.md`
> reserves `0001`–`0005` for its five and records why #85 took `0006`.
>
> **#91** is startable in parallel; **#94**, **#95**, **#96**, **#98** and **#99** are
> open and none is an unfreeze condition. **#100 is no longer the thing blocking a believable full
> run** — `pytest` with no `-m` is **1531 passed, 26 m 45 s** as of 2026-09-13; see the top of this
> block for why it is still `doing`. **#7** still owes a portable
> artifact — `artifacts/` is gitignored, so `v3` is on the maintainer's machine and nowhere else,
> and a fresh clone has no model.
>
> **Two generated documents on this board, and the rule is the same for both.** `docs/API.md`
> (`python -m hydms.delivery.apidoc --emit`) and `reports/loco/loco.md`
> (`python -m hydms.surrogate.loco --emit`) are rebuilt by code and a test asserts the committed
> bytes are what that code produces. Change the code and regenerate; an edit there fails the suite.
> `docs/API.md`'s examples come from `--probe`, the only part needing a promoted artifact — so
> after a new fit, re-probe, or the page keeps describing `v3` while saying so on its own face.
>
> **This block is a pointer with a date on it, not a source.** It is the one place on this board
> that restates state, which means it is the one place that can silently go stale — the cards and
> `show_blocked.sh` are the authority and they win on sight. **Rewrite it when you close a card**,
> the way you already append to a card's `## Narrative`; if its date is older than the newest entry
> in [../docs/archive/HANDOFFS-PHASE-H.md](../docs/archive/HANDOFFS-PHASE-H.md), distrust it and ask
> the board: `bash ../.claude/skills/kanban-ai/scripts/show_blocked.sh .`

This file owns the board's *own logic* — how cards are organised here, how the two boards share one
id space, and where to start. It does not restate what lives elsewhere:

| Looking for | Read |
|---|---|
| Why this phase exists, the leak inventory, the stage order and steps | [../docs/PHASE-H-RUNBOOK.md](../docs/PHASE-H-RUNBOOK.md) |
| What is frozen, why, and the unfreeze condition | [../docs/FREEZE.md](../docs/FREEZE.md) |
| The frozen inverse-design programme | [../docs/PRD-inverse-design.md](../docs/PRD-inverse-design.md), [../kanban/README.md](../kanban/README.md) |
| What a card *is now* | the card itself — it outranks every document above on its own status |
| What a card must prove before it is done | [../docs/QA-PROTOCOL.md](../docs/QA-PROTOCOL.md) |
| What is still broken, and what to take next | [../docs/PHASE-H-FINDINGS.md](../docs/PHASE-H-FINDINGS.md) |
| Why a past decision went the way it did | [../docs/archive/HANDOFFS-PHASE-H.md](../docs/archive/HANDOFFS-PHASE-H.md) |

---

## Two directories, one id space

Cards live in two directories that are validated together:

| Directory | Ids | State |
|---|---|---|
| `kanban-hardening/` | 1–37, 44, 48, 49, 68, 69–96 | **Active** |
| `../kanban/` | 38–43, 45–47, 50–67 | **Frozen** — every card must stay `backlog` |

**The directories are a freeze boundary, not an id-space boundary.** `blocked_by` reaches across
them, ids are unique across both, and `scripts/check_board.py` loads them as a single graph. Ids were
preserved when cards migrated: renumbering would have broken every `blocked_by` edge, every
`Traces to` link, and the `## Narrative` notes that the ADRs and card #37 are written from.

Three cards were pulled out of the frozen PA phase — **#44** (screen interface), **#48**
(applicability-domain ceiling), **#49** (ElMD novelty). They are not inverse-design work: they are
what lets the interface **refuse** to answer instead of guessing. #44 landed 2026-09-04 and owns
the contract the other two implement. **Only #48 waited on #30** — its ceiling is derived from the
leave-one-alloy-class-out result — and this line said "both of those" until 2026-09-11. #49 was
blocked by #44 alone, which is right on the substance: an ElMD distance is a property of two
compositions and reads nothing the surrogate produces. All three are `done`; S5 is closed.

**The next free id is #105** (as of 2026-09-25). Scan both directories for `max(id) + 1` — this
line has been stale before (it said #94 while #103 existed), so scan rather than trust it.

---

## Layers

Unchanged from the original board — each layer owns one kind of knowledge, and nothing outside it
needs to know that knowledge.

| Layer | Owns | Cards here |
|---|---|---|
| **L0 Foundation** | environment, config, artifact store, gates, CI, **test infrastructure** | 1–7, 68, 69–74, 86 |
| **L1 Data** | source schemas, merge keys, the canonical composition key, split protocol, CleanLab | 9–15, 87 |
| **L2 Descriptors** | element property tables, statistics, the 22-feature contract | 8, 16–22 |
| **L3 Surrogate** | model choice, scaler, quantiles, conformal calibration, the validation protocol | 23–34, 88 |
| **L4 Screens** | the screen verdict, the AD ceiling, novelty | 44, 48, 49, **90** (L4 *and* L6 — it is the catalogue of what both refuse) |
| **L6 Delivery** | the prediction contract, the API, the app, the chart vocabulary | 75–84, 91 |
| **L7 Evidence** | glossary, ADRs, the reconciliation, the Chapter 1 revision | 35, 36, 37, 85, 89 |

L5 Search is entirely frozen — it is how *candidates are proposed*, which is inverse design.

---

## Stage → card map

The runbook executes these in order. S2 and S3 are the only pair that may run in parallel.

| Stage | Cards | Days |
|---|---|---:|
| **S0** Freeze & tooling | 72 | 1 |
| **S1** QA foundation | 69, 70, 5, 71 | 2 |
| **S2** Data layer | 3, 9, 10, 11, 87, 12, 13, 14, 15 | 7 |
| **S3** Descriptor layer | 16, 17, 18, 19, 20, 21, 22 | 6 |
| **S4** Surrogate layer | 23, 24, 25, 88, 26, 27, 28, 29, 30, 31, 32, 33, 34, 97, 98, 104 | 13 |
| **S5** Guard rails | 44, 48, 49 | 2.5 |
| **S6** Delivery: contract + API | 75, 76, 77, 78, 79, 80 | 5 |
| **S7** Delivery: interface | 81, 82, 83, 84 | 3.5 |
| **S8** Evidence & close | 89, 85, 86, 35, 36, 37, 99 | 5 |
| **No stage** | 1, 2, 4, 6, 7, 8, 68, 73, 74, 90, 91, 92, 93, 94, 95, 96 | — |

**Cards 92–99 were found during the phase, not planned into it.** Each was filed by a card working
somewhere else, each names the card that found it, and **none is an unfreeze condition** — that
list is fixed and `../docs/FREEZE.md` exists to resist widening it. They are placed in a stage row
above where they belong to one (97 and 98 are surrogate-layer defects, 99 is prose), and in *No
stage* where they are CI or board work that slots in wherever its blockers allow. The day count in
each row is the runbook's original estimate and is deliberately not re-added to: it is what the
phase was planned at, and #92 is the card that makes this table checked rather than remembered.

**Every card's own first line now states its stage, and this table is where it comes from.** Until
2026-09-11 thirty-nine cards still carried the *frozen* board's `Phase 0 / Phase 1 / Phase A`
heading — they were `git mv`-ed here by #72 with their ids preserved and their prose untouched — so
a reader opening #26 was told "Phase 1", a vocabulary that belongs to [../kanban/README.md](../kanban/README.md).
Two more were worse than stale: #73 and #74 claimed **Stage S1** when the runbook §2 says in so many
words that both landed after S4 closed, and #91 claimed **S6** when the paragraph below says it is in
no stage at all. Nothing reads that line — no test, no gate, no `--emit` — which is exactly why it
drifted; #92 is the card for making it checkable.

**The `S1`…`S12` in a card's `tags:` are not stages.** They are the PRD's **user stories** (§5) — `S10`
on #78 is "explore results without running code", not "Stage 10", and there is no Stage 10. The stage
is the bold line under the title; the tag is a trace. They were never the same vocabulary and reading
one as the other is the single most available mistake on this board.

**#90 and #91 are in neither stage and that is deliberate.** They came out of a grilling session on
2026-09-07 about catching bugs during the working cycle, and neither is an unfreeze condition —
`../docs/FREEZE.md` fixed those four "before results are seen, so it cannot be softened later", and
widening that list is the one thing it exists to resist. **#90** (the refusal catalogue) has no
unfinished blocker and slots in wherever there is room; **#91** (the prediction record and replay)
belongs beside S6 but may sit open across the lift. The gate they will eventually register, HG-5, is
boxed on #91 and is explicitly post-freeze.

Cards **1, 2, 4, 6, 7, 8, 68, 73, 74** are foundation and CI work that slots in where its blockers
allow rather than sitting in one stage — the environment pin, the package scaffold, the artifact
store, both CI lanes, the `elem_prop` provenance spike, the board integrity check, and the two
suites (#73 smoke, #74 metamorphic) that could not be written until `predict()` existed. **#5** (the
gate harness) was the same kind of card and has landed inside S1, where it belonged: every gate card
on the board was blocked behind it.

---

## Gates

Nine are live in this phase — four new, five inherited from the PRD's acceptance criteria. The full
table with failure conditions is in [../docs/PHASE-H-RUNBOOK.md](../docs/PHASE-H-RUNBOOK.md) §4.

All of them are registered in the gate harness (#5), together with the three frozen criteria, so the
registry is the complete list of what the project has promised to check rather than the subset it can
currently check. Ask it rather than this table: `python -m hydms.gates list`.

| Gate | Card | | Gate | Card |
|---|---|---|---|---|
| **HG-1** leak sentinels | 71 | | AC-1 seed reproducibility | 32 |
| **HG-2** no bare numbers | 77 | | AC-2 featuriser parity | 21 |
| **HG-3** transport parity | 79 | | AC-3 conformal coverage | 31 |
| **HG-4** hygiene | 86 | | AC-4 known-alloy round-trip | 33 |
| | | | AC-6 leave-one-class-out | 30 |

AC-5 is thermodynamic and AC-7/AC-8 are inverse-design; all three stay frozen with their cards.

**Two hard gates block everything behind them.** #21 (featuriser parity) gates every card downstream
of selection — if the reimplementation does not reproduce CBFV to 1e-9, the reimplementation is
wrong, not CBFV. And #71 (leak sentinels) is what makes the phase durable.

**#71 has landed, and it will interrupt you.** It is the one gate that goes red at a moment you did
not choose: each sentinel names the module its leak would reappear in, and HG-1 fails as soon as that
module exists with nothing wired to it. It has already happened once: creating `hydms/data/merge.py`
turned the build red with `L9 [unwired] #10 -- guarded in name only` before a wrong line had been
written, and stayed red until #10 added the `live` hook in `hydms/qa/sentinels.py`. That is the
mechanism working: a sentinel written six weeks early against a miniature becomes a real guard only
when somebody points it at the real thing. #10, #13, #14 and #12 have since wired theirs, and the audit
reports **5 of 13 leaks guarded** — L3, L8, L9, L10, L13. It has now happened twice: #20 creating
`hydms/descriptors/featurize.py` turned L13 `unwired` and took eight tests red with it, and #12
closed it the same day. #24, #88 and #26 have since wired
theirs, the last of them writing the L12 sentinel it also owed, and the audit now reports **12 of
13**. **#29 closed the last one, L11, on 2026-09-05: the audit now reports 13 of 13 and
`hydms.qa.sentinels.DEFERRED` is empty.** The empty tuple is kept rather than deleted — a gap
nobody wrote down is indistinguishable from coverage, and the next leak this project finds should
be recorded there on the day it is found.
Read the per-leak table with:

```bash
conda run --no-capture-output -n Project python -c "from hydms.qa import audit; [print(f'{r.leak:4} {r.status:9} #{r.owed_by}  {r.title}') for r in audit()]"
```

---

## Start here

Ask the board rather than trusting a list — a list here goes stale the moment a card moves.

```bash
S=../.claude/skills/kanban-ai/scripts
bash $S/show_blocked.sh .          # what is waiting on what
bash $S/view_board.sh .            # everything by status
bash $S/list_all_cards.sh .        # id | status | blocked_by | title
```

Then read the **▶ Next action** block at the top of this file, and the card itself. Those two plus
the board scripts are the whole of what a session needs to begin. If the block's date is older than
the newest entry in the handoff archive, distrust it and ask the board.

### Where the history went

Everything this file used to carry below this line — the accreted `Start here` handoffs and the
full handoff log back to 2026-09-03, 3,600 lines of it — is in
[../docs/archive/HANDOFFS-PHASE-H.md](../docs/archive/HANDOFFS-PHASE-H.md), verbatim and
uncorrected. It moved on 2026-09-13 because this file had become 3,925 lines of which 93 % was
past, and every session was paying for all of it to find the twenty lines that were present.

Open the archive when you need **intent** — why a decision went the way it did, what a session
believed at the time, which numbers have since moved (its superseded-values table lists them). Do
not open it for current state: the cards are the authority, and the archive is explicitly not
corrected in place.

---

## Using the board

Unchanged from the original board's rules:

- Move a card by editing its `status`: `backlog` → `todo` → `doing` → `done`.
- **Before moving a card to `doing`, every id in its `blocked_by` must be `done`.** CI enforces this.
- Append to `## Narrative` when a card teaches you something, ISO-dated, `(by @...)`. Those notes are
  the record of *why*, and they are what the ADRs (#36) and the Chapter 1 revision (#37) are written
  from.
- New cards carry: `id`, `status`, `priority`, `blocked_by`, `assignee`, `tags`; an
  `> **Owns (hidden behind this module):**` blockquote; `## Why this exists`; `## Done when`;
  a single-command `## Runnable check`; `## Traces to`; and `## Narrative`.
- Tags lead with the phase, then the layer, then traces: `ph, l3, HG-1, AC-6`.

`scripts/check_board.py` will reject a dangling `blocked_by`, a dependency cycle, an id that does not
match its filename prefix, an illegal status, a card on the frozen board that has left `backlog`, and
any relative Markdown link that does not resolve.

**It does not read checkboxes, and six cards plus this file used to say it did** (#68, found
2026-09-13). A `done` card carrying an unticked box is this board's way of recording a *finding that
is not work* — the convention is good and stays — but it is a convention enforced by nobody:
`hydms`, `scripts/` and `tests/` contain nothing that reads a `- [ ]`, and #1, #14, #30, #34 and #86
are `done` with eleven unticked boxes between them while the checker prints `OK`. Do not file a card
on the belief that the checker will catch it; #97 and #100 both were. The open inventory of those
boxes is [../docs/PHASE-H-FINDINGS.md](../docs/PHASE-H-FINDINGS.md).

---

## A note on the ML skills

Covered once, in [../CLAUDE.md](../CLAUDE.md) — the caveat there spans all three installed skills
(`ml-model-training`, `ml-fundamentals`, `ml-model-trainer`), records the 2026-09-05 audit against
the live pipeline, and sits beside the authority order it depends on. This section used to restate
a third of it for one skill; two copies of a caveat is one copy and one thing that goes stale.
