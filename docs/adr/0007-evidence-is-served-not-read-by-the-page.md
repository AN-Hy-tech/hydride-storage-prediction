---
status: accepted
date: 2026-09-26
cards: "#83 (the page that needs it), #105 (the run record it stands on); settled in the 2026-09-26 architecture grilling"
---

# Evidence is served, not read by the page

The model-card page (#83) shows the three scores, their intervals, the per-family transfer scores
and two parity panels. All of it lives in committed tables under `reports/`, and none of it is a
prediction. **The service reads that evidence once, at startup, and serves it on
`GET /v1/evidence` (the scores) and `GET /v1/evidence/parity` (the scored rows). The page gets it
over HTTP like everything else it shows.** This extends [ADR 0006](0006-the-delivery-seam.md) to a
kind of data 0006 did not mention. It does not amend 0006.

## Why this is not obvious

The evidence is files, not model output. Letting the page read them in-process is shorter, needs no
contract change and no regenerated `docs/API.md`. ADR 0006's argument ("one prediction path")
does not literally cover it. It was rejected for three reasons, in order of weight:

1. **One snapshot, one process.** The domain reference, which carries the per-family transfer
   scores that every `untrusted-family` refusal quotes, is loaded once at startup with the bundle.
   A page that read `reports/` itself would show the *regenerated* Mg transfer score beside a
   service still refusing with the *old* one. That actually happened on 2026-09-25: the service
   on port 8000 kept quoting −0.338 after the tables said −0.508. Served from the same startup
   read, the two cannot disagree, and `/health` reports an evidence digest beside the reference
   digests so a stale service is visible.
2. **The page stays a client.** `tests/delivery/test_app.py` allows `app/main.py` three imports.
   Reading evidence in-process would widen that set to a module that does file I/O. It would also
   make the page a second place that decides what a committed table means.
3. **The reading of a table happens once.** Whether a table is a probe's, whether its run record
   exists and which of the three scores a number is are decided by the Evidence Reader on the
   service side, never by a consumer. That is the defect `domain.transfer_table` had: it read
   `loco-per-class.csv` and never asked whether a probe wrote it.

## Considered and rejected

- **Add the scores to `GET /v1/model`.** That payload answers "what is answering me". The
  transfer and procedure scores describe the *modelling procedure*, not the promoted artifact.
  Putting them there is the conflation the glossary's three score terms exist to prevent.
- **Read on every request.** Never stale, but it reintroduces reason 1's disagreement between the
  route and the refusals after any regeneration.
- **Refuse to start without evidence.** A prediction does not depend on the evidence, so refusing
  to predict because a report is missing punishes the wrong thing.

## Consequences

- A score whose table is absent, whose run record is absent, or whose record says `probe` is served
  as **absent, with its reason**. It is never omitted and never shown as a number. This is
  `modelcard.py`'s rule ("an absent record is reported as absent") applied to evidence.
- Refreshing the served evidence means restarting the service. That was already true of the
  domain reference, and the digest in `/health` makes it checkable.
- The contract grows two routes, and `docs/API.md` is regenerated (`apidoc --probe --emit`), never
  edited.
