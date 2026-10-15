# Research Checklist

The workflow that produced the current content, and the one to repeat before extending it.

## Standing rules for this skill

1. **Primary sources only.** Peer-reviewed papers with DOIs, official documentation, official database/API
   docs. Not blog posts, not secondary summaries, not another model's recollection.
2. **Every number gets a link.** Capacities, enthalpies, temperatures, dataset sizes, DOE targets — these are
   exactly the claims that get misremembered, and exactly the ones a thesis cannot afford to get wrong.
3. **Mark unverified claims `**unverified**` inline.** A smaller honest module beats a padded one.
   Never invent a DOI or a figure to fill a gap.
4. **Date anything time-sensitive.** Package versions, database sizes, "current" targets, API details.
5. **Prefer the repo's own numbers over recollection.** `docs/chapter1-revision.md` and the tables
   `hydms/` writes under `reports/` are the authority on this project's results. The old `REPORT.md` is
   history (git tag `machine-model-archive`), never current. Check before quoting.

## Before extending a module

1. Identify the freshness risk — standards, targets, database contents and package APIs drift; thermodynamics does not.
2. Search official docs, release notes and 2024+ literature.
3. Record title, URL/DOI and access date alongside the claim.
4. Validate existing text against the new sources; correct what has drifted.
5. Log anything still open in `known-gaps.md`.

## Provenance of the current content

- `modules/metal-hydride-families.md` — rewritten from `research/hydride-domain-grounding.md` §2, researched
  against primary literature by a dedicated agent. The most rigorously sourced module.
- `modules/hydrogen-storage-fundamentals.md` — DOE targets from the primary EERE page, accessed 2026-08-29;
  remainder from `research/hydride-domain-grounding.md` §1.
- `modules/ml-for-hydrides.md` — `research/hydride-domain-grounding.md` §3.
- `modules/computational-materials-informatics.md` — `research/hydride-domain-grounding.md` §4. **Its DFT
  subsection is domain knowledge, not retrieved sources** — the least-sourced part of the skill.
- `modules/generative-ai-inverse-design.md` — derived from `research/inverse-design-methods.md`,
  a DOI-cited memo written against primary sources on 2026-08-29.
- `modules/project-context.md` — read directly from this repo's `README.md`, `REPORT.md` and the
  archival `src/` on 2026-08-29; marked history-only by card #107.

Both memos live in `research/`. They are the citation authority; these modules summarise them. When they
disagree, the memo wins — and fix the module.
