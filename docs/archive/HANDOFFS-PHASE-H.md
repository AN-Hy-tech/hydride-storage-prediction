# Phase H — the handoff archive

**This file is history, not status.** It is the tail of
[../../kanban-hardening/README.md](../../kanban-hardening/README.md) exactly as that file stood on
2026-09-13, moved here so a cold session pays for the board's *interface* and not for its whole
past. Nothing was corrected, reordered, or summarised on the way in — only the relative links were
re-pointed for the new depth.

**Authority: none.** A handoff records what one session believed when it wrote it. Where one
contradicts a card, the card wins. Where one contradicts
[../PHASE-H-RUNBOOK.md](../PHASE-H-RUNBOOK.md) on the phase, the runbook wins. Where one contradicts
the board's `▶ Next action` block, that block wins. Read these for *intent* — why a thing was done
the way it was — and never for a current number. The superseded-values table under
"Reading the handoffs" below is the list of numbers already known to have moved.

**Reading order.** Block 00 was added 2026-10-15, blocks 0 and 0b 2026-09-26; then two blocks, each newest-first, in the order they appeared in the README:

1. **The `Start here` accretion** (2026-09-12 → 2026-09-06) — handoffs that were written into the
   board's opening section instead of its log, and that the `▶ Next action` block replaced.
2. **The handoff log proper** (2026-09-13 → 2026-09-03), with its own preamble and the
   superseded-values table.

---

## 00. The `▶ Next action` block retired 2026-10-15

Moved verbatim when #108 and #99 closed; links re-pointed only. Carried out: #99. Not carried out:
#96, #94 and the LOACO repeat, all handed over in the block that replaced it.

