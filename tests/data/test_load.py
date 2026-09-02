"""L1 -- the raw loaders and their schemas. Card #9.

Three things are being checked, and they are different questions:

  - **Golden.** The three files load, with the shapes and column names they are documented
    to have. A file that has quietly changed size fails here rather than three stages later.
  - **The grammar.** :func:`parse_formula` accepts what the data contains and rejects the
    four things CBFV silently accepts. The parity test proves the first half against CBFV
    itself, over every formula in both datasets; the rejection tests prove the second half.
  - **The failure path.** Every kind of schema violation raises, and the message names the
    offending row. ``docs/QA-PROTOCOL.md`` section 4.1: delete a line of the implementation
    in your head and something must go red.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pandas", reason="the loaders are pandas frames end to end")

import pandas as pd  # noqa: E402  -- only importable once the skip above has passed
from hydms.data.load import (  # noqa: E402
    ELEMENT_SYMBOLS,
    ColumnSpec,
    FormulaError,
    SchemaViolation,
    SourceSchema,
    hydride_data_schema,
    load_hydride_data,
    load_ml_hydpark,
    load_prefeaturized,
    ml_hydpark_schema,
    parse_formula,
    prefeaturized_schema,
    validate,
)

# A miniature schema exercising all four kinds, so the failure-path tests do not depend on
# the real files and stay readable.
TOY = SourceSchema(
    name="toy",
    filename="toy.csv",
    expected_rows=3,
    columns=(
        ColumnSpec("formula", "formula"),
        ColumnSpec("klass", "string", allowed=("A", "B")),
        ColumnSpec("count", "integer", minimum=0.0),
        ColumnSpec("value", "number", minimum=0.0, maximum=10.0, nullable=True),
    ),
)


def toy_frame() -> pd.DataFrame:
    """Three rows that satisfy :data:`TOY`."""
    return pd.DataFrame(
        {
            "formula": ["Mg1.5Ni1", "TiFe", "La(Ni0.5Co0.5)5"],
            "klass": ["A", "B", "A"],
            "count": [0, 7, 42],
            "value": [1.0, None, 9.5],
        }
    )


# --------------------------------------------------------------------------------------
# The grammar
# --------------------------------------------------------------------------------------


def test_element_symbols_is_the_periodic_table() -> None:
    assert len(ELEMENT_SYMBOLS) == 118
    assert {"H", "Og", "Fe", "U"} <= ELEMENT_SYMBOLS
    assert "Xx" not in ELEMENT_SYMBOLS


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("Mg1.5Ni1", {"Mg": 1.5, "Ni": 1.0}),
        ("Th2Al", {"Al": 1.0, "Th": 2.0}),
        ("Mg0.872Al0.128", {"Al": 0.128, "Mg": 0.872}),
        ("LaFe(CuNi)2", {"Cu": 2.0, "Fe": 1.0, "La": 1.0, "Ni": 2.0}),
        ("Mg14(TiAl4)3", {"Al": 12.0, "Mg": 14.0, "Ti": 3.0}),
        ("(Sc)(Fe)2", {"Fe": 2.0, "Sc": 1.0}),
        ("Ti1Ti1", {"Ti": 2.0}),  # a repeated element accumulates rather than overwriting
    ],
)
def test_parse_formula_reads_the_shapes_the_data_contains(
    formula: str, expected: dict[str, float]
) -> None:
    assert parse_formula(formula) == pytest.approx(expected)


def test_parse_formula_returns_symbols_in_sorted_order() -> None:
    assert list(parse_formula("Ti1Fe0.5Co0.5")) == ["Co", "Fe", "Ti"]


@pytest.mark.parametrize(
    ("written", "clean"),
    [
        ("Mg2Al3 ", "Mg2Al3"),  # 34 rows of hydride_data.csv carry a trailing space
        ("Ti1Mn1.5V0.425 Fe0.075", "Ti1Mn1.5V0.425Fe0.075"),  # 9 carry an internal one
        ("Zr1Fe1.6 V0.4", "Zr1Fe1.6V0.4"),
    ],
)
def test_stray_whitespace_does_not_change_the_composition(written: str, clean: str) -> None:
    """The parser tolerates the whitespace; the loader still stores the string as written.

    Normalising it here would move the unique-formula count from 1149 to 1142 without
    saying so, and pre-empt the canonical key (card #87).
    """
    assert parse_formula(written) == parse_formula(clean)


@pytest.mark.parametrize(
    ("formula", "fragment"),
    [
        ("Xx2", "not a chemical element"),
        ("Hf2Cu (M)", "not a chemical element"),
        ("Mg0", "must be positive"),
        ("Mg-1", "unexpected character"),
        ("", "names no elements"),
        ("   ", "names no elements"),
        ("Mg(Ni", "unclosed"),
        ("Mg)2", "never opened"),
        ("Mg()2", "names no elements"),
        ("(Fe)0", "must be positive"),
        ("2Mg", "unexpected character"),
    ],
)
def test_parse_formula_rejects_what_cbfv_waves_through(formula: str, fragment: str) -> None:
    """The four measured CBFV behaviours, plus the structural errors, all raise.

    ``Xx2`` -> ``{'Xx': 2.0}``, ``Mg0`` -> ``{}``, ``Mg-1`` -> ``{'Mg': -1.0}`` and
    ``Hf2Cu (M)`` -> an element ``'M'`` are what the installed CBFV returns. Downstream the
    first is dropped into an unread ``skipped`` list and the second crashes
    ``generate_features`` with ``zero-size array to reduction operation maximum``.
    """
    with pytest.raises(FormulaError) as caught:
        parse_formula(formula)
    assert fragment in str(caught.value)
    assert repr(formula) in str(caught.value)


def test_parse_formula_rejects_a_non_string() -> None:
    with pytest.raises(FormulaError, match="must be a string"):
        parse_formula(None)  # type: ignore[arg-type]


def test_parse_formula_matches_cbfv_on_every_formula_in_both_datasets() -> None:
    """Parity with the parser the archival pipeline used, on real data.

    This is what makes the rejection tests above a *tightening* rather than a divergence:
    where CBFV produces a sane answer, so does this parser, on all 2051 strings.
    """
    composition = pytest.importorskip(
        "CBFV.composition", reason="CBFV is only installed in the Project environment"
    )
    frames = [
        (load_hydride_data(), "Composition"),
        (load_ml_hydpark(), "Composition_Formula"),
    ]
    checked = 0
    for frame, column in frames:
        for formula in frame[column]:
            theirs = composition._element_composition(formula)
            assert parse_formula(formula) == pytest.approx(theirs), formula
            checked += 1
    assert checked == 1279 + 772


# --------------------------------------------------------------------------------------
# Golden: the real files
# --------------------------------------------------------------------------------------


def test_load_hydride_data_has_its_documented_shape() -> None:
    frame = load_hydride_data()
    assert frame.shape == (1279, 6)
    assert list(frame.columns) == [
        "Composition",
        "Alloy_class",
        "Dataset",
        "H2_W% (max)",
        "temperature(K)",
        "Citation",
    ]


def test_load_prefeaturized_has_its_documented_shape() -> None:
    frame = load_prefeaturized()
    assert frame.shape == (1279, 6)
    assert "log_H2_W% (max)" in frame.columns
    assert "H2_W% (max)" not in frame.columns


def test_load_ml_hydpark_has_its_documented_shape() -> None:
    frame = load_ml_hydpark()
    assert frame.shape == (772, 13)
    assert frame["Composition_Formula"].notna().all()


def test_every_formula_in_the_curated_dataset_parses() -> None:
    """The loader's version of ``assert len(skipped) == 0``.

    ``extract_features_cbfv.py`` never looked at the ``skipped`` list CBFV handed it, so a
    row with an unrecognised element would have vanished between the raw file and the
    feature frame without a word. Nothing may vanish here.
    """
    frame = load_hydride_data()
    parsed = [parse_formula(formula) for formula in frame["Composition"]]
    assert len(parsed) == 1279
    assert all(parsed)
    elements = sorted({symbol for composition in parsed for symbol in composition})
    assert len(elements) == 55, "REPORT.md says 54; the file contains 55 (card #89)"
    assert set(elements) <= ELEMENT_SYMBOLS


def test_the_two_curated_files_declare_the_same_formula_column() -> None:
    """Both schemas read their column names from `pipeline.yaml`, so they cannot drift."""
    assert hydride_data_schema().columns[0].name == prefeaturized_schema().columns[0].name


# --------------------------------------------------------------------------------------
# The failure path
# --------------------------------------------------------------------------------------


def test_a_conforming_frame_passes_through_unchanged() -> None:
    frame = toy_frame()
    returned = validate(frame, TOY)
    assert returned is frame


def test_a_missing_column_is_named() -> None:
    frame = toy_frame().drop(columns=["klass"])
    with pytest.raises(SchemaViolation, match=r"missing column\(s\): 'klass'"):
        validate(frame, TOY)


def test_an_unexpected_column_is_named() -> None:
    frame = toy_frame().assign(surprise=[1, 2, 3])
    with pytest.raises(SchemaViolation, match=r"unexpected column\(s\): 'surprise'"):
        validate(frame, TOY)


def test_an_unexpected_column_is_allowed_when_the_schema_says_so() -> None:
    schema = SourceSchema(
        name=TOY.name,
        filename=TOY.filename,
        expected_rows=TOY.expected_rows,
        columns=TOY.columns,
        allow_extra_columns=True,
    )
    validate(toy_frame().assign(surprise=[1, 2, 3]), schema)


def test_a_row_count_mismatch_is_a_violation() -> None:
    with pytest.raises(SchemaViolation, match="expected 3 rows, found 2"):
        validate(toy_frame().head(2), TOY)


def test_a_truncated_file_fails_to_load(tmp_path) -> None:
    """The row-count assertion reached through the real loader, not just `validate`."""
    truncated = tmp_path / "hydride_data.csv"
    load_hydride_data().head(1200).to_csv(truncated, index=False)
    with pytest.raises(SchemaViolation, match="expected 1279 rows, found 1200"):
        load_hydride_data(truncated)


def test_a_missing_file_says_where_to_look(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="pipeline.yaml"):
        load_hydride_data(tmp_path / "absent.csv")


def test_an_empty_cell_in_a_non_nullable_column_names_the_row() -> None:
    frame = toy_frame()
    frame.loc[1, "klass"] = None
    with pytest.raises(SchemaViolation) as caught:
        validate(frame, TOY)
    message = str(caught.value)
    assert "'klass' is not nullable" in message
    assert "row 1 is empty" in message


def test_a_value_outside_the_allowed_set_names_the_row_and_the_value() -> None:
    frame = toy_frame()
    frame.loc[2, "klass"] = "Z"
    with pytest.raises(SchemaViolation) as caught:
        validate(frame, TOY)
    assert "row 2 ('Z') is not one of A, B" in str(caught.value)


def test_a_value_below_the_minimum_names_the_row() -> None:
    frame = toy_frame()
    frame.loc[0, "count"] = -1
    with pytest.raises(SchemaViolation, match=r"row 0 \(-1\) is below the minimum of 0"):
        validate(frame, TOY)


def test_a_value_above_the_maximum_names_the_row() -> None:
    frame = toy_frame()
    frame.loc[0, "value"] = 10.5
    with pytest.raises(SchemaViolation, match="is above the maximum of 10"):
        validate(frame, TOY)


def test_a_fraction_in_an_integer_column_is_a_violation() -> None:
    frame = toy_frame()
    frame["count"] = frame["count"].astype(float)
    frame.loc[0, "count"] = 1.5
    with pytest.raises(SchemaViolation, match="is not a whole number"):
        validate(frame, TOY)


def test_text_in_a_numeric_column_is_a_violation_rather_than_a_coercion() -> None:
    frame = toy_frame()
    frame["count"] = frame["count"].astype(object)
    frame.loc[1, "count"] = "7"
    with pytest.raises(SchemaViolation, match="expected a number, got str"):
        validate(frame, TOY)


def test_an_unparseable_formula_names_the_row_and_the_reason() -> None:
    frame = toy_frame()
    frame.loc[1, "formula"] = "Xx2"
    with pytest.raises(SchemaViolation) as caught:
        validate(frame, TOY)
    message = str(caught.value)
    assert "column 'formula' (formula)" in message
    assert "row 1" in message
    assert "not a chemical element" in message


def test_a_duplicate_in_a_unique_column_is_a_violation() -> None:
    schema = SourceSchema(
        name="unique-toy",
        filename="toy.csv",
        expected_rows=3,
        columns=(ColumnSpec("klass", "string", unique=True),),
        allow_extra_columns=True,
    )
    with pytest.raises(SchemaViolation, match="must be unique"):
        validate(toy_frame(), schema)


def test_every_problem_is_reported_at_once() -> None:
    """One raise, every problem. Fixing them one reload at a time is the failure mode."""
    frame = toy_frame().head(2)
    frame.loc[0, "klass"] = "Z"
    frame.loc[1, "formula"] = "Mg0"
    with pytest.raises(SchemaViolation) as caught:
        validate(frame, TOY)
    message = str(caught.value)
    assert "expected 3 rows, found 2" in message
    assert "'klass'" in message
    assert "'formula'" in message


def test_the_offender_listing_is_truncated_but_the_total_is_not() -> None:
    schema = SourceSchema(
        name="wide",
        filename="wide.csv",
        expected_rows=20,
        columns=(ColumnSpec("count", "integer", minimum=0.0),),
    )
    frame = pd.DataFrame({"count": [-1] * 20})
    with pytest.raises(SchemaViolation) as caught:
        validate(frame, schema)
    message = str(caught.value)
    assert "20 row(s)" in message
    assert "and 12 more" in message


# --------------------------------------------------------------------------------------
# The schema declarations themselves
# --------------------------------------------------------------------------------------


def test_a_column_spec_rejects_an_unknown_kind() -> None:
    with pytest.raises(ValueError, match="is not one of"):
        ColumnSpec("x", "boolean")


def test_bounds_on_a_string_column_are_rejected_at_declaration() -> None:
    with pytest.raises(ValueError, match="bounds apply to numeric kinds only"):
        ColumnSpec("x", "string", minimum=0.0)


def test_an_allowed_set_on_a_numeric_column_is_rejected_at_declaration() -> None:
    with pytest.raises(ValueError, match="string kinds only"):
        ColumnSpec("x", "number", allowed=("1",))


def test_ml_hydpark_marks_only_the_structural_columns_non_nullable() -> None:
    required = {spec.name for spec in ml_hydpark_schema().columns if not spec.nullable}
    assert required == {"Unnamed: 0", "index", "Composition_Formula"}
