---
id: 103
status: done
priority: High
blocked_by: [34]
assignee: "@amirhossein"
tags: [ph, l7, R4]
---

# The deployed model's test score is committed nowhere

**Stage S8 — Evidence and close** · **L7 Evidence** · Estimate: 0.25 d

> **Owns (hidden behind this module):** How the certified test-split score of the promoted artifact reaches a committed file.

**This card is NOT an unfreeze condition.** It is the fix for one box on #37, which is. It was
split off #83 on 2026-09-24 by the maintainer's decision, so that the last unfreeze bullet does not
wait on #82's Streamlit pin, a lock decision it has nothing to do with.

## Why this exists

Gates AC-1 and AC-3 score the deployed model once on the 254 held-out `test` rows: R² **0.7071**,
RMSE 0.5420, MAE 0.3117, calibrated coverage **0.7795** at a mean width of 0.8630 wt%. Those
numbers were recorded only in the gate report sealed into `artifacts/v3/manifest.json`, and
`/artifacts/` is gitignored. So the Chapter 1 revision (#37) could cite them only with a † that
means "a fresh clone cannot check this". That is REPORT.md's defect in a smaller form.

The committed `reports/model/conformal-coverage.csv` is **not** this number. It reports R² 0.8255
and coverage 0.8081 over the 172 **calibration** rows.

## Done when

- [x] `hydms/evidence/artifact_score.py`. `--probe` copies the promoted version's AC-1 and AC-3
      records verbatim, with the manifest's SHA-256, to `reports/model/artifact-gates.json`.
      `--emit` parses that into `reports/model/artifact-score.csv`. Both files are committed.
- [x] **Read from the gate record, never re-scored.** The AC-3 module is "the one place the test
      split is read", and this card keeps that true. Nothing is fitted or loaded, and `--emit`
      needs no artifact, so CI can check its bytes.
- [x] **Refuses rather than publishes**: a gate that is absent or not `PASSED`, a split other than
      `test`, row counts that disagree, gate wording the parser no longer recognises, an unknown
      or missing AC-1 metric, and a refit whose coverage disagrees with the stored model's (below).
      One test per refusal in `tests/evidence/test_artifact_score.py`.
- [x] #83's publishing half moved here. #83 still owes *showing* the three R² readings on the
      model card, and it now reads them from this table.
- [x] #37's box 5 ticked: the † rows now trace to the committed table.

## Narrative

**2026-09-24.** Built as a read of the sealed record rather than a fresh scoring, for two reasons.
First, `ac3_conformal_coverage.py` says it is the only reader of the test split, and a second
reader would falsify that sentence even if it adjusted nothing. Second, the certified numbers are
the ones a gate run was recorded against before promotion. A re-score would be a new measurement
that happens to agree.

**AC-1's R² is a claim about a refit, and the table says how that is tied back.** AC-1 runs
`deployed_fit` twice to prove seed reproducibility, so its metrics come from those runs and not
from `model.joblib`. AC-3 scores the stored model. Both report the calibrated coverage on the same
254 rows: 0.779528 from the refit and 0.7795 from the stored model. `rows()` refuses unless they
agree to AC-3's printed precision. So an R² from a model the service does not serve cannot reach
the table.

**Parsing a message is the weak point, and it is fenced rather than hidden.** The sealed `v3`
manifest carries the metrics only inside the gate's message string: AC-1's `measured` is the
0.0 difference between its two runs. A manifest cannot be amended, so a structured record would
mean a new version and a new promotion, with no new information. The parser matches the gates'
own f-strings and refuses on any drift. The durable fix is for AC-1 and AC-3 to put their metrics
in a structured field at the next promotion. That is an open box on nothing yet. Whoever next
promotes a version should file it.

**Values are the gate's text, not re-rounded floats.** `+0.037355` and `0.000000` survive as
written. A test pins this, because a float round-trip would silently lose the precision the gate
chose.

**The provenance test runs only here.** `test_the_committed_record_is_the_promoted_manifests`
reads `artifacts/` and skips in CI, and says so in its reason. CI checks the table against the
record. Only the maintainer's machine checks the record against the model. After any promotion,
run `python -m hydms.evidence.artifact_score --probe --emit`.