> ## ▶ Next action — as of 2026-09-26 (the docs compaction; #83 and #104 `doing`)
>
> **Take the open findings in band order, cheapest first:** **#99** (P1, 0.25 d), then **#96**
> (P1, 0.25 d), then **#94** (P2, 0.25 d; one crossed band still fails a whole `predict_many`
> batch). The ranked list is [../docs/PHASE-H-FINDINGS.md](../PHASE-H-FINDINGS.md).
> **#83** waits on the per-row width table (its population is a decision) and on #104's repeat.
>
> **The LOACO repeat (#104; heavy, the maintainer runs it).** About five hours each, one after the
> other, on an idle machine with sleep disabled (`docs/RUNNING-THE-FIT.md` Step 10). Run A writes
> the committed tables, run B a gitignored scratch directory, then the diff. Only
> `loco-chosen.csv`'s `seconds` column may differ. **Anything else moving is a new #104 finding,
> not a failed run.** Commit A's tables either way, then the regeneration chain in Step 10.
>
> ```powershell
> & "C:\Users\Asus\miniconda3\envs\Project\python.exe" -u -m hydms.surrogate.loco --target capacity | Tee-Object -FilePath .\reports\_loco-run-a.log
> & "C:\Users\Asus\miniconda3\envs\Project\python.exe" -u -m hydms.surrogate.loco --target capacity --report .\reports\_loco-b | Tee-Object -FilePath .\reports\_loco-run-b.log
> foreach ($t in 'loco-per-class','loco-summary','loco-out-of-fold','loco-chosen') { git diff --no-index --stat "reports/loco/$t.csv" "reports/_loco-b/$t.csv" }
> ```
>
> **Traps.** `apidoc-examples.json` stores the over-limit request *shortened*, with
> `candidates_total` beside it; do not "fix" it back to 4,097 rows. Any change to a table the
> Evidence Reader serves changes `evidence_sha256`: re-run `apidoc --probe --emit` after
> `loco --emit` or `evaluate`.
>
> **This block is one handoff, never a log.** Replace it when you close a card, and move the one it
> replaces to the top of [../docs/archive/HANDOFFS-PHASE-H.md](HANDOFFS-PHASE-H.md)
> in the same commit. The cards win on sight.

---

## 0. The `▶ Next action` blocks retired 2026-09-26 (2026-09-26 → 2026-09-24)

Moved verbatim from the top of the board README when it was compacted to one handoff. Newest first; links re-pointed only.

> *Below: the block this one replaces. Carried out, except the LOACO repeat, which is handed over above.*
>
> **(2026-09-26 evening, #83 built)**
>

> **Handoff, one line: #83's model card is built and served (`GET /v1/evidence`, `/v1/evidence/parity`, `app/pages/1_Model_card.py`) and stays `doing` on the per-row width table and #104's repeat; start #84 (`predict_many`); the maintainer's next full LOACO run is the first with a run date *and* the #104 fix, so rerun it twice and diff.**
>
> **What landed.** #104: the drift was `label_issues`' parallel forest (its `predict` sums trees
> in thread-finishing order). It runs on one thread now and refuses a parallel estimator; the
> refusal then caught the same defect in `hydms/pipeline/smoke.py`. AC-1 still reproduces `v3`
> exactly. #106: `select` writes `selection<variant>-run.csv` and the comparison is dated from it.
> #83: `hydms/evidence/reader.py` (standard library only) turns the committed tables into
> `Score`s, the service reads it once at startup, `loco --emit` writes `loco-intervals.csv`, and
> reconciliation reads through the reader. `docs/API.md` was re-probed against `v3`.
>
> **Three things that would cost an afternoon.** (1) Any change to a table the reader serves
> changes `evidence_sha256`, and so `docs/API.md`'s captured example: re-run
> `apidoc --probe --emit` after `loco --emit` or `evaluate`. (2) The first LOACO and `train` runs
> after the #104 fix will move the tables **once** (new code, one draw of the old spread). Only a
> second run on unchanged code tests the fix. (3) The fast lane took 53 min this session with
> 1765 passed. Its 10 smoke failures were the #104 refusal, fixed since (smoke 19/19); the lane
> was not rerun whole.
>
> *Below: the block this one replaces. Carried out, except #84, which is still unstarted.*
>
> **(2026-09-26, #105 `done`)** **Handoff, one line: #105 is `done`: every run now stamps a run record via `hydms/provenance.py`,
> and `result()` is the only "is this a result?". Start #83 (the Evidence Reader, ADR 0007) and
> read runs through `provenance.read`/`result`; #84 is startable beside it. The next full LOACO
> run (#104's) is the first with a run date. #106 (select/comparison) is split off and small.**
>
> **What landed.** `hydms/provenance.py`, standard library only: `begin()` stamps before the
> fit, `Stamp.finish()` returns the row, `write()` writes it, `read()` never raises, `result()`
> refuses an absent, unreadable, probe or unparseable-`probe` record. `train`, `loco`,
> `evaluate` (`evaluation-run.csv`) and `calibrate` (`conformal-run.csv`) write records, and the
> last two carry `source_run_id` back to the train record. AC-6, `evaluate`, `loco --emit`,
> `domain.transfer_table` and the figures test read through it. `domain --emit` **refuses** a
> probe's transfer table (exit 2, reference untouched). `tests/test_provenance.py` fails any
> module under `hydms/{delivery,screens,figures,gates}` or `app/` that parses a record itself.
>
> **Three things that would cost an afternoon.** (1) The committed `model-run.csv` and
> `loco-run.csv` predate the fields and were **not** rewritten. They read *not recorded*, and so
> do `loco.md` and `evaluation.md`. Never fill a run date from `git log`. (2) `evaluation.md`'s
> `Emitted:` line is the **emit's** date and commit, not the run's; the `Run date:` line is the
> run's. (3) `docs/RUNNING-THE-FIT.md`'s commit lists now name `conformal-run.csv` and
> `evaluation-run.csv`. A run that leaves them unstaged has lost its record.
>
> **For #83.** Caption the LOACO parity panel with `provenance.read(...).run_date_text`, which
> says *not recorded* today, and name the run by its commit (`d8734ec`), labelled as a commit.
> Do not open `*-run.csv` by hand: the source-parsing test will fail it under `app/`.
>
> *Below: the block this one replaces. Carried out.*
>
> **(2026-09-26, architecture settled; #105 filed)** **Handoff, one line: start #105 (the run record: `hydms/provenance.py`, standard library only)
> and land it before any full LOACO run. Then #83 (the Evidence Reader, per ADR 0007), then #84
> (`predict_many`). Every decision is on those three cards. #104's four probes are running, and
> their diff goes on #104.**
>
> *Below: the block from when #98 closed. Superseded on order only: #83 is now blocked by #105.*
>
> **(2026-09-25 evening, #98 `done`; #104 filed)**
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
> [../docs/PHASE-H-FINDINGS.md](../PHASE-H-FINDINGS.md)'s rule, because it makes a published
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
> [../docs/chapter1-revision.md](../chapter1-revision.md). After that, #37 → `done`, lift the
> freeze per [../docs/FREEZE.md](../FREEZE.md), then the two API additions for #82.**
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
> **Handoff, one line: #37 is drafted ([../docs/chapter1-revision.md](../chapter1-revision.md))
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
> [../docs/REPORT-RECONCILIATION.md](../REPORT-RECONCILIATION.md).** It lists twelve
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
> [../docs/archive/](./), verbatim. Two new entry points:
> **[../docs/PHASE-H-FINDINGS.md](../PHASE-H-FINDINGS.md)** is every open finding in priority
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
> [../docs/ENVIRONMENT.md](../ENVIRONMENT.md) and #93 already describe — the runner resolves `matplotlib>=3.8` to its own
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

---

## 0b. The board README's reference sections as they stood 2026-09-26

Moved verbatim before the README was rewritten compactly. The README's current version wins.

This file owns the board's *own logic* — how cards are organised here, how the two boards share one
id space, and where to start. It does not restate what lives elsewhere:

| Looking for | Read |
|---|---|
| Why this phase exists, the leak inventory, the stage order and steps | [../docs/PHASE-H-RUNBOOK.md](../PHASE-H-RUNBOOK.md) |
| What is frozen, why, and the unfreeze condition | [../docs/FREEZE.md](../FREEZE.md) |
| The frozen inverse-design programme | [../docs/PRD-inverse-design.md](../PRD-inverse-design.md), [../kanban/README.md](../../kanban/README.md) |
| What a card *is now* | the card itself — it outranks every document above on its own status |
| What a card must prove before it is done | [../docs/QA-PROTOCOL.md](../QA-PROTOCOL.md) |
| What is still broken, and what to take next | [../docs/PHASE-H-FINDINGS.md](../PHASE-H-FINDINGS.md) |
| Why a past decision went the way it did | [../docs/archive/HANDOFFS-PHASE-H.md](HANDOFFS-PHASE-H.md) |

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

**The next free id is #107** (as of 2026-09-26). Scan both directories for `max(id) + 1` — this
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
| **S4** Surrogate layer | 23, 24, 25, 88, 26, 27, 28, 29, 30, 31, 32, 33, 34, 97, 98, 104, 105, 106 | 13 |
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
a reader opening #26 was told "Phase 1", a vocabulary that belongs to [../kanban/README.md](../../kanban/README.md).
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
table with failure conditions is in [../docs/PHASE-H-RUNBOOK.md](../PHASE-H-RUNBOOK.md) §4.

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
[../docs/archive/HANDOFFS-PHASE-H.md](HANDOFFS-PHASE-H.md), verbatim and
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
boxes is [../docs/PHASE-H-FINDINGS.md](../PHASE-H-FINDINGS.md).

---

## A note on the ML skills

Covered once, in [../CLAUDE.md](../../CLAUDE.md) — the caveat there spans all three installed skills
(`ml-model-training`, `ml-fundamentals`, `ml-model-trainer`), records the 2026-09-05 audit against
the live pipeline, and sits beside the authority order it depends on. This section used to restate
a third of it for one skill; two copies of a caveat is one copy and one thing that goes stale.

---


**Next session, in one line.** **#34 is `done` — `current` points at `v3`, so two of the four
unfreeze conditions are met and the other two are #80 (`docs/API.md`) and #37 (Chapter 1, waiting
on #89 alone); #36 is unblocked too, and #81, #85, #91 are startable in parallel.** The three
deferred boxes below stay parked, #30's third box is still an obligation that travels, and #1 ends
in an OPEN maintainer decision that needs an answer before anyone re-solves the lock.
~~#79 is `done` … #86 (HG-4) is now the last unfinished blocker on #34~~ — both closed on
2026-09-12.

**Handoff, 2026-09-12 (superseded) — #79 is `done`; HG-3 is green, and #86 is the last gate #34 waits
on.** This is the live handoff; the three below it are history in the order they happened.

**What landed, and one thing that had not.** `hydms/gates/hg3_transport_parity.py` replaces the
`Pending`, over a new `hydms/delivery/api/openapi.py` and the contract it commits,
`hydms/delivery/api/openapi.json`. **#78's service was still uncommitted in this worktree** — the
card was `done`, the handoff written, and nothing was in git — so it is committed here first, under
its own message, and #79's commit sits on top of it. The two commits share three documents
(`docs/PHASE-H-RUNBOOK.md`, this file, `CONTEXT.md`) because both cards' paragraphs were written
into them in the same tree; the second commit carries them and says so.

**Numbers, with the command that produced each.** `python -m hydms.gates run HG-3` — **PASSED in
4.52 s** against `v2`: 11 probes (3 answered, 8 refused), 8 malformed requests, 257 candidates
against the published limit of 256, **0 differences**. `pytest tests/gates/test_hg3_transport_parity.py
tests/delivery/test_openapi.py` — **37 passed**. `pytest tests/delivery` — **160 passed, 12.9 s** (was 145). `pytest tests/delivery
tests/gates/test_harness.py tests/gates/test_cli.py` — **195 passed, 9 min 57 s**. The fast lane, `pytest -m "not slow"` —
**1440 passed, 4 deselected, 12 min 3 s** (was 1371/1375 before #78 and #79), measured before the
last documentation edits and one test rename; the `tests/delivery` run above is after them. The gate
lane, `run --fast` — **7 passed, 0 failed, 2 skipped, 26.2 s** (was 6/3); `run --all` — **8 passed,
0 failed, 4 skipped, 3.0 min**. The remaining skips are AC-5, AC-7 and AC-8 (frozen) and **HG-4**.
ruff and mypy clean over `hydms/ tests/ scripts/`; `check_board.py` OK over 92 cards.

**The opening move, and it is the only one.** **#86 (HG-4)** is now the *single* unfinished blocker
on **#34**, which is promotion, which is the unfreeze condition. `#34` waits on `[29, 31, 32, 33,
77, 79, 86]` and six of the seven are `done`. #86 is CI hygiene — ruff, mypy and a coverage floor
over `hydms/` — and it carries a decision nobody has taken: **neither `pytest-cov` nor `coverage` is
installed in `Project`**, so the floor in `pyproject.toml` is unenforceable anywhere today, and
installing one invalidates `environment.lock.yml`. Read `docs/PHASE-H-RUNBOOK.md` §5's boxed note
before planning it. **#80** (the API reference) is the other card #79 unblocked and is S6's last;
**#81** opens S7 and needs nothing that is not already `done`.

**What S6 finished that S7 must use rather than rebuild.** The app is an **HTTP client**, not an
in-process caller — that is why HG-3 covers the interface at all, and #85's ADR is where the
argument is written down.

- **The shapes are a file now.** `hydms/delivery/api/openapi.json` is the published contract,
  generated by `python -m hydms.delivery.api.openapi --emit` and asserted byte-identical by a test.
  Read it instead of guessing what a route returns, and never edit it by hand.
- **One door back from JSON.** `hydms.delivery.contract.answer_from()` rebuilds an answer or a
  refusal and **refuses** an error body. A page that branches on the HTTP status alone will read a
  rejected request as a declined material: both are 422 and only the body separates them
  (`refused` versus `error`). HG-3 measures that from both sides; `CONTEXT.md` has the term.
- **The batch limit is 256 and it is published, not assumed.** `GET /v1/health` reports
  `max_batch_rows`; read it rather than importing a constant. A served prediction costs **66–78 ms**
  and is linear in the rows with nothing amortised, so a CSV of thousands cannot go through the
  loop — the fix is a batched call in the *library*, and it is boxed on **#84**.

**Three things that would otherwise cost an afternoon each.**

- **CI installs the `api` extra now** (`.[dev,uq,novelty,api]`). Without it `fastapi` is absent, the
  service cannot be built, HG-3 reports SKIPPED on every push and `tests/delivery/test_api.py` skips
  itself away beside it — and the OpenAPI comparison is precisely the half that needs no artifact
  and therefore the only half the fast lane *can* run. The consequence to expect: those 32 tests now
  run in CI, so a transport failure is a red push rather than a local surprise.
- **The snapshot moves when FastAPI or pydantic moves.** That is intended — a generated document
  that changed is a change to what a client reads — but it means a dependency bump lands as a red
  HG-3 with a pointer diff, and the fix is `--emit` plus a look at the diff, not a widened check.
- **A gate that cannot run says so.** HG-3 skips, loudly and naming the extra, where the service
  cannot be started, and skips again where no artifact is on disk — but the document and the
  request-door checks run *before* either skip, so it can go red in a checkout where it can never go
  green.

**The findings of this session, and what was done about each.**

- **The comparator was blind to an empty container.** `differences()` flattens a document to
  `{pointer: scalar}`, and recursing into `{}` or `[]` emitted nothing — so a key whose value is
  empty vanished from *both* sides and a response that dropped `screens: []` compared equal to one
  that kept it. Found by a test that expected the dropped key reported and got silence. Fixed (an
  empty container is its own leaf) and pinned. It matters because that one function is read twice:
  on the OpenAPI document, and on **every served answer against the library's**.
- **A test name collided with one the runbook names in prose.**
  `test_the_committed_document_is_what_the_code_produces` already exists in
  `tests/surrogate/test_loco.py`, and §5 names it when it explains why the suite has no skips. The
  new one is `test_the_committed_openapi_document_is_what_the_code_produces`, with the reason in its
  docstring.
- **The probe set is HG-2's, imported rather than re-listed.** A second list would drift from the
  one whose *library* behaviour is pinned, and "the API agrees with the library" would then be
  established over inputs nobody checked the library on. `untrusted-family` stays `NEVER` at both
  doors from one record, so #78's inherited box is discharged without a second place to maintain.

**Still parked, and still owed.** The three deferred boxes below stay parked, **#30's third box** is
an obligation that travels, and **#1** ends in an OPEN maintainer decision that needs an answer
before anyone re-solves the lock — the `defaults` channel is 403 and supplies `python` and `numpy`
themselves, so `verify_environment.py` cannot pass here until it is re-solved. Do not start one
unasked.


**Handoff, 2026-09-12 (later) — #78 landed, and the card's own two boxes collided.**

`POST /v1/predict`, `POST /v1/predict/batch`, `GET /v1/health`, `GET /v1/model`, in
`hydms/delivery/api/` over a new `hydms/delivery/modelcard.py`. 32 tests, 13.6 s; the whole of
`tests/delivery` is **145 passed in 30.8 s**; ruff, mypy, `check_board.py` and `check_freeze.py`
clean; **HG-2 still PASSED against `v2` (6.2 s)**.

**The finding, and it is a conflict between two authorities rather than a defect.** The card
says "a malformed request is a 422" and the runbook's own acceptance `curl` says a refusal is
"HTTP 422 — never a number". Both are binding, so the card's *next* box — "a refusal is
distinguishable from an error … in the status code and the body" — cannot hold in its strong
reading for those two. The split moved into the body: **an answer carries `refused`, a rejected
request carries `error`, and the two share no key.** `answer_from()` rebuilds the first and
refuses the second with its own sentence. A refusal is still separated from a *low prediction*
(200) and from a *deployment error* (500) by the status as well. `CONTEXT.md` gained the term,
and #79 gained a box to gate it.

**The API did not become the third door #77 warned about.** That handoff said a batch endpoint
accepting a frame with an alloy-class column would make `untrusted-family` reachable and oblige
`NOT_ALWAYS` to explain it. The batch body declares exactly the contract's two fields under
`extra="forbid"`, so the HTTP door *is* the request door and HG-2 needed no change — which is
why it is still green without being touched.

**One number worth carrying: a served prediction costs 66–78 ms** against `v2` (13 ms
featurise, 22 ms surrogate, 34 ms screens) and is **linear in the rows with nothing amortised**,
because each candidate goes through `predict_capacity` as its own one-row frame. That is what
set the batch limit at 256 (~19 s, and ~38 s on a machine half this speed, inside the 60 s a
client or proxy typically allows) and it is boxed on **#84**: a CSV of thousands needs a batched
call in the *library*, not a bigger limit.

**`uvicorn hydms.delivery.api:app` cannot serve today, and that is the card working.** It
resolves the **promoted** version at startup and nothing is promoted, so it exits with
`load_bundle`'s sentence. The runbook's acceptance checks were run against the real `v2` through
the gate door instead, and produce exactly what §6 says they will.

**Handoff, 2026-09-12 (later still) — the four owed findings, cleared.**

All four resolved. Two of them dissolved on measurement rather than on argument, which is the
result worth carrying forward: **both were posed as "design this", and both turned out to be
"check whether the bill is already paid".**

1. **#23 — the scaler payload leaves the next version's contract.** Decided, not built. What
   settled it was not the missing reader but `deploy.py`'s own stated invariant: the three payload
   keys are "each declared by the module that reads it back, **so this mapping cannot name a key
   nothing loads**". `SCALER_PAYLOAD` is now the counter-example, and restoring the invariant
   admits only two moves — find a reader, or drop the key. #48 *measured* that distance in the
   model's feature space does not order transfer failure, so that consumer is not returning;
   #49's ElMD reads compositions. So the key goes. `v1`/`v2` keep it — a version is sealed when
   written — and the removal was boxed on **#34**, with `CONTEXT.md`'s **Artifact version** entry
   listed there because nothing tests that file. **Moved to #7 on 2026-09-12 when #34 closed, and
   the move corrected the premise:** #34 wrote `v3` that evening and it carries the scaler, because
   `promote` copies the payload set of the version it certifies and fits nothing. **Only a fit can
   drop a key**, so the owner is the next retrain. `CONTEXT.md` had already predicted the opposite
   and has been corrected there. **Four live sentences rested on the retired
   reason** and were corrected (`deploy.py`'s invariant, the `test_the_stored_scaler_is_never_applied`
   docstring, two passages in this README); #76's box list carried the same false consumer.

2. **#14 and #9 — no correction layer, and no data-layer plausibility filter.** The joint question
   was whether the data layer may change a value it was given. **Answer: no**, and the loader's
   "normalises nothing" contract stands unchanged.

   The measurement that decided #14: running the stage's real path over the 893 training rows,
   **CleanLab already removes both impossible training rows and ranks them the two worst labels
   of 893** — `Ce1Ni3Cr2` quality 3.07e-08 (rank 1), `Ce1Ni4Zr1` 3.42e-08 (rank 2) — knowing
   nothing about hydrogen, mass or the ceiling. A declared ceiling-based drop would therefore
   change nothing it is allowed to change, and for the third row it would *break* the contract:
   `Ce1Ni4Cr1` is in `val`, and a finding on a held-out row is reported, never acted on. The
   ceiling stays an L4 screen, and the two mechanisms agreeing by unrelated routes is
   corroboration worth keeping rather than duplication worth merging.

   The fourth over-ceiling row is why the instinct to repair is dangerous here:
   `Ti1.1Cr1Mn1V0.255Fe0.045` is a **real material** at Sahlberg's limit, over by <0.01, and it
   scores 4.26e-04 at rank 11 — four orders of magnitude clear of the two defects. **Do not turn
   3e-08 into a threshold**; nothing in the code reads it.

   #9 follows from the same split: the Mg row is *repairably* wrong, the Ce-Ni rows are
   *detectably* wrong but not repairable. A correction table can only carry what it can justify,
   so its entire payoff was one training row of 893 — against making the data layer the first
   place entitled to rewrite an input, trusted downstream and checked by nothing. Same
   unfalsifiability that decided #23.

   **One obligation travelled:** `Ce1Ni4Cr1`'s impossible label sits in `val` and feeds early
   stopping and every validation figure. Not removable under L3, and that is the right rule — so
   it is a **stated limit, boxed on #83**, with an unticked box on #14 that carries no action.

   The warning in the old handoff held: `tests/screens/test_applicability.py` still asserts the
   four over-ceiling rows exactly, and still passes — it measures the *curated record*, which
   screening never edits.

3. **#72 — the deny-list is authoritative, and the charter now says so.** Cleared first because
   it gated #1. `docs/FREEZE.md` § "Allowed paths" is replaced by "Everything else is allowed",
   naming the old list as the thing it corrects. The reasoning is about which document gets
   edited: an allow-list must be widened every time work reaches an unlisted file, turning the
   one document meant to resist widening into the most-edited one. `DENIED` stays short, and the
   charter now states that adding to it needs a reason of the same kind as the five.

4. **#1 — measured, and worse than assumed. The remedy is an OPEN decision.** The 403 is
   permanent (`pkgs/main` 403, `conda-forge` 200, re-probed 2026-09-12), and it is not an
   incidental tail: **95 of 248 conda packages come from `defaults`, including `python`
   (`3.10.13=h966fe2a_0`), `numpy` (`1.26.4=py310h055cbcc_0`) and the whole MKL stack.** So the
   rebuild box is unrepeatable by anyone here, not just inconvenient. Every pinned version —
   MKL included — *is* on `conda-forge`, so a re-solve with `blas=*=mkl` is viable, but ~95 builds
   change and `mkl_fft`/`mkl_random` have no equivalent. Because the manifest records versions
   rather than builds or BLAS, a re-solved env would claim identical provenance while possibly
   computing differently — which AC-1 and AC-2 are exactly the instruments to detect. The card
   carries three options; **option 1 is gated on a throwaway-env gate run, and nobody should
   start it unasked.**

**Verification.** Fast lane **1371 passed / 4 deselected of 1375 collected (14 min 9 s)**,
`ruff` and `mypy` clean, `check_board.py` and `check_freeze.py` green. Nothing in this session
changed a code path — the diff is three decisions, one measurement, and the sentences that rested
on them — so no heavy run was needed and nothing was promoted.

**Deferred by design — leave these parked. Each states its own reopen condition.**

- **#9, first box (the HyStor spreadsheet has no loader). SETTLED 2026-09-12 by #86: the
  dependency is not added, so the reopen condition cannot be met.** The box read *"Reopen this
  box only if #86 adds the dependency **and** a card needs the four extra rows"*, and #86
  declined the dependency — `openpyxl` would invalidate the lock, and #1 has since found the
  lock cannot be rebuilt here at all, which makes changing it a larger question rather than a
  smaller one.

  **The second half of that condition was never askable, and the correction is worth keeping.**
  #86 read the sheet with stdlib `zipfile`: it is `A1:F1284`, so 1,283 data rows over six
  columns, and the CSV is not a copy of it missing four rows — it is a **renormalisation**.
  The sheet writes `CaNi5` and `CaAl1.8B.2 (M)` where the CSV writes `Ca1Ni5` and
  `Ca1Al1.8B0.2`; only **117** of ~1,180 composition strings match literally, and the header is
  `H2_W%` against `H2_W% (max)`. So *"the four extra rows"* names nothing anyone could go and
  fetch — the join key was rewritten between the two files. What became of them, and what
  `(M)` meant, is a data-provenance question for **#89**, which already carries a HyStor
  row-count box. Nothing in the repository reads the spreadsheet, and nothing should start
  without that card.
- **#30, first box (the LOCO run has no resume, 4.7 h).** *"Accepted as-is for this run."* It is
  boxed so the **next** protocol that costs hours is built with checkpointing, not so this one is
  retrofitted.
- **#30, second box (the run is silent).** Same destination, and the reason is the seam rather
  than the effort: the fold loop is `hydms.surrogate.validation.nested_scores`, shared with
  `train`, whose run is already published — adding a print there changes the path behind a
  committed result. If it is done, it goes with the checkpointing as one change to that loop.

**Not a task — an obligation that travels.**

- **#30, third box (per-class scores carry no interval).** The headline transfer number is a point
  estimate over ten class folds with no stated uncertainty, and a class with nineteen rows weighs
  the same as one with two hundred. Nothing to build; it must be *said* wherever the number is
  published — **#83** (model card), **#37** (Chapter 1), **#89** (reconciliation). The per-class
  table carries `rows_scored` beside every row precisely so it can be said.
- **#14, second box (an impossible label sits in `val`).** Added 2026-09-12 when #14's first box
  was cleared. `Ce1Ni4Cr1` is recorded at 4.73 wt%, implied H/M **3.339** against `LaNi5H6`'s 1.0,
  and it is in the validation split — so it feeds early stopping and every validation figure. L3
  forbids touching a held-out row and that is the right rule, so there is nothing to build: it is
  a **stated limit**, boxed on **#83**. Say both halves wherever it appears — the defect *and* why
  it was left in place. A limits section that names the row without the reason reads as an
  oversight.

**None of this is an unfreeze condition, and none of it may become one.** If clearing a box turns
into real work, cut a card and mark it *not an unfreeze condition*, the way #92 is marked.

**Then #78.** It is unblocked (#76 and #77 both `done`), `fastapi 0.115.0` / `uvicorn 0.30.6` /
`httpx 0.28.1` already import in the `Project` env, and `tests/delivery/test_api.py` does not exist
yet — the Runnable check names a file you will be creating.

**Handoff, 2026-09-12 — QA on #77 found the second instance the last handoff told it to look for.**

The previous handoff's QA item 1 ended: *"Look for a second instance of that shape: any check that
reads a message without pinning which screen produced it."* There was one, in the same function,
one field over.

`probe.names` — the card's "naming the parse failure" and "naming the element" made executable —
tested `wanted in explanation`. Every one of those strings is **also a substring of the probe's own
formula**: `'Xx'` is in `'Xx2'` and `'LaNi5Xx2'`; `'Rn'` and `'Xe'` are in `'Xe1Rn1'`. Every refusal
sentence on this path quotes the composition it was handed, so the assertion could not fail for any
refusal that echoed its input. Measured: with the featuriser's sentence replaced by
`f"{formula}: cannot predict"`, HG-2 still reported **PASSED, 9/9 codes**.

**The fix is not the one the sibling check used, and that is the interesting part.**
`names_the_window` was repaired by reading the verdict of the screen that *owns* the code. That
could not be reused, because dumping every probe's verdict shows the three `indeterminate` probes
come back with **zero screen verdicts** — `featurize` raises before any screen is reached, which
#77 already documented for `unreadable-formula`. No screen owns the sentence; the featuriser does,
and it is not a screen. So the check subtracts the probe's formula from the explanation and asks
what is left. **When "ask the owner" has no owner, subtract the input.**

Nothing on the delivery path changed and no number moved — `v2` genuinely says
`Blocking element(s): Rn, Xe` today. What changed is that it now has to keep doing so. HG-2 stays
green (2.35 s against `v2`), 20 tests in the gate file where there were 19.

**The graph is current again.** Two `--update` runs took it from a 24-file build to **5,369 nodes /
12,308 edges / 229 communities**, with 0 documents unstamped. A new `.graphifyignore` scopes the
corpus to the project: it drops `Machine_Model/reports/` (122 archival plots) and `.claude/skills/`
(77k words of installed tooling prose). Note `graphify-out/manifest.json` is gitignored, so
incremental state is local to a machine; a fresh clone rebuilds from scratch.

**Handoff, 2026-09-11 — the board's blockers and stages were repaired; QA #77 next.**

**What moved, so you can trust the board again.** Four `blocked_by` edges and thirty-nine stage
lines were wrong, and none of them could go red — `check_board.py` reads ids, statuses, blockers
and links, and nothing reads a stage line at all. **#34** was `doing` with all four declared
blockers `done`, which reads as "ready to close", while the runbook said three times that promotion
waits on HG-2, HG-3 and HG-4; it is now `backlog` behind `[29, 31, 32, 33, 77, 79, 86]` and renamed
off `v1`, because `artifacts/v1` records `code_modified: true` and can never be promoted. **#89**
carried an edge to #34 that its own *Done when* does not support — its sources are #29's and #30's
committed CSVs, not a promoted pointer — so that edge is cut and **#89 is startable today**, which
also unshuts **#83**, whose model card must link to the file #89 writes (#83 and #37 gained that
edge). Thirty-nine cards stated the frozen board's `Phase 0/1/A` heading, or an S-number the map
contradicts; all sixty-five now state the stage this README assigns. **#92** is the card for making
that checkable instead of remembered — explicitly **not** an unfreeze condition.

**Read `S1`…`S12` in `tags:` as PRD user stories, never as stages.** `S10` on #78 is "explore
results without running code". There is no Stage 10. The stage is the bold line under the title.

**QA #77 before you open #78.** The gate is green — `python -m hydms.gates run HG-2` exits 0
against `v2` — so QA here is not "does it pass", it is **does it pass for its stated reasons**. Four
things are worth an hour, in this order:

1. **Make it go red on purpose, twice.** HG-2's three claims fail differently: give
   `PredictionResult` a default for `interval` (structural claim), add a `return 0.0` branch to
   `predict_capacity` (the read-the-exits claim), and confirm the gate names *which* claim broke
   rather than reporting one failure. #77's narrative records that staging the red case already
   found a defect — the "names the range" check was satisfied by a **neighbouring screen's**
   sentence, which is #49's partial-parse defect one layer up. Look for a second instance of that
   shape: any check that reads a message without pinning which screen produced it.
2. **Check the red-in-CI-but-not-green claim.** #77 says the structural half needs no artifact, so
   HG-2 can fail in CI where it cannot pass. Run `python -m hydms.gates run HG-2` in a tree with no
   `artifacts/` and confirm `SKIPPED`/exit 1 with the structural half still executed — not skipped
   wholesale. If the structural half is skipped with the rest, the gate is weaker in CI than it
   reads.
3. **Audit the `NOT_ALWAYS` split, which is the subtle part.** It separates "no fit can reach this
   code" (red if it appears) from "this fit does not" (reported). `untrusted-family` is in the first
   bucket at the request door and must stay unreachable there; `above-physical-ceiling` and
   `out-of-domain` are in the second on `v2`. Confirm nothing quietly moves a code from bucket one
   to bucket two to keep a run green — that is the failure mode the whole gate exists to prevent.
4. **Two of #77's own four named causes were not rules this system has.** There is no
   element-membership screen (`Tc2Ni` is *answered*, 4.17 against an 11.73 ceiling — #49 built
   novelty as a composition distance on purpose), and the AD ceiling is a **capacity**, not a
   distance (#48). Check `docs/REFUSALS.md` still says so; it is generated
   (`python -m hydms.delivery.refusals --emit`), so regenerate and diff rather than reading it.

**Then #78, which inherits one boxed finding and one standing obligation:** a `ContractError` must
become a **422** at the transport rather than a 500, and `GET /v1/model` should report
`ArtifactBundle.reference_digests`. Read #77's narrative first — `bundle_from()` is the seam it
added, the same split #33 made on `load_surrogate` one layer up, and `load_bundle` still refuses an
ungated version with a test pinning that.

**#81 and #89 are also unblocked** if you want parallel work: #81 is the chart vocabulary (pure
`hydms/figures/`, needs no API) and #89 is the reconciliation. **#7** is unblocked too but it is the
slow lane and it will want a machine.

Grep `../CONTEXT.md` for your card's number before you close it — **nothing reads that file**, no
test, no gate, no `--emit`.

**The knowledge graph is stale and a rebuild is a whole session's budget.** `graphify-out/cost.json`
records its last completed run as **2026-08-29** — it has never seen S5, S6, `hydms/delivery/`,
`hydms/screens/`, or any card from #75 up, so `CLAUDE.md`'s "ask the graph before you grep" will
answer you out of a corpus that predates the delivery layer. A rebuild was attempted on 2026-09-11
and **failed**: six subagents over 117 files / 1.26 MB of prose hit the session rate limit after
reading their chunks and before writing them, so nothing was salvaged and `graph.json` is untouched.
If you want it fresh, run `/graphify . --update` **first, before any other work** — the durable
caches under `graphify-out/cache/` replay what has not changed — and delete
`graphify-out/.graphify_{ast,cached,detect,uncached}.*` if it aborts again; they are untracked but
not gitignored, and a leftover `.graphify_cached.json` can be merged by the next run.

**Handoff, 2026-09-07 (latest) — #49 is `done` and S5 is closed.** `hydms/screens/novelty.py`
ships `novelty_screen()`, whose verdict frame carries `novelty.distance` and `novelty.nearest`
spelled exactly as `contract.Novelty` needs them. Three things to know before you touch it.

**The threshold rejects nothing on this corpus, and that is correct.** #48 had already removed the
calibration target this card was written to expect, so the ceiling is the corpus's own widest
internal gap — **11.7320**, from `Li0.94Pd1` to `Ce1Ni1`, computed by `--emit` rather than typed.
Against the held-out rows it fires **0 times in 385**. Do not "fix" that by lowering it: the card's
own last box warned that a threshold fitted to look busy on a chemically homogeneous corpus is
fitted to noise, and the distance rides on every verdict regardless, which is what AC-7 asks for.
It is **novelty evidence, never the applicability domain** — #48 measured why they are different.

**ElMD is installed (0.5.15) and it moved no pin, but it has two defects you inherit.** It returns
an *empty composition* instead of raising on an unparseable formula, so anything calling it must
check normalisation itself; and its `ratio_vector` is **not reproducible across processes** for
three or more elements, which is why `hydms.screens.novelty.vectors()` does the normalising sum
itself in sorted symbol order. Both are written up in `docs/LIBRARY-APIS.md` with the measurements.
CI now installs the `novelty` extra — the asymmetry with `parity` is deliberate and the reason is
in `ci.yml`.

**The decision left for you is on #76**, boxed there in full: putting the screen into
`delivery_screens()` makes an optional extra a hard requirement of every prediction. AC-7 arguably
demands it; the alternative is letting `PredictionResult.novelty` stay `None`, which is that
field's documented meaning and is also how a promise quietly becomes optional. `novelty-reference.json`
also inherits #48's pin-or-digest question — answer both the same way.

**Handoff, 2026-09-07 (later) — #73, #74 and #75 are `done`; S6 is open at #76.** All three
landed together and **two of them found that a box was asking for the wrong thing**, so read the
narratives before you trust the card text.

**#75 is the one that matters to you.** `hydms/delivery/contract.py` exists: `PredictionRequest`,
`Interval`, `ScreenVerdict`, `DomainVerdict`, `Novelty`, `PredictionResult`, `Refusal`, and
`answer_from()` — the one door back from JSON, which #79's transport-parity gate needs on both
sides of its comparison. The bare number is **unspellable**: `interval` and `domain` have no
defaults, so omitting one is a `TypeError` and passing `None` is a `ContractError`. `refused` is a
**property** on both answer types, never a field. The code set is derived by `reason_codes()` from
`delivery_screens()` — `temperature_window()` and `applicability_domain()`, #49 absent — and the
test asserts the set *equals* what the screens declare rather than naming the codes. Two boxes were
left for you, both on the cards that own them: **#76** and **#77** now carry the finding that an
unparseable formula and an unknown element have **no screen code**, that `INDETERMINATE` is the
answer (it is a rejection, and #48's screen already emits it for exactly this case), and that this
costs you an ordering choice — screen before featurising, or catch `FeaturisationError` and map it.
Pick one and say so in the ADR (#85). `novelty` is a required field that may be `None`, meaning
"not measured"; the day #49 lands, the vocabulary widens on its own.

**#73 runs the *live* stage order, not the card's.** `python -m hydms.pipeline.smoke` is
`load -> canonicalise -> split -> featurise -> merge -> screen -> select -> fit -> predict` in
**12.1 s** over a 235-row committed fixture at `hydms/pipeline/smoke-fixture.csv` (package data, so
it works in a container with no `Machine_Model/`). The card's arrows are the archival script's;
canonicalisation precedes the split because the split groups on the canonical key (L8), and the
merge follows featurisation because the merge this pipeline has is `with_features` (L9, L13). Three
things worth carrying forward: **`merge_features` still has no production caller** — #10's keyed
merge is exercised only by the L9 sentinel; **two budgets had to be invented**, `SMOKE_SPLIT`
(3x3 strata: 173 compositions cannot fill 25, and the second cut then hands
`StratifiedShuffleSplit` a class of one) and `SMOKE_FOREST_TREES` (screening was 18.5 s of a 21 s
run, because `label_issues` defaults to a 100-tree forest and CleanLab cross-fits it five times);
and **the fixture must be filtered by `computability(...).complete`**, because `Eu` is four empty
cells in the `jarvis` table and an Eu row kills the run at featurisation on a table defect rather
than a broken link.

**#74 contradicted two of its own boxes, and both contradictions are the finding.** A **case
change raises** rather than being absorbed — `Co` is cobalt and `CO` is carbon and oxygen, so a
case-folding parser would silently swap one material for another — and pairing case with whitespace
in one box is what made them look like one property. **Scale invariance is bit-exact only for
integer rescalings**: `La0.2Ni1` differs from `La1Ni5` by 2.776e-17, because `0.2 / 1.2` and `1 / 6`
are different binary numbers, so the featuriser gets a 1e-12 tolerance and the *booster* gets the
exact assertion. **Temperature is not monotone** (5 of 39 steps fall on a fixture whose target rises
by construction; `monotone_constraints` exists and this project does not set it). And the most
useful test in the file catches nothing: the response is **flat outside the fitted range**, which is
risk R1 measured rather than argued.

Nothing here needed a heavy run and nothing here promotes anything. Full suite **1229 passed,
0 skipped, 24 min 58 s** (up from 1153); `gates run --fast` 5 passed / 0 failed / 4 skipped with
HG-1 still 13/13; `check_board.py`, `check_freeze.py`, ruff and mypy all green.

**Handoff, 2026-09-07 — #73, #74, #75 and the start of S6.** Four cards are unblocked and three
of them are the ones to take, because **#49 is the only one that needs a decision you cannot make
alone**: `ElMD>=0.5` is declared as the `novelty` extra but is **not installed** in the `Project`
env, so that card starts with a GPL-3.0 dependency going into the maintainer's environment and an
API nobody here has run ([LIBRARY-APIS.md](../LIBRARY-APIS.md) says so) — and #48's box on it
already establishes that its threshold cannot come from the LOCO curve and that it is novelty
evidence for AC-7 rather than a domain verdict, so nothing downstream is waiting on it. Take
**#75 first**, because it is S6's opening card and the only one of the three that unblocks
anything: it defines `hydms/delivery/contract.py`, the package is still an empty docstring and
`tests/delivery/` is an empty directory, and its last box is the one that matters — **the refusal
codes are enumerated from the screens, never hand-written**, which as of #48 means `ADMITTED` plus
`temperature_window`'s two codes plus `ApplicabilityDomain`'s six (`OUT_OF_DOMAIN`,
`ABOVE_PHYSICAL_CEILING`, `OUTSIDE_FEATURE_RANGE`, `UNTRUSTED_FAMILY`, `HIGH_UNCERTAINTY`,
`INDETERMINATE`), derived from each screen's `reasons` at construction time so the set cannot drift;
note that the card's result field list still says "ElMD distance to the nearest known alloy" and
#49 does not exist, so decide deliberately whether that field is optional or whether the contract
waits — it is the one place #75 and #49 actually touch. Then **#73**, the end-to-end smoke run,
whose real work is the committed fixture rather than the runner: it has to hold multiple alloy
classes, a repeated canonical composition and a near-duplicate formula string, and it must clear
the whole chain in 60 s, so sample it against `hydms.data.canonical.collapse` rather than by eye —
and check the two traps this repo has already paid for, that a fixture under a gitignored path
never reaches CI, and that `--report`-style flags are input paths as well as output ones. **#74**
is the cheapest of the three and can go at any point: its permutation and scale cases
(`Ce1Mg12`/`Mg12Ce1`, `Mg1Al1`/`Mg0.5Al0.5`) are real cross-split collisions and are already
asserted at the featuriser, so the new ground is `predict()` and the temperature-monotonicity box,
which the card correctly frames as *record the actual behaviour rather than assert a wish* — measure
it before writing the assertion. One caution carried from #48: `Surrogate.predict()` returns
`q0.1/q0.5/q0.9/lcb/interval_width` and **no formula column**, while `ApplicabilityDomain` requires
one, so the predict-then-screen assembly is #76's and neither #73 nor #75 should invent a second
version of it. Both heavy runs are done and nothing here needs one; the full suite is **1153 green
in 20 min**, so budget for that rather than being surprised by it.

**Next session, in one paragraph.** **S4 is closed and the artifact to promote is now `v2`,
not `v1`.** #30 moved to `done` on 2026-09-07 -- its three unticked boxes are recorded findings,
not work -- and the deployed fit was re-saved from the clean tree at `4a06011`, so
**`artifacts/v2` records `code_modified: false`** where v1 records `true`. It is the same model:
correction **+0.037355**, identical to AC-1's, from the same `model-chosen.csv:outer-0`
configuration; v1 is superseded, not deleted, because a version is written once. **#34 itself
still cannot close, and that is by design** -- promotion needs HG-2, HG-3 and HG-4, built by
**#76-#79 (S6)** and **#86 (S8)**, and they are Phase H's own criteria so they **must not be
waived** (only AC-5, AC-7 and AC-8 are, and `tests/artifacts/test_waiver_scope.py` derives that
set from the board so it cannot quietly grow). **Four cards are unblocked right now: #49,
#73, #74 and #75.** ~~Five, including #48, which is the one with a decision in it: it has to say
what a macro transfer R2 of 0.2734 against a random-split 0.7459 means for the domain ceiling,
and #30's evidence says that ceiling cannot be a single scalar distance.~~ *(taken 2026-09-07.
The decision **dissolved** rather than resolving: both options -- per-family, or one distance
calibrated against the per-class curve -- assume the degradation is mediated by a composition
distance, and measurement says it is not. Per-class transfer R2 against per-class isolation is
Spearman **-0.2727** in element-fraction space and **-0.2848** in the model's own 14-feature
space, n=10, and inverted at the ends. The feature-space figure is what settles it for ElMD too:
the model reads fourteen numbers, so no metric over a space it never reads can be the mechanism
behind its failures. **The ceiling is a capacity: 5.19 wt%**, the highest level more than one
alloy class reaches in training -- above it the corpus holds 21 rows and every one is `Mg`, the
family #30 measured at R2 -0.3381. #48 is `done`; the box it left on **#49** says that card's
threshold cannot come from the LOCO curve either, and that it is novelty evidence rather than a
domain verdict.)*
**There is still no measurement left to take.** One trap found while doing the re-save and boxed
on #34: `calibrate --report` is both where the tables are written *and* where
`model-chosen.csv` is read from, so redirecting it silently falls back to CatBoost defaults --
the command says so on stdout, and the fit it saves is not the deployed one.

**The paragraph written when the run finished, superseded where the S4 close changed it:**

**The 4.7-hour run is done and AC-6 is green; every gate not
sitting behind unbuilt delivery work now passes.** The LOCO run happened once on 2026-09-06,
18:16:09 to 22:23:13 -- **4 h 07 m** -- and published macro transfer R2 **0.2734** against the
random-split **0.7459**. Measured after it: suite **1117 passed, 0 skipped** (29 min), gates
**6 passed / 0 failed / 6 skipped**, leaks 13 of 13, board and freeze OK. **The six remaining
skips are exactly two groups and neither is a gap in the surrogate:** AC-5, AC-7 and AC-8 are
frozen with Phases T and A and are the three `promote --waive` accepts; HG-2, HG-3 and HG-4 are
Phase H's own and are blocked behind the delivery cards that build them (#77 waits on #76, #79 on
#78, #86 on #6 and #79). **So the whole remaining distance to lifting the freeze is S6 onward
plus #34's promotion, #80's API doc and #37's Chapter 1 revision** -- there is no measurement
left to take. **#75 and #49 are unblocked right now** and neither is blocked by #34. ~~**One open
decision, and it is the maintainer's:** #30 is still `doing` ... and moving it to `done` is what
unblocks #48.~~ *(taken 2026-09-07: #30 is `done`, #48 is open.)* Full detail in the handoff dated
2026-09-06 (evening) below.

**Finishing S4, in one paragraph — written before it was finished, and kept for the reasoning
rather than the state.** **Eleven of S4's thirteen cards are done and the two that are
left are not the same kind of left.** **#30 is one status flip** -- every done-criterion is met,
its three open boxes are recorded findings rather than work (the absent resume, the silent run,
the per-class scores carrying no interval), and moving it to `done` is what unblocks **#48**; it
was left `doing` only because closing another person's card is the maintainer's call. **#34
cannot be finished inside S4 at all, and that is by design rather than an oversight**: promotion
now needs HG-2, HG-3 and HG-4, which are built by **#76-#79 (S6)** and **#86 (S8)**, and they are
Phase H's own criteria so they **must not be waived** -- only AC-5, AC-7 and AC-8 are waivable,
and `tests/artifacts/test_waiver_scope.py` derives that set from the board so it cannot quietly
grow. So S4 closes as far as a stage can close while one of its cards waits on two later ones.
**There is one piece of #34 that can be done now and should be, because it is cheap and its cost
is otherwise permanent:** `artifacts/v1`'s manifest records `git.code_modified: true` against sha
`5fd9be5`, honestly, because a concurrent session had uncommitted work when it was saved -- the
tree is clean now, `python -m hydms.surrogate.calibrate --save` costs **0.7 min**, and it writes a
version whose provenance stamp says what it should. Do that before promoting, not after, since
the note travels with the artifact. **Then S4 is spent and S6 opens at #75 and #49**, neither of
them blocked by #34.

**The review session's paragraph, superseded only where the run above changed it:**

**Nothing is half-finished and there is no open decision on the
board.** A review session on 2026-09-06 measured the phase end to end -- suite **1115 passed, 1
skipped** (21 min 21 s), gates **5 passed / 0 failed / 7 skipped**, leaks **13 of 13**, board and
freeze OK -- fixed the one code defect it found, and closed **#35**. **The whole remaining distance
to lifting the freeze is one command and one layer.** The command is
`python -m hydms.surrogate.loco --target capacity` (4.7 h, then `--emit`, then commit
`reports/loco/` **by name**), which turns AC-6 green with no code change and closes the suite's one
skip. The layer is S6 -- **#75 and #49 are unblocked right now** and neither is blocked by #34.
Start the run first, because nothing else can run beside it. Full detail in the handoff dated
2026-09-06 (review) below.

**And the session before that:** **#34's wall is down and #15's silent defect is closed; what
remains on the promotion path is work, not a decision.** #34's OPEN decision is **settled, and by
none of the three shapes it offered** — not a phase-scoped subset, not a fourth gate status, not
`require_gates=False` in the delivery path. A promotion may now name **waivers**:
`python -m hydms.surrogate.promote --waive AC-5 --waive AC-7 --waive AC-8`. The insight is that
the fix belongs to the *act* rather than to the criterion or to the rule — a promotion is already
a dated one-line decision in `current.json`, and all it lacked was the ability to say what it was
proceeding without. A **`FAILED` criterion is never waivable**; a passed one and an unknown name
are refused too; the reason recorded is the **gate's own** skip message, not prose typed at the
prompt; and the waiver dies when the pointer moves, because `load()` honours it only for the
version the pointer names. **`hydms/gates/` and `Manifest` are untouched** — that was the target,
not a side-effect: the promoted version's embedded report still says AC-5 was `SKIPPED`, so the
artifact's account of what was *measured* is as truthful as before. The guard against "out of
scope" drifting into "not done yet" is `tests/artifacts/test_waiver_scope.py`, which **derives**
the waivable set from the board (each gate's card, each card's board directory) and pins it at
`{AC-5, AC-7, AC-8}` — it is not in `scripts/check_board.py`, where it was written first, because
`artifacts/` is gitignored and a rule about a *committed* `current.json` would never once fire.
**#34 is still open and now blocked by work:** AC-6, HG-2, HG-3 and HG-4 are Phase H's own (#30,
S6's #76–#79, S8's #86) and **must not be waived**. **#15 is done.** Its owed box predicted
`screened.rows_out`/`screened.removed` would *move* once #24 landed; they cannot — `measure()`
calls `screen(raw, split)` with no `label_issues=`, so no CleanLab verdict has ever reached that
call and `screened.removed: 2` is permanently the structural answer, while the deployed path drops
**20 of 893** (18 CleanLab + 2 structural, reconciling with `reports/model/conformal-rows.csv`).
`tests/data/test_golden.py` now carries a second record, `DEPLOYED_SCREENING`, measured through
`hydms.surrogate.model.screened_rows` — the entry point `deploy` calls — plus
`screened.label_quality_findings: 0` so `GOLDEN` *states* that no judgement reached it. That test
is `slow` (~17.5 s of CleanLab cross-fitting) and CI runs it anyway: nothing else pins what the
pipeline drops. **#29's Q8 came to #15 and closed by arithmetic** — 1,115 vs 1,114 is one row,
`Eu1Ni5`, refused by the 21-feature contract and the sole row of its canonical composition, sitting
in `test`; Q8's own "temperature duplicates" hypothesis was wrong, since both numbers count
compositions. **#30 is built and handed over, and its 4.7-hour run is the one
thing this session did not do.** `python -m hydms.surrogate.loco` is `train`'s protocol with
`outer=leave_one_class_out` — one keyword argument, no second scoring path — and everything the
module adds is the *reporting* layer, because AC-6 asks that the extrapolation number be
published **alongside** the interpolation one and the ways a table fails that are all about
presentation. **AC-6's gate is written**, reads the committed tables rather than refitting (a
gate cannot pay 4.7 h, and one fitting a cheaper version would certify a number nobody
publishes), and its lane moved `SLOW` → `FAST`. `reports/loco/` had to be **un-ignored** —
under `/reports/*` the gate would read an empty directory in CI, the same trap `current.json`
sprang while settling #34, so *check whether a file reaches CI before writing a check that reads
it* is now a two-instance pattern here. **Owed:**
`python -m hydms.surrogate.loco --target capacity` then `--emit`, ~4.7 h (10 class folds x 3
inner x 25 trials at 22.6 s, about 2.0x the random-split run), then commit `reports/loco/` **by
name** — AC-6 goes green with no further code change. Sentinel-budget probe numbers, **not a
result**: macro R2 0.2240 against the random-split 0.7459, worst HEA -0.3026, best A2B 0.6703,
all ten classes estimable. That probe also **falsified a sentence the module had already
written** — the weighted average does not "flatter", it came out *lower* than the macro one — so
the document computes the direction instead of predicting it. Next: **S6** (#75–#80); note it is
**not blocked by #34**, since its tests can build their own versions with a stub gate report.
**Verified here:** `tests/data/test_golden.py` 8 passed in 20 s, `tests/artifacts/` +
`test_promote.py` 102 passed, `test_loco.py` + `test_ac6_loco.py` 31 passed 1 skipped, ruff and
mypy clean, `check_board.py` OK with the freeze in force, **full suite 1115 passed 1 skipped in
21 min 06 s** — the one skip is `test_the_committed_document_is_what_the_code_produces`, which
waits for the LOCO run and is guarded by AC-6 reporting the same absence as SKIPPED. **Stage by name** — this tree is
shared and `artifacts/` is gitignored.

---

## Reading the handoffs below

They are an **archive, newest first**, and they are deliberately **not corrected in place**: a
handoff is the record of what a session believed when it wrote it, and editing that after the fact
destroys the only evidence of what was known when. The cost is that some numbers below are
superseded. Here is every one of them, so nobody has to discover it by quoting it.

| Superseded | Correct value | Why it moved |
|---|---|---|
| Raw coverage **0.6628** | **0.6744** | The 2026-09-05 calibration ran nine hours before `model-chosen.csv` existed, so it silently used CatBoost's defaults |
| Correction **+0.030990** | **+0.037355** | Same cause |
| Width **0.7317 → 0.9155** (+25 %) | **0.6741 → 0.8951** (+33 %) | Same cause |
| Full run **~3.5 h** | **1 h 41 m** | The estimate predates #29's search-space narrowing |
| R² **0.746** (probe), **64.4 %** raw coverage (probe) | 0.7481 out-of-fold; 0.6744 raw | Probe numbers at reduced budget — never results |
| "L11 is deferred / 12 of 13 leaks" | **13 of 13** | #29 closed L11; `bf0b841` re-aimed it at the deployed fit |
| "`artifacts/` holds only `gate-results.json`" | `artifacts/v1` exists, uncertified | Written 2026-09-06 by `calibrate --save` |
| Probe macro R2 **0.2240**, worst **HEA** -0.3026, best **A2B** 0.6703 | macro **0.2734**, worst **Mg** -0.3381, best **SS** 0.7626 | Sentinel-budget probe. The real run sized the gap the same and named different families at *both* ends |
| Suite **1115 passed, 1 skipped**; gates **5 / 0 / 7** | **1117 passed, 0 skipped**; gates **6 / 0 / 6** | The LOCO run closed the skip and turned AC-6 green; the review session's promote test added the extra pass |
| "AC-6 is SKIPPED / the run is owed" | **AC-6 PASSED** | The run happened 2026-09-06, 18:16:09 to 22:23:13 |
| Any handoff implying CI was green | **CI had never once completed the `suite` job** | #86 read `gh run list` on 2026-09-12: every push run was `cancelled` or `failure`, the job timing out at its 20-minute cap against a 24 m 58 s suite. Local suite counts in older handoffs are still correct *about the machine lane*, and were never evidence about CI |
| "the four extra rows" in the HyStor spreadsheet | **Not identifiable** | The CSV is a renormalisation of the sheet, not a copy of it: 117 of ~1,180 composition strings match literally, so no join key supports a difference of four (#86, 2026-09-12) |

Anything else in an older handoff that contradicts a *card* — the card wins. Anything that
contradicts `docs/PHASE-H-RUNBOOK.md` on the phase — the runbook wins. The handoffs are narrative,
and their authority is over intent, not over facts.

---

### Handoff -- 2026-09-13 (latest) - #100 is repaired without a traceback, and three green runs were measuring nothing

**The suite is green: 1531 passed, 26 m 45 s, exit 0**, `pytest` with no `-m`, `--tb=long -rf`
redirected to a file, on a machine checked to be quiet before and after. That is the number to
quote, and it is the first one on this card that was measured under conditions anybody stated.

**#100's renderer is repaired and the card stays `doing`.** `hydms/figures/render.py` no longer
calls `matplotlib.use()` and no longer imports `pyplot`; it builds `matplotlib.figure.Figure`
directly and lets `savefig` attach the canvas the format needs, so `save()` has nothing to close
and the rendering path holds no process-wide state. `test_rendering_leaves_the_interpreter_as_it_found_it`
renders in a **subprocess** and asserts a fresh interpreter finishes a `save()` with pyplot
unimported and the stored backend unmoved -- in-process it would compare two identical values and
pass against the code it exists to reject. None of this is claimed as the fix: five full-length
runs since the filing are green, so **no traceback exists**, the card's second box stays unticked
on purpose, and only a future red run can tick it.

**The part worth carrying forward is not the repair.** Two sessions worked #100 concurrently in
this one worktree on the night of 2026-09-12/13, neither aware of the other, and **three of the
four green runs the card rested on overlapped each other**. One session landed its repair at
00:29:18 while the other's run -- started 00:10:59 -- had not yet reached the figures tests.
pytest imports test modules at collection but a production module whenever the code first reaches
it, so that run collected the *old* test body and then imported the *new* renderer off disk
twenty-five minutes later. Its green described a combination nobody wrote. The card recorded that
run as "on the same commit with a clean tree": true of git, false of the machine.

So **"clean tree" is not the check** -- `git status` cannot see another process. Before a run you
intend to quote a number from:

```
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select ProcessId, CreationDate, CommandLine
```

and print `Get-Date` either side of it, so a source mtime inside that window tells you the run was
not a measurement. Contention costs only a minute or two of wall clock here (26 m 45 s quiet against
28 m 24 s contended), which is the trap: **the number that misleads is the pass, not the duration.**
`docs/PHASE-H-RUNBOOK.md` §5 now carries this beside the two suite counts.

**Two findings boxed on other cards while passing through, neither actioned, neither an unfreeze
condition.**

| Card | Finding |
|---|---|
| **#1** | `matplotlib` is installed twice in `Project` -- conda's 3.9.2 metadata with pip's 3.10.1 written over it, one package directory, `_version.py` reading 3.10.1. So `conda env export` reports a version this machine does not run, and `pyproject.toml` floors it at `>=3.8` so CI resolves a third. First instance found where the shadowed package is one a *test* depends on |
| **#68** | **`scripts/check_board.py` has no done-card checkbox rule**, and #23, #29, #71, #94, #97, #100 and this README all state that it does. Its docstring lists six promises and boxes are not among them; nothing in `scripts/` or `tests/` reads a `- [ ]`; and #1, #14, #30, #34 and #86 are `done` carrying **eleven** unticked boxes while the checker prints `OK   100 cards`. The convention is good and worth keeping -- a `done` card's unticked boxes are how this board records a finding that is not work -- but it is a convention, and #97 and #100 were both *filed* on the belief that it was a check |

**S7's opening move is unchanged: #82**, `app/main.py` as an HTTP client of the service, handing
each `PredictionResult` to a builder in `hydms.figures`. It must not acquire a matplotlib call of
its own -- and after this card, there is no longer a global backend for one to fight over.

### Handoff -- 2026-09-12 (earlier) - #81 is done; S7 has started and the charts found two defects

**Start here.** Ask the board, not this block:

```bash
bash ../.claude/skills/kanban-ai/scripts/show_blocked.sh .
```

**What landed.** `hydms/figures/` — the chart vocabulary, three modules — and
`tests/test_figures.py`, 55 tests in 4.4 s, nothing marked `slow`. S7's first card is closed and
**#82 is unblocked** (78 and 81 both `done`).

**The shape, because #82 and #83 both build on it.** A chart is a *description* before it is an
image. `charts.py` builds `Figure` objects and imports no plotting library; `render.py` draws one
in matplotlib and is thin. That split is not tidiness — **every promise the card makes is a
property of the description**: a `Series` with `origin=PREDICTED` cannot be constructed without a
band, a quantitative `Axis` cannot be constructed without a unit, a `Panel` refuses a series or a
marker its axis would clip (so a builder widens the axis instead of clipping), and `Figure.shared`
makes "at the same scale" a checked equality rather than an intention. In the renderer, each of
those would have been a guarantee that only runs where a plotting library is installed, and CI's
install list would have decided which guarantees this project has.

**The five builders take the delivery contract's own types**, so the app stays an HTTP client: read
a JSON answer through `answer_from()`, hand the `PredictionResult` to a builder. No chart function
loads a model, reads an artifact, or touches the surrogate.

**Two defects the card found by measuring its own instructions, both filed, neither an unfreeze
condition.**

**#99 — the card told it a number that is no longer true.** *"Only 39 test rows sit above 500 K"*
traces to `REPORT.md:394`, a count over the archival pipeline's **247-row test split**. That split
does not exist under the group-aware nested protocol, which scores every row out of fold.
Measured against `reports/model/model-out-of-fold.csv`: **130 of 893**. The *claim* is untouched —
15.8 % then, 14.6 % now — and only the number was inherited, which is why `TemperatureSupport`
takes counts instead of carrying a constant. The string still stands in three production
docstrings and two tests.

**#98 — the honest protocol throws away the evidence a chart needs.**
`hydms/surrogate/train.py:369` writes `evaluation.out_of_fold`; `hydms/surrogate/loco.py:595`
writes four tables and that is not one of them. So the random-split protocol leaves 893 scored rows
and the leave-one-alloy-class-out protocol leaves ten class averages. `parity()` requires at least
**two** readings by construction — a parity plot of one protocol is the optimistic number on its
own page — so the figure #83 is meant to carry **cannot be built from committed evidence today**,
and the refusal's own message says so and names the card. The code change is small; getting the
table needs a LOACO run, which is the maintainer's. Do not relax `parity()` to draw the panel it
can.

**A word this project already spends, nearly spent twice.** `Series` was first written with a
`reading` field holding `measured` / `predicted`. "Reading" already means *which evidence set a
number was computed over* — the procedure, artifact and transfer scores are three readings of one
model, and `evaluation-metrics.csv` has a column of that name. Two senses in one module, one import
away from a page drawing both. The field is `Series.origin`; `parity(readings=...)` keeps the word
in the glossary's sense; `CONTEXT.md` now has the entry, and nothing enforces it but that entry.

**The palette is computed, not chosen.** Three slots, run through the `dataviz` skill's Node
validator on the **all-pairs** list in both modes: worst CVD ΔE 9.2 light / 9.4 dark against a gate
of 8, worst normal-vision ΔE 24.0 / 20.9 against a floor of 15. Three and not eight because the
reference palette's full set clears only the *adjacent* list and these are scatter and dot plots.
The light aqua raised the one contrast WARN, so slot 3 carries the relief rule: a series in it needs
a visible direct label, `Figure.relief()` reports any that does not, and **the renderer refuses such
a figure**. `tests/test_figures.py` pins every hex and every reported number — which cannot prove
the palette is safe, because the simulation that decides that runs in another language outside this
repository, but does force the command in `palette.py`'s docstring to be re-run rather than the
reasoning re-done.

**Open the PNGs. Two things only the rendered figure showed.** The sweep was first two panels side
by side sharing an x axis, and a support histogram *beside* the curve it supports is not the claim
the card makes — hence `Figure.layout='column'`, which is required to share x because stacking is
itself the claim that the panels line up. And the support bins are unequal (55 K to 100 K), so a
uniform bar width overstated the narrow bins by up to 2×; `Series.widths` carries the bin extent.
Both were invisible in the spec and obvious in the image, which is the last step of the skill's
procedure and the one easiest to skip.

**matplotlib is a new `figures` extra and CI installs it.** `figures = ["matplotlib>=3.8"]`,
`app = ["hydms[figures]", "streamlit>=1.30"]`, and the workflow now installs
`.[dev,uq,novelty,api,figures]`. Both lock files already carry matplotlib as a leftover of the
archival pipeline — `matplotlib-base=3.9.2` and `matplotlib==3.10.1` — so the floor names a version
`Project` already satisfies and nothing was re-solved. Naming it in CI is the point: an extra CI
skips is a guarantee nobody checks. It is a *separate* extra from `app` because `render.py` is its
only importer and the description tests must run with no plotting library at all.

**What #82 should not do.** Not add a matplotlib call of its own. A chart it needs that
`hydms.figures` does not have is a builder added *there*, with its guards — the five exist so the
prediction page and the model card cannot draw the same quantity two different ways, which is the
drift a per-page chart helper always reaches.

---

### Handoff -- 2026-09-12 (earlier, late evening) - #80 and #85 are done; S6 is closed and three of four unfreeze conditions hold

**Start here.** Ask the board, not this block:

```bash
bash ../.claude/skills/kanban-ai/scripts/show_blocked.sh .
```

**What landed.** `docs/API.md` (#80) and `docs/adr/0006-the-delivery-seam.md` (#85), written
together because #80's last box owes ADRs to `docs/adr/` and #85 is the ADR for the seam #80
documents. S6 is closed: #80 was its last card.

**The one question #80's card required answering before a word was written** — *how does a caller
tell a refusal from a genuinely low prediction?* — has a crisp answer, which is why the document
could be written at all. Three ways: `200` vs `422`, `refused` false vs true, and `capacity`
**present vs the key not existing**. The third is structural, not conventional: `refused` is a
property on both answer types rather than a field on either, and a `Refusal` has no field a number
could occupy. The page leads with `Mg2Ni` at 573 K, refused `high-uncertainty` for a 1.36 wt% band
against the 1.12 limit — refused for *width*, not for a small number, which is the case a caller
misreads.

**`docs/API.md` is generated. Do not edit it.** `python -m hydms.delivery.apidoc --emit`; the prose
lives in `hydms/delivery/apidoc.py` beside the facts, the arrangement `refusals.py` already uses.
It draws on three sources kept deliberately apart:

| Source | What it supplies | Needs an artifact? |
|---|---|---|
| the code, read live | reason-code vocabulary, batch limit, schema strings, element coverage | no |
| the committed `openapi.json` | the route table, summaries, status codes | no |
| the committed example fixture | every request and response on the page | **only to refresh it** |

**`--probe` is split from `--emit` because `artifacts/` is gitignored**, and a generator that
needed a live model would be a check that silently never runs — the trap already found on
`artifacts/current.json` (#34) and `reports/loco/` (#30). This was **verified, not assumed**: with
`artifacts/` renamed away, the check still reports the page current and all nine tests still pass.
The consequence for you: **after a new fit, run `--probe` or the page keeps describing `v3`** — it
says which version on its own face, so it goes stale visibly rather than silently.

**Reachability is now measured rather than hedged, and it will look like it contradicts the
gates.** A 50 x 10 sweep through the request door against `v3` reaches **8 of the 9** declared
codes; only `untrusted-family` is unreachable, structurally, because the API declares exactly two
fields. HG-2 and HG-3 report `above-physical-ceiling` and `out-of-domain` as *unreached on this
fit* — which is the honest statement for eleven probes, not a disagreement. `docs/API.md` carries a
paragraph saying so, and `CONTEXT.md` gained **Reachable** as a term with all three readings, since
this is now written three ways in three documents a reader will put side by side.

**A box was nearly ticked falsely, and the fix is on the page.** #80 asks the page to state the
trained ranges *including elements*; the draft had temperature, capacity, feature spans and the
LOACO table and no elements at all. They are derivable with no artifact from the novelty screen's
committed reference: **50 elements over 780 canonical compositions, 9 of them in two compositions
or fewer**. The page states it is **not a bound** — nothing refuses a composition for naming an
element outside the set, because the novelty screen measures distance instead — since a list on an
API page otherwise reads as a rule. `CONTEXT.md` gained **Trained range vs Applicability domain**
for the same reason.

**On the ADR numbering, so nobody re-takes it.** #85's ADR is **`0006`**, not `0001`. #36's
done-when names `docs/adr/0001..0005-*.md`, so those five are **reserved**; `docs/adr/README.md`
records the reservation, the reasoning, and #36's own standing decision that the card is not
renamed — *the ADRs are numbered, not counted*. #36's later candidates take `0007` onward.

**What the ADR argues that its title does not.** "The API owns no ML logic" is the easy direction.
The same seam means **the library owns no I/O**, and that is where a future reader will push,
because #91's rejected alternative — the library owning its own prediction record — is a real
guarantee. The ADR states the cost plainly instead of hiding it: **a script that imports the
library leaves no record.** It also names three conditions that *would* justify reversing the seam,
and one that would not (that the HTTP hop looks like overhead — it is the overhead that buys one
prediction path, and the 66-78 ms is measured).

**Next — and this handoff's first draft got it wrong, which is worth more than the answer.** It
said *"#89 is the only thing standing between this phase and its close"* and listed the interface
cards as skippable. Both halves were wrong. **The runbook's execution order puts S7 next**
(`S7 needs S6`, `S8 needs S7`, *"everything else is a chain"*), and **the interface is the phase's
stated objective**, not an optional extra — `docs/FREEZE.md` §Why says the freeze exists to stop
that interface being built on indefensible numbers, which presumes it gets built.

The error was collapsing *"not an unfreeze condition"* into *"not important"*. The unfreeze
condition gates the **frozen** board reopening; it is not a plan for Phase H.

So: **#81** (S7 entry, unblocked) is the next card, with **#89** beside it since it is independent
and #83 needs it. **#36** now has a directory and a convention to land into. #91, #94, #95, #96,
#97 are open; none is an unfreeze condition, and #97 is `High`.

**One thing this card did not cause and did not fix.** Before claiming the push was green I ran
`gh run list` and found the branch red on `test_comparison.py`'s byte-identity test. **The first
reading of that was wrong and is corrected on #97:** it looked like a platform difference, and it
is not — the same runner passed it twice afterwards on identical resolved versions. It is
*intermittent*, and the cause is `comparison.py:703` sorting with pandas' default unstable
quicksort over rows that tie at `rows_blocked == 1`. Filed as **#97** (`High`, not an unfreeze
condition, one keyword to fix). It could not go on #25 as a box — #25 is `done` and #26 is `done`
behind it, so reopening it makes `check_board.py` fail on a blocker that is no longer done.

**CI is green on the branch head**, and the `#80`/`#85` push run shows `cancelled` only because the
`#97` push superseded it — `cancel-in-progress` disguises a supersede as a failure-looking status,
which this board has been caught by before.

**Verification.** `tests/delivery` **179 passed** (up from 160); `tests/delivery` +
`tests/screens` **334 passed**. Fast lane `pytest -m "not slow" --cov`: **1461 passed, 4
deselected, 1038 s (17 m 18 s)**, coverage **87.89 %** against the 80 % floor. Gates `run --fast`:
7 passed / 0 failed / 2 skipped — AC-5 (frozen) and HG-4, which correctly reports that its coverage
data predates this change. ruff, ruff format and mypy clean. `pyproject.toml` gained `delivery/*.json` to package data, because the module's
docstring claimed the fixture ships in a wheel and it did not.

---

### Handoff -- 2026-09-12 (earlier) - the artifact is promoted; the unfreeze condition is half met and the rest is ordinary work

**Start here.** Ask the board, not this block:

```bash
bash ../.claude/skills/kanban-ai/scripts/show_blocked.sh .
```

**What happened.** The maintainer ran the promotion this session's predecessor handed over:

```
conda run --no-capture-output -n Project python -m hydms.surrogate.promote --waive AC-5 --waive AC-7 --waive AC-8
```

It certified `v2` -- 3 payloads, fitted at `4a06011` on 2026-09-06T21:31:41Z, notes `deployed
fit` -- with **9 passed, 0 failed, 3 skipped, 0 errored in 175.56 s**, then wrote **`artifacts/v3`**
carrying the gate report and pointed `current` at it. **#34 is `done`.** Two directories for one
model is the design working, not a mistake: a manifest is sealed when written, so the report cannot
be added to `v2`, and `v2` stays as the record of the fit.

**Where the unfreeze condition stands: two of four.** Every gate green -- met. An artifact version
promoted -- met. `docs/API.md` -- **#80**. The Chapter 1 revision -- **#37**, which now waits on
**#89 alone**. Nothing that remains needs a fit, a decision, or a pipeline run. **#36 is also
unblocked** by #34's close.

---

**Three things this close leaves behind, and the middle one is the interesting one.**

**1. #96 is new.** `calibrate --report` is both the directory a run writes its tables to and the
directory `deploy.py:163` reads `model-chosen.csv` from. Redirecting it to a scratch directory --
the careful thing to do -- makes the chosen configuration unfindable and falls back to **CatBoost's
own defaults**, and `--save` then persists that as `deployed fit`. It happened on 2026-09-07: a
correction of **+0.030990** instead of +0.037355, caught in a minute because the command says so on
stdout. It was a box on #34; it is a seam decision, so it got a card.

**2. `promote` copies payloads; only a fit can change them.** #34 carried a box reading "the next
version's payload set drops `SCALER_PAYLOAD`", boxed there "because this card writes the next
version". #34 *did* write the next version -- **and `v3` carries the scaler**, because a promotion
certifies and copies, it does not fit. The box moved to **#7**, whose retrain is the next actual
fit. `CONTEXT.md`'s *Artifact version* entry had already promised that "the next version written
holds a model, its correction and a manifest"; it was falsified within a day, by a command nobody
thought of as writing a version. **The correction is kept in the file rather than tidied away** --
nothing tests `CONTEXT.md`, so a prediction written into it is a claim no diff can go red on.

**3. The promotion did not make the model portable.** `artifacts/` is gitignored. `v3` is on the
maintainer's machine and nowhere else; a fresh clone has no model and `predict()` refuses there.
That is card **#7**'s to fix, and it does not reopen the unfreeze bullet, which asks for a promoted
version and not for a portable one.

---

**One box was ticked without being worked, and it is worth saying why.** #34's "the waiver summary
counts wrong, and no test asserts the string" had been *fixed* -- `promote.py:222` prints
`len(outstanding)` and `test_promote.py:335` asserts the rendered sentence -- and nobody had ticked
it. The real run confirmed it: 9 passed and 3 waived printed **"0 of 12 criteria left to
establish"**, which is `len(outstanding)`; the broken expression would have said 9. **Read the code
before believing a card's open box**; a box can outlive its defect, and an open box on a closing
card is the last moment anyone will check.

### Handoff -- 2026-09-12 (superseded) - every reachable gate is green; #34 is one command from done, and that command is the maintainer's

**Start here.** Run this, and nothing else, before planning anything:

```powershell
conda run --no-capture-output -n Project python -m hydms.surrogate.promote --waive AC-5 --waive AC-7 --waive AC-8
```

It is **three minutes and fits nothing.** It writes a new sealed version carrying the gate report
and points `current` at it, which is **the unfreeze condition's second bullet**. Do not run it from
an agent session: it was denied here by auto mode (*Blind Apply*), and correctly — it moves the
pointer `predict()`, the API and the model card all read.

---

**The gate run, so you do not pay 194 s to learn it again.** `promote --dry-run` against `v2`
(fitted at `4a06011`, 2026-09-06T21:31:41Z, `code_modified: false`, catboost 1.2.8) returned
**9 passed, 0 failed, 3 skipped, 0 errored**. The first time every reachable criterion has been
green at once. The full table and AC-1's per-metric agreement are on #34; the headline is that the
three skips are AC-5, AC-7 and AC-8 — all frozen, all exactly the three #34 settled as `--waive` —
and the four the runbook says must **never** be waived (AC-6, HG-2, HG-3, HG-4) are green, their
owing cards #30, #77, #79 and #86 having closed. The command then refuses, correctly: *"a SKIPPED
gate is a criterion nobody checked."*

**Correcting a claim this board carried for weeks, and which this session repeated twice before
checking: #34 needs no fit.** Step 4's 1 h 41 m is already paid, `model-chosen.csv` is committed,
`reports/model/` holds its numbers, and `artifacts/v2` is the deployed fit built from that
configuration in about two minutes. `docs/RUNNING-THE-FIT.md` Step 9.5 says promotion *"fits
nothing"* apart from AC-1's two fits, which are most of those 194 seconds. **Read the operator doc
before repeating a cost estimate from card prose.** The deferral to the maintainer still stands,
but for consequence rather than for wall time.

**`artifacts/` is gitignored, so `v2` exists on the maintainer's machine and nowhere else.** A
fresh clone has no model. If the promotion is run somewhere else, it has nothing to certify.

---

**What #93 was, in one paragraph**, because the card that filed it guessed wrong and the guess is
instructive. Two tests failed only on CI. The suspect on record was Linux, a different BLAS and a
two-core runner. The variable was the `pip install` line: `suite` resolves `pyproject.toml`'s
**floors**, not `requirements-lock.txt`, and `catboost>=1.2` resolved to **1.2.10** against the
`Project` environment's **1.2.8**. A venv on the resolved versions reproduces both failures **on
the maintainer's Windows box** to every digit; restoring scikit-learn and pandas and leaving
CatBoost at 1.2.10 leaves them unchanged. **One wheel.** Neither test was fixed with a tolerance:
one compared a constant (calibrated coverage is the conformal rank over n, `46/56`, everywhere) to
a variable (raw coverage, 49/56 here and 44/56 there), and the other demanded positive widths where
`quantile_metrics` measures quantile crossing at **23 % of rows**. The recipe for rebuilding the
CI-resolved venv is in #93's *Runnable check*; a CI-only failure costs one `gh run view`, not a
round trip.

---

**Three cards were opened and one PR closed, none of them unfreeze conditions.**

**#94** — a crossed band leaves the surrogate as a negative width by design, and
`hydms.delivery.contract.Interval` raises `ContractError` on it. `hydms/delivery/predict.py` never
checks the sign, so that is a loud failure rather than a refusal with a reason code. Its first box
is *measure before adding a code*: the candidates that cross are the ones #48 and #49 should
already be refusing.

**#95** — the freeze is unenforced on `main`, which has no `check_freeze.py` at all. PR **#7** was
green and MERGEABLE while editing six cards under `kanban/`, because the check was **absent**, not
passing. It is now **closed unmerged** (`mergedAt=null`; branch left on origin at `d07a66e`), so
#6 is the only open PR. What #95 still owes is one paragraph in `docs/FREEZE.md`: `main` gets a
freeze check only when #6 merges, and the freeze prevents that until it lifts. **Bounded, not
fixed.**

**A box on #7** — the slow lane must install from `requirements-lock.txt`, because a floor-resolved
retrain is not a retrain of the published pipeline.

---

**Two things this session could not run, and both should be handed on rather than routed around.**

| Command | Denied as | Cost | Why it matters |
|---|---|---|---|
| `promote --waive AC-5 --waive AC-7 --waive AC-8` | *Blind Apply* | ~3 min | The unfreeze condition's second bullet |
| `pytest -m slow` | *CI Bypass* | ~15 min | The four tests **no push checks any more** — #7's open box |

**Where the unfreeze condition stands.** Every gate green — the dry-run now says yes. An artifact
version promoted — **the command above**. `docs/API.md` — **#80**, startable. The Chapter 1
revision — **#37**, which waits on #34 and #89. So two of four are answered and the other two are
ordinary work. **#81, #85, #89, #91** are startable in parallel.

Ask the board rather than trusting this paragraph:

```bash
bash ../.claude/skills/kanban-ai/scripts/show_blocked.sh .
```

---

### Handoff -- 2026-09-12 (earlier today) - #93 closed, #86 closed, the lane is green

**The two CI-only failures were not what the card that filed them guessed, and the difference
matters more than the fix.** #93's "Why this exists" reasons from AC-1's thread-invariance
docstring to Linux, a different BLAS and a two-core runner. Every link in that chain is plausible.
None of them was the variable. The `suite` job runs

```
pip install -e ".[dev,uq,novelty,api]"
```

which resolves **`pyproject.toml`'s floors** — not `requirements-lock.txt`, not `Project`.
`catboost>=1.2` resolved to **1.2.10**; `Project` holds **1.2.8**. A throwaway venv on the resolved
versions, **on the maintainer's own Windows box**, reproduces both failures to every digit the
runner printed; restoring scikit-learn and pandas to the `Project` versions and leaving CatBoost at
1.2.10 leaves them unchanged. **The cause is one wheel.**

The practical consequence for whoever hits the next CI-only red: `gh run view <id> --log | grep
"Successfully installed"` costs one command, and a venv on those versions turns a thirteen-minute
round trip into seconds. #93's *Runnable check* now carries the recipe. Do not start from `uname`.

**Neither test was fixed by choosing a tolerance, and `1e-09` was never the question.**

*`test_calibration_moves_coverage_toward_nominal`* compared a **constant to a variable**.
Calibrated coverage on the calibration rows is `ceil((n + 1) * level) / n` = **46/56 =
0.8214285714285714**, identical on all three installations to every digit, because split CQR takes
the correction to be the k-th smallest conformity score and exactly k of n rows then sit inside the
widened band. It knows nothing about the fit. The **raw** coverage is the fitted half and moved
49/56 → 44/56. So the old assertion was really "CatBoost's uncalibrated heads are worse than the
conformal overshoot" — and **conformal prediction never promises coverage nearer nominal, only
coverage ≥ nominal**. On a finite calibration set the guaranteed value overshoots by up to
`(1 + level) / n`, so a *better* uncalibrated model pushes the calibrated number further away and
the test must fail. The runner failed it by fitting a better model. It now asserts the rank
identity, the `>= nominal` guarantee and the overshoot bound — three theorems — and is renamed
`test_calibration_pins_coverage_at_the_conformal_rank`.

*`test_the_width_is_the_calibrated_span_and_varies_row_to_row`* asserted
`(frame[INTERVAL_WIDTH] > 0.0).all()` and **contradicted a decision this repository had already
made and measured**. `quantile_metrics` counts `crossings` because "MultiQuantile fits the heads
jointly but does not constrain them to be monotone … measured at **23 % of rows** on a small fit"
(`model.py:1291`), and `conformal.py`'s header states that **CQR's widening cannot repair a
crossing**. Two of its three candidates — `Ti1Fe1`, `Mg2Ni1` — are outside the fixture's La–Ni
training family, and on the runner they came back at **−0.094422** and **−0.029760** wt%. The test
was asserting that three extrapolation candidates all dodge a 23 %-likely event; it passed here at
roughly coin-flip odds. The sign claim is gone, the test is
`test_the_width_is_the_calibrated_span_and_is_not_one_constant`, and a deterministic sibling,
`test_a_crossed_band_reaches_the_caller_unclipped`, pins the behaviour on the assembly step where
no fit can move it. **AC-3 inherits nothing to weaken** — it measures coverage on the *test* split,
which is generalisation; this was only ever arithmetic on the calibration rows.

Both tests now build a `measured` string — coverages, counts, the rank, the correction, the raw
crossings, the widths and the heads — so the next red reports its numbers instead of `assert False`.

**Two things were filed rather than fixed here.**

**#94** (new, `backlog`, *not an unfreeze condition*): a crossed band leaves the surrogate as a
negative width by design, and `hydms.delivery.contract.Interval` then raises `ContractError` on
`upper < lower`. `hydms/delivery/predict.py` never mentions crossing, so that is a **loud failure,
not a refusal carrying a reason code** — the one shape of answer this project has decided it does
not give. A batch screen loses the batch on one bad row; the API returns 500. The card's first box
is *measure before adding a reason code*: the candidates that crossed are exactly the ones #48 and
#49 should already refuse, and a code no request can reach is the defect #90's reachability check
exists to find. #77, #90 and #48 are all `done`, which is why it is a card and not a box.

**A box on #7**: the slow lane must install from `requirements-lock.txt`. #7 already said it is the
only lane that rebuilds the pinned environment, on the grounds that nothing otherwise proves
`Project` still recreates. This is the sharper reason — **a floor-resolved retrain is not a retrain
of the published pipeline**, and promoting a version fitted by a wheel nobody pinned puts a silently
different model behind `current`. The fast lane installing from floors stays correct and
deliberate; what it owes is to *say* which versions it resolved.

**A graph edge was removed.** #93 carried `blocked_by: [86]`, which pointed the wrong way: #86
*found* this card, which is not the same as this card needing anything from #86, and #86's own last
box says "Blocked on #93". `check_board.py` therefore refused to let #93 move to `doing` at all,
while the only card that could open #86 sat behind it. Audit an edge against the card's own
*Done-when*, not against the prose that created it.

**Where the board stands.** #86 and #93 are `done` against run **`34698963428`** — hygiene green
in 13 s, `suite` green in **14 m 12 s**: `1443 passed, 9 skipped, 4 deselected in 12 m 45 s`,
coverage **88.77 %** against the 80 % floor, fast gates `3 passed, 0 failed, 6 skipped, 0 errored`.
The same selection on the maintainer's machine is `1452 passed, 4 deselected in 12 m 13 s` — the
nine-test gap is the nine that skip on the runner, which is what #86 measured and why a percentage
in a progress bar cannot identify a test. #34 — train and
publish the deployed artifact version — is the next unblocked card and it is the unfreeze
condition's second bullet; it is a **multi-hour fit and the maintainer runs those**, so build and
verify at sentinel budget and hand over one command. #80, #81, #85, #89 and #91 are startable in
parallel. Ask the board rather than trusting this paragraph:

```bash
bash ../.claude/skills/kanban-ai/scripts/show_blocked.sh .
```

---

### Handoff -- 2026-09-12 (earlier) - #86 is written but NOT closed; the lane works and #93 is why it is still red

**#86 is `doing` with one box open, and the box is the point of the card.** Everything else in it
is done: the HG-4 gate is implemented and registered, `--cov` and `-m "not slow"` are in the
workflow, `--summary` writes the verdict into `$GITHUB_STEP_SUMMARY`, and both dependency
decisions are made. What is not done is *verification*, and it cannot be done from the machine.

**Start here, before you read any file:**

```bash
gh run list --limit 5          # is there a green push run yet?
gh run view <id>               # per-job outcome, and the ANNOTATIONS block
gh run view --job <id> --log   # the only place the error text lives
```

**Why this is the first thing.** #86 found that **CI has never once completed the `suite` job on
this branch.** Every push run in the history is `cancelled` or `failure`. `cancel-in-progress`
made that look like ordinary supersession; it was not. The newest run — the only one with no
push after it to blame — carries *"The job has exceeded the maximum execution time of 20m0s"*.
The job caps at 20 minutes and the full suite is 24 m 58 s, a number the runbook has recorded
since 2026-09-07. Both facts were written down in different files and nobody had multiplied them.
So: **no handoff below this one was ever evidence about CI**, however green its local numbers.

**What #86 changed, and what it costs.**

- The `suite` job now runs `pytest -m "not slow" --cov`. `-m "not slow"` is what
  `pyproject.toml` has said the marker means since #69 (*"excluded from the CI fast lane"*) and
  the workflow had simply never done it. The log shows the old job reaching 89 % and then
  stalling nine minutes with no output, which lands exactly at
  `tests/surrogate/test_selection.py` and its eleven-minute Boruta test.
- **The four `@pytest.mark.slow` tests are now checked on no push at all.** That is a
  deliberate regression, boxed on **#7**, which owns repaying it. It is worse than a lane that
  ran them and better than a lane that timed out before reaching the gates.
- CI's `mypy` was **red**, on six `import-not-found` errors for fastapi/uvicorn/pydantic that
  #78 and #79 added without touching `[[tool.mypy.overrides]]`. It passed locally **only
  because this machine has those packages installed and a bare runner does not**. Fixed, and
  the lesson is in the runbook §5: reproduce the lane with a bare venv, not with your `mypy`.
- `pytest-cov` is now in `Project` as well as the `dev` extra. Full-suite **test** coverage is
  **88.43 %** against the 80 % floor. (`CONTEXT.md` now separates *test* coverage from
  *conformal* coverage — they are both percentages in `gate-results.json` and mean nothing
  about each other.)

**The one thing you must chase — and it is now named, in card #93.** The commit was pushed while
this session was still open, so the answer arrived rather than being left as a guess. Run
`34696231293`: hygiene **green in 16 s**, suite **finished in 13 m 40 s** — the first completed
`suite` job this branch has ever had — and it reported two failures that **pass locally on the
same commit**:

```
FAILED tests/surrogate/test_conformal.py::test_calibration_moves_coverage_toward_nominal
  - assert 0.021428571428571352 <= (0.014285714285714346 + 1e-09)
FAILED tests/surrogate/test_predict.py::test_the_width_is_the_calibrated_span_and_varies_row_to_row
  - assert False
```

That is a claim about the surrogate's numbers on hardware that is not a twenty-core Windows box;
AC-1's own docstring warns that its thread-invariance measurement buys no cross-platform
determinism. **#93 owns it, and #86's last box is blocked on it.** #93 is explicitly *not* an
unfreeze condition.

*An earlier draft of this handoff guessed those failures were near `test_model.py` and
`test_promote.py`, by mapping the 84 % and 89 % progress marks onto the collection order. That
was wrong — CI skips nine tests the machine does not, so the orders differ. **Do not identify a
test by its position in a progress bar.** The fix was to make the run print its own summary.*

**Then:** tick #86's timeout box against a green `suite` job and close it. #86 is the last
unfinished blocker on **#34** (promotion), which is the unfreeze condition, so closing it is what
unblocks the critical path. #80 (S6's last card), #81, #85, #89 and #91 remain startable in
parallel and none of them is touched by this.

**Unchanged and still parked:** the three deferred boxes, #30's third box, and #1's OPEN
maintainer decision about re-solving the lock. #86 added `coverage` and `pytest-cov` to
`requirements-lock.txt` by pip, which is the #27/#49 precedent and **not** a re-solve — it does
not touch that decision. While counting, the lock header was found stale at 209 against 210
actual; it now says 212 and `docs/ENVIRONMENT.md` agrees.

---

### Handoff -- 2026-09-12 (later) - #78 is done; #79 is yours, with #85 and #91 beside it

**What landed.** `hydms/delivery/api/` — `service.py`, `schemas.py`, `__main__.py` — over a new
`hydms/delivery/modelcard.py`, serving `POST /v1/predict`, `POST /v1/predict/batch`,
`GET /v1/health` and `GET /v1/model`. Every box on the card is ticked and one of them carries a
stated qualification rather than a silent tick; see the card.

**Numbers, with the command that produced each.** `pytest tests/delivery/test_api.py` — **32
passed, 13.6 s**. `pytest tests/delivery` — **145 passed, 30.8 s**. `pytest tests/gates -m "not
slow"` — **116 passed, 1 deselected, 21 min 47 s** (that figure was measured on a loaded machine
and is a ceiling, not a benchmark). `python -m hydms.gates run
HG-2` — **1 passed, 6.2 s**, against `v2`, untouched by this card. ruff and mypy clean over
`hydms/ tests/ scripts/`. `check_board.py` OK over 92 cards; `check_freeze.py` OK over 298
changed paths.

**The one design decision, and it was forced.** Two authorities put two unrelated things at
HTTP 422 — the card ("a malformed request is a 422 with a structured body") and the runbook's
acceptance `curl` ("a structured refusal … HTTP 422"). So the status code cannot carry the card's
next box, and the distinction lives in the body: `refused` on an answer, `error` on a rejected
request, no shared key, and `answer_from()` refusing the second rather than half-reading it. The
term is in `CONTEXT.md`; the gate obligation is boxed on **#79**; the ADR argument is boxed on
**#85**.

**Two things #79 inherits.** (a) The 422 carries two shapes and HG-3 should measure both,
including that `answer_from()` *refuses* the error body — a client that reads one as the other
fails silently. (b) The HTTP door accepts no field `predict_capacity()` does not (`extra="forbid"`
over exactly `formula` and `temperature_k`), which is what kept `untrusted-family` unreachable at
the request door and HG-2 green without an edit. Pin it there.

**What #78 measured, for whoever hits it next.** A served prediction is **66–78 ms** against
`v2` — 13 ms featurise, 22 ms surrogate, 34 ms across the three screens — with no hot spot and
nothing amortised across candidates, because each goes through `predict_capacity` as its own
one-row frame. The batch limit of **256** is that arithmetic against a 60 s client timeout, and
the consequence for a real CSV is boxed on **#84**: the fix is a batched call in the library, not
a larger limit.

**Two small changes outside `api/`, both argued in the card's narrative.** `ArtifactBundle` now
carries the version's `manifest` (`None` through the gate door, so an absent record reads as
*unknown* and never as clean) and `tests/delivery/test_predict.py`'s public-surface assertion
grew `manifest` with a comment saying why.

**The service cannot actually serve yet**, and that is the card working: it resolves the
*promoted* version at startup and nothing is promoted, so `uvicorn hydms.delivery.api:app` exits
with `load_bundle`'s own sentence. **#34** is what changes that, and it still needs HG-3 and
HG-4.

---

### Handoff -- 2026-09-12 - #77 is QA'd and stays done; #78 is yours

**What QA established, before what it found.** `hydms.gates run HG-2` **PASSED in 2.35 s** against
the deployed `v2` — 9/9 codes, 3 exits read from source, 11 probes, 3 answered and 8 refused.
`pytest tests/gates/test_hg2_refusal_path.py tests/delivery` **133 passed in 13.4 s** (was 132).
ruff and mypy clean. `check_board.py` OK over 92 cards; `check_freeze.py` OK over 291 changed paths.

**What it found.** Three of the gate's assertions were decoration — see the dated handoff at the
top of this file for the full account. The short version: `wanted in explanation` where every
`wanted` is also inside the probe's own formula, and every sentence quotes its formula. Staged red
by degrading the featuriser's sentence; the gate stayed PASSED. Fixed by striking the input out of
the sentence first, and pinned by
`test_a_sentence_that_only_echoes_the_formula_does_not_count_as_naming`.

**A second, smaller one, in my own fix.** The first version of the new failure message said
"nowhere but inside the echo" even when the string was simply absent — a guard naming a cause it
had not observed, which is a box #77 already carries about `PredictionRequest.__post_init__`. Split
into its two real cases before committing. Worth saying because it happened *while writing the fix
for exactly that defect class*.

**The fast lane.** `conda run -n Project python -m pytest -m "not slow"` — **1371 passed, 4
deselected, 647.90 s**, run on the final tree after every edit. That is the previous session's 1370
plus this card's one new test, and the four deselected are the slow tests the lane always defers.

**Your card is #78** (FastAPI service: predict, batch, health and model), unblocked now that #76
and #77 are `done`. **#89** (REPORT.md reconciliation) and **#92** (the stage line checked rather
than remembered) are startable beside it and neither is an unfreeze condition.

**One thing to carry into #78.** #77 established that reachability is *per door*, and the API is a
third door. `untrusted-family` is `NEVER` at the request door because a caller supplies no
alloy-class label — if #78's batch endpoint accepts a frame with a class column, that changes, and
`NOT_ALWAYS` in `hydms/gates/hg2_refusal_path.py` is where it has to be said. HG-2 goes red if it
becomes reachable and nothing says why. That is the gate working, not the gate breaking.

### Handoff -- 2026-09-11 (later) - #76 is tested and QA'd; #77 is yours

**The QA pass asked for below has run.** #76 stays `done`. Three findings, one fixed in place and
two boxed; nothing was mis-refused and no number was wrong, which is worth saying because all three
are about a guard or a sentence rather than about arithmetic.

**Fixed on #76, because it is #76's own code.** The card's one added guard, `_check_heads`, was
aimed one step away from its subject and covered one of the two columns that need covering. The
premise is sound and worth carrying forward: `ApplicabilityDomain` is deliberately **partial** --
it judges whichever of its signals a frame carries, so a column it cannot find does not raise, the
rule simply does not run, and the screen answers `admitted` because nothing judged it. It is the
only screen that can do that; the window and the novelty screen both raise `ScreenError`. The
bundle is the first object that knows both what the screens will look for and what `_candidate`
writes, so this layer is the only place the two can be made to agree -- and it was comparing
*config*'s median head to the artifact's, never reading the screens it was handed. Those agree on
the default path, the one path where the check is redundant; on an explicit `screens=`, which is
how #78 and every test here assemble a bundle, nothing was checked. Measured: a domain screen aimed
at `q0.42` loaded silently, and one aimed at a different `width` answered `PredictionResult` with
`domain: admitted` while `high-uncertainty` -- the only rule that judges the *band* -- could never
fire. `_check_columns` now reads each screen's own `prediction` and `width`. `alloy_class` stays
deliberately unrequired and has a test saying so.

**Boxed on #77, and they are the same question it already owns.** Both are *wrong words*, the class
§4.8 of the protocol exists for. (a) A formula that is not a string is told "the formula is empty"
-- false about the input, reachable through `from_dict` from any JSON or CSV transport, and an
asymmetry inside one `__post_init__`, since `temperature_k` one line below distinguishes its two
arms properly. (b) `docs/REFUSALS.md` catalogues the *screens'* sentence for `unreadable-formula`,
which `predict_capacity()` cannot produce: `featurize` raises first, so a typed `LaNi5Xx2` comes
back with the featuriser's sentence and zero verdicts. Two true sentences, and the page shows the
one the API will not send. #77 already carries this shape for `untrusted-family`; it is now three
rows, and the gate owns the qualifier.

**What is still not done, unchanged from below:** the module has **not** run against a real fitted
artifact. `v2` records no gate run, so `load_surrogate` refuses it -- correctly -- and that is
**#34**'s to close. Every QA measurement above was taken against the fixture store.

**#77 is the unblocked card.** 28 tests in `tests/delivery/test_predict.py`, 4.9 s; fast lane
(`pytest -m "not slow"`) **1337 passed, 4 deselected, 643 s** — 1334 plus these three; `ruff` and
`mypy` clean; `check_board.py` and `check_freeze.py` green; the gate harness reports 6 passed /
6 skipped, with HG-2 still skipped because #77 has not built it.

---

### Handoff -- 2026-09-11 - #77 is closed; HG-2 is green against a real artifact; QA it, then #78

**Do this first, before any card.** The maintainer has asked that the next session **fix the
board's blockers and stages** before taking new work: the `blocked_by` graph and the stage
assignments have drifted from the runbook's prose, and S4 already taught this board that the
arrows and the graph disagree (#88 opened S4, not the #24 the prose pointed at). Ask the board,
not the prose: `bash $S/show_blocked.sh .` and `bash $S/list_all_cards.sh .`, and reconcile
against `docs/PHASE-H-RUNBOOK.md` §2. Then the QA pass below, then #78.

**What you are being asked to do next.** Take a QA pass at **#77** before starting #78 -- the
**L6** row in `docs/QA-PROTOCOL.md` §2 and the reviewer checklist in §4. HG-2 is the gate this
whole phase is named for, and a gate that quietly establishes nothing is worse than no gate. Then
#78, the FastAPI service.

**Start with the runnable check.**

```bash
conda run -n Project python -m hydms.gates run HG-2          # 2.5 s, green against v2
conda run -n Project python -m pytest tests/gates/test_hg2_refusal_path.py
```

**The thing that changed, and it is not small: `predict_capacity()` has answered from `v2`.**
Every handoff since #76 has carried "the module has never run against a real artifact -- `v2`
records no gate run, so `load_surrogate` refuses it". That is the *same knot* card #33 untied one
layer down, and it takes the same resolution rather than a waiver. `bundle_from(surrogate, ...)`
is everything in `load_bundle` below the version lookup; HG-2 loads its candidate through
`gates/_artifact.candidate` (`require_gates=False`, the door the store documents) and assembles
the bundle `load_bundle` would have. **`load_bundle` grew no parameter and lost no guarantee** --
`test_the_version_it_scored_is_one_the_delivery_path_refuses` names `v1` explicitly and demands
`GatesIncomplete`, so the escape cannot widen without something going red. Read that test first
if you are checking anything here.

**Three claims, and only one needs an artifact -- so HG-2 can go red in CI where it cannot go
green.** The structural half (no default for `interval` or `domain`, no field a number fits in on
`Refusal`) and the exhaustive half (every `return` in `predict_capacity` **read from its source**
and required to be one of the two contract types) both run in an empty checkout. `.gitignore`
excludes `/artifacts/`, so the behavioural half skips in CI and reports `SKIPPED` rather than a
pass. That asymmetry is deliberate; do not "fix" it by fitting a model inside the gate.

**Two of the card's four named causes were not rules this system has.** Worth knowing before you
write API documentation that repeats them. There is **no element-membership screen**: `Tc2Ni` is
*answered* (technetium is in no training alloy, sits 4.17 from the corpus against an 11.73
ceiling), because #49 built novelty as a distance between *compositions* on purpose -- an
element-membership rule would refuse every genuinely new candidate and admit every
re-proportioning of an old one. And the applicability ceiling is a **capacity**, not a distance
(#48); the distance belongs to `beyond-known-chemistry`. Both boxes are struck through on the card
with the measurement beside them.

**Reachability is now per door, and `NOT_ALWAYS` is the only declared thing in the gate.** `NEVER`
means no fit can reach it and the gate is **red** if it appears -- `untrusted-family` is the whole
of that class, and it is #76's finding turned into an assertion. `SOMETIMES` means the fit
decides: reported, never required. One entry surprised us -- **`beyond-known-chemistry` is
fit-dependent**, because the novelty screen runs third and `resolve` reports the *first* rejecting
screen's code, so the applicability screen between it and the window can take the code first.
Deployed `v2` answers `K1Rb1` with it; the cheap fixture fit answers with a domain code.

**`docs/REFUSALS.md` is regenerated and no longer over-claims.** Every row carries a `Door`, the
label **derived** from what the probe varies rather than declared beside it, and a new table shows
what a caller typing each `request` row actually receives -- including the featuriser's own
sentence for `LaNi5Xx2`, which is the sentence the API will send and which the page previously did
not show. It is `--emit`-generated; do not hand-edit it.

**Two things #78 inherits.** (a) A malformed request **raises** rather than refusing -- settled on
#77, and the type had already settled it, since a `Refusal` carries the request it declines. The
transport owes the **422**; a `ContractError` reaching a client as a 500 is the finding. (b)
`GET /v1/model` should report `ArtifactBundle.reference_digests`, which is the half of the
pin-or-digest question #76 could answer; the fit-time binding is boxed on **#91**.

**What is still not done.** **#34** cannot close: promotion needs HG-3 and HG-4, built by #79 and
#86. Promote **`v2`**, never `v1`.

**Numbers, with the command that produced each.** `python -m hydms.gates run HG-2` — 1 passed,
2.5 s. `python -m hydms.gates run --fast` — **6 passed / 3 skipped** (was 6/6; AC-5, HG-3, HG-4
remain). `python -m pytest -m "not slow"` — **1370 passed, 4 deselected, 705 s** (was 1337).
`python -m pytest tests/gates/test_hg2_refusal_path.py` — 19 passed, 9.0 s. ruff, mypy,
`check_board.py` and `check_freeze.py` all clean.

---

### Handoff -- 2026-09-11 - #76 is closed; the next session tests it and runs a QA

**What you are being asked to do.** `hydms/delivery/predict.py` exists and `predict_capacity()`
answers. Do **not** move straight to #77. Take a QA pass at #76 first -- `docs/QA-PROTOCOL.md`, the
**L6** row in §2 and the reviewer checklist in §4 -- because three things are true at once: the
module is green on its own 25 tests, it has never been exercised against a real fitted artifact,
and it took three decisions that other cards now depend on. A session that writes the API on top
of an untested assumption is how this repository got REPORT.md.

**Start with the runnable check, then read the card's narrative.**

```bash
conda run -n Project python -m pytest tests/delivery/test_predict.py
conda run -n Project python -m pytest tests/delivery tests/screens      # 251, ~14 s
conda run -n Project python -m pytest -m "not slow"                     # 1334 passed, 4 deselected, 872 s
ruff check hydms/ tests/ scripts/ && mypy                                # outside `Project`
```

**Where to aim a QA pass, in the order the risk sits.**

1. **It has never run against a real artifact.** `v2` records no gate run, so `load_surrogate`
   refuses it -- correctly, and that is #34's to close, not a defect here. Every number in
   `tests/delivery/test_predict.py` comes from a 400-row synthetic fixture whose target was
   *deliberately* scaled to land under the 5.19 wt% ceiling, so the admitted branch runs at all.
   **That fixture is a shape check, not evidence about the model.** The first real prediction this
   project makes will come from whoever closes #34.
2. **`resolve()` and `_verdicts_for` moved.** `resolve()` is in `contract.py` now (it needs no
   pandas -- it reads `ScreenVerdict`) and raises `ContractError`, not `CatalogueError`;
   `_verdicts_for` is `predict.screen_verdicts()`. `hydms/delivery/refusals.py` imports both, so
   the dependency runs generator -> production instead of the reverse. Check nothing else copied
   either rule.
3. **The vocabulary widened and `docs/REFUSALS.md` was regenerated.** The novelty screen is in
   `delivery_screens()`, so `beyond-known-chemistry` is reachable and the page has a thirteenth
   probe. **Never hand-edit that file** -- `python -m hydms.delivery.refusals --emit`. The
   `unreadable-formula` row now carries #49's sharper sentence; read it and judge whether it is
   *true*, which is the only check that page has.
4. **A stand-in had gone green for the wrong reason, and the same trap is live elsewhere.**
   `_Extra` in `tests/delivery/test_refusals.py` declared `beyond-known-chemistry` as its fictional
   "code nothing declares"; the novelty screen made that code real and two vocabulary tests started
   asserting nothing. Re-aimed at `smells-wrong`. **Look for the same shape anywhere a test double
   borrows a real name.**
5. **Two findings were boxed, not fixed, and a QA pass should confirm the boxes are in the right
   place.** `untrusted-family` is declared and published but **unreachable through
   `predict_capacity()`** -- a novel composition has no alloy class, and supplying an unknown one
   would refuse every novel candidate for the wrong reason (boxed on **#77**, which owns
   reachability). And **`"NaN"` is sodium-plus-nitrogen to both parsers**: it cannot be guarded once
   it is a string, so the obligation is #84's CSV `na_values` decision (boxed on **#84**). A
   blocklist here refuses a real material -- a test pins that.

**The three decisions, so you can disagree with them on the record rather than by accident.** All
three are owed to #85's ADR and boxed there.

- **The assembly order was forced, not chosen.** The applicability screen judges a *prediction*, so
  "screen before featurising" never existed; a parse failure is caught where it raises and mapped
  to `INDETERMINATE` with the featuriser's own sentence.
- **ElMD is now required to predict at all.** The cost the card warned about was already paid:
  `pyproject.toml` calls `novelty` a prediction-path dependency, CI installs it, and this project is
  GPL-3.0-or-later *because* ElMD is. The alternative bought only a deployment where
  `PredictionResult.novelty` is permanently `None`, which no test would ever show.
- **The screen references are digested, not pinned.** `ArtifactBundle.reference_digests` says which
  reference answered; it does **not** say that reference matches what the fit was validated against,
  because nothing records that yet. The fit-time binding is boxed on **#91**, marked *not an
  unfreeze condition*. Until it lands, an absent record means unknown -- never "matching".

**One guard the card did not ask for.** `load_bundle` raises `DeliveryError` if the artifact's
median head is not the one config's `model.quantiles` names. Without it the domain screen finds no
prediction column and silently falls back to judging feature spans alone -- dropping
`above-physical-ceiling` and `out-of-domain`, the two rules that bound the number itself.

**One measurement worth keeping.** `load_config()` is 14.4 ms and each of the three screens loads
its own, so rebuilding the screens per call costs ~47 ms against ~4 ms to featurise one candidate.
That, not purity, is why the bundle holds them and why `delivery_screens()` grew a `cfg` argument.

**After the QA pass, #77 is the unblocked card** -- HG-2, the gate that asserts no path through
`predict_capacity()` returns a point estimate without an interval and a verdict. Ask the board
rather than trusting this line.

### Handoff -- 2026-09-08 - #90 is closed, and #76 is the card it was written for

**#90 landed** (`8bd8737`): `docs/REFUSALS.md` is generated from twelve chosen probes run through
the real screens and the real #75 contract -- input, code and reason on one line each, so a false
sentence lands in a diff. 28 tests in 1.1 s, suite **1308 passed / 4 deselected** (1312 collected),
gates 5/0/4 with HG-1 13/13, ruff and mypy clean. It is **not** a gate and must not become one;
HG-5 stays boxed on #91.

**Next is #76** -- every blocker (#28, #48, #49, #75) is `done`, it is the S6 critical path, and it
now carries two boxes this card put there:

- **Call `hydms.delivery.refusals.resolve()`; do not re-derive it.** It is the one rule that turns
  several screen verdicts into one code and one sentence, and `docs/REFUSALS.md` is generated
  through it. A second copy is how the catalogue and the API come to explain the same refusal
  differently -- the defect #90 exists to make visible. Moving it into `contract.py` is fine;
  copying it is not.
- **On #77:** `PredictionRequest` refuses a non-finite `temperature_k`, so the temperature window's
  declared `INDETERMINATE` -- and the sentence it writes for it -- is unreachable from a real
  request. Decide it rather than inherit it; the page states the gap under "One sentence this page
  cannot show".

When #76 admits #49's ElMD novelty screen into `delivery_screens()`, the vocabulary widens on its
own, `--emit` refuses `beyond-known-chemistry` as dead vocabulary until a probe reaches it, and the
byte-identity test stays red until the page is regenerated. That sequence is the design.

Also unblocked and untouched: **#7** (CI slow lane; #4 and #6 are `done`). **#34** is still `doing`
-- it is the heavy fit and the maintainer runs it.

---

### Handoff -- 2026-09-07 (late) - #49's reason, and two cards for the bug that goes red on nothing

#49 is closed for real -- `01eabda` makes each refusal carry the cause `_vector` actually found
instead of a template written for a different defect (55 on the card, 1282 full suite, `--emit`
byte-identical, gates 5/0/4 with HG-1 13/13) -- and `a04ec6f` adds **#90** (the refusal catalogue,
no unfinished blocker, workable now) and **#91** (the prediction record and replay, blocked by #76,
#78), both explicitly **not** unfreeze conditions with HG-5 deferred until the freeze lifts: start
at #90, or ask the board.

---

### Handoff -- 2026-09-06 (evening) - the LOCO run, and what it said

**The run is spent. There is no measurement left in this phase.** `loco --target capacity` ran
once, 18:16:09 to 22:23:13 -- **4 h 07 m**, inside the `--budget` ceiling of 4.7 h and past the
3 h 21 m - 3 h 50 m this session projected by scaling the random-split run's measured wall time,
so `--budget` was the better bound and the scaling was optimistic by about 7 %. `loco-run.csv`
records `probe=False`, 25 of 25 trials, screening on, 10 folds, seed 42.

**The headline, and it is a wide gap: macro transfer R2 0.2734 against the random-split 0.7459.**
Support-weighted 0.2153, *below* the macro average -- the same direction the probe found, which
is why the document computes the direction rather than asserting it. All ten classes estimable.
AC-6 passed on the committed tables with no code change, which was the whole design of that gate.

**The probe sized the gap and named the wrong families at both ends.** It said worst **HEA**
-0.3026 and best **A2B** 0.6703. The run says worst **Mg** -0.3381 and best **SS** 0.7626. A
sentinel-budget run can tell you how big the gap is; it cannot tell you where the gap lives, and
where it lives is the part #48 needs. Anyone tempted to skip a heavy run because a cheap one
"already showed the answer" should read those two lines together.

**Mg is the finding.** R2 -0.3381 over 96 rows with MAE **1.577**, against 0.24 to 0.49 for every
other class. Mg-based hydrides are this dataset's high-capacity corner, so a fold that holds them
out removes the model's only evidence of what high capacity looks like -- and it then predicts
that family as though it were the families it kept. Negative R2 means worse than predicting the
mean, in the exact direction an optimiser pushes. That sentence belongs in Chapter 1 (#37) and in
the model card (#83).

**The finding nobody asked for, and it is boxed on #48 because it changes what that card is
for.** `loco-per-class.csv` carries `interval_coverage`. Against the random-split out-of-fold
reading of **0.6293**: Mg **0.1146**, SS 0.1644, MIC 0.4713, AB 0.4746, MEA 0.5000 -- while HEA
reads 0.8824 and A2B 0.7586. Coverage out of family is not merely lower, it is *unpredictably*
lower, and its worst case sits on the worst R2. **Said precisely, because it is easy to
overclaim:** these are the raw quantile-head bands, not the conformalised ones. The deployed path
adds a correction calibrated in-distribution (AC-3: 0.7795 against a nominal 0.8 on 254 test
rows), and **nothing here measures the conformal band out of family**. But conformal coverage is
marginal and assumes exchangeability, which holding out a whole family breaks by construction, so
there is no reason to expect it to survive the move and now some evidence the underlying band
does not. The consequence for #48 is concrete: `HIGH_UNCERTAINTY` cannot stand in for
`OUT_OF_DOMAIN`, because a candidate can be out of family *and* carry a narrow band. Its second
consequence is that a single scalar ElMD ceiling fitted to the average would admit candidates
near Mg and reject candidates near SS on the same evidence.

**Two risks this session wrote down did not fire, and their boxes stay.** The run has no resume
and prints nothing per fold; it survived four hours unattended anyway. A risk that did not
materialise is not a risk that was wrong, and both boxes are records for the *next* protocol that
costs hours. What the silence did cost is real though: the only live signal available was
cumulative process CPU, and `docs/RUNNING-THE-FIT.md` step 10 now tells the next operator to run
under `python -u` teed to a log and to watch that CPU, because this session had to work it out
while a four-hour run was already going.

**Measured here, after the run.** Suite **1117 passed, 0 skipped** in 29 min 08 s -- the count
rose by two from the review session's 1115 + 1 skip: the skip now runs, and the review's own
`test_the_two_counts_one_run_prints_are_the_same_count` is the other. That 29 min overlapped
`gates --all` for its first three, so the clean 21 min still stands as the idle reading. Gates
`--all`: **6 passed, 0 failed, 6 skipped** in 188.51 s. Board OK over 89 cards, freeze OK over
265 paths, ruff and mypy clean over 64 files.

**Left open deliberately: #30 is still `doing`.** Every done-criterion on it is met and its three
remaining boxes are recorded findings rather than work -- but moving it to `done` unblocks #48,
and a session that closes somebody else's card at midnight to tidy a board has made a decision
that was not its own. The maintainer flips it.

**Next.** S6: #75 and #49, neither blocked by #34. Nothing on the board now waits on a
measurement.

---

### Handoff -- 2026-09-06 - review session - written for whoever starts the LOCO run

**Nothing here was a card until it had to be.** This was a review of the code, the pipeline, the
guard rails, the tests and the QA, run with three questions: does the pipeline do what the documents
say, is anything measured but unpublished, and is any check unable to fire. Seven findings; one was
a code defect and it is fixed; the rest are boxed on the cards that own them.

**Measured here, on a clean tree at `8477737`.** Suite **1115 passed, 1 skipped** in 21 min 21 s --
matching the committed count exactly. Gates `--all`: **5 passed, 0 failed, 7 skipped** in 157.89 s
(AC-1, AC-2, AC-3, AC-4, HG-1). Leak audit **13 of 13 green**. `check_board.py` OK over 89 cards,
`check_freeze.py` OK over 257 changed paths. ruff and mypy clean over 64 files.

**The one code defect, and it is small but instructive.** `promote --dry-run --waive AC-5 --waive
AC-7 --waive AC-8` printed "*v1 therefore has **9** of 12 criteria left to establish*" and then, six
lines later on stderr, "*4 of 12 criteria are unestablished*". One run, one concept, two answers.
The waiver summary computed `len(results) - len(waived)` and so ignored every criterion that had
**passed**. The count is now derived **once** and read twice, and
`test_the_two_counts_one_run_prints_are_the_same_count` asserts both numbers against a fixture where
the naive expression would say three and the right one says one. **It was seen red on the
reintroduced defect before being trusted.** The rule it violated is this project's own: no number in
prose that a test does not check -- which applies to prose the *code* prints, not only prose a human
writes.

**Two numbers exist, are honest, and are published nowhere. Both are now boxed on #83.** First, the
**deployed model's own held-out score**: gate AC-1 computes R2 **0.7071**, RMSE 0.5420, MAE 0.3117
on 254 `test` rows as a side effect of proving reproducibility, and it lives only in a gate message
and in gitignored `artifacts/gate-results.json`. `reports/model/evaluation.md` promises exactly that
reading in its own words and names #34 as where it arrives -- so it has arrived and nothing
publishes it. Second, `reports/model/evaluation-subgroups.csv` records the **near-ambient
temperature bin, (195, 293] K, at R2 0.187 with a 95 % CI of [-0.012, 0.423]** -- the interval
includes zero, in the regime a practical storage material has to work in, against 0.66-0.77 for the
four warmer bins. Neither is a defect. Both are results sitting in committed tables that no prose
mentions.

**A gap in HG-1 that a green gate cannot see, now a rule.** From `da8de59` (2026-09-05 20:24) to
`bf0b841` (2026-09-06 01:45) -- **five hours twenty-one minutes, ten commits** -- the L11 sentinel
guarded `model.final_fit` while the object that shipped had become `deploy.deployed_fit`. HG-1 read
**13/13 PASSED** throughout, and the sentinel's assertion was *true* the entire time: it was true
about the wrong model. Section 1 of `docs/QA-PROTOCOL.md` already covers a subject that is
**missing**; nothing covered a subject that is present, wired, working and no longer what ships.
There is now a sixth rule in section 5, and `CONTEXT.md` carries **`Sentinel subject`** as a term.
The mechanical check is **deferred with its reason on #71**: every proxy in reach is weaker than the
structural fix that already landed, and the only strong one -- *the deployed fit is whatever
`artifacts/current` was built from* -- is unavailable in CI because `artifacts/` is gitignored.

**#35 is done and was opened out of order on purpose.** `CONTEXT.md` exists: 26 terms in nine
groups, glossary only, every term carrying the words it is confused with. The trigger was the
maintainer asking in review **why three R2 values exist and whether two should be deleted** -- which
is the question the file exists to prevent, arriving from the person who owns the domain. They are
not three attempts at one number. **`Procedure score`** (0.7481 out-of-fold) is a claim about a
*method*; **`Artifact score`** (0.7071 on test) about *one model*; **`Transfer score`** (AC-6,
unmeasured) about *extrapolation to an unseen family*. The gaps are the findings -- a small
procedure-to-artifact gap is evidence the procedure is stable, and a large procedure-to-transfer gap
is the argument for every guard rail in the project -- and choosing between the three after seeing
all three is leak **L2**'s shape at the reporting layer. The card's runnable check was changed from
counting `### ` to counting `**`, and the reason is recorded on the card rather than applied
silently.

**Before you start the 4.7-hour run, two things about it are boxed on #30.** `loco.py` has **no
resume and no incremental write** -- a crash at hour four costs the whole run. Accepted as-is,
because building resumability first delays the long pole by about an hour to prevent an outcome that
probably will not happen; disable sleep, run it detached, and `--budget` it first. And the per-class
scores carry **no bootstrap interval, deliberately** -- `summary()` documents why (like-for-like
against `train`'s fold mean) -- which means the headline transfer number is a point estimate over
ten class folds where a 19-row class weighs as much as a 200-row one in the macro mean. Say so
wherever it is published; `rows_scored` sits beside every row so it can be said.

**#36 gains three ADRs and keeps its name.** Its list of five predates this week entirely. Added:
*a waiver is an act, not a property*; *one definition of the deployed fit*; *`load_surrogate` splits
into locating and assembling*. Each meets all three bars the card sets, and each has written-down
alternatives that were genuinely considered.

**Documentation, deduplicated rather than added to.** The board's `ml-model-training` note was a
strict subset of `CLAUDE.md`'s, which covers all three installed skills and carries the audit
result -- it is a pointer now, because two copies of a caveat is one copy and one thing that goes
stale. `CLAUDE.md` no longer refers to `docs/REPORT-RECONCILIATION.md` in the present tense; the
file does not exist and #89 owes it. The runbook's section 5 said "724 green as of 2026-09-04" and
now says 1115 with the one skip **named**, plus the `-q` trap and the fact that `gates run` with no
selection exits 2. And the archive above these handoffs now carries a **corrections index**: every
superseded number in the handoffs below, with its correct value and why it moved, so nobody
discovers one by quoting it.

**Next.** Start the run. Then **#75** and **#49** in parallel -- both unblocked, both feeding #76,
neither blocked by #34. **#34 closes last**, because it waits on AC-6 *and* HG-2/3/4; when you get
there, re-save the deployed fit from a clean tree first (0.7 min), because `artifacts/v1`'s manifest
records `code_modified: true` and the promotion note is permanent. **Stage by name** -- this tree is
shared and `artifacts/` is gitignored.

---

### Handoff — 2026-09-06 · the run, the deployed fit, and two latent defects

**`artifacts/v1` exists** — model, conformal correction and
scaler, written 2026-09-06 by `python -m hydms.surrogate.calibrate --target capacity --save` in
**0.7 min**, with **no gate report**, which is the honest state for a model nobody has certified: it
cannot be promoted and `predict()` refuses it. #34's open decision is **settled, and the answer was
neither option it offered**: the deployed fit was two different models — `train.py` grew one on 873
screened rows and explained it, `calibrate.py` carved a calibration slice first and conformalised a
701-row model — so the committed `model-shap.csv`/`model-pdp.csv` described something with no band
while the correction belonged to something with no explanation. `hydms/surrogate/deploy.py` is now
the single definition (screen → carve → fit → calibrate), `train.py` builds no deployed fit at all,
the two explainability tables moved to the command that does, and the L1/L11 sentinels were re-aimed
at the real deployed fit. **Do not re-run `train`:** its 1 h 41 m buys nothing measurable —
`nested_scores` never touches a deployed fit, `evaluate` reads only `model-out-of-fold`,
`model-per-fold` and `model-run`, and `git diff a101205 HEAD` over every fitting path is empty, so
**R2 0.7481 [0.6889, 0.7985] stands untouched**. **Two latent defects surfaced only because the
command was actually run, and both had been invisible for a day:** `calibrate._params` selected
hyperparameters by a *deny*-list, so against a real `model-chosen.csv` it handed
`CatBoostRegressor` a `features=14` count and a set of `param.`-prefixed names and died — it is an
allow-list on `PARAM_PREFIX` now; and every conformal number this project had quoted was measured on
**CatBoost's defaults**, because the 2026-09-05 calibration ran at 14:35, nine hours before
`model-chosen.csv` was written, and `_params` took its "no configuration on disk" branch and said so
only on stdout. The real figures are **correction +0.037355, raw coverage 0.6744 → 0.8081, width
0.6741 → 0.8951, zero crossings**, carve 172 of 873 so the trees grow on 701; `docs/PHASE-H-RUNBOOK.md`
S4 and card #27's narrative are corrected, the handoffs below are left as the record of what those
sessions believed, and `research/PHASE-H-PERSONAL-REPORT.md` still quotes the old ones (the freeze
denies `research/**`, so it is owed a pass when the freeze lifts). **Verified there:** suite **1005 green in 13 min 55 s**, ruff and
mypy clean, board and freeze OK, HG-1 **13/13**, AC-2 green. **Read the AC-3/AC-4 result with its
caveat.** `gates run --fast` reported **4 passed, 0 failed** including AC-3 at **coverage 0.7795
against nominal 0.8** on 254 held-out test rows (raw 0.6575 on the same heads — inside the 0.05
tolerance by about two binomial standard errors, so it passes and not by much) and AC-4 agreeing to
0.0000e+00 across all ten alloy classes. **But this commit does not contain those gates.** A
**concurrent session shares this checkout** and had uncommitted implementations of #31 and #33 in
the tree — `hydms/gates/_artifact.py` plus changes to `ac3_conformal_coverage.py`,
`ac4_known_alloy_round_trip.py`, `hydms/surrogate/predict.py` and `tests/gates/conftest.py`, none of
it staged here, and at this commit both gate modules are still `Pending` stubs. The two sessions
dovetailed rather than collided: their gates had a version to score because this one wrote `v1`. So
**re-run the gates after their work lands** and treat those two numbers as observed-once, not
inherited. *(They landed in the next commit and the numbers re-measured identically — see the
paragraph above.)* Their design also answers the circle #33 was written to worry about — load the bundle
with `require_gates=False` and build the `Surrogate` through the same `surrogate_from` the delivery
path uses, so the only line skipped is the check the gate is producing — which is option (A) on #33
with the guarantee intact; confirm it landed before re-deriving it. Remaining order: ~~**#32** is the
one real decision left in S4 (whether `thread_count` joins `FIXED` or AC-1 varies it; pinning it
*changes the fitted model* if CatBoost is not already thread-invariant, so it means re-running the
two-minute save), then close **#31** and **#33**, then **#34**, which now owes only the manifest and
the promotion, never a fit.~~ *(All four are addressed in the paragraph above; the `thread_count`
worry was measured away and no re-save was needed.)* **#30** is independent and can run alongside any
of it. And **stage by name** — this tree holds another session's work. Standing facts that outlive this: `CONTRACT` is the published 22 and AC-2's
parity set while `SELECTED` is the 14 a model is fitted on; `group_keys` is the one definition of
"the same material"; every `--save` writes a **new** version because a version is written once, so
name the version you promote and read its manifest `notes` first; and `artifacts/` is gitignored —
stage `reports/model/` by name, never `git add -A`.

---

### Handoff — 2026-09-06 · OPEN DECISION: persist versus refit · written for whoever picks this up (SETTLED — see the two handoffs above)

**Read this before opening a card.** It is not a recommendation. It was found at the end of the
session that ran the fit, and deliberately left undecided rather than settled by a tired session.

**The finding.** `hydms/surrogate/train.py` **persists no model.** `final_fit` is called, handed to
SHAP and PDP, and dropped; grep the file for `joblib`, `dump` or `save` and the only hits are
argparse's `store_true`. So the 2026-09-05 run produced eight tables and nothing loadable. Three
cards need a fitted model and none of them owns creating one:

- **#34** says "this card promotes *that* run (decided 2026-09-05, #29 Q12)". There is nothing to
  promote. Its premise is broken as written.
- **#31** (AC-3) measures coverage on the held-out test set.
- **#33** (AC-4) round-trips through `predict()`, which needs `load_surrogate` over a version dir.

**The decision.** How does #34 get a model?

- **A — refit the deployed configuration.** Everything needed is committed: `model-chosen.csv` gives
  outer-0's params (the deployed choice, inner objective 0.11850), and `model-fits.csv` clocks that
  final fit at **32.979 s**. Cheap, and it needs no second search.
- **B — add persistence to `train.py` and re-run.** **1 h 41 m**, and the promoted model is then
  literally the one that produced the numbers.
- **C — some hybrid**, e.g. refit but gate promotion on a proof of equality.

**What the decision actually turns on, measured rather than argued:**

1. **The out-of-fold numbers are not at risk either way.** R2 0.7481 and everything in
   `evaluation-metrics.csv` came from the **five outer-fold models**, none of which is the deployed
   fit. A refit cannot invalidate them.
2. **`model-shap.csv` and `model-pdp.csv` are the real stake.** Those *were* computed on the
   deployed fit. If a refit lands on a different model, the committed explainability tables no
   longer describe the shipped one — and REPORT.md section 6.1 being a test-set artefact (leak L11)
   is precisely the kind of mismatch this phase exists to remove.
3. **The fit is seeded but not thread-pinned.** `random_seed` is `settings.seed`, the stopping slice
   is seeded, the Optuna sampler is seeded — but `model.FIXED` pins only `grow_policy`,
   `bootstrap_type`, `task_type`, `verbose` and `allow_writing_files`. **There is no
   `thread_count`.** CatBoost under `Lossguide` with a Bayesian bootstrap is not guaranteed
   thread-invariant, and #7's slow lane runs on `windows-latest`, which does not have this machine's
   core count.
4. **So #32 as written may not be a sufficient licence for A.** "Pipeline run twice with the same
   seed produces identical metrics" holds thread count constant if both runs are on one machine.
   Whoever settles this should decide whether AC-1 must also vary `thread_count`, or whether
   `thread_count` simply joins `FIXED`.

**Do not run `train` again while settling this.** If the answer is B, that is a deliberate 1 h 41 m
spend, not an accident.

---

### Handoff — 2026-09-06 · the run landed, #29 closed · written for #31/#32/#33, and for #34

**What happened.** The maintainer ran the fit 2026-09-05 22:03:51 to 23:44:46 and this session drove
Steps 5-8. `model-run.csv` says `probe=False`, 25 of 25 trials, screening on, 5x3 folds, `SELECTED`,
seed 42. Eleven files committed by name in `reports/model/`; the three `conformal*.csv` probes were
left untracked, which is the whole reason Step 7 stages a list.

**The numbers, and how to quote them.** R2 **0.7481 [0.6889, 0.7985]**, RMSE 0.5616, MAE 0.3332,
resampling **canonical compositions** — that is the interval to quote. Two others are published
beside it so the choice can be checked: rows [0.6808, 0.7999] and per-fold [0.7085, 0.7918]. The
per-fold one is the **narrowest and least trustworthy**, exactly as #29's Q5 box predicted, because
the folds trained on 525-564 rows and part of what it prices is training size. #26's probe measured
0.746 and the full run landed at 0.7481 — the probe was reading true, which vindicates that card's
caution and is *not* licence to quote probes.

**Two defects were found and one was fixed mid-run.** `describe_git` computed cleanliness over the
whole tree, so the eight CSVs #29 un-ignored made `evaluate --emit` report a dirty tree *always* and
`RUNNING-THE-FIT.md` Step 6 asked the operator to check for the opposite — unsatisfiable by
construction. Fixed in `00bb16e`: `Git.dirty` is now `Git.code_modified`, `OUTPUT_PATHS` excludes
`reports/` and `artifacts/` by git pathspec, the document reads `(code committed)`. **Do not add a
second stamp in a caller** — `artifacts/store.py` reads the same field for #34's manifest. The
second defect is still open and moved to **#34**: nothing records which commit a fit ran from, so
this run fitted from `a101205` and stamps `5f696d9` (empty diff over every fitting path — checked,
not assumed).

**Do not re-run `train`.** #34 promotes from this run. Also: `--budget` over-projects by ~45 %
because it multiplies the mean of the six *scored* fits by all 381 and models no pruning — boxed on
#7.

---

### Handoff — 2026-09-05 · #29's machinery landed · written for the maintainer, and for #34

**Where the phase is.** Thirty-four cards done. **#29 is still `doing`, and deliberately so:** every
box on it but three is ticked, the machinery is committed, and what is owed is *the run*. Fast suite
**1004** green in 11 min 37 s (it was 961 before this card; measure it, do not copy this number
forward), ruff and mypy clean, `check_board.py` and `check_freeze.py` OK, and
`python -m hydms.gates run --fast` exits 0 with AC-2 at 2.7285e-12 and **HG-1 `PASSED` at 13/13** —
"all 13 leaks are guarded against the real pipeline". L11 was the last one in the inventory and
`hydms.qa.sentinels.DEFERRED` is now empty.

**The one thing this handoff is for.** Two commands, once, on the maintainer's schedule.
**[../docs/RUNNING-THE-FIT.md](../RUNNING-THE-FIT.md) is the step-by-step version** — written
for an operator rather than a reader, with the ten-minute smoke test to run first, what each line of
output means, the three exit codes and what each one costs you, and how to stage the results without
committing a probe alongside them. The short version:

```bash
conda run --no-capture-output -n Project python -m hydms.surrogate.train --target capacity
conda run --no-capture-output -n Project python -m hydms.surrogate.evaluate --emit
```

The first is the ~3.5 h fit — **now cheaper than that, see the search space below** — and writes
seven tables into `reports/model/`, which this card un-ignored on #25's precedent. The second reads
them, puts an interval on every number and regenerates `evaluation.md` in about a second, stamping
the git SHA into the document. Then commit `reports/model/` **by name**: the directory also holds
#27's local probe CSVs, and `git add -A` there would commit a cost check as a result.

**Do not run `train` twice.** That is the whole reason the bill moved from #34 to #29: two
independent runs would mean Chapter 1 reports a different model from the one that ships. #34
promotes the artifact **from this same run**, and it has `blocked_by: 29` for that reason.

#### What changed in the code, in the order it matters

**The search space is narrower by one bound, and the bound is a measurement.** #26 recorded that the
`learning_rate` 1e-4 x `iterations` 30,000 corner cost 397 s against 7 s and scored worse, and left
it ported. This session measured the whole decade — one real fit per rate, one real inner fold,
everything else held:

| learning_rate | best iteration | seconds | R² |
|---|---|---|---|
| 0.005 | 813 | 4.4 | 0.6800 |
| 0.001 | 4,230 | 12.9 | 0.6847 |
| 0.0005 | 8,501 | 25.7 | 0.6831 |
| 0.0003 | 13,991 | 44.1 | 0.6816 |
| 0.0001 | **29,999** | 82.4 | 0.6803 |

The best iteration goes as roughly `4.2 / learning_rate`, **R² is flat across the decade**, and at
the archival lower bound the optimum *is* the cap — the fit never converged. Since `iterations` is
sampled from 10,000, the new bound is **5e-4**: the measured rate whose optimum still falls inside
the smallest budget the space can hand a trial. Nineteen times the wall time for the same model,
removed **before** the run this thesis quotes, because narrowing afterwards would publish a model
the project then changed. `test_the_search_space_is_the_archival_one_but_for_one_measured_bound`
is the deliberate update, and the table is on `SEARCH_SPACE`.

**No fit re-reads `pipeline.yaml`.** `ModelSettings` now carries the target and temperature column
names; `from_config` resolves them once and `_resolve` **refuses** rather than falling back to disk.
A fallback that fires only sometimes is the same race with a smaller window, and a smaller window is
harder to find. A test counts the reads inside `fit_quantile_model` and requires **zero**.

**The out-of-fold predictions are kept, through a seam that checks them.** `ScoringTask` gained a
`keep` sink (defaulted to a no-op, so both sentinels and every existing contender are untouched),
and `nested_scores` supplies one per (contender, fold) that asserts what arrives **is** that fold's
held-out labels, in both directions, before keeping it. A contender handing back rows it was
*fitted* on would look like out-of-fold predictions, would score beautifully, and nothing downstream
could tell. `Evaluation.out_of_fold` is Q11's defaulted field.

**`hydms/surrogate/evaluate.py` is the module.** It fits nothing. Bootstraps 2,000 resamples over
**canonical compositions**; reports R², RMSE, MAE and the quantile metrics on **both** scales, each
taken from the model's own two prediction methods rather than from a round trip (#11 measured
`expm1(log1p(y))` returning `y` exactly on only 794 of 1,279 rows); breaks out per outer fold and
per temperature band from **one** split-level resample, recording each band's smallest and largest
*n* across replicates; publishes the group-versus-row comparison side by side; and carries
`reading`, `feature_set` and the full too-narrow sentence as **columns on every row**, because a row
is what gets quoted into a chapter. `--artifact current` stays as the second reading and **refuses
by name**, saying it needs #34 and that the primary path needs no artifact.

**SHAP is native and cheap, which is the opposite of what the card budgeted.** CatBoost answers
`get_feature_importance(type="ShapValues")` for a `MultiQuantile` loss, returning
`(rows, heads, features + 1)` — exact TreeSHAP, one explanation per head, base value last — in
**0.02 s** on a 200-tree fit over 708 rows. The `shap` package is installed and is not used. PDP is
hand-rolled over each feature's own observed quantiles, because this model predicts three columns
at once and scikit-learn's estimator checks are written for one; a Cartesian grid in composition
space walks straight out of the applicability domain, and quantiles do not.

**L11 is closed and HG-1 is 13/13.** The detector is
`hydms.qa.detectors.assert_explanation_is_not_held_out`, and it treats a record with **no**
`computed_on` column as the same defect as one naming `test` — that missing column is the archival
state proper, where a figure existed and the population did not. The live hook explains the real
deployed fit under the sentinel budget, and checks the *premise* before the conclusion: a record
covering three of fourteen features while `computed_on` said `train` would satisfy the detector and
explain a different model.

#### Two findings from verifying it, that the card did not predict

**The *cruder* interval is the *tighter* one.** At the sentinel budget the three readings of R² wt%
came out as groups `[0.6289, 0.7256]` (width 0.097), rows `[0.6247, 0.7262]` (0.102) and per-fold
`[0.6537, 0.7020]` (**0.048**). The group correction is worth about 5 % of the width — small, as the
13 %-fewer-units measurement predicted — while the per-fold interval is **half the width of either**.
The card expected the two to disagree and did not say which way. A reader who picks the
authoritative-looking number picks the *most* overconfident one, which is why all three ride in one
table with `interval_from` on every row instead of one being chosen for them.

**The group-versus-row difference is inside Monte-Carlo noise at this n, and that is the point.**
On the real two-trial tables the group interval came out slightly *narrower* than the row one
(`[0.6860, 0.8019]` against `[0.6769, 0.8012]`); at the sentinel budget it was slightly wider. So
the 13 %-fewer-independent-units correction is real in principle and not measurable in the bound.
That is the strongest form of the card's own "principle, not magnitude" framing, and it is exactly
why both readings are published rather than one asserted.

**A probe's tables and a real run's tables are the same shape, and `--emit` did not care.** The first
document generated in this session came from a two-trial probe and read as a finished result:
`train.py` prints `These numbers are a cost check, not a result` to stdout, and stdout is not what
#37 reads six weeks later. `train.py` now writes an eighth table, `model-run.csv`, and `evaluate`
leads the document with a warning banner unless it says the run was full. An **absent** record
defaults to "unknown", not to the good case.

#### Two things not to undo

**`reports/model/` is versioned now, and `git add -A` in it is a trap.** `train.py --trials` prints
`These numbers are a cost check, not a result` because a probe's CSV is the same shape as a
result's. Stage by name.

**The run's numbers are not yet in this repository, and no number in this layer is a result yet.**
0.746, 64.4 %, 0.6628 and every figure in the table above are probe numbers from reduced runs. The
card's last unticked box says exactly what is owed and how to close it.

---

### Handoff — 2026-09-05 · #29 opened · written for the session that implements it

**Where the phase is.** Thirty-four cards done, **#29 `doing` with nothing implemented**. Fast suite
**961** green in 11 min 44 s, ruff and mypy clean, `check_board.py` and `check_freeze.py` OK,
AC-2 green at 2.7285e-12, **HG-1 still 12/13**. The changes on disk are #29's card, #36's card,
this file, and **docstring-only corrections** in `hydms/surrogate/predict.py` and
`hydms/surrogate/conformal.py` — no behaviour, nothing half-built.

**The suite count is 961, not the 960 every handoff below quotes.** Measured here by running it;
this session touched no test file, so the number was already wrong when it was written. The older
handoffs are left as they stand, because they are the record of what those sessions believed.
Quote 961, and **re-measure rather than copying forward** — an off-by-one nobody checks is how the
1,114 / 1,115 canonical discrepancy boxed on #29 got there too. Note that `pyproject.toml` already
sets `-q`; adding your own `-q` suppresses the `N passed` line the handoff needs.

**Read the card's new boxes before writing anything.** This session did not implement; it measured
the card's premises, and two of them were wrong. Taking the card literally would have produced
either a meaningless interval or a four-card wait.

#### What was measured, and why it changes the plan

**(a) There is nothing to bootstrap.** `hydms/surrogate/model.py:_score_fold` computes
`model.predict(scored)`, hands it to `quantile_metrics`, and **throws the frame away**. Nothing in
`validation.py` retains a row-level prediction; `Evaluation.per_fold` is one aggregate row per
(model, fold). So the only resamplable object today is **five fold scores** — and card #29's own
box, inherited from #26 and #24, says that spread is confounded with training size (screening
removes 15–144 of a fold's ~710 rows, 571 vs 704 in practice). A 2000-resample CI over five
confounded numbers is not the interval the domain memo asks for; the memo's warning (n=239, R²
0.916) is about resampling **rows**.

**(b) The runnable check cannot run.** `artifacts/` holds only `gate-results.json` — no version
directory, no `current.json` — so `load_surrogate()` raises `PredictionError: nothing is promoted`.
The artifact is #34's, behind #31/#32/#33. Making the card's primary number depend on it would
serialise the whole tail of S4 and put #37 behind all four.

**(c) #26's tables are not on disk either.** `reports/model/` holds only #27's three conformal
CSVs, because `/reports/*` is gitignored except `feature_selection/`. The `model-per-fold.csv` the
fold-size box builds on costs a real `python -m hydms.surrogate.train` run — ~3.5 h — to
regenerate.

#### The decision

**The primary number is a bootstrap over out-of-fold predictions, resampling canonical groups**
— a claim about the *procedure*, no artifact required. It is the number R4 is about: #26's
**probe** measured a nested R² of **0.746** wt% against REPORT.md's published **0.892**, and
this card puts an interval on the real version of it. **0.746 is a probe number** — a
reduced-trial cost check whose own output prints `These numbers are a cost check, not a result`
— and it must not be quoted as a result. No full run has ever been made in this project.

**The artifact-scored number is the second reading**, once #34 lands — a claim about **a model**
on held-out rows. Both are legitimate and they are different claims, so every row of the record
names which, exactly as #25 forced for the feature set.

#### The work, in order — steps 0–4 land together, then the run

**Step 0 — before anything else, the two boxes that moved from #34.** Thread the target column into
`ModelSettings` so `model._columns` never falls back to `hydms.config.load`, with a test asserting
`fit_quantile_model` reaches it **zero** times; and narrow the search space, updating
`tests/surrogate/test_model.py::test_the_search_space_is_the_archival_one` deliberately, with the
reason in it. Both are prerequisites of a run anyone can trust.

1. **Keep the out-of-fold predictions.** `_score_fold` already computes them; stop discarding them
   and hang an `out_of_fold: pd.DataFrame` field off `Evaluation`, defaulted empty so the L2 and L4
   sentinels are untouched. Small, and no new science.
2. **Write `hydms/surrogate/evaluate.py`** — R²/RMSE/MAE on **both** log and wt% scales, the
   bootstrap at 2000 resamples **over canonical groups**, broken out per split and per temperature
   subgroup, the feature set (`SELECTED`, 14) named on every row, the too-narrow caveat as a table
   column, and `per_fold` beside it as the second interval. **Expect HG-1 to go red the moment this
   module exists** and nothing is wired to it — the sentinel mechanism working, not a regression;
   it has already happened twice this phase (#10, #12).
3. **SHAP and PDP on the deployed fit's training rows, never test** (leak L11:
   `benchmark_model_selection.py:1375,1383,1394`), with an explicit `computed_on` column.
4. **Then the L11 sentinel** in `hydms/qa/sentinels.py`: assert `computed_on` is not in
   `hydms.surrogate.validation.HELD_OUT_SPLITS`. It cannot be written before step 3, which is why
   #71 recorded it as a `Deferral` rather than guessing. Last of the thirteen — **HG-1 goes 13/13**.

**Then commit, and hand the run over.** The tables must be traceable to a SHA, so commit steps 0–4,
verify the whole path end to end against a sentinel-budget probe, and only then give the maintainer
**one command** to run. Stamp the SHA into the emitted tables. The `--emit` flag rebuilds the prose
from the tables in a second, on the #25 pattern, with a test asserting the committed document is
what the code produces.

#### Two things not to do

**Do not measure the bootstrap.** 2000 resamples over a few hundred rows is milliseconds. The cost
in this card is SHAP over a MultiQuantile CatBoost — a step-3 question.

**Do not re-aim the runnable check to make it green.** `--artifact current` stays as the second
reading; the card's own text now says it cannot run until #34, and the primary path is the one that
does not need it.

#### The design is settled — eleven decisions, on the card

A grilling session the same day settled the open questions; they are boxed on #29 under *Settled
by a grilling session*, with the measurements behind them. The four that change what you write:

**The bootstrap resamples canonical groups, not rows.** `group_keys` is the seam #13, #87 and #88
all share, and a row resample would be a fourth meaning of "the same material". **Measured:** 893
training rows in **780 canonical groups**, sizes 1–6, **692 singletons** — so this is worth 13 % of
the independent units, not a halving. Principle, not magnitude, and the card says so.

**The interval is knowingly too narrow, and the table must say so.** Out-of-fold predictions come
from five models with overlapping training sets; there is no unbiased estimator of K-fold CV
variance (Bengio & Grandvalet 2004). The caveat goes in the emitted table as a column or header
row — **not prose**, which is what a session drops — and `Evaluation.per_fold` rides along as a
second, cruder interval.

**One resample at the split level; every breakdown computed from it.** 83 of the 780 groups span
more than one temperature, so a resampled group carries all its temperature rows. Subgroup *n*
varies between replicates; record its min and max so a thin bin is visible.

**#29 produces the real numbers — this reverses the first version of this handoff.** An earlier
round settled that #34 would pay for the run; that was overturned the same day, and the reason
matters more than the decision: **two independent 3.5 h runs mean Chapter 1 describes a different
model from the one that ships.** So there is **one run** — #29 pays for it and writes the tables,
#34 gates and promotes the artifact from that same run, and #34 has gained `blocked_by: 29`.
`reports/model/` gets un-ignored on the #25 pattern. Budget, measured: `5 x 3 x 25` = 375 tuning
fits + 6 = **381 fits at ~33 s = ~3.5 h**.

**Two of #34's boxes moved to #29, because ownership followed the bill.** #34 owned both on its own
stated ground — "this card pays the 3.5-hour bill, so it owns the fix". Both must land *before* the
run. **(i) The config re-read race:** `hydms.config.load` is uncached and the scoring path calls it
~6 times a fit — **~2,300 windows** in a 381-fit run where a working-tree edit changes what the run
believes. It has already killed a probe on trial 3, and two sessions share this worktree. **(ii)
Search-space narrowing:** the `learning_rate` 1e-4 x `iterations` 30,000 corner costs 397 s against
7 s, is unconverged at iteration 29,999, and scores *worse*. Narrow before the run, not after —
narrowing afterwards publishes a model the project then changed.

**The heavy run is the maintainer's to execute.** Standing rule from 2026-09-05: the agent builds
and verifies against a sentinel-budget probe; the maintainer runs the multi-hour fit. So #29's
deliverable is **machinery plus one documented command**, and #29 stays `doing` across the gap
between the machinery landing and the numbers arriving. **Do not start a multi-hour fit unasked.**

#### What this session got wrong, so you do not inherit it

**0.746 is a probe number and this session dropped the qualifier.** [Card #26](../../kanban-hardening/archived/026-catboost-multiquantile-with-honest-early-stopping.md)
says "*the probe's* honest cross-validated R² is 0.746"; the first version of this handoff and of
#29's box said "#26's honest nested 0.746". `train.py` prints `These numbers are a cost check, not
a result` on every probe run. Corrected here, on the card, and in the `predict.py` and
`conformal.py` docstrings, which stated 64.4 % just as flatly. **No full run has ever been made in
this project.**

**The verification finding underneath it.** None of this layer's headline numbers — 0.746, 64.4 %,
0.6628, +0.030990 — is asserted by any test; they live in card prose and in docstrings, and
`pipeline.yaml` comments *depend* on them. `git ls-files reports/` returns only
`feature_selection/`; `git ls-files artifacts/` returns **nothing**. On a fresh clone every #26 and
#27 number is unverifiable prose. The Q4 and Q9 boxes on #29 exist to end that.

---

### Handoff — 2026-09-05 · #28 closed · written for #29, and for #33

**Where the phase is.** Thirty-four cards done. Fast suite **960** green, ruff and mypy clean,
`check_board.py` and `check_freeze.py` OK, `python -m hydms.gates run --fast` exits 0, AC-2 green at
2.7285e-12, **HG-1 still 12/13** — #28 touched no sentinel, and L11 remains #29's. **Nothing is
`doing`.** The chain from here is `#29 -> #30 -> #31/#32/#33 -> #34`.

**The front is #29**, evaluation metrics with bootstrap confidence intervals, whose only blocker was
#28. It is also the card that owes the L11 sentinel and carries #26's `rows_fitted` / `rows_scored`
box.

#### What #28 left you

```python
from hydms.surrogate import load_surrogate, predict

predict(["La1Ni5", "Ti1Fe1"], 298.0)              # -> q0.1 q0.5 q0.9 lcb interval_width, wt%
predict(formulas, kelvin, version="v2", store=d)  # a named version in a named directory
load_surrogate(store=d).feature_names             # the fitted column order, for a diagnosis
load_surrogate(store=d).describe()                # one row: which artifact answered, and its band
```

`Surrogate` is frozen; its public surface is *facts* — `version`, `quantiles`, `feature_names`,
`confidence_level`, `columns` — and the model, the correction and the contract are private fields.
`clear_cache()` exists for a test that writes a version into a directory the process has read.
New beside `QuantileModel`: `MODEL_PAYLOAD` and `model_from(bundle)`, completing the
`scaler_from` / `conformal_from` trio that had no sibling for the model.

**Three things #29 and #33 must not undo.**

**The heads are not renamed.** The card's job story writes `[p10, p50, p90, ...]`; the frame carries
`column_names(quantiles)` — `q0.1`, `q0.5`, `q0.9` — because `model.quantiles` is configuration and
`column_names` is the one place a CatBoost column position becomes a name. The payoff is direct:
`quantile_metrics(truth, frame.loc[:, list(HEADS)], quantiles)` scores this frame with no new
measurement code, which is what #29 was promised.

**`lcb` is read off `conformal.lower`, not off column 0**, and `interval_width` off
`conformal.upper` minus that. It duplicates a head column deliberately — the point is that no caller
derives the ranking key — but the derivation is by name, so a band whose quantiles are not ascending
still gets the bound its own calibration targeted.

**Nothing is clipped and nothing is refused.** A negative `lcb` survives; the temperature window,
the AD ceiling and the novelty distance are L4 screens and the refusal is L6. A surrogate that
silently declined rows would make the screen verdict unobservable.

#### The trap that is now boxed on #33

**`predict()` returns the calibrated band; the training-time heads are raw.** A round trip that
compares all three head columns against `QuantileModel.predict(features)` will match on the median
and fail on `q0.1` and `q0.9` by the transformed correction — on a pipeline that is working. Either
score the median head alone, or build the reference with `calibrated_heads(model, features,
conformal=conformal)`, which is exactly what `predict()` calls. `store=` is how AC-4 scores a
candidate version before the promotion pointer moves.

#### Two things measured rather than asserted

**The scaler is never applied**, and the test proves it the only way a negative can be proved: a
second artifact version stores a `FittedScaler` subclass that raises on `transform`, the test arms
the trap (loads it back and confirms it still raises after a joblib round trip) and then demands
`assert_frame_equal` against the ordinary version. The card's own box was right about *persisting*
the scaler and wrong about where it is applied — it named #48's distance-based AD as the consumer,
and **that consumer never arrived**: #48 landed as a capacity ceiling reading no scaled matrix, so
the payload has no reader at all. #23 decided it leaves the next version's payload set; the test is
unaffected, because it proves a negative rather than exercising a reader.

**`interval_width` is not the stored constant doubled.** The correction is constant in `log1p` space
and `expm1` is convex, so the same widening is a wider band at a high prediction than at a low one:
three candidates at 250/400/600 K return three distinct widths. That is why AC-7 asks a published
candidate to carry a width rather than reading it off the manifest.

#### One decision worth knowing before #76

`load_surrogate` never forwards `artifacts.load`'s `require_gates=False` and takes no equivalent, so
a version with a `SKIPPED` criterion cannot answer a prediction at all. That is **strictly stronger
than the promotion pointer**: `promote()` already refuses a version whose gates are incomplete, so
*promoted* implies *gates established* and the converse is what this adds. Naming a version stays
legal, because #33 and a rollback inspection both score a candidate before the pointer moves.
The load is memoised by `(store, version)` — safe, because a version is written once and never
edited — while the pointer itself is re-read every call, so a rollback takes effect on the next
prediction rather than the next process. #76's "no global mutable state" box has been annotated:
wrap this cache, do not add a second one.

---

### Handoff — 2026-09-05 · a training run died on a config it had not been started with

**One paragraph.** A `conda run -n Project python -m hydms.surrogate.train --target capacity
--trials 8` probe died on Optuna trial 3 with `ConfigError: pipeline.yaml:model: unknown key(s)
['calibration_folds']`, and **no commit is broken** — HEAD loads that file cleanly
(`Model(..., calibration_folds=5)`, `Conformal(confidence_level=0.8)`), so the first thing to do
is simply run it again. What happened is that `hydms.config.load` is **uncached and re-parses the
YAML on every call**, and `hydms.surrogate.model._columns` calls it through `load_config()` whenever
`target_column` is `None` — the whole scoring path — so the running process kept re-reading the
working tree while the #27 session was writing into it: Python had the *old* `Model` dataclass
frozen in memory from import time, the file on disk was the *new* one, and trial 3 was the first
read after the write. The measurement that makes this worth fixing rather than shrugging at is in
**#34's boxes**: 210 re-reads in one sentinel-budget nested run of ~35 fits, 7.6 ms each, **21.6%
of that run's wall time**, which scales to roughly **2,300 windows** across the configured
381-fit, 3.5-hour run — a long run is not hermetic against its own configuration file, and it
silently loses ~15 minutes of compute when one of those windows catches an edit. #34 owns the fix
because #34 pays the bill: thread the target column into `ModelSettings` so `_columns` never falls
back to disk, record the config the run actually used in the manifest (today `artifacts/store.py`
records only `load_config().seed`), and guard it the way this project guards everything else — a
test asserting `fit_quantile_model` reaches `hydms.config.load` zero times. Until that lands the
operational rule is the one already in memory for this worktree: **do not edit `hydms/` or
`pipeline.yaml` while a training run is in flight**, and prefer running a long fit from a clean
checkout rather than the working tree two sessions are sharing.

---

### Handoff — 2026-09-05 · #27 closed · written for #28, and for #31

**Where the phase is.** Thirty-three cards done. Suite **937** green, ruff and mypy clean,
`check_board.py` and `check_freeze.py` OK, `python -m hydms.gates run --fast` exits 0, AC-2 green at
2.7285e-12, **HG-1 still 12/13** — #27 touched no sentinel, and L11 remains #29's. **Nothing is
`doing`.** The chain from here is `#28 -> #29 -> #30 -> #31/#32/#33 -> #34`.

**The front is #28**, the surrogate's public `predict()`, whose only blocker was #27.

#### What #27 left you

`hydms/surrogate/conformal.py`, and the whole of its interface is four calls:

```python
fitting, calibrating = calibration_slice(frame, screened_train_rows)  # one fold of 5, grouped
conformal = fit_conformal(frame, model, calibrate_on=calibrating)     # the only step needing MAPIE
conformal.apply(model.predict_model_space(X))                         # model space -> model space
calibrated_heads(model, X, conformal=conformal)                       # -> weight percent
```

Plus `CONFORMAL_PAYLOAD` and `conformal_from(bundle)`, which is the artifact contract #34 writes,
and `compare_metrics(raw, calibrated)`, which is how a before-and-after table is built.
`python -m hydms.surrogate.calibrate --target capacity` runs the lot in about 25 s and writes
`conformal.csv`, `conformal-coverage.csv` and `conformal-rows.csv` under `reports/model/`.

**Three things #28 must not undo.**

**MAPIE is never on the prediction path.** It is imported lazily inside `fit_conformal`, the
artifact stores a float, and `test_applying_a_stored_correction_does_not_import_mapie` asserts it in
a subprocess. A `predict()` that imports `hydms.surrogate.conformal` is fine; one that reaches
`mapie` is a regression that test will catch.

**`apply` returns the same columns in the same order**, which is what lets
`quantile_metrics(truth, raw_or_calibrated, quantiles)` score either frame with no new measurement
code. Do not let `predict()` rename or reorder the heads on the way out.

**Rank on the calibrated lower bound, never the raw one.** The point of the constant is that the
raw P10 does not mean 10 %.

#### Two numbers, and the cost

Raw coverage on the 172 calibration rows is **0.6628** against nominal 0.80 — a second, independent
measurement of the gap #26 found at 0.644 across its nested folds, on different rows and with
different hyperparameters. The correction is **+0.030990** in model space, calibrated coverage on
those rows is 0.8081, and the mean width goes 0.7317 -> 0.9155. **Zero crossings** before and after.

**The cost, stated because it must be reported and not inferred.** `model.calibration_folds: 5`
carves 172 rows off the 873 screened training rows, so the deployed model grows on **701** where the
cross-validation that estimated its performance fitted on folds cut from 893. `conformal-rows.csv`
carries the whole accounting in one row for exactly that reason.

#### The trap that was not in the design

**MAPIE does not check its own prefit contract.** `_check_prefit_params` counts to three and never
asks which quantile an estimator predicts, so `confidence_level: 0.90` beside heads at
`[0.1, 0.5, 0.9]` — which is what `pipeline.yaml` shipped — would have produced a calibrated
interval silently, and the only thing that would ever have noticed is AC-3, the gate the
calibration exists to let pass. The level is now **0.80**, and `hydms.config._validate` refuses a
file where it and `model.quantiles` disagree. That flipped a landed test:
`test_an_alpha_passed_as_a_confidence_level_is_caught` used to assert 0.10 was *accepted* with a
warning, and now asserts 0.20 is *refused*. Do not relax it back.

Related: MAPIE's prefit list is `[lower, upper, median]` with the median **last**, and
`fit_conformal` asserts that two ways — MAPIE's public `predict` must return the median head, and
the estimator list must hold the adapters this module put there. `docs/LIBRARY-APIS.md` now carries
the four source-level facts instead of a RISK block.

#### For #31 (AC-3) specifically

`hydms.surrogate.calibrate` deliberately **does not read `test`**. Coverage on held-out data is
AC-3's to measure, and printing it here would invite the calibration to be adjusted until the gate
passed — leak L2 in new clothes. What #31 needs is a calibrated model over the test split and the
nominal level from `conformal.confidence_level`; the calibrated coverage this command prints is
nominal *by construction* and establishes nothing about generalisation.

MAPIE **1.5.0** is installed in `Project` and pinned in `requirements-lock.txt` (**209** packages;
the misfiled-name check in `docs/ENVIRONMENT.md` still reports `none`). It stays in the optional
`uq` extra because it is genuinely fit-time — but **CI now installs `.[dev,uq]`**, since the parity
and prefit-ordering tests are the only checks of a number whose wrongness is otherwise invisible.

---

### Handoff — 2026-09-05 · #26 closed · written for #27, and for the rest of S4

**Where the phase is.** Thirty-two cards done. Suite **901** green, ruff and mypy clean,
`check_board.py` and `check_freeze.py` OK, `python -m hydms.gates run --fast` exits 0, AC-2 green at
2.7285e-12, and **HG-1 is 12/13** — L1, L5 and L12 all went green in this card, and **L11 is the
only leak left in the inventory**. It is #29's, deferred with its reason recorded. **Nothing is
`doing`.**

**The front is #27** (MAPIE conformal calibration), whose only blocker was #26. **#15 and #49
remain unblocked** and neither is on the S4 chain; #15 is still owed a re-measure now that screening
flags rows for real. The chain from here is `#27 → #28 → #29 → #30 → #31/#32/#33 → #34`.

#### The number #27 exists to fix, measured before #27 starts

**The raw quantile heads under-cover: 64.4 % against a nominal 80 %.** Fold by fold, in a nested,
group-aware five-fold run over the real matrix: 0.57, 0.63, 0.70, 0.69, 0.63. Under-covered in
*every* fold, so this is not noise and #27 is not a formality on top of an already-honest interval.
What is already good: **zero crossings on real rows** — the P10/P50/P90 heads came back ordered on
every one of them, where a small synthetic fit crossed on 23 %. So the monotonicity CQR would want
is there to start with, and `crossings` is reported as a number rather than assumed away.

`hydms.surrogate.model.quantile_metrics` already emits `interval_coverage`, `interval_width` and
`crossings`, so #27's before-and-after is a column comparison rather than new measurement code.

#### What #26 built

```python
from hydms.surrogate.model import capacity_contender, capacity_matrix, final_fit, fit_quantile_model

frame, split = capacity_matrix()                 # 1,278 rows x the 14 SELECTED features
fit_quantile_model(frame, train=, eval_on=, scored_on=, where=)   # one honest fit
final_fit(frame, split)                          # grown on train, stopped on val, reported on test
capacity_contender(settings=, log=)              # this model as a #88 contender
```

```bash
python -m hydms.surrogate.train --target capacity            # the slow lane, ~3.5 h
python -m hydms.surrogate.train --target capacity --trials 2 # a probe, and it says so in its output
python -m hydms.surrogate.train --target capacity --budget   # fits nothing; the arithmetic
```

- **The honesty check is in the signature.** `fit_quantile_model` cannot be called without naming
  the rows the resulting model will be *claimed about*, and the first statement of the body hands
  those identities to `assert_early_stopping_is_honest`. There is no path through the module that
  fits without it, which is why the L1 and L5 sentinels point at the real function rather than at a
  copy of it. `scored_on` is never read.
- **`tests/surrogate/test_no_test_leak.py` asserts that by value as well as by identity**: the
  scored rows are filled with `NaN` and the fit is expected to succeed. Write a stray
  `to_model_space(frame[target])` over the whole frame and it goes red — which is exactly what it
  found on the first run, and the transform is now scoped to the two row sets a fit owns.
- **Two refusals beyond the inventory**, both `ModelError` so that a raised `LeakDetected` always
  means L1: fitting on the scored rows, and *growing* on the eval set. The second is the one worth
  remembering — early stopping that watches rows the trees are already growing on never fires, and
  the result reads afterwards as a model that happened not to overfit.
- **The eval set inside the folds is a cut, not a config value.** `stopping_slice` takes one fold of
  the new `model.stopping_folds` (5) out of the rows a fit already owns, using `grouped_folds`, so
  no composition spans the two sides. The final fit needs no cut: `val` is already a group-disjoint
  tenth, which is what `pipeline.yaml`'s `early_stopping_rounds` comment has said all along.
  **#27's calibration split must be disjoint from whichever rows that cut chose**, per fit — read
  `reports/model/model-fits.csv`, do not assume a fixed slice.
- **No scaler.** CatBoost splits on thresholds and `FittedScaler` is affine, so the fit is invariant
  to it. A model from here consumes **raw** features and records that in `feature_names`; applying
  the persisted scaler on the way into `predict` would feed it a matrix it was never fitted on.
  The scaler turned out to have **no** job: #48 landed as a capacity ceiling reading no scaled
  matrix, so nothing reads the persisted payload back. #23 decided it leaves the next version's
  payload set, and #34 carries the removal.
- **Two prediction spaces.** `predict` returns weight percent; `predict_model_space` returns the
  `log1p` the booster emits. The back-transform is exact, not approximate: `expm1` is strictly
  increasing and a quantile is equivariant under a monotone map. Nothing is clipped.

#### Four measurements, three of which corrected something

- **`early_stopping_rounds: 5000` was paying four times over for an identical model.** At `od_wait`
  5000 a real inner fold costs **26.9 s**; at 500, **6.9 s**; at 200, **5.4 s** — and all three
  return the same model, best iteration 1042 and R² 0.7050 to four decimals. `od_wait` only
  multiplies the trees grown *after* the optimum, which `use_best_model` then discards.
  `pipeline.yaml` now says 500, with the measurement beside it.
- **The budget: 4,500 fits is 42 hours; 25 trials is 3.5.** A real end-to-end probe ran 35 fits in
  **19.4 min**, so **33 s a fit** on this machine. `optuna_trials` came down from the archival 300
  to **25**. The nesting was not touched, which is the one thing the card forbade. **Where the hours
  are:** the ported space pairs `learning_rate` down to 1e-4 with `iterations` up to 30,000, and at
  that corner one fit costs **397 s** against 7 s at the fast corner, has *not converged* at
  iteration 29,999, and scores **worse** — R² 0.691 against 0.705. Sixty times the cost for a worse
  model. The space is still ported verbatim, because the card's instruction was to lower the trial
  count; **narrowing it is boxed onto #34**, which is the card that has to pay the bill.
- **One of the archival search's nine dimensions did nothing.** `bagging_temperature` is a
  Bayesian-bootstrap parameter and CatBoost's CPU default is not Bayesian. Measured: under the
  default, temperature 0.0 and 1.0 give a bit-identical fit — same trees, same best iteration, the
  same loss to six decimals — while under `Bayesian` they give 0.1444 and 0.1526. `FIXED` pins the
  bootstrap; it is the one departure from the archival parameters, and it is what makes a sampled
  dimension mean something.
- **Two other beliefs about that space were checked and were wrong.** `depth=25` under `Lossguide`
  is **accepted**, not refused (`max_leaves` makes it mostly inert), so the bound is ported verbatim
  rather than clamped. `od_type='IncToDec'` alongside `early_stopping_rounds` is **accepted** too —
  a redundancy, not a conflict — and the module sets only the one `pipeline.yaml` declares. And
  `MedianPruner(n_startup_trials=5, n_warmup_steps=10, interval_steps=3)` at `Catboostmodel.py:541`
  reported one step per fold over ten folds, steps 0 to 9, every one below the ten-step warmup: **the
  archival pruner never pruned.** The warmup here is 1, over three inner folds.

#### L12 is closed, and the sentinel needed two perturbations

The weighting decision is **unweighted**, and the whole of the decision is the blindness. L12 is not
the number 3 — raising it to 4 fixes nothing — it is that the weighting is a function of `y`. So
`sample_weights(frame, settings)` slices to the declared features in its first statement and never
reads the frame again, the same guard `select_features` uses for L6, and
`assert_weights_ignore_target` measures the consequence rather than trusting the statement.

**A test is what found the detector's first version too weak.** Written with one perturbation —
shuffle plus a 1.5× affine — it *passed* `np.where(y > 9, 2, 1)` over a batch topping out at 5 wt%,
because that weighting is constant before and after. The second pass replaces the column with a ramp
over a millionfold range. What remains uncoverable is stated on the detector rather than hidden: on
the rows it is given, a threshold beyond even the ramp *is* a constant function, and no behavioural
check can say otherwise.

**The fold-size argument the card offered as a second reason to weight does not land.** A 571-row
fold and a 704-row fold being treated as equal evidence is an argument about how folds are
*aggregated*, not about how rows inside one fit are weighted. It is answered by carrying
`rows_fitted` and `rows_scored` as metrics, so the spread sits in the same table as the scores —
#29 carries that box.

#### One number to quote carefully

The probe's honest cross-validated **R² is 0.746** in weight percent — median head, nested,
group-aware, five outer folds, screening off. Against REPORT.md's published test R² of 0.892 and the
committed CSVs' 0.376. It is a **probe**: two trials against the configured 25, and the run says so
in its own first line. The configured run is #34's to execute and publish; quote this one as a cost
check, which is what it was.

---

### Handoff — 2026-09-05 (earlier) · #25 closed · written for #26, and for the rest of S4

**Where the phase is.** Thirty-one cards done. Suite **857** green (842 + 15 — note the previous
handoff's 841 does not reproduce on this tree, and the one-test difference is not in #25's files).
The 857 run predates two cosmetic edits made after it; the final tree was re-verified with
`pytest -m "not slow"` and the whole of `tests/surrogate/test_comparison.py`, and nothing changed
in between that a `slow` test reads. ruff and mypy clean, `check_board.py` and `check_freeze.py` OK, AC-2 green at 2.7285e-12, `run --fast` exits 0,
**HG-1 still 9/13** — L1, L5, L11 and L12 are owed by #26 and #29, and nothing in #25 could move
that number. **Nothing is `doing`.**

**The front is #26** (CatBoost MultiQuantile with honest early stopping): its three blockers — #23,
#25 and #88 — are all done. Two cards off the S4 chain are also unblocked and neither is a
prerequisite for anything on it: **#15** (data-layer golden tests, and still *owed* a re-measure —
see the previous handoff, which remains the live description of what that re-measure is) and **#49**
(ElMD novelty, in S5).

**S4 closes at #34**, artifacts v1, and the chain from here is
`#26 → #27 → #28 → #29 → #30 → #31/#32/#33 → #34`.

#### The one thing to know before writing a line of #26

**There are now two feature contracts and they are not interchangeable.**

```python
from hydms.descriptors.contract import CONTRACT, SELECTED

CONTRACT   # the published 22 — archival record, the candidate pool selection runs over,
           # and the set gate AC-2 checks featuriser parity across. Not what a model sees.
SELECTED   # the consensus 14 — what #25 declared and what a fitted model is built on.
```

`featurize(..., contract=SELECTED)` builds the training matrix for #26; the manifest records
`SELECTED`, not the 22. Replacing `CONTRACT` was considered and rejected: it would have made the
next selection run circular — the pool would be its own output — and would have quietly narrowed
AC-2's parity check from 22 columns to 14.

**Do not re-run selection inside #26's tuning loop.** Boruta at the configured budget is **676 s a
pass**, and #88's protocol is 5 outer × 3 inner × 300 trials per contender. Per-fold selection
inside that is not slower, it is impossible. The honest consequence is a *sentence*, not a defect,
and #26 and #29 both carry it as a box: the folds that produced the stability table each selected
**16–20** features, so any score from a fixed 14-column pipeline belongs to that pipeline and not
to the procedure that chose the columns. Say which, in the metrics record itself.

#### What #25 built

```bash
python -m hydms.surrogate.select --emit-comparison   # republish; fits nothing, takes a second
```

```python
from hydms.surrogate.comparison import Comparison, row_cost

c = Comparison.read(Path("reports/feature_selection"))
c.consensus, c.union, c.verdict()   # what the folds agreed, and the old-22 row-by-row table
row_cost()                          # per feature, the curated rows it alone makes unfeaturisable
```

- **`reports/feature_selection/` is versioned** — `/reports/*` plus a negation in `.gitignore`,
  because git does not descend into an excluded directory and a plain negation under one does
  nothing. The hour-long run's raw output stays local in `reports/selection/`; the tables the
  write-up quotes travel with it.
- **The document is generated and checked.** `old_vs_new.md` is a pure function of the CSVs beside
  it, and `test_the_published_document_is_the_one_this_code_generates` fails if the two ever
  disagree. Its run date comes from `provenance.csv`, not a file's mtime, so a fresh clone
  reproduces the same bytes. This is the specific failure `REPORT.md` has, made impossible here.
- **`SELECTED` is tied to the run that justified it.** It is a hand-typed name list — it must be,
  since importing the contract module reads no files — and
  `test_the_declared_set_is_the_consensus_of_the_published_run` asserts those names *are* the
  consensus of the published stability table, order included.

#### The result, in one paragraph, so it is not re-derived

**The four readings nest: consensus 14 ⊂ 22-candidate 16 ⊂ whole-split 18 ⊂ pool 21.** The published
set is the consensus. The union is the entire candidate pool, so the permissive reading performs no
selection at all; a threshold would be a cut chosen after seeing where the features fell, which is
the defect this phase exists to remove rather than relocate. The one serious alternative was the
**refit** reading — in nested CV the folds estimate the *procedure* and the deployed model refits the
procedure, selection included, on all the training rows, which would publish the whole-split 18. It
was rejected because Chapter 3 reports the feature set **as a finding**, and a set from a single fit
carries no evidence about its own stability. Since the consensus is a strict subset of that 18,
choosing it contradicts nothing. All of it is argued in `reports/feature_selection/old_vs_new.md`;
bring new evidence rather than a preference.

#### Findings of this session

- **#24's statistical-power reading was confounded, and the run #25 owed is what caught it.** The
  previous handoff recorded the whole-split pass selecting **14** against the folds' 16–20 and read
  it as fewer rows rejecting less. That 14 was the **unscreened** probe. Screened — 864 rows of 893
  — the same pass selects **18**, inside the folds' own range. Row count and screening move together
  across all three runs, so the direction can be stated and the size cannot; screening is not
  neutral thinning, it removes the rows CleanLab finds least consistent. And *within* the folds the
  row count does not order the answers at all: 571 rows → 16 features, 704 → 18, 635 → 20. That last
  is the real argument for the consensus — what separates the folds is *which* compositions were
  held out, not how many rows survived.
- **The 22-candidate run does not select the feature that defines the 22.** Same 700-row pool, same
  seed, same budget as #24's controlled comparison, which confirmed `dev_Gordy_electonegativity`;
  the only difference is the **71 rows screening drops**, and they reverse the verdict. Two single
  passes, opposite answers. #24 settled that trade on rows rather than on importance, and this is
  the measurement showing it had to be settled that way.
- **Computability is now a measured table, not an argument.** `row_cost()` charges each of the 22
  the curated rows it alone makes unfeaturisable: **266 of 1,279** for Gordy, **one row each** for
  six JARVIS features, and that one row is the same `Eu1Ni5` every time. So the consensus cut is
  *free* on this axis — the new 14 cover exactly what the 21-candidate pool covered — and the whole
  computability gain in the comparison is #24's Gordy trade.
- **`dev_voro_coord_divi_mol_vol` stays, on a stated condition.** The JARVIS table's
  `voro_coord = 1.0` for `Cs` and `Gd` is filler; of the two only gadolinium is in this dataset, in
  **18 of 1,279 rows (1.4 %)**, so that feature is computed from a placeholder for those rows.
  Against that, all five folds selected it, and hand-removing a unanimously-selected feature after
  seeing the result is the decision this phase exists to remove. Kept — and **#83 owes the sentence**
  in the model card, boxed there.
- **A report directory can now say what varied.** `--all-features` and `--no-screening` suffix the
  table names, so a cheap probe cannot silently overwrite an hour-long result. The five-fold
  screened run over the 21 candidates is the unsuffixed one, because that is the run this project
  means when it says "selection".

---

### Handoff — 2026-09-05 (earlier) · #24 and #14 closed · written for #25

**Where the phase is.** Thirty cards done. Suite **841** green (807 + 34), ruff and mypy clean,
`check_board.py` and `check_freeze.py` OK, AC-2 green at 2.7285e-12, `run --fast` exits 0, and
**HG-1 is at 9/13** — L6 went green the hour `hydms/surrogate/selection.py` appeared. **Nothing is
`doing`**: #14 closed with #24, in one commit, which is what the previous handoff asked for.

**The front is #25**, unblocked and holding the most interesting result in the phase so far. Two
other cards came unblocked in the same commit and neither is on the S4 chain: **#15** (data-layer
golden tests — and it is *owed* a re-measure, see below) and **#49** (ElMD novelty screen, in S5).

**Read `reports/selection/` before you re-run anything.** The five-fold run at the configured budget
has already been done — about 50 minutes — and its tables are on disk (gitignored; publishing them
into the repo is #25's job). What they say is the finding the whole card exists to produce:

> **"The 22 features" was never a stable object.** Under the group-aware fold cut, **every one of
> the 21 candidates is selected by some fold** — the union is the whole pool — while only **14 are
> selected by all five**. `range_Atomic_Weight` is selected by exactly one fold.

Two numbers from that run are boxed onto other cards rather than acted on here. **#25**: per-fold
selection is *larger* than a whole-split pass (16–20 features against 14), because fewer rows make
Boruta less able to reject against its shadow features — so the new N and the published 22 were not
produced under equal statistical power, and the write-up must say so. **#26**: CleanLab removes
between **15 and 144** of a fold's ~710 training rows depending on the fold, so `outer-1` fits on
571 rows where `outer-2` fits on 704 — a 23 % swing in training size before the model sees anything.

**#15 is owed a re-measure and its own handoff said so.** Screening now flags rows for real, so
`screened.rows_out` and `screened.removed` move. Note *which* call to pin: the fold-level screening
inside the selector produces five different counts, and the numbers #15 and #37 want come from a
**pipeline-level `screen` over the whole frame**. Nothing else in the golden record should move; if
it does, that is the finding.

#### What #24 built, that #25 and #26 use rather than re-invent

```python
from hydms.surrogate import select_features, select_across_folds, SelectionSettings

folds = select_across_folds(frame, split)   # one selection per outer fold of #88's grouped_folds
folds.consensus()   # chosen by every fold        folds.union()       # chosen by any
folds.stability()   # how many folds chose each   folds.per_fold()    # rows, removals, features
select_features(frame, train_labels).trace()      # the stage-by-stage funnel, for #37
```

- **`select_features` slices to `train` in its first statement and never reads the frame again.**
  That is the whole of the L6 fix — structural, not care — and it is what
  `assert_selection_ignores_holdout` measures. A test also deletes the held-out rows entirely, which
  catches a stage that computes over the whole frame and then subsets.
- **There is deliberately no "the selected features" on a `FoldSelection`.** Selection inside the
  folds has one answer per fold; collapsing them into one is **#25's decision**, and the two obvious
  readings are offered side by side so neither wins silently.
- **The three stages are the three that exist.** `Boruta_FeatEng.py`'s variance filter, Boruta and
  the iterative VIF loop — not REPORT §3.3's five, which are in neither archival selector.
  `Feature_selection.py` is dead code reading a directory whose writer was deleted in `5c3bcb1`.
- **CleanLab is called from `hydms.data.screening.label_issues`, not from the surrogate layer.** The
  judgement lives with the card that owns "which rows are label-suspect" (#14); the selector only
  supplies the matrix. It returns two of CleanLab's four columns — `predicted_label` is
  `CleanLab.py:90`'s leak in raw form, and there is now no object a caller could reach one through.
- **Screening runs inside the folds too**, for the same reason selection does: a verdict fitted over
  the whole training split would choose each fold's training rows with that fold's held-out rows in
  view.

#### Three numbers for the S4 chain

- **A pass costs 676 s of Boruta** at `selection.boruta_max_iter` of 2000, plus 14 s of CleanLab, on
  the real 893 x 21 matrix. `python -m hydms.surrogate.select` is a **slow-lane command**, about 50
  minutes. Nothing in a test or a gate may run the configured budget.
- **`SENTINEL_BUDGET` is why HG-1 can still be `Speed.FAST`** — the L6 live hook runs the *real*
  selector under ten Boruta iterations and a fifty-tree forest, with every other threshold
  configured. It changes how long the stages run, not which rows they read, and a `slow`-marked test
  checks that claim at the real budget rather than asserting it.
- **The variance filter drops nothing on the real matrix.** The lowest variance among the 21 is
  `dev_Covalent_Radius` at 0.0032, triple the 0.001 threshold.

#### Findings of this session

- **Two of #24's own boxes were wrong about the data, and measuring the premise first is what caught
  it.** The card predicted `VarianceThreshold` would drop `avg_is_alkaline` because its
  inter-quartile span over the training rows is exactly zero. **A zero IQR is not constancy**: the
  column takes 75 distinct values over the 893 rows and its variance is 0.0707, seventy times the
  threshold. It survives — raw or scaled, since a `FittedScaler` substitutes a scale of 1.0 for a
  zero span and subtracting a median does not change a variance — and Boruta then *confirms* it. The
  verdict is a test on the real rows, not a narrative note, because a note would not go red if the
  featuriser ever made the column genuinely constant.
- **The Gordy trade is settled: drop the feature, keep the rows.** #24 and #25 both carried it as an
  open question. Measured over the 700 training rows where all 22 features are computable — same
  seed, configured budget, only the column varying — Boruta **does** confirm
  `dev_Gordy_electonegativity` when it can. But twelve of the thirteen confirmations are the same
  either way; its absence is taken up by `dev_gilmor_number_of_valence_electron` and by
  `temperature(K)`. Against that, carrying it costs **193 of 893 training rows (21.6 %)**,
  concentrated in AB5 (67 of 143) and MIC (37 of 87) — the two classes AC-6 scores. A quarter of the
  training rows against a substitutable descriptor is not a close trade. `--all-features` runs the
  other way for #25's comparison.
- **`Boruta` and `statsmodels` are now declared dependencies.** Both were already installed in
  `Project` for the archival pipeline, so the lock files stay valid; what changed is that they are
  in `pyproject.toml` and in `RECORDED_PACKAGES`, because a distribution whose version can change a
  fit and which no manifest records is a provenance hole. A test in `tests/artifacts/` enforces the
  pairing — and it parses the dependency block with a regex, so **do not put a double-quoted phrase
  in a comment inside `dependencies = [...]`**; it will be read as a package name.

---

### Handoff — 2026-09-04 · #88 closed · written for #24

**Where the phase is.** Twenty-eight cards done. Suite **807** green (770 + 37), ruff 0.8.4 and
mypy 1.13.0 clean, `check_board.py` and `check_freeze.py` OK, AC-2 green at 2.7285e-12,
`run --fast` exits 0, and **HG-1 is at 8/13** — L2, L4 and L7 went green the same hour the module
they name appeared, which is what the `unwired` state exists to force. One card is still `doing`:
**#14**, unchanged.

**The front is #24, and it is blocked by a card that is waiting on it.** #24's `blocked_by` is
[#14, #20, #88]; #20 and #88 are done, so the only thing in front of it is #14's `doing` status —
and #14's one remaining box reads *"feature selection (#24) consumes CleanLab's output"*, which is
#24's work. That is not a board error, it is one unit of work cut across two cards, and
`check_board.py` will refuse `#24 → doing` until #14 is `done`. **Do them in one sitting**: build
#24's selection against `hydms.data.screening.screen()`, tick #14's box and close #14 in that
commit, then move #24. Do not close #14 first to unlock the board — the box is the record that the
CleanLab call was never exercised end to end.

Independent of all that, **#7 (CI slow lane) has been unblocked since #6 landed** and nothing in
S4 waits on it.

**What #88 leaves for #26 to trip over.** The tuning budget is now a product:
`model.cv_folds` (5) x `model.inner_cv_folds` (3, new in `pipeline.yaml`) x
`model.optuna_trials` (300) = **4,500 CatBoost fits per contender**. That is boxed on #26. If it is
prohibitive, lower a number in config — collapsing the nesting is leak L4 walking back in.

#### What #88 built, that the rest of S4 uses rather than re-invents

`hydms/surrogate/validation.py` — the folds, and the guarantee that the data which produced a score
never chose it.

```python
from hydms.surrogate import Contender, grouped_folds, leave_one_class_out, nested_scores

folds = grouped_folds(training_rows, name="outer")   # the project's ONLY fold generator
evaluation = nested_scores(features, split, [Contender("catboost", tune, score)])
evaluation.records          # one SelectionRecord per model — tuned_on, scored_on, metrics
evaluation.per_fold         # the spread behind the mean; chosen[model, fold] holds the winner
nested_scores(features, split, contenders, outer=leave_one_class_out)   # #30's AC-6, same path
```

- **You cannot cross-validate without saying which rows are training rows.** `nested_scores` takes
  the whole matrix *and* #13's split assignment and selects them itself, refusing a split that
  holds nothing out — the same guard `fit_scaler` makes, for the same reason. It follows that no
  metric in a record may be named `val` or `test`; both are refused, which is **stricter** than
  `assert_selection_is_nested`'s default of `("test",)` and deliberately so — what L2 published was
  a *validation* score.
- **`grouped_folds` is the only fold generator, and a test asserts it** by refusing any other module
  under `hydms/` that imports a `KFold`. `hydms/data/splits.py`'s `StratifiedShuffleSplit` cuts the
  train/val/test split, not folds, and is deliberately not one.
- **The outer partition is an argument.** `outer=leave_one_class_out` gives #30 the AC-6 protocol
  with everything between proposal and score unchanged. A second scoring path in #30 is the
  duplication the whole board is shaped to prevent.
- **A fold id is issued for content**, not by counting: `FoldSpace` maps the set of canonical
  compositions a fold holds out to an id, so an inner fold over an outer fold's materials collides
  with it and `tuned_on ∩ scored_on` is a real question. Two independent counters would have made
  the L4 detector decoration. `space.known(...)` is the read-only lookup the L4 live hook checks
  that premise with before it checks the conclusion.
- **`tuned_on` is measured.** The inner folds handed to a search record every fold it reads, and a
  search that read none is refused. It cannot catch a tuner that rebuilds folds from the frame — but
  the frame it is handed holds the outer fold's training rows and nothing else.
- **Stratification is #13's `stratify`, not a second scheme**, recomputed for each fold set from the
  rows that set may see. Quantile bins are a function of the targets they are computed over; taking
  them once over the whole training matrix would let every fold's held-out rows shape the folds.

#### Three numbers for the S4 chain

- **181 of 893, not 141 of 896.** The archival row-level shape re-run over the reproduced training
  split leaves **20.3 % of rows** in a fold their canonical composition also occupies, against 144
  under the raw formula string. The runbook's L7 row now carries both.
- **156 compositions in each of five outer folds** — 780 training compositions over 893 rows,
  divided exactly. `grouped_folds` costs 0.23 s on that frame, `nested_scores` about 0.9 s with two
  trivial contenders; the stratification is ~35 ms a call.
- **The smallest alloy-class fold is 19 rows.** LEA 19 / 19 compositions, then A2B 29 / 21, HEA
  51 / 47, AB 59 / 55, SS 73 / 69, MEA 76 / 69, MIC 87 / 81, Mg 96 / 89, AB5 143 / 123, AB2
  260 / 207. Boxed on #30: an R² over 19 rows is not the claim an R² over 260 is, and it must be
  reported beside its support.

#### Findings of this session

- **`min_stratum_size` and `cv_folds` are coupled, and nobody had written it down.** Rare strata are
  merged up to `split.min_stratum_size` (5) compositions, and `StratifiedGroupKFold` cannot spread a
  stratum over more folds than it has members. At 5 and 5 the real data sits exactly on that line;
  the config loader now refuses `cv_folds > min_stratum_size` rather than leaving it to a warning
  nobody reads.
- **A metric that arrives as `"0.94"` is refused by type, not by `float()`.** `float("0.94")`
  succeeds, so a coercion would have accepted a score something upstream had stringified.
- **The card asked for stratification on the binned target; it got #13's merged
  `(temperature, target)` key.** `splits.stratify` was exposed for exactly this and says so in its
  own docstring. The box is ticked on the ground that two stratification schemes are two answers to
  one question — if a later card wants the target alone, that is a change to #13's function, not a
  second one here.

---

### Handoff — 2026-09-04 (earlier) · #23 closed, **S4 open** · written for #88

**Where the phase is.** Twenty-seven cards done and S4 has started. Suite **770** green (724 + 46),
ruff 0.8.4 and mypy 1.13.0 clean, `check_board.py` and `check_freeze.py` OK, AC-2 green at
2.7285e-12, HG-1 still `SKIPPED` at **5/13**, `run --fast` exits 0. **One card is still `doing`:
#14**, unchanged.

**The front is #88, not #24.** The runbook draws the S4 chain as `#23 → #24 → #25 → #88 → #26`,
which is the order the *work* reads in; the `blocked_by` graph disagrees and it is the authority.
#24 is blocked by #14 (`doing`) and by **#88**, and #88 is blocked by #13 and #23 — both now done.
So #88 is the only S4 card with nothing in front of it, and #24 opens behind it.

**#88 will turn the build red the day it creates its file, and that is correct.** Three sentinels —
L2, L4 and L7 — name `hydms.surrogate.validation` as their subject, and all three read `pending`
today for one reason only: the module does not exist. The moment `hydms/surrogate/validation.py`
appears they go `unwired` and HG-1 goes **red on purpose** until #88 gives each a `live` hook
against the real protocol. That is the L13 shape from S3, twice over. **Never re-aim a subject to
make a sentinel green.** Landing all three takes HG-1 from 5/13 to 8/13.

#### What #23 built, that the rest of S4 uses rather than re-invents

`hydms/surrogate/scaler.py` — the scaling transform, and the fact that it belongs to the trained
model rather than to the batch in front of it.

```python
from hydms.surrogate import fit_scaler, scaler_from

scaler = fit_scaler(features, split)      # the WHOLE matrix + #13's assignment; it selects train
scaler.transform(candidates)              # by name, in fitting order, returns a DataFrame
artifacts.save({"scaler": scaler, ...}, contract=CONTRACT, gates=report)
scaler_from(artifacts.load(...))          # the way back, checked against the manifest
```

- **You cannot fit it without saying which rows are training rows.** `fit_scaler` takes the whole
  matrix *and* the split, selects the rows itself, and **refuses a split that holds nothing out**.
  Do not pre-filter to a training subset and hand that in — it is the one call the guard is shaped
  to refuse. The result records `fitted_rows` against `held_out_rows` (893 / 385 on the real
  matrix), so the artifact states the ratio rather than implying it.
- **What is stored is the fitted transform, not the estimator** — names, medians, IQRs. There is no
  `fit` inside to reach; `fit`, `fit_transform` and `partial_fit` raise and say why. A scikit-learn
  upgrade therefore cannot change what a saved `v1` does, which is the AC-1 failure mode. Nothing is
  lost to it: `(x - centre) / scale` is **bit-identical** to `RobustScaler.transform` over all
  1,278 × 21 values of the real matrix, and a test re-measures that rather than trusting it.
- **`transform` takes a `DataFrame` and refuses an array.** Measured on scikit-learn 1.6.1: a
  `RobustScaler` fitted on a frame raises on a reordered one, but accepts a bare `ndarray` with only
  a `UserWarning` — and `fit_transform` returns an `ndarray`, so the names are gone one line after
  the fit. That is where a permuted matrix becomes plausible, wrong numbers. The output is always in
  **fitting** order, whatever order the caller had, which is what #26 and #28 need.
- **`scaler_from` checks a subset, not an equality.** The stored scaler's columns must be *among*
  the version's feature contract. #24 is expected to narrow them; equality would go red on correct
  code the day selection lands.
- **`require_gates=False` is still open and still closes at #34.** A version saved before
  #31/#32/#33 records no passing gate run and will not load without it. `tests/surrogate/test_scaler.py`
  passes it in one fixture, with the reason written beside the call.

#### Two numbers for the S4 chain

- **`transform` costs 0.29 ms for 1,278 × 21 and 0.19 ms for a single row** — a per-call floor, like
  `featurize`'s 5 ms one, and the same instruction follows: **scale in batches**. scikit-learn's own
  `transform` is 0.60 ms on the same matrix. These are the second and third numbers #22 asked for;
  **[../docs/BENCHMARKS.md](../BENCHMARKS.md) still has no end-to-end rate and must not be given
  one until #28's `predict()` exists.**
- **The real training matrix is 1,278 rows of 21 features.** Dropping `dev_Gordy_electonegativity`
  (266 rows refused) leaves every row but `Eu1Ni5`, whose jarvis cells are empty for six features.
  The trade stays #24 and #25'. If you need the refused rows in a fixture, ask
  `CONTRACT.computability()` once per **element**, not once per row — a hole is a (feature, element)
  pair, so fifty-odd verdicts answer for all 1,279.

#### Findings of this session

- **`avg_is_alkaline` is constant over the training split.** Zero inter-quartile span over the 893
  training rows, so `RobustScaler` substitutes a scale of 1.0 and the scaled column is all zeros.
  `VarianceThreshold(0.001)` should drop it and the archival counts do not say whether it did —
  **boxed on #24**, to be recorded rather than assumed. `FittedScaler.degenerate` captures such
  features at fit time, the only moment a scale of 1.0 is still distinguishable from an IQR that
  genuinely equals 1.0.
- **`hydms.config.load()` parses `pipeline.yaml` on every call and is not cached.** Harmless
  everywhere it is used today; it is not harmless on a per-candidate path. `transform` reads no
  configuration at all for that reason — it gets the check it needs from requiring the column set to
  *equal* the fitted features, which is strictly stronger than `refuse_non_features` and free. Worth
  knowing before #28 and #76 put anything else on that path.
- **No sentinel names `hydms.surrogate.scaler`,** so unlike `merge.py`, `featurize.py` and the
  modules #88 and #26 are about to create, this one was not expected to move HG-1 — and did not.

---

### Handoff — 2026-09-04 (earlier) · #44 closed · written when the front was still #23

**Where the phase is.** Twenty-six cards done. #44 landed out of stage order for the same reason #4
did: it is blocked only by #3, and S5's other two guard rails wait on #30. Suite **724** green, ruff
0.8.4 and mypy 1.13.0 clean, `check_board.py` and `check_freeze.py` OK, HG-1 `SKIPPED` at 5/13 —
**no sentinel names `hydms/screens/`**, so unlike `merge.py` and `featurize.py` this package did not
turn the build red on the day it appeared.

**The opening move is unchanged and it is not this card's.** It is **#23**, then thirteen cards of
S4 chain, and the handoff directly below this one is the live one for it — read it for what #4
built, the `require_gates=False` window that closes at #34, and where the transform-only wrapper
lives. The 63 tests it lists as uncommitted work on #44 are what landed here: **661 + 63 = 724**,
which resolves its last finding.

#### What #44 built, that S5 and S6 are expected to use rather than re-invent

`hydms/screens/` — `protocol.py` is the contract, `window.py` is the worked screen.

```python
from hydms.screens import apply_screens, temperature_window

verdicts = apply_screens(candidates, [temperature_window(), ceiling, novelty])
verdicts.table            # admitted, then <screen>.passed / .code / .reason / evidence columns
verdicts.rejections()     # long form: one row per rejection, with the sentence
verdicts.summary()        # per candidate: which screens rejected it, and why — the CSV of S3
shortlist = verdicts.select(candidates)   # the filtering: afterwards, explicit, by a caller
```

- **Nothing is filtered by a screen, ever.** A rejected candidate is a row with `passed=False`, not
  an absent row, and `select()` is the only thing that removes anything. That is the whole card.
- **The runner is the enforcement point; the protocol is only a promise.** `apply_screens` refuses a
  screen that drops, adds or reorders a row, writes into the batch, returns a malformed verdict, or
  emits a code it never declared — by name, every time. `verdict_table()` is a convenience and
  validates nothing, deliberately: a screen that builds its frame by hand is checked identically.
- **The vocabulary is declared, not discovered.** Each screen exposes `reasons`, and a code outside
  it is refused. **#75 derives its refusal schema from that union rather than restating it** — boxed
  there, and on #48, whose `OUT_OF_DOMAIN` / `HIGH_UNCERTAINTY` distinction is now something a test
  can assert rather than a naming convention.
- **Extra columns are evidence and are carried through prefixed.** #49's ElMD distance and nearest
  formula ride on the verdict frame as `novelty.distance` / `novelty.nearest`; do not build a second
  return channel that can disagree with the verdict. Boxed on #49.
- **`INDETERMINATE` is a rejection.** A screen that cannot judge a candidate does not admit it —
  fail-closed, because the alternative is a candidate reaching the shortlist *because* the rule
  meant to stop it broke. It is a declared code, not an exception and not a `None`.
- **One call per screen per batch, whatever the size**, asserted at 1, 10 and 1,000 rows by a screen
  that counts its own calls. `Verdicts.durations` and `counts()['seconds']` are there because the
  one thing the runner cannot see is a screen looping *internally* — the 200× shape #22 measured.
- **`temperature_window()` is the outer bound and never an applicability domain.** It reads
  195–773 K and the column name from config, and admits all 1,279 curated rows — which is the check
  that the bounds really are the measured span. **#76 uses it rather than re-writing the
  comparison**, boxed there; coverage inside is uneven (39 test rows above 500 K) and #48 is what
  speaks to that.

#### Findings of this session

- **A window shipped with the protocol, and the blocker is why.** A bare `Protocol` needs no config
  loader, yet #44 is blocked by #3 — and `docs/QA-PROTOCOL.md` asks this layer for *boundary cases
  on each window, both sides* when no window existed. `Window` is that, `temperature_window()` is
  the config-driven instance, and it demonstrates once the property #48's ceiling is required to
  have. It is the only scope this card took beyond its four boxes.
- **Catching a mutation needed a content fingerprint, not a structural check.** A screen that
  overwrites one cell in place, or sorts the batch in place, passes every comparison of shape,
  columns and dtypes — and an in-place sort is the worse of the two, because the *next* screen then
  judges a differently ordered frame and the result silently depends on the order the screens ran
  in. `hash_pandas_object` weighted by row position catches both; an unweighted sum would miss the
  permutation. One O(rows) pass per screen, against the seconds that batch spends being featurised.
- **Two sessions shared this working tree.** #4 and #44 were being written at the same time in the
  same checkout, which is why the commit for this card stages named paths and not `-A`:
  `.gitignore` (a local `research/` exclusion) and #23's move to `doing` are somebody else's
  in-flight work and were left untouched. If you are about to run two cards at once, land them in
  different worktrees or accept that every commit has to be path-scoped.

---

### Handoff — 2026-09-04 (earlier) · #4 closed · written for S4, opening at #23

**Where the phase is.** Twenty-five cards done. #4 landed out of stage order because **#23 was
blocked by it** and S4 is a thirteen-card chain that starts there; `#23` is now unblocked and
nothing stands in front of it. Suite **661** green, ruff 0.8.4 and mypy 1.13.0 clean,
`check_board.py` and `check_freeze.py` OK, HG-1 `SKIPPED` at 5/13, AC-2 green, `run --fast` exits 0.

**Read the next handoff down as well** — the one written when #22 closed S3. It carries #22's 13×
finding and the four things S3 left for S4 that are not repeated here in full: `with_features` is
the only place the record and the matrix become one
frame, the full 22 cannot build a training matrix at all (266 of 1,279 rows refused, 265 for
`dev_Gordy_electonegativity` alone), `featurize` has a 5 ms per-call floor so featurise in batches,
and HG-1 goes from 5/13 to 11/13 across S4 with the sentinels already written.

#### What #4 built, that S4 is expected to use rather than re-invent

`hydms/artifacts/` — `manifest.py` records, `store.py` stores, and `save()` / `load()` are the only
doors. **#23 is the first caller**: the fitted `RobustScaler` is a payload in a version, not a
pickle beside a script.

```python
from hydms import artifacts
artifacts.save({"model": m, "scaler": s}, contract=CONTRACT, seeds={...}, gates=report)
bundle = artifacts.load()                 # the promoted version, gates checked
bundle["scaler"].transform(X)             # never .fit
```

- **A version is written once.** `save` stages `.v{N}.partial` and renames it into place, refuses an
  existing version, and never re-uses a number a dead run left behind. Do not write into a version
  directory by hand: every payload carries a SHA-256 and `load` re-hashes it.
- **The gate report is embedded verbatim, not re-formatted.** `save(gates=report)` takes either a
  `GateReport` or the mapping its `to_dict()` produced — the same object
  `python -m hydms.gates run` already writes to `artifacts/gate-results.json`.
- **A version whose recorded gates did not all pass will not load and cannot be promoted, and a
  `SKIPPED` gate counts.** That is stricter than `GateReport.ok`, deliberately: `ok` tolerates a
  skip under a broad selection so CI is not red for the length of the phase, and that leniency is
  right for a CI log and wrong for an artifact about to answer a prediction. **So a version saved
  today cannot load without `require_gates=False`** — pass it in #23 through #33 and expect to stop
  passing it at #34, which is blocked on #31/#32/#33 for exactly this reason.
- **The contract is not optional and is not decorative.** `save(contract=...)` refuses anything that
  is not a `FeatureContract` or its `as_manifest()` payload. Swapping two features in a stored
  manifest still loads the bundle — the payload bytes are untouched — and then raises `ContractError`
  from `bundle.contract()`, which is the AC-4 failure caught by #19's digest rather than by a person.
- **Promotion is `current.json`.** `promote(version)` refuses an unestablished one; rollback is
  `promote(older)`. That is card #7's contract, made structural here rather than in a workflow file.

#### The opening move

**#23, and S4 is thirteen cards of chain.** Fit the `RobustScaler` on train only, persist it into
the artifact version, and make the load path expose `transform` and not `fit`. Two things to settle
inside the card rather than around it:

- **Where the transform-only wrapper lives.** The card asks that `fit` raise on the loaded object.
  The store deliberately does not know what a scaler is — it stores objects — so the wrapper is
  `hydms/surrogate/`'s, and `save` stores the wrapped thing. Wrapping at load time would mean the
  store growing per-payload knowledge, which is the seam this board is shaped to keep closed.
- **#23's `blocked_by` is satisfied but #88 is not.** #88 (group-aware nested CV) is blocked by
  #23, and #23 needs a train split to fit on — that is #13's `hydms/data/splits.py`, which is done.
  Use it; do not derive a split inside the surrogate layer.

**And before you land a gate:** `tests/gates/` takes an `unwritten` fixture (`tests/gates/conftest.py`)
wherever it needs "a criterion nobody has written yet". Use it for #26, #28, #30, #31, #32, #33, #77,
#79 and #86 — naming a gate there is what card #21 had to undo.

**S4's exit check:** `conda run -n Project python -m hydms.gates run --fast` · all HG-1 sentinels green.

#### Findings of this session

- **`joblib` needed a mypy override.** It ships neither inline types nor a `py.typed` marker and the
  conda-free lint lane installs nothing, so `import joblib` under `hydms/` aborted the type check.
  Added to the existing `ignore_missing_imports` block in `pyproject.toml` with the reason beside it.
- **`versions()` sorts numerically, never lexicographically.** A string sort puts `v10` before `v9`
  and promotes the wrong artifact on the tenth retrain. One `int()`, one test, a real incident avoided.
- **`RECORDED_PACKAGES` is checked against `pyproject.toml` by a test,** not maintained by memory:
  a new core dependency that nothing records leaves "it used to reproduce" as the only evidence when
  AC-1 goes red after an upgrade.
- **`tests/screens/` is uncommitted work on #44 that this session did not touch.** Two modules
  under `hydms/screens/` — `protocol.py` and `window.py` — and their 63 tests are in the working
  tree and pass; the card is still `backlog` and the files are untracked. That is the difference between the **661** reported above
  and the **724** a bare `pytest` prints. It is #44's to land — S5's card, not S4's.

---

### Handoff — 2026-09-04 (earlier) · #22 closed, **S3 closed** · written for S4, opening at #23

**Where the phase is.** Twenty-four cards done and **the descriptor layer is finished**. Suite
**593** green, ruff 0.8.4 and mypy 1.13.0 clean, `check_board.py` and `check_freeze.py` OK, HG-1
`SKIPPED` at 5/13, AC-2 green at 2.7285e-12 in 1.28 s. S2 and S3 have both closed as far as they can;
**everything left in this phase is a chain, and it starts at #23.**

**#22 was budgeted as a printout and returned a 13× defect in the layer it measures.** This is the
one thing to carry forward from it.

- **The number this project has been quoting since #20 was measured on four formulae.** *10,000
  formulae in 0.31 s* — in `featurize`'s docstring, in #20's narrative and in three handoffs below
  this one — came from `["LaNi5", "TiFe", "Mg2Ni", "Ti0.8Zr0.2Mn1.4V0.2Cr0.4"] * 2500`. Ten thousand
  rows, **four** distinct compositions. The computability verdict is memoised per element *set*, so
  that batch answered it four times instead of ten thousand. Ten thousand genuinely distinct
  candidates took **3.34 s** — 2,996/s, three times the card's feasibility floor rather than forty.
  **Those earlier handoffs are history; the number is now 0.245 s.**
- **97% of the wall clock was one cache that no caller could reach.** `cProfile`:
  `FeatureContract.computability` → `PropertyTable.has`, **13.8 million calls to answer nineteen
  questions**. The servable-element set was cached only for the *shipped* tables, keyed by table name
  — and `featurize._sources` always hands `computability` a resolved `tables=` mapping, so the cached
  branch was unreachable from the featuriser. Its comment said the uncached path was "affordable
  because the only caller is a gate that runs once". Every caller was on it. The memo now lives on
  the table (`PropertyTable.servable`, a `cached_property`) and `contract._servable` is a one-line
  forward. **10k distinct 3.3375 → 0.2448 s, 100k 21.03 → 2.23 s, curated 0.1602 → 0.0221 s, the
  suite 24.9 → 17.9 s, AC-2 1.54 → 1.28 s. No expected value in any test moved.**
- **A benchmark is only evidence if the workload is the one the decision is about.** That is why the
  candidates are asserted distinct *and* their element sets distinct — distinct strings alone would
  let the workload silently become a cache again — and why the parse half is timed separately. The
  parser turned out to be 22%, so the card's instruction was right about the principle and wrong
  about the culprit.

**What R6 now knows, and the sentence not to drop.** A 1e6-point grid featurises in ~24 s, 1e7 in
~4 min, NSGA-II's whole 100,000-evaluation budget in 2.2 s. **Featurisation does not decide between
Architecture A and Architecture B.** What decides it is unmeasured: one evaluation is featurisation
*plus* the scaler, the surrogate, the conformal interval and two screens — #23, #26, #27, #44, #48,
#49, none of which exists. [../docs/BENCHMARKS.md](../BENCHMARKS.md) says so in bold, because
the failure mode of that document is somebody quoting 44,000 candidates/s as an end-to-end rate.
**Re-measure when #28's `predict()` lands and put the number there beside this one.**

#### The opening move

**#23, and S4 is thirteen cards of chain.** The fit-once scaler: fit on train, persist, never refit.
Four things not worth re-deriving:

- **`hydms.data.metadata.with_features` is the only place the record and the matrix become one
  frame.** #23, #24 and #26 each need a training matrix and none of them should write a `concat`.
  Boxed on #24, with the reason: `temperature(K)` is a column of the raw file **and** one of the 22
  features, so a plain concat returns that name twice, `int64` beside `float64`.
- **The full 22 cannot build a training matrix at all.** 266 of 1,279 rows are refused by the shipped
  tables, 265 for `dev_Gordy_electonegativity` alone; without that one feature the remaining 21 cover
  1,278. The trade is #24/#25's to make and AC-2 restates it in its own output every run.
- **Featurise in batches, and now there is a number for why.** `featurize` has a **5 ms per-call
  floor** — `require_self_consistent` re-auditing both tables' composite columns — which is 2% of a
  ten-thousand batch and 57% of a batch of one. Boxed on #44, where a per-candidate loop would make
  it a 200× cost. It was measured and deliberately *not* optimised: it moves no number #22 publishes.
- **HG-1 goes from 5/13 to 11/13 across S4**, and the sentinels are already written. #24 owes L6, #88
  owes L2/L4/L7, #26 owes L1/L5 — each is `pending` today only because its subject module does not
  exist. Expect the same shape as L13 in S3: the day the module appears the sentinel reads `unwired`
  and HG-1 goes **red on purpose** until the owning card gives it a `live` hook. Do not re-aim a
  subject to make it green.

**One card is still `doing`: #14**, and S4 is where it comes due — #24 consuming its output closes the
`Boruta_FeatEng.py:23-25` bypass and supplies the feature matrix CleanLab needs to produce
`label_issues` at all. **#15 is written, green, and stays `backlog` behind it**; when #24 lands,
`screened.rows_out` and `screened.removed` move and those two facts are re-measured. Nothing else in
`tests/data/test_golden.py` should move, and if it does, that is the finding.

**And before you land a gate:** `tests/gates/` takes an `unwritten` fixture (`tests/gates/conftest.py`)
wherever it needs "a criterion nobody has written yet". Use it for #26, #28, #30, #31, #32, #33, #77,
#79 and #86 — naming a gate there is what card #21 had to undo.

---

### Handoff — 2026-09-04 (earlier) · #21 closed, AC-2 green · written for #22, then S4

**Where the phase is.** Twenty-three cards done, and **S3 has one card left**. The suite is **577**
green, ruff 0.8.4 and mypy 1.13.0 clean, `check_board.py` and `check_freeze.py` OK, HG-1 still
`SKIPPED` at 5/13, and the fast lane exits 0 with **AC-2 the first `PASSED` row the gate table has
ever carried**. The hard gate of S3 is answered: `2.7285e-12` against a tolerance of `1e-9`, over
1,278 of the 1,279 curated formulae, in 1.5 s.

**#21, and why a gate expected to be green was still a day's work.** #20 had already measured the
16-formula version at 4.547e-13, so the outcome was never in doubt. What the card actually bought is
everything around the number.

- **The exclusion is derived from both sides.** The card says no europium formula may be compared and
  that the exclusion must be *recorded*, not filtered. Hard-coding `"Eu"` would have satisfied the
  letter of that. A row is instead excluded when this layer refuses it — `computability` against the
  tables the gate is actually using — **or** when CBFV lists it in the `skipped` array that
  `extract_features_cbfv.py` never read, and the result prints the two counts separately, because
  the case worth seeing is the two *disagreeing*. Today they are the same single row. Measured on the
  way: **CBFV's `jarvis.csv` has no europium row at all** (82 elements, not 85), and CBFV emits a
  full row for `Eu1Ni5` anyway — `avg_atom_mass` 48.911 is `(0×1 + 58.6934×5)/6`. The all-zero
  property vector is now arithmetic rather than inference.
- **The gate reads CBFV's installed table, not the committed fixture** — a correction to two boxes
  and to the last handoff. The numbers are identical (zero differing cells, because the fixture was
  written with `repr(float)`), but the gate imports CBFV anyway to produce the expected values, and a
  second source of the *table* admits a skew between the two halves of one comparison that would
  surface as a parity failure rather than as the stale fixture it is. It also keeps package code out
  of `tests/`. The fixture gained a test that pins it against the installed table cell by cell.
- **Supplying CBFV's JARVIS copy as well changes nothing — 2.7285e-12 either way, same cell.** #16
  recorded the two copies of NIST's file agreeing to 7.3e-12 and the worst offender here is a JARVIS
  composite of magnitude ~4e3, so table skew was the reasonable suspect. It is not. The whole residue
  is #17's element order, and the card's "suspect the order before the arithmetic" is now measured.
- **A green gate has to be able to say what it did not establish.** Two of the card's boxes are about
  AC-2's blind spots and both are lines of the result — what was excluded, and that the *shipped*
  tables could not have featurised **266 of 1,279** rows at all. Writing them found that
  `_report.py` printed multi-line detail only for `FAILED` and `ERRORED`, so both lines lived only in
  the JSON. Any status prints it now; HG-1's per-leak listing had been invisible for the same reason.

**The thing to know before you touch `tests/gates/`.** Landing the first real gate broke six tests
that were never about it: `test_harness.py` and `test_cli.py` used the literal `AC-2` wherever they
meant "a criterion nobody has written yet", so a passing AC-2 turned four strictness tests and two
CLI tests into tests of featuriser parity. They now take the **`unwritten` fixture** in
`tests/gates/conftest.py`, which asks the registry which gates are still `Pending` and asserts the
answer is non-empty. **Use it when you land #26, #28, #30, #31, #32, #33, #77, #79 or #86** — do not
substitute another gate name, or the next card repeats this. Four doc comments that used AC-2 as the
standing example of an unimplemented gate were repointed at HG-2 -- and **card #77 landed HG-2, so
the sentence went untrue again**. They now name **AC-5**, which is frozen with Phase T and
therefore outlives this phase: the example stops chasing whichever card landed last. The reason is
written beside it on `GateReport.ok`.

#### The opening move

**#22, and it is the last card in S3.** The featurisation throughput benchmark. It starts from
numbers already measured rather than from nothing: **10,000 formulae in one call take 0.31 s** and
the curated 1,278 take **0.21 s** (`featurize`'s module docstring quotes both), and this card added a
third — the whole AC-2 gate, which featurises 1,279 rows once and runs CBFV over them twice, takes
**1.5 s** end to end. What #22 owes is a benchmark that is a *check* rather than a printout: a
threshold that fails the build, a shape that says whether the cost is per-call or per-formula, and a
statement of what it is defending — the memo's practical check 3 warns against a per-formula loop,
and Architectures A and B both evaluate candidates in batches. `pyproject.toml` declares a `slow`
marker for tests that take more than a few seconds; decide whether this one earns it.

**Then S3 closes and S4 opens at #23**, the fit-once scaler. Two things there that are not worth
re-deriving:

- **`hydms.data.metadata.with_features` is the only place the record and the matrix become one
  frame.** #23, #24 and #26 each need a training matrix and none of them should write a `concat`.
  Boxed on #24. The reason is on that box too: `temperature(K)` is a column of the raw file *and* one
  of the 22 features, so a plain concat returns the name twice, `int64` beside `float64`.
- **The full 22 cannot build a training matrix at all** — 266 of 1,279 rows are refused by the
  shipped tables, 265 for `dev_Gordy_electonegativity` alone. Without that one feature the remaining
  21 cover 1,278. That trade is #24/#25's to make, and AC-2 says so in its own output every time it
  runs, precisely so a green gate is never read as "the featuriser can produce all 22 for every row".

**One card is still `doing`: #14.** It owes S4, not S3 — #24 consuming its output is what closes the
`Boruta_FeatEng.py:23-25` bypass and supplies the feature matrix CleanLab needs to produce
`label_issues` at all. #15 is written, green, and stays `backlog` behind it.

---

### Handoff — 2026-09-04 (earlier) · #12 closed · written for #21, then #22

**Where the phase is.** Twenty-two cards done and **the tree is green again**: 567 tests pass, ruff
0.8.4 and mypy 1.13.0 clean, `check_board.py` and `check_freeze.py` OK, HG-1 **skipped at 5/13**
rather than failing. The eight red tests the last handoff described were one fact and it closed the
way it was written down: #20 created the featuriser, the L13 sentinel went `unwired`, #12 pointed it
at the real thing. The subject string was never touched.

**#12, the second half.** It landed its data half on 2026-09-03 and could not finish: three boxes
named `hydms.descriptors.featurize`, which did not exist. All three closed here.
`hydms.data.metadata.with_features(record, features)` is the join — `refuse_non_features` on the
way in, `assert_metadata_survives` on the way out, by label, refusing every way that join has
silently gone wrong in this repository — and the L13 `live` hook runs it over the real featuriser
across **1,278 of the 1,279** curated rows. 11 new tests on the join, one on the end-to-end path,
and one that puts `extract_features_cbfv.py:19-21` back into the real seam and asserts the audit
reports L13 `broken` — the only thing that distinguishes a hook watching the pipeline from a hook
watching a copy of it.

**Three things it taught.**

- **The join needed a function, not a line.** The card prescribed `pd.concat([metadata, features],
  axis=1)` and the hook could have written it inline. That would have made the L13 sentinel guard
  four lines of `hydms/qa/sentinels.py` — the same mistake, in the other direction, as pointing
  L13 at the data layer would have been in S2. So the guard lives in the pipeline (the #14 pattern:
  `screen` calls its detector before it returns) and the sentinel re-runs it. Weakening the check
  inside the join cannot make HG-1 green.
- **Writing the join found that the prescribed `concat` was subtly wrong.** `temperature(K)` is a
  column of the raw file **and** one of the 22 features, so concatenating the record with the matrix
  returns a frame carrying that name **twice**, `int64` beside `float64`, and pandas hands it over
  without a word. `merge_datasets.py:49` is the archival answer —
  `df_merged.loc[:, ~df_merged.columns.duplicated()]`, keep whichever arrived first — which
  makes this the third disguise of one defect (#10 found the second, one line below the leak).
  `with_features` takes the **matrix's** copy, because that one carries #19's cast (313.5 K must not
  become 313), but only after checking the two agree exactly. That check is free — widening
  `int64` to `float64` is exact — and it is the only tie in the frame between a record and a
  matrix that claims to describe it: featurise at other temperatures and it refuses, by row.
- **The hook's coverage was a choice, and it is documented as one.** The full 22 featurise only
  **1,013** of the 1,279 rows (the Gordy hole, measured again here); without
  `dev_Gordy_electonegativity` it is **1,278**, everything but `Eu1Ni5`. The hook drops that one
  feature so it checks the file rather than three quarters of it, and its docstring says this is a
  statement about the *check's* coverage and **not** a decision about the feature set, which is
  #24/#25's to make. The rows it keeps come from asking `FeatureContract.computability`, the idiom
  `featurize`'s own docstring documents, so the refused row is named by the verdict rather than by a
  list in a sentinel. An empty selection raises rather than asserting over nothing: a vacuous pass
  is the shape of the leak this sentinel exists to catch.

**The seam S4 must use, not re-derive.** `with_features` is now the only place the record and the
matrix become one frame. #23, #24 and #26 each need a training matrix; none of them should write a
`concat`. It is boxed on #24, which is the first card that builds one.

#### The opening move

**#21, the hard gate of S3, and it is the only card that is both unblocked and load-bearing.**
Parity with CBFV to 1e-9 over all 1,279 formulae. It inherits three boxes from #20 — the
`tables=` seam and how to build the reference table, "compare in one batch and here is why", and the
news that a 16-formula version already passes at **4.547e-13**. Its remaining work is the other
1,263 formulae, a failure output that names the column and the worst-offending formula rather than a
boolean, and the line stating how many rows the *shipped* tables could not have featurised at all
— because AC-2 runs against CBFV's table, where neither the Gordy hole nor the wrong-axis
reduction is visible. Two amendments from #16 still stand: parity is measured against the reference
table, and **no Eu-containing formula can be compared at all**, because this layer refuses where
CBFV returns a silently-zeroed number.

**Then #22**, the throughput benchmark, which starts from the numbers already measured: 10,000
formulae in **0.31 s**, the curated 1,278 in **0.21 s**. After that S3 is closed and S4 opens at
#23.

**One card is still `doing`: #14.** It owes S4 rather than S3 — #24 consuming its output is what
closes the `Boruta_FeatEng.py:23-25` bypass and supplies the feature matrix CleanLab needs to produce
`label_issues` at all — so it is not in S3's way. #15 is written, green, and stays `backlog`
behind it.

---

### Handoff — 2026-09-04 (earlier) · #20 landed · written for #12, then #21

**Where the phase is.** Twenty-one cards done, and **the tree is red on purpose.** 554 tests,
**546 pass and 8 fail**; every one of the eight is the same fact — `hydms/descriptors/featurize.py`
now exists, so the L13 sentinel reads `unwired` and HG-1 fails at **4 of 13**. ruff 0.8.4 and mypy
1.13.0 clean, `check_board.py` and `check_freeze.py` OK. This was written down in advance on three
cards and it happened exactly as written. **Do not re-aim the sentinel's subject and do not delete
it.** #12 is `doing`, was blocked only on this module, and closes it.

**#20, the featuriser.** `featurize(formulas, temperatures, *, contract=None, tables=None)` →
`(n, 22)` of float64, in contract order, on the caller's index. 52 tests. No CSV in, no CSV out;
one parse pass, then 19 fancy-indexes and 19 batched reductions — 10,000 formulae in **0.31 s**.
Four things it taught, one of which changed a module that was already `done`.

- **A batch of one was not the same arithmetic as a batch of many, and only from eight elements
  up.** #17 established that the reduction must run down the *leading* axis because numpy sums the
  fast axis pairwise. But a batch of **one**, transposed, leaves the leading axis contiguous too —
  and numpy's contiguous sum switches from a plain loop to an eight-accumulator unrolled one at
  exactly eight elements. Measured over 200 random compositions per arity: identical to the bit up
  to arity 7, and from **arity 8** a lone composition disagrees with itself inside a batch by up to
  **5.5e-12** on `avg` and `dev`. That is three orders inside AC-2's 1e-9, so **no gate would ever
  have caught it**; what it would have done is make a single-formula prediction (#82) and AC-4's
  round-trip (#33) disagree with the training matrix, for the eleven curated rows of eight elements
  or more, silently. Fixed in `stats.statistics` — a lone composition is duplicated, the pair is
  reduced, the copy discarded — rather than worked around in the featuriser, because that is where
  the axis decision lives. #17's own test passed throughout because its arity was 5; it is now 10,
  and deleting the fix turns it red. No committed number moves: every existing pin is a batch.
- **The refusal is much bigger than "seven features are not always computable" sounds.** Counted as
  rows a caller loses, the published 22 cannot featurise **266 of the 1,279** curated rows — 265
  for `dev_Gordy_electonegativity` alone, and `Eu1Ni5` for seven features at once. So the full
  contract **cannot build the training matrix at all**. Drop Gordy and the remaining 21 cover
  **1,278 of 1,279**. One feature is the difference between 1,278 rows and 1,013, which is the
  decision #24/#25 are actually making; boxed there.
- **#21's requirement turned out to be a requirement on this module's interface.** "The featuriser
  reproduces CBFV *given the same table*" cannot be arranged from outside a function that resolves
  its own tables. So `tables=` is a parameter — and that forced the honest version of the verdict:
  `FeatureContract.computability(..., tables=)`, because asking the *shipped* table whether a row
  is featurisable while reading CBFV's numbers would refuse the 266 rows the gate exists to
  compare. `PropertyTable.of()` was added so a caller builds a table without reaching through a
  frozen dataclass's underscored field. This is the layer's existing convention, not a new one —
  `disagreements`, `require_coverage` and `require_self_consistent` all take their table.
- **The value pin found nothing wrong, which is worth saying out loud.** All 22 columns against
  CBFV's own output over the sixteen fixture formulae, with CBFV's own table supplied: worst
  **4.547e-13** absolute and **6.828e-15** relative. The assembly — right statistic, right
  property, right table, right column — was correct first time, and the residue is the element
  order #17 already measured.

**Two interface decisions that are not in the card and will look arbitrary later.** The frame comes
back on the **caller's index** (a `Series` keeps its labels, a list gets a `RangeIndex`), a repeated
label is refused, and a `temperature` Series whose index disagrees with the formulae's is refused
rather than zipped by position — all three because the metadata AC-6 needs is re-attached to this
matrix afterwards, and the way that goes wrong is leak L9. And **nothing is ever dropped**: an
unparseable formula, a hole, a non-finite temperature each raise, listing every offender with its
label, because a featuriser that quietly returns fewer rows than it was given is how a feature
matrix comes to be joined to the wrong compositions.

#### The opening move

**#12, and it is the only one.** It is `doing`, it is unblocked, and it is what turns the tree
green. Three boxes are owed and all three name the module that now exists: the class surviving
featurisation, its absence from `X`, and the **L13 `live` hook**. The shape is on the card. Two
practical notes: the join is `pd.concat([metadata, features], axis=1)` and is label-aligned by
construction, never positional; and a `live` hook that featurises real rows must either pick
well-covered formulae or pass a contract without `dev_Gordy_electonegativity`, because the full 22
refuse 266 of the 1,279.

**Then #21, the hard gate of S3.** It inherits three boxes from this card — the `tables=` seam and
how to build the reference table, "compare in one batch and here is why", and the news that a
16-formula version of the gate already passes at 4.547e-13. Its remaining work is the other 1,263
formulae, a failure output that names the column and the row, and the line stating how many rows
the *shipped* tables could not have featurised at all — because AC-2 runs against CBFV's table,
where neither the Gordy hole nor the wrong-axis reduction is visible. Then #22, the benchmark,
which starts from 0.31 s / 10k.

---

### Handoff — 2026-09-04 (earlier) · #18 landed · written for #20

**Where the phase is.** Twenty cards done. The tree is green: **502 tests**, ruff 0.8.4 and
mypy 1.13.0 clean, `check_board.py` and `check_freeze.py` OK, `gates run --fast` exit 0,
`audit()` unchanged at **4 of 13** — `hydms/descriptors/composites.py` is no sentinel's
subject either, and L13 still waits on `hydms.descriptors.featurize`, which is #20.

**#18, the composites.** `hydms/descriptors/composites.py`: `INFIXES` (two entries — the whole
spec), `decompose()`, `composite_properties()`, `disagreements()` and
`require_self_consistent()`. 21 tests. The card asked for the construction order, both orders
behind a flag, a declarative spec and six hand pins. The order was already settled by #16 and
the statistic already built by #17, so the real work was the thing the by-construction argument
*assumes* — that a column named `a_divi_b` is `a` divided by `b`. Checked across all 156
composite columns instead of the five in play:

- **Eleven of the 156 are not the arithmetic their names claim.** One family,
  `*_mult_voro_coord`, and two elements, **Cs and Gd**, where every one of them is `0.0` —
  formed as though `voro_coord` were 0, while the `voro_coord` column stores `1.0` and
  `voro_coord_divi_mol_vol` uses that 1.0 (Gd: `1/19.9 = 0.05025125628140704`, the stored
  value). NIST's file contradicts itself about two elements. No tolerance would have shown
  this: the disagreement is a relative **1.0**.
- **The other 145 — and all five selected composites — equal their parts bit-exactly.** Not to
  a tolerance; the same double, on every one of the 82 elements carrying them. Which is what
  makes the rule cheap and easy to lose: **read the published column, never a derived value.**
  It is what CBFV reads, so it is what parity means (#21). Today the two routes are identical
  for the five in the 22; the eleven are why it is a rule.
- **`voro_coord = 1.0` for Cs and Gd is a placeholder, and it reaches a selected feature.**
  Every other element in the table sits between 3 and 12, and gadolinium is hcp with twelve
  nearest neighbours. Gd is in **18 of the 1,279** rows, through
  `dev_voro_coord_divi_mol_vol`. Not a bug, not a parity problem — a limit to state. Boxed on
  **#83**; whether the feature survives re-selection is **#25**'s, boxed there with the eleven.

**Two smaller things worth having.**

- **The naming grammar is a parse, not a guess, and that is measured**: 156 of JARVIS's 438
  columns carry an infix, `oliynyk` carries **none**, no name carries two, every one splits
  into two names that are themselves columns, and none splits two ways. So `INFIXES` can be a
  spec rather than a branch table. The trap it guards: a *feature* name is not a *property*
  name — `avg_polzbl_divi_atom_mass` splits into `avg_polzbl` and `atom_mass`, and `decompose()`
  refuses it rather than featurising from the wrong pair.
- **The rejected order is kept as a failing assertion rather than deleted.** No flag was ever
  written: the card's "both orders behind a flag, loser deleted before merge" would have left
  nothing behind, and the measurement leaves a test. Over the sixteen fixture formulae
  composite-of-statistic misses CBFV by between **1.8%** (`avg_first_ion_en_mult_X`) and a
  factor of **65** (`dev_bp_divi_atom_mass`), while statistic-of-composite agrees to
  **9.1e-13**. Some of the gap is structural rather than large — `range(a)/range(b)` is not a
  range of anything, and `dev_voro_coord_divi_mol_vol` computed the wrong way on a two-element
  composition is exactly zero.

**The hand pins.** Six features × five statistics on `Mg2Ni1`, where the fractions are 2/3 and
1/3 and the closed forms fit on one line: `avg = (2a+b)/3`, `dev = (4/9)|a−b|`, `range = |a−b|`.
Every expected value is exact decimal arithmetic from the two element values — not numpy, not
the code under test — and the element values are asserted against the table first, so a table
revision breaks the test at the value it changed rather than at a statistic three lines later.
Agreement: **1.9e-16** relative at worst. If you need a second worked example, `Ti1Fe1` gives
`avg = (a+b)/2`, `dev = |a−b|/2`.

#### The opening move

**#20, `featurize()`.** The last card of the layer before the gates, and it now carries four
obligations rather than two:

1. **The `int64` → `float64` cast for `temperature(K)`** (#19). `assert_contract` refuses the
   integer column by name; a candidate at 313.5 K truncates to 313 in silence otherwise.
2. **Call `CONTRACT.computability(composition)` before building a row** (#19). Seven of the 22
   are not computable everywhere. The contract answers per composition and names the blocking
   element — **ask before you build, do not fill after.** A NaN here is one median-fill away
   from a number that looks like a measurement.
3. **Read the published composite column; call `require_self_consistent()` on the composite
   properties you featurise** (#18). Cheap, once per property set.
4. **The parser is `hydms.data.load.parse_formula`, not `pymatgen.core.Composition`** (#87).

And **creating `hydms/descriptors/featurize.py` turns HG-1 red before you write a wrong line** —
the L13 sentinel names that module as its subject and has no `live` hook yet, so `audit()` will
report `L13 [unwired] #12`. That is the mechanism working. **Do not re-aim the sentinel's
subject.** #12 owes the hook and is `doing` precisely because it waits on #20; the two halves
are boxed on the two cards. HG-1 goes green again at 5/13.

---

### Handoff — 2026-09-04 (earlier) · #19 landed · written for #18, then #20

**Where the phase is.** Nineteen cards done. The tree is green: **481 tests**, ruff 0.8.4 and
mypy 1.13.0 clean, `check_board.py` and `check_freeze.py` OK, `gates run --fast` exit 0,
`audit()` unchanged at **4 of 13** — `hydms/descriptors/contract.py` is no sentinel's subject
either, and L13 still waits on `hydms.descriptors.featurize`, which is #20.

**#19, the 22-feature contract.** `hydms/descriptors/contract.py`: `CONTRACT` over 22
`FeatureSpec`s carrying `(name, statistic, table, property)`, `assert_contract(df)`,
`FeatureContract.from_names()` for #25's regeneration, `as_manifest()`/`from_manifest()` for
#4, and `computability(composition)` — the verdict the card existed to deliver. 42 tests.
The card told you to record computability per composition; measuring it first corrected
**three** of its own claims:

- **"Two of the 22" is seven.** The card folded the six JARVIS features into one because
  they all fail on the same element. As columns they are six, and a caller asking "can I
  build this matrix?" needs six answers. `dev_Gordy_electonegativity` is uncomputable on
  **266 of 1,279 rows / 236 of 1,115 compositions**; each JARVIS feature on `Eu1Ni5` alone.
- **The Gordy hole belongs to the citable edition, not to CBFV — so AC-2 cannot see it.**
  CBFV's copy of the Oliynyk table supplies `gordy_en` for **all twenty-one** elements the
  2024 revision leaves blank (Ce 4.5734, Hf 6.3704, Pr 4.6395, …). #16 made CBFV's table
  AC-2's reference input by necessity, so the gate will be green throughout while the
  shipped featuriser cannot build that column for 266 rows. That is the **second** defect
  AC-2 structurally cannot detect, after #17's wrong-axis reduction, and for the same
  reason both times. Boxed on **#21**; the trade — carry the feature and lose 266 rows, or
  drop the feature and keep them — boxed on **#24** and **#25** with the numbers.
- **The loss falls on AB5 and MIC, not on "AB5 and AB2".** Rows losing at least one feature:
  AB5 91/196 (46.4%), MIC 54/127 (42.5%), HEA 26.0%, AB 24.4%, SS 18.4%, MEA 11.0%,
  A2B 9.4%, **AB2 34/371 (9.2%)**, Mg 7.4%, LEA 0/26. The card's sentence was a physical
  intuition about where rare earths live; the Laves phases are barely touched.

**Two things the card did not ask about and the next cards need.**

- **The training column order was never persisted.** I went looking for `selected_train.csv`
  to pin it and found `Machine_Model/data/processed_data/` is not in the repository at all,
  and that all three committed listings of the 22 are sorted by three different keys —
  `feature_selection_report.csv` by SHAP, `feature_importance.csv` alphabetically,
  `feature_target_pearson_corr.csv` by correlation. There is no history to be faithful to,
  so the contract *declares* REPORT.md §3.2's SHAP order and the test asserts it against
  that CSV. AC-4 is protected by there being one declaration, not by matching the past.
- **`temperature(K)` is `int64` in the raw file and `float64` in the contract.** Every column
  is `float64`; the cast is #20's, and `assert_contract` refuses the integer column by name.
  Not tidiness: a candidate at 313.5 K truncates to 313 in an integer column, silently.

**One thing that was confirmed rather than corrected.** The naming rule — a feature is
`f"{statistic}_{property}"`, with a 13-entry alias map for CBFV's Oliynyk spellings, the
JARVIS half needing none because CBFV's `jarvis.csv` *is* NIST's file — is provably
regenerable: **2,685 names over 5 statistics × 537 properties, all distinct**, and the two
tables share **no** property name. `from_names(CONTRACT.names) == CONTRACT` is a test, and
it is the path #25 takes.

#### The opening move

**#18, the composites.** Now the only unblocked S3 card, and still smaller than it looks:
#16 settled R3 (the composites are per-element **columns** of the JARVIS table, so the form
is statistic-of-composite by construction) and #19 has already resolved and tested every one
of the five against `hydms.descriptors.element_data` — `polzbl_divi_atom_mass`,
`atom_mass_mult_therm_cond`, `bp_divi_atom_mass`, `first_ion_en_mult_X`,
`voro_coord_divi_mol_vol`. What is left is reproducing the statistic over the column and
pinning each against a hand-computed value. It chooses nothing.

**Then #20**, which unblocks the rest of the layer and carries two obligations from this
card (the `int64` → `float64` cast, and calling `computability()` before building a row) plus
the L13 sentinel going red the moment `featurize.py` exists. That is planned; #12 owes the
hook.

---

### Handoff — 2026-09-03 (earlier still) · #17 landed · written for #19, then #18

**Where the phase is.** Eighteen cards done. The tree is green: **439 tests**, ruff 0.8.4 and
mypy 1.13.0 clean, `check_board.py` and `check_freeze.py` OK, `gates run --fast` exit 0,
`audit()` unchanged at **4 of 13** — `hydms/descriptors/stats.py` is no sentinel's subject, and
L13 still waits on `hydms.descriptors.featurize`, which is #20.

**#17, the composition statistics.** `statistics(weights, values) -> Statistics` over `avg`,
`dev`, `range`, `max`, `min`, plus 28 tests and a committed CBFV golden. The card told you to
measure `dev` rather than assume it, and measuring it **confirmed the card** — it is the
fraction-weighted mean absolute deviation, exact to 0.0 against CBFV. Three things it found
instead, and each is now somebody's:

- **The axis is the whole card.** Reducing the natural `(n_compositions, arity)` batch over its
  fast axis makes numpy sum pairwise; over the leading axis it accumulates sequentially, and a
  padded exact zero is then invisible. The wrong axis differs from CBFV by **2.794e-09 on
  jarvis — over AC-2's 1e-9** — while the right one is **bit-identical**. `statistics()`
  transposes internally so no caller can get it wrong, and the tests state it as arithmetic
  rather than as a shape.
- **AC-2 cannot see that defect.** On the 22 selected columns the wrong axis costs only
  2.274e-12 and passes. A featuriser with a real numerical fault would go green today and red
  the moment #25 re-runs selection. Boxed on **#21**, together with the reason parity can never
  be an equality: `parse_formula` sorts elements by symbol, CBFV keeps parse order, and that
  alone moves a cell by up to 3.638e-12.
- **`docs/QA-PROTOCOL.md` §L2 asks for two invariances that do not exist exactly.** Permutation
  and rescaling hold to `atol = rtol = 1e-12` (measured need: 4.3e-16 and 5.3e-15) and no
  tighter — CBFV moves by 1.364e-12 when a formula string is merely *reversed*, on 293 of 400
  real formulae. The protocol is right to ask; it just cannot have them to the bit.

**One thing was fixed in passing, because it blocked the card.**
`scripts/build_element_tables.py` demanded `--oliynyk` and `--jarvis` even to write a CBFV
fixture needing neither — and those are one-off downloads the repository does not keep, so
**#16's own AC-2 reference fixture was already unregenerable on a clean clone.** Both are now
optional and must be given together; `--cbfv-statistics` is #17's golden. Recorded on #16.

#### The opening move

**#19, the 22-feature contract.** Its blockers are done and it is the card the last two have
been piling findings onto: it must record computability **per composition**, because `gordy_en`
is empty for 21 of the 55 elements and every jarvis property of europium is a sentinel. #17
deliberately left the property axis outside `statistics()` so that decision lands here rather
than being forced by an array shape.

**#18, the composites, is also unblocked** and is smaller than it looks — #16 settled R3, so
#18 reproduces a statistic over a per-element column and chooses nothing. Both feed #20.

---

### Handoff — 2026-09-03 (earlier) · #6 and #16 landed · written for #17

**Where the phase is.** Seventeen cards done. Two landed since the handoff below, and both were
worth more than their card text promised.

**#6, the CI fast lane.** `.github/workflows/ci.yml`, two independently-reporting jobs, green in
32 s + 56 s. `integrity.yml` is absorbed into it and deleted. Three things to know:

- **CI now runs on every push to every branch.** The old workflow filtered `push: branches: [main]`,
  so the freeze check and the board check had not run once across the eight Phase H commits on this
  branch. If you push, you will get a result.
- **The `suite` job is not the `Project` environment and cannot be.** `environment.lock.yml` is
  win-64 by construction, so a Linux runner cannot restore it; the job runs
  `pip install -e ".[dev]"` instead. The consequence is #7's: nothing in CI proves the lockfile
  still recreates, and only `windows-latest` ever could.
- **`ruff` and `mypy` are pinned exactly** (`0.8.4`, `1.13.0`) to the machine lane's versions. Not
  caution — a floor resolved newer on the first run and raised RUF100 on a `# noqa` the older ruff
  requires, which makes the two versions mutually unsatisfiable. Bumping them is a deliberate commit.

**#16, the element property tables.** `hydms/descriptors/element_data.py` over two committed CSVs
built from their publishers by `scripts/build_element_tables.py`; `data/SOURCES.md` is the record.
**The numpy wall is down** — the mypy override is applied with its cost stated in `pyproject.toml`,
and numpy may now be imported under `hydms/`. Read `SOURCES.md` before #17; four findings change
what the rest of S3 is:

| Finding | Who inherits it |
|---|---|
| CBFV's `jarvis.csv` **is** NIST's `Elements.json` (7.3e-12), and the five composites are per-element **columns** — so **R3 is settled**, statistic-of-composite by construction | **#18** inherits the answer, not the question; its budgeted slack is free |
| The Oliynyk table was **revised for 2024** — 8 of 13 needed properties disagree with CBFV, up to 10.0 | **#21**: AC-2 means "reproduces CBFV *given the same table*", supplied from `tests/descriptors/data/` |
| `gordy_en` is blank for **21 of the 55** elements (nearly the rare earths); europium's JARVIS properties are `-9999` | **#19** must record computability per *composition*; #24/#25 may have to re-run selection |
| CBFV answers for `Eu1Ni5` anyway, substituting an all-zero property vector — row 516 of the published matrix is that row | **#89**, as a data-integrity disagreement |

**The tree is green:** 411 tests, ruff and mypy clean, both CI jobs green, `audit()` still reports
4 of 13 leaks guarded (no sentinel changed hands — `element_data.py` is not a subject any sentinel
names; L13 still waits on `hydms.descriptors.featurize`, which is #20).

#### The opening move

**#17, weighted composition statistics.** It is the only S3 card whose blockers are all done. It
takes property vectors from `element_data.PropertyTable.vector()` and must reproduce CBFV's `avg`,
`dev` and `range` — and note that `dev` is CBFV's own definition, not a standard deviation, so
measure it against CBFV rather than assuming. #19 (the feature contract) is also unblocked and can
run beside it.

---

### Handoff — 2026-09-03 · S2 closed as far as it can close · written for S3

**Where the phase is.** S0, S1 and **S2** are done with S2 as far as the data layer can go alone.
Six of S2's nine cards are `done` — **#3** (config), **#9** (loaders), **#10** (keyed merge),
**#11** (target transform), **#87** (canonical key) and **#13** (splits). **#15**'s file is written
and green, but its card is held in `backlog` by the board's own rule and by the substance: two of its
pinned facts move when #24 lands. The other two are `doing`, and both wait on a *later* stage rather
than on anything in S2 — **#12** needs the featuriser S3 builds, **#14** needs the feature matrix
S4's #24 supplies. Fifteen cards on the board are done.

`audit()` reports **4 of 13 leaks guarded against the real pipeline** — L3, L8, L9 and L10, which is
exactly the set the runbook's S2 exit check names. The tree is green: 391 tests, ruff and mypy clean,
`check_board.py` and `check_freeze.py` both OK.

#### The opening move, and why it is the only one

**#16, the element property tables.** Everything else in S3 is downstream of it: #17 needs property
vectors to take statistics over, #18 needs #17, #19 and #20 need all three, and #21 — the parity gate
that blocks every card downstream of selection — cannot run until #20 exists.

```
#8 provenance ✔ → #16 tables → #17 statistics → #18 composites → #20 featurize()
                             ↘ #19 the 22-feature contract ↗          ↓
                                                              #21 GATE AC-2 · #22 throughput
```

And #16 carries two boxes added on the way out of S2 that will otherwise cost you the first morning.
Read them before you write a line.

#### The wall S3 hits in its first hour, and the tested way through

**NumPy cannot currently be imported anywhere under `hydms/`.** mypy runs *outside* the `Project`
environment by design — that is the conda-free lint lane (#68, `docs/QA-PROTOCOL.md` §6), and its
whole value is that it still gives a red/green signal when the environment is broken or absent. The
cost is that mypy resolves numpy from the machine's 3.13 site-packages, whose `__init__.pyi` uses PEP
695 `type` statements that `python_version = "3.10"` rejects as a **syntax** error. That aborts the
*entire* run — `Found 1 error in 1 file (errors prevented further checking)` — not just the importing
file, and `ignore_missing_imports` does not suppress it, because it is not a missing import.

#71 sidestepped it with stdlib `random`. #11 sidestepped it with `math.log1p`, at a measured cost of
one ulp against `numpy.log1p`. **The descriptor layer cannot sidestep it**, and #16 now carries a
remedy that was actually run rather than reasoned about: a `follow_imports = "skip"` override for
`numpy` and `numpy.*`, verified on 2026-09-03 by adding a numpy-importing module under
`hydms/descriptors/` and getting `Success: no issues found in 40 source files`. It is deliberately
**not applied** — choosing it, and writing what it costs into `pyproject.toml`, is #16's decision.
The cost: numpy becomes `Any`, so mypy stops checking dtype and shape mistakes in the layer with the
most array code. That is the same trade already made for pandas, scipy and scikit-learn, which is an
argument for it and not a reason to skip stating it.

#### What S2 built that S3 is expected to *use*, not re-derive

Five seams. Each exists because two modules would otherwise disagree about the same thing.

- **`hydms.data.load.parse_formula`** is the grammar. Not CBFV's, which validates nothing —
  measured: `Xx2` → `{'Xx': 2.0}`, `Mg0` → `{}`, `Mg-1` → `{'Mg': -1.0}` — and not
  `pymatgen.core.Composition`, which #20's own card rules out. Three parsers would mean three ideas
  of what a formula is, and the differences would surface as compositions that featurise but cannot
  be keyed.
- **`hydms.data.canonical.group_keys`** is what makes two rows the same material. Splits group on
  it, #88's folds group on it, the class join uses it. Call it; never re-derive it.
- **`hydms.data.target.to_model_space` / `to_wt_pct`** are the only two transform entry points, and
  a named `Series` carries its space in its name — `H2_W% (max)` in, `log_H2_W% (max)` out, and a
  second transform *refuses* rather than producing `log_log_`. If S3 ever needs the target, it goes
  through these.
- **`hydms.data.metadata.metadata_columns()`** is the list a featuriser must carry through, and
  **`non_feature_columns()`** is that list plus the target in both spaces.
  **`refuse_non_features(X)` is meant to be called on what #20 returns.** The two lists differ by
  exactly the target, and the difference is the point: a featuriser dropping `Alloy_class` costs
  AC-6; a feature matrix *containing* `H2_W% (max)` costs everything at once and looks like an
  excellent model rather than like a bug.
- **`hydms.data.splits.assign_splits`** returns `train`/`val`/`test` per row and checks its own
  disjointness before returning, so a caller cannot receive a leaking split.

#### Four things that will otherwise cost an afternoon each

1. **Creating `hydms/descriptors/featurize.py` turns the build red before you write a wrong line.**
   The L13 sentinel names that module as its subject and has no `live` hook, so HG-1 will report
   `L13 [unwired] #12 -- guarded in name only` the moment the file exists. That is the mechanism, not
   a bug: **do not re-aim the sentinel's `subject` to make it green.** #12 owes the hook —
   `assert_metadata_survives(before, after, columns=metadata_columns())` on the real featurisation
   path — and #12 is `doing` precisely because it is waiting for #20. Coordinate; #20's card carries
   the box and #12's carries the other half.
2. **The featuriser sources from two tables, not one.** `extract_features_cbfv.py:31` says
   `elem_prop='magpie'`, and magpie produces **none** of the 21 published descriptors. The real set
   is 15 `oliynyk` + 6 `jarvis` + `temperature(K)`, resolved empirically by #8 and written up in
   [hydms/descriptors/FEATURE_PROVENANCE.md](../../hydms/descriptors/FEATURE_PROVENANCE.md). A
   single-table reimplementation cannot pass #21 no matter how correct its Oliynyk half is.
3. **The dataset contains 55 elements, not 54.** `REPORT.md` §2.3 and the PRD's dataset table both
   say 54; counted from the parsed compositions of all 1279 rows it is 55, seven of them appearing
   exactly once (N, Eu, Lu, Pb, Au, Os, Re). #16's coverage check was written against 54 and has been
   corrected; a table validated against the wrong number passes while one element silently has no
   properties.
4. **Nothing in this project compares two float vectors with `==`, and #21's 1e-9 is not an
   accident.** #11 measured three independent one-ulp effects on the target alone: the published
   `log_H2_W% (max)` column round-tripped through decimal text and differs from `log1p` of the target
   on 274 of 1279 rows; `math.log1p` and `numpy.log1p` differ on this data; and `expm1(log1p(y))`
   returns `y` exactly on only 794 rows. Parity to 1e-9 is loose enough to survive all of that and
   tight enough that a wrong property table cannot hide.

#### S3 is done when

`#21` is green — every one of the 22 columns agreeing with CBFV to 1e-9 over all 1279 formulae, with
a failure message that names the column and the worst-offending formula rather than a boolean — and
`#22` has written a throughput number into `docs/BENCHMARKS.md`. Along the way, `hydms/descriptors/`
imports CBFV nowhere: it is unlicensed, which is why the layer is being reimplemented, and it stays a
`parity` extra used only by the gate that diffs against it.

Expect **HG-1 to go red during S3 and stay red until #12 closes.** That is planned. It goes green
again at `5/13`.

#### Findings from this session, and what was done with each

| Finding | Where it went |
|---|---|
| The published `log` column is `log1p` only to one ulp — it was written by `to_csv` and read back through decimal text, bit-identical on 1005 of 1279 rows | Card #11's boxes and `hydms/data/target.py`'s docstring; `ROUND_TRIP_TOLERANCE = 1e-12` |
| `REPORT.md` §4.2's Overfitting footnote subtracts a weight-percent number from a log-space one, and the code computes something else again | A tenth disagreement, boxed on **#89** |
| `alloy_class_table` ordered labels by `ALLOY_CLASS_PRECEDENCE.index` *before* validating them, so a bad label crashed with `tuple.index(x): x not in tuple` and `reconcile_class`'s refusal was unreachable | Fixed in #87's module — the refusal is the decision #12 was making, and a bare `ValueError` is not a refusal |
| Nothing stopped the target reaching the feature matrix | `non_feature_columns()` and `refuse_non_features()`, card #12 |
| The card's `UNKNOWN` alloy class would be a label with no members that still changes AC-6's fold count | Settled as a **refusal** at the door, card #12 |
| `Mg0853Ni0.125La0.022` is a missing decimal point whose correction must be applied *upstream of the canonical key*, which screening is not | Dropped from training and named in `MALFORMED_FORMULAE`; the correction-layer decision boxed on **#9** |
| A golden record that stops covering a stage reports agreement it never checked | `diff()` treats an absent fact as a difference, card #15 |
| NumPy still aborts the whole mypy run; a `follow_imports = "skip"` override was tested and works | Boxed on **#16**, unapplied — the trade is that card's to make |
| The dataset has 55 elements, not the 54 #16's coverage check named | Corrected on **#16**; already recorded as #89's ninth disagreement |
| A runbook line I had *just* written said `tests/data` is 89 tests; it is 215 over eight files | Corrected in the same commit. Prose rots the moment it is written, including new prose |

---

