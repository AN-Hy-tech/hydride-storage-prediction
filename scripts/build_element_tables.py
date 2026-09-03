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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oliynyk", type=Path, required=True, help="the Mendeley xlsx")
    parser.add_argument("--jarvis", type=Path, required=True, help="NIST Elements.json")
    parser.add_argument("--dest", type=Path, default=DEST)
    parser.add_argument(
        "--cbfv-reference",
        type=Path,
        default=None,
        help="also write the AC-2 reference fixture here (needs the `parity` extra)",
    )
    args = parser.parse_args()

    print("Oliynyk -- Lee et al. 2024, Data in Brief 53, 110178 (CC BY 4.0)")
    build_oliynyk(args.oliynyk, args.dest)
    print("JARVIS -- Choudhary et al. 2020, npj Comput. Mater. 6, 173 (NIST, public domain)")
    build_jarvis(args.jarvis, args.dest)
    if args.cbfv_reference is not None:
        print("AC-2 reference fixture -- CBFV 1.1.0's own oliynyk.csv, for tests only")
        build_cbfv_reference(args.cbfv_reference)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
