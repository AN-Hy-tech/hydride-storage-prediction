# Hydrogen Storage Fundamentals and Targets

**Confidence**: 🟢 Medium-high. DOE targets read from the primary EERE page on 2026-08-29.

## The distinction that gets misreported constantly

**DOE targets are SYSTEM-level, not material-level.** The DOE states targets are "for a complete system,
including tank, material, valves, regulators, piping, mounting brackets, insulation, added cooling capacity,
and all other balance-of-plant components"
([DOE EERE](https://www.energy.gov/eere/fuelcells/doe-technical-targets-onboard-hydrogen-storage-light-duty-vehicles)).

So **a 7 wt% material does not meet a 5.5 wt% system target.** The tank, heat exchanger and balance of plant
typically cost a factor of ~2 or worse in gravimetric terms. This project predicts *material* capacity.
Never compare its wt% outputs directly against DOE system targets without saying which is which — this is the
single most common error in hydride papers' introductions, and a thesis examiner will notice.

## DOE onboard light-duty vehicle targets

| Parameter | 2025 | Ultimate Full Fleet |
|---|---|---|
| System gravimetric | 1.8 kWh/kg (**0.055 kg H₂/kg**, i.e. 5.5 wt%) | 2.2 kWh/kg (**0.065 kg H₂/kg**, 6.5 wt%) |
| System volumetric | 1.3 kWh/L (0.040 kg H₂/L) | 1.7 kWh/L (0.050 kg H₂/L) |
| Storage system cost | $9/kWh net ($300/kg H₂) | $8/kWh net ($266/kg H₂) |
| Operating ambient temp | −40 °C to +60 °C (full solar load) | same |
| Min/max delivery temp | −40 °C to +85 °C | same |
| Operating pressure | 5–12 bar (absolute) | same |
| Fill time | 3–5 min | same |
| Cycle life | 1,500 cycles (¼ to full) | same |

Onboard capacities of **5–13 kg H₂** are needed to cover the light-duty platform range.
Targets are set through the U.S. DRIVE Partnership (DOE + USCAR + energy companies).
The revision date is not stated on the page itself — cite the page with an access date rather than a year.

The delivery-temperature and pressure rows matter more than they look: a hydride that only desorbs usefully
above 85 °C or below 5 bar is disqualified on *operating window*, whatever its capacity. Capacity alone is
never the whole story.

## Storage classes and where hydrides sit

| Class | Mechanism | Strengths | Weaknesses |
|---|---|---|---|
| Compressed gas (350/700 bar) | Physical | Mature, fast fill, ambient temp | Poor volumetric density, tank cost, high pressure |
| Cryogenic liquid | Physical | Good density | Liquefaction energy (~30% of LHV), boil-off |
| Cryo-compressed | Physical | Best physical volumetric | Complexity, boil-off |
| Physisorption (MOFs, carbons) | Van der Waals | Fast, fully reversible | Needs cryogenic temps for useful uptake |
| **Metal hydrides** | Chemical (interstitial) | High volumetric density, low pressure, safe, near-ambient | Heavy, heat management, gravimetric capacity |
| Complex hydrides | Chemical (ionic/covalent) | High gravimetric capacity | Poor reversibility and kinetics |

DOE's stated pathways: near-term 700 bar compressed with focus on cost reduction; long-term cold/cryo-compressed
and materials-based storage.

## Why hydrides still matter despite missing vehicular targets

Intermetallic hydrides have usable capacities generally **below 2 wt%** under practical pressure/temperature
swing constraints (see `modules/metal-hydride-families.md` for the sourced per-family figures) — so they will
not win onboard light-duty storage.

The operating-window rows above disqualify materials independently of capacity: MgH₂ is excluded outright by
its ~300 °C 1-bar plateau, not by its 7.66 wt%. And the 1,500-cycle requirement sits against AB₂ losing ~20%
capacity in 150 cycles. Hydrides remain strongly relevant for:

- **Stationary storage**, where mass is nearly free and volumetric density plus safety dominate.
  See [Wang et al. 2025, *Adv. Sci.*, technoeconomic analysis of metal hydrides for stationary storage](https://doi.org/10.1002/advs.202415736).
- **Thermal energy storage and heat pumps** — see [Nizam et al. 2026, *Asia-Pac. J. Chem. Eng.*](https://doi.org/10.1002/apj.70161)
  for Mg-based thermal storage. The often-quoted "~156 kWh/m³ at ~89.4% efficiency" for Mg₂Ni + LaNi₅-type
  systems is **unverified** — search-summary only, primary source never traced. Trace it or drop it.
- **Hydrogen compression** — thermally driven, no moving parts.
- **Purification**, exploiting selective absorption.

Framing the thesis around stationary/thermal applications is more defensible than framing it around
automotive targets the material class cannot meet.
