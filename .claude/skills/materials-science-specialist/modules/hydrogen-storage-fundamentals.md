# Hydrogen Storage Fundamentals and Targets

**Confidence**: 🟢 High. DOE targets verified 2026-08-30 against the primary
[Target Explanation Document](https://www.energy.gov/sites/prod/files/2017/05/f34/fcto_targets_onboard_hydro_storage_explanation.pdf) — the authoritative source, of which the
[EERE page](https://www.energy.gov/eere/fuelcells/doe-technical-targets-onboard-hydrogen-storage-light-duty-vehicles) is only a summary. See `research/hydride-domain-grounding.md` §1.

## The distinction that gets misreported constantly

**DOE targets are SYSTEM-level, not material-level.** The DOE states targets are "for a complete system,
including tank, material, valves, regulators, piping, mounting brackets, insulation, added cooling capacity,
and all other balance-of-plant components. All capacities are defined as usable capacities that could be
delivered to the fuel cell system. **All targets must be met at the end of service life.**"
([DOE TED, footnote (a) to Table 1](https://www.energy.gov/sites/prod/files/2017/05/f34/fcto_targets_onboard_hydro_storage_explanation.pdf)).

Two clauses there are easy to miss and both bite: capacities are **usable** (not maximum), and every target
must hold **at end of service life** — i.e. after the 1,500 cycles, not on a fresh sample.

So **a 7 wt% material does not meet a 5.5 wt% system target.** This project predicts *material* capacity, and
its target variable is `H2_W% (max)`, so the overstatement is two steps: material→system and maximum→usable.
*(An earlier version of this module claimed balance of plant "typically costs a factor of ~2 or worse in
gravimetric terms". **No source was found for that ratio and it has been removed** — the argument does not
need it.)*
Never compare its wt% outputs directly against DOE system targets without saying which is which — this is the
single most common error in hydride papers' introductions, and a thesis examiner will notice.

## DOE onboard light-duty vehicle targets

The table has **three** target columns, not two, and the third is headed **Ultimate** — "Ultimate Full Fleet"
is the superseded 2009 label.

| Parameter | 2020 | 2025 | Ultimate |
|---|---|---|---|
| System gravimetric (usable) | 1.5 kWh/kg (0.045 kg H₂/kg) | 1.8 kWh/kg (**0.055 kg H₂/kg**, i.e. 5.5 wt%) | 2.2 kWh/kg (**0.065 kg H₂/kg**, 6.5 wt%) |
| System volumetric (usable) | 1.0 kWh/L (0.030 kg H₂/L) | 1.3 kWh/L (0.040 kg H₂/L) | 1.7 kWh/L (0.050 kg H₂/L) |
| Storage system cost | $10/kWh net ($333/kg H₂) | $9/kWh net ($300/kg H₂) | $8/kWh net ($266/kg H₂) |
| Operating ambient temp | −40 °C to +60 °C (full solar load) | same | same |
| Min/max delivery temp | −40 °C to +85 °C | same | same |
| Delivery pressure (min/max) | 5–12 bar (absolute) | same | same |
| Fill time | 3–5 min | same | same |
| Cycle life | 1,500 cycles (¼ to full) | same | same |
| Dormancy (min. to first release) | 7 days | 10 days | 14 days |

Onboard capacities of **4–10 kg H₂** cover the light-duty platform range — the TED states this three times.
*(An earlier version of this module said "5–13 kg". That figure appears in neither the TED nor the EERE page.)*
For a normalised comparison against the targets the TED specifies using a **usable capacity of 5.6 kg H₂** at
hydrogen's lower heating value of 33.3 kWh/kg.

Targets are set through the U.S. DRIVE Partnership (DOE + USCAR + energy companies).

**Revision history — there is a defensible date, and it is three dates.** Originals were **set in 2003**; the
**last major revision was 2009**; the current Table 1 is headed **"updated May 2017"**. The 2015 targets were
not met and were **re-dated to 2025** after DOE hydrogen storage funding fell. U.S. DRIVE intends to review the
targets **approximately every 5 years**, so keep an access date too. All from the
[TED](https://www.energy.gov/sites/prod/files/2017/05/f34/fcto_targets_onboard_hydro_storage_explanation.pdf), read 2026-08-30.

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
- **Thermal energy storage and heat pumps** — see [Nizam et al., *Asia-Pac. J. Chem. Eng.* 21](https://doi.org/10.1002/apj.70161)
  for Mg-based thermal storage. The often-quoted **"156 kWh/m³ at 89.4% efficiency"** for Mg₂Ni + LaNi₅ is now
  **traced** to [Malleswararao, Aswin, Srinivasa Murthy & Dutta 2020, *Int. J. Hydrogen Energy* 45(31),
  16239–16253](https://doi.org/10.1016/j.ijhydene.2020.03.251) — **but it is a 3-D COMSOL simulation, on the
  third cycle, charging at 300 °C and discharging at 230 °C. It is not a measurement.** Quote it only with
  those qualifiers; the 300 °C is what makes it far less practical than the bare number sounds.
- **Hydrogen compression** — thermally driven, no moving parts.
- **Purification**, exploiting selective absorption.

Framing the thesis around stationary/thermal applications is more defensible than framing it around
automotive targets the material class cannot meet.
