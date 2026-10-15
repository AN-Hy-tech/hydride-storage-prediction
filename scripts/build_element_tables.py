"""Build ``hydms/descriptors/data/*.csv`` from the two cited primary sources.

The descriptor layer must not vendor CBFV: it carries no licence at all, is unmaintained
since 2022, and this is a GPL-3.0 deliverable (card #16). The replacement takes its numbers
from publications that may be redistributed, and this script is the audit trail between them
and the CSVs in the package. Nothing in ``hydms/`` reads a downloaded file; the CSVs are the
committed artifact and this script is how they were made.

    Oliynyk elemental property list -- Lee, Chen, Garcia & Oliynyk (2024),
      *Data in Brief* 53, 110178.  https://doi.org/10.1016/j.dib.2024.110178
      Data:  https://data.mendeley.com/datasets/bt6gv5z6yv/1  (CC BY 4.0)
      File:  oliynyk-elemental-property-list.xlsx

    JARVIS elemental descriptors -- Choudhary et al. (2020),
      *npj Comput. Mater.* 6, 173.  https://doi.org/10.1038/s41524-020-00440-1
      Data:  https://github.com/usnistgov/jarvis  ->  jarvis/core/Elements.json
      A NIST work; not subject to copyright in the United States.

Usage:

    python scripts/build_element_tables.py --oliynyk oliynyk-elemental-property-list.xlsx \\
                                           --jarvis Elements.json

Deliberately stdlib-only, for two reasons. ``openpyxl`` is not in the pinned environment and
adding it is card #86's decision, not one to make in passing -- an xlsx is a zip of XML and
this sheet is a plain rectangle, so ``zipfile`` and ``ElementTree`` are enough. And a build
step that needs the scientific stack cannot run in the conda-free lane (card #68).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

#: Where the committed tables live. `pyproject.toml` ships them as package data, so the
#: descriptor layer never depends on the repository layout to find them.
DEST = Path("hydms/descriptors/data")


def normalise(name: str) -> str:
    """A published column header to a stable, quotable identifier.

    The published headers carry embedded newlines, doubled spaces, units in parentheses and
    characters like ``^`` and ``Ω``. They are human labels, not keys. This flattens them to
    lowercase underscore-separated ASCII, which is what the feature contract (card #19) will
    quote. The mapping is recorded in ``SOURCES.md`` so a name can always be traced back.
    """
    text = name.replace("\n", " ").strip().lower()
    text = text.replace("^", "")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


# --------------------------------------------------------------------------------------
# xlsx, without openpyxl
# --------------------------------------------------------------------------------------


def _column_index(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref)
    index = 0
    for char in letters.group(0) if letters else "A":
        index = index * 26 + (ord(char) - 64)
    return index - 1


def read_sheet(path: Path) -> list[list[str]]:
    """The first worksheet as a list of rows of raw cell text."""
    with zipfile.ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = [
                "".join(node.text or "" for node in item.iter(f"{NS}t"))
                for item in root.findall(f"{NS}si")
            ]
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))

    rows: list[list[str]] = []
    for row in sheet.iter(f"{NS}row"):
        cells: dict[int, str] = {}
        for cell in row.findall(f"{NS}c"):
            index = _column_index(cell.get("r") or "A")
            value = cell.find(f"{NS}v")
            text = "" if value is None else (value.text or "")
            if cell.get("t") == "s" and text:
                text = shared[int(text)]
            elif cell.get("t") == "inlineStr":
                inline = cell.find(f"{NS}is")
                text = (
                    "".join(node.text or "" for node in inline.iter(f"{NS}t"))
                    if inline is not None
                    else ""
                )
            cells[index] = text
        if cells:
            rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
    return rows


# --------------------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------------------


def _cell(value: object) -> str:
    """A value as text that reads back as the identical float.

    ``repr`` of a float round-trips exactly in Python 3, which is what lets the loader
    promise that the CSV is the number and not a rendering of it. An empty string is a
    *hole* -- the published table has no value there -- and the loader raises on it rather
    than letting a NaN travel (card #16).
    """
    if value is None or value == "":
        return ""
    return repr(float(value))


def write_table(path: Path, columns: list[str], rows: dict[str, dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["element", *columns])
        for element in sorted(rows):
            values = rows[element]
            writer.writerow([element, *(_cell(values.get(c, "")) for c in columns)])
    print(f"  wrote {path}  ({len(rows)} elements x {len(columns)} properties)")


# --------------------------------------------------------------------------------------
# The two sources
# --------------------------------------------------------------------------------------


def build_oliynyk(source: Path, dest: Path) -> None:
    sheet = read_sheet(source)
    header = [normalise(name) for name in sheet[0]]
    columns = [name for name in header[1:] if name]

    rows: dict[str, dict[str, object]] = {}
    holes = 0
    for raw in sheet[1:]:
        symbol = (raw[0] if raw else "").strip()
        if not symbol:
            continue
        values: dict[str, object] = {}
        for index, name in enumerate(header):
            if index == 0 or not name:
                continue
            text = raw[index].strip() if index < len(raw) else ""
            try:
                values[name] = float(text)
            except ValueError:
                holes += 1
        rows[symbol] = values

    write_table(dest / "oliynyk.csv", columns, rows)
    print(f"  {holes} cells are blank in the published table and are written as holes")


def build_jarvis(source: Path, dest: Path) -> None:
    payload = json.loads(source.read_text(encoding="utf-8"))
    columns = sorted({key for values in payload.values() for key in values})

    rows: dict[str, dict[str, object]] = {}
    for symbol, values in payload.items():
        rows[symbol] = {key: value for key, value in values.items() if value is not None}

    write_table(dest / "jarvis.csv", columns, rows)


#: The thirteen Oliynyk properties the 22 selected features are built from (card #8), under
#: CBFV's spelling. The typo in `Gordy_electonegativity` is CBFV's and is reproduced here so
#: the column can be found; the published table spells it `Gordy EN` and leaves it empty.
CBFV_OLIYNYK_PROPERTIES = (
    "Zunger_radii_sum",
    "Pauling_Electronegativity",
    "valence_d",
    "specific_heat_(J/g_K)_",
    "gilmor_number_of_valence_electron",
    "Covalent_Radius",
    "Mulliken_EN",
    "heat_of_vaporization_(kJ/mol)_",
    "Gordy_electonegativity",
    "Mendeleev_Number",
    "Density_(g/mL)",
    "Atomic_Weight",
    "Number_of_unfilled_s_valence_electrons",
)


def build_cbfv_reference(dest: Path) -> None:
    """Emit CBFV's own Oliynyk values as a **test** fixture, never as package data.

    Gate AC-2 asks for featuriser parity with CBFV to 1e-9. The published Oliynyk table was
    revised for 2024 and disagrees with CBFV's copy on eight of the thirteen properties, so
    parity cannot be a claim about the numbers -- it is a claim about *this code*: the
    featuriser must reproduce CBFV given the same table. That makes CBFV's values reference
    input for one test rather than something the package ships, which is the only footing on
    which an unlicensed table may be touched at all.

    Requires the `parity` extra. Deliberately not run by default and not by CI.
    """
    # Imported here and nowhere else: this is the only function that needs the
    # scientific stack, and the only place in the repository allowed to touch CBFV.
    import CBFV
    import pandas as pd

    source = Path(CBFV.__file__).parent / "element_properties" / "oliynyk.csv"
    table = pd.read_csv(source)
    table = table.set_index(table.columns[0])

    rows = {
        str(element): {
            prop: float(table.loc[element, prop])
            for prop in CBFV_OLIYNYK_PROPERTIES
            if not pd.isna(table.loc[element, prop])
        }
        for element in table.index
    }
    write_table(dest / "cbfv_oliynyk_reference.csv", list(CBFV_OLIYNYK_PROPERTIES), rows)


#: The formulae the statistics fixture pins, chosen from ``hydride_data.csv`` to span every
#: arity the dataset contains -- 2 through 10 distinct elements -- because the arity is what
#: decides how many terms the reduction accumulates, and the reduction order is the whole
#: question (card #17). No formula here contains europium: every jarvis property of europium
#: is a ``-9999`` sentinel, so the committed table refuses it where CBFV silently zeroes it.
CBFV_STATISTICS_FORMULAE = (
    # arity 2..10, every one of them present in the dataset
    "Mg1.5Ni1",
    "Ti1Fe1",
    "La1Ni5",
    "Mg2Ni1",
    "Ti1V1Mn",  # an implicit amount of 1, which both parsers must read the same way
    "Mg0.874La0.021Ni0.105",
    "Mg0.7Li0.1Ni0.1Cu0.1",
    "Ti0.8Zr0.2Mn1.4V0.2Cr0.4",
    "La1Ni5.5Mn0.1Al0.05",
    "Ti0.9Zr0.15Mn1.6Cr0.2V0.2",
    "Ti0.85Zr0.15Mn1.65Cr0.2Nb0.15",
    "Co1Fe1Mn1Ti1V1Zr3",
    "Ti0.8Zr0.2V0.6Mn0.2Pd0.1Ni0.8Fe0.2",
    "Ti0.52Zr0.48Ni1.01V0.39Cr0.22Mn0.21Fe0.19Al0.19",
    "La0.5Ce0.4Ti0.1Ni3.77Cu0.6Fe0.6Cr0.6Mn0.36Al0.27",
    "Ti0.12Zr0.215V0.10Cr0.075Mn0.081Fe0.01Co0.07Ni0.322Sn0.003Al0.004",
)

#: The six jarvis properties behind 6 of the 22 selected features. Five are composites and
#: are per-element *columns* of NIST's ``Elements.json``, not something CBFV synthesises --
#: card #16 measured that and it settled PRD risk R3. ``atom_mass_mult_therm_cond`` is here
#: for its magnitude as much as its selection: at ~2e4 it is where an absolute 1e-9
#: tolerance has least room, and where a reduction down the wrong axis first shows.
CBFV_JARVIS_PROPERTIES = (
    "polzbl_divi_atom_mass",
    "atom_mass_mult_therm_cond",
    "bp_divi_atom_mass",
    "first_ion_en_mult_X",
    "voro_coord_divi_mol_vol",
    "is_alkaline",
)


def build_cbfv_statistics(dest: Path) -> None:
    """Emit CBFV's ``avg``/``dev``/``range``/``max``/``min`` as a **test** fixture.

    Card #17's third box asks that ``dev`` match CBFV's definition exactly. It does -- it is
    the fraction-weighted mean absolute deviation about the fraction-weighted mean, and
    transcribing that reproduces CBFV to 0.0 over all 1,279 formulae -- but a measurement
    made once in a session is a claim, not a check. This fixture is what turns it into one:
    ``tests/descriptors/test_stats.py`` reads it and reproduces every cell without importing
    CBFV, which CI cannot do because ``parity`` is an optional extra and the package is
    unlicensed.

    It pins both tables, as ``docs/QA-PROTOCOL.md`` §L2 requires: the oliynyk half is
    checked against ``cbfv_oliynyk_reference.csv`` so the numbers are CBFV's own, and the
    jarvis half against the committed ``jarvis.csv``, which *is* CBFV's source -- NIST's
    ``Elements.json``, agreeing to 7.3e-12 (card #16).

    Requires the `parity` extra. Deliberately not run by default and not by CI.
    """
    import numpy as np
    import pandas as pd
    from CBFV.composition import generate_features

    frame = pd.DataFrame({"formula": list(CBFV_STATISTICS_FORMULAE), "target": 0.0})
    wanted = {
        "oliynyk": CBFV_OLIYNYK_PROPERTIES,
        "jarvis": CBFV_JARVIS_PROPERTIES,
    }

    dest.mkdir(parents=True, exist_ok=True)
    path = dest / "cbfv_statistics_reference.csv"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["formula", "table", "property", *STATISTIC_PREFIXES])
        cells = 0
        for table, properties in wanted.items():
            emitted, _, formulae, _ = generate_features(
                frame.copy(), elem_prop=table, drop_duplicates=False, extend_features=False
            )
            order = list(formulae)
            for formula in CBFV_STATISTICS_FORMULAE:
                row = emitted.iloc[order.index(formula)]
                for prop in properties:
                    values = [row[f"{stat}_{prop}"] for stat in STATISTIC_PREFIXES]
                    if any(np.isnan(v) for v in values):
                        raise SystemExit(
                            f"CBFV emitted nan for {formula} / {table} / {prop}. It "
                            f"median-fills those, so the fixture would pin a dataset "
                            f"median rather than a statistic."
                        )
                    writer.writerow([formula, table, prop, *(_cell(v) for v in values)])
                    cells += len(values)
    print(f"  wrote {path}  ({cells} statistics over {len(CBFV_STATISTICS_FORMULAE)} formulae)")


#: CBFV's own prefixes, in CBFV's own order. Duplicated from
#: ``hydms.descriptors.stats.STATISTICS`` rather than imported: this script is stdlib-only
#: by design (see the module docstring) and importing the package here would make building
#: the tables depend on the layer the tables feed.
STATISTIC_PREFIXES = ("avg", "dev", "range", "max", "min")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    # Optional, not because the tables are optional but because the *fixtures* are separable.
    # Both sources are large one-off downloads that nothing in the repository keeps, and the
    # two CBFV fixtures need neither of them -- they are built from CBFV's own installed
    # copy. Requiring the downloads to regenerate a fixture made the fixtures effectively
    # unregenerable, which is how a golden record quietly stops being checkable (card #15).
    parser.add_argument("--oliynyk", type=Path, default=None, help="the Mendeley xlsx")
    parser.add_argument("--jarvis", type=Path, default=None, help="NIST Elements.json")
    parser.add_argument("--dest", type=Path, default=DEST)
    parser.add_argument(
        "--cbfv-reference",
        type=Path,
        default=None,
        help="also write the AC-2 reference fixture here (needs the `parity` extra)",
    )
    parser.add_argument(
        "--cbfv-statistics",
        type=Path,
        default=None,
        help="also write card #17's statistics fixture here (needs the `parity` extra)",
    )
    args = parser.parse_args()

    if (args.oliynyk is None) != (args.jarvis is None):
        parser.error(
            "--oliynyk and --jarvis go together: the descriptor layer sources from both "
            "tables (card #8), and rebuilding one alone would leave the pair inconsistent."
        )
    if args.oliynyk is None and args.cbfv_reference is None and args.cbfv_statistics is None:
        parser.error("nothing to build: pass --oliynyk/--jarvis, --cbfv-reference or "
                     "--cbfv-statistics.")

    if args.oliynyk is not None and args.jarvis is not None:
        print("Oliynyk -- Lee et al. 2024, Data in Brief 53, 110178 (CC BY 4.0)")
        build_oliynyk(args.oliynyk, args.dest)
        print("JARVIS -- Choudhary et al. 2020, npj Comput. Mater. 6, 173 (NIST, public domain)")
        build_jarvis(args.jarvis, args.dest)
    if args.cbfv_reference is not None:
        print("AC-2 reference fixture -- CBFV 1.1.0's own oliynyk.csv, for tests only")
        build_cbfv_reference(args.cbfv_reference)
    if args.cbfv_statistics is not None:
        print("Card #17 fixture -- CBFV 1.1.0's composition statistics, for tests only")
        build_cbfv_statistics(args.cbfv_statistics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
