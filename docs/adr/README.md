# Architecture decision records

One file per decision that is **hard to reverse**, **surprising without context**, and **the result
of a real trade-off**. If any of the three is missing there is no ADR to write: an easy reversal
gets reversed, an unsurprising choice raises no question, and a decision with no alternative is
just the obvious thing.

Format: `NNNN-slug.md`, following `.claude/skills/domain-modeling/ADR-FORMAT.md`.

## The records

| | Decision | Owns | Card |
|---|---|---|---|
| 0001 | *reserved* — optimise in composition space; never invert descriptors | | #36 |
| 0002 | *reserved* — reimplement the featuriser rather than depend on unlicensed CBFV (**and** the ElMD licence, which is the same finding with the opposite sign) | | #36 |
| 0003 | *reserved* — rank by conformalised LCB, not predicted mean | | #36 |
| 0004 | *reserved* — new `hydms/` package; `Machine_Model/src/` archived rather than rewritten | | #36 |
| 0005 | *reserved* — pymoo with the element subset fixed per run, over mixed-integer encoding | | #36 |
| [0006](0006-the-delivery-seam.md) | The delivery seam: the API owns no ML logic, and the library owns no I/O | The one hard-to-reverse decision of the delivery layer | #85 |
| [0007](0007-evidence-is-served-not-read-by-the-page.md) | Evidence is served, not read by the page | How committed evidence reaches the model-card page, and why it is read once at startup | #83, #105 |

## Why 0001–0005 are reserved rather than taken

The numbering rule is "scan for the highest and increment", and this directory was created by card
#85, which would ordinarily have taken `0001`. It did not.

Card #36 declares its own done-when as `docs/adr/0001..0005-*.md`, one per the five programme-level
decisions listed on that card. Taking the low numbers here would have falsified that box and forced
#36 to be edited to accommodate a file it has nothing to do with — so the five are held, and the
delivery seam sits at `0006`.

**#36 carries more than five candidates** (a sixth on how the reported interval is constructed, and
three more added in review — the waiver as an act, one definition of the deployed fit, and splitting
`load_surrogate` into locating and assembling). Those take `0007` onward as they are written. The
card is deliberately **not** renamed: "five" was the count when it was cut, and *the ADRs are
numbered, not counted*.
