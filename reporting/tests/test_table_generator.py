from reporting.models.table import Table
from reporting.generators.table_generator import generate_table_latex


def test_table_generator_basic():
    t = Table(
        headers=["Item", "Value"],
        rows=[["A", "1"], ["B", "2"]],
        col_spec="ll",
        use_longtable=False,
        caption="My Table",
        label="tab:my",
    )
    latex = generate_table_latex(t)
    assert r"\begin{table}" in latex
    assert r"\caption{My Table}" in latex
    assert r"\label{tab:my}" in latex
    assert "A & 1" in latex


def test_table_generator_longtable():
    t = Table(
        headers=["X", "Y"],
        rows=[["1", "2"]],
        use_longtable=True,
    )
    latex = generate_table_latex(t)
    assert r"\begin{longtable}" in latex
    assert r"\end{longtable}" in latex
<<<<<<< HEAD


# ── Status-column Pass/Fail cell coloring ────────────────────────────────

def _status_table(status_value, **kwargs):
    return Table(
        headers=["Check", "Status"],
        rows=[["Bolt shear", status_value]],
        col_spec="ll",
        **kwargs,
    )


def test_status_pass_cell_colored():
    latex = generate_table_latex(_status_table("Pass"))
    assert r"\cellcolor{passgreen}Pass" in latex


def test_status_fail_cell_colored():
    latex = generate_table_latex(_status_table("Fail"))
    assert r"\cellcolor{failred}Fail" in latex


def test_status_unknown_value_not_colored():
    latex = generate_table_latex(_status_table("N/A"))
    assert r"\cellcolor{passgreen}" not in latex
    assert r"\cellcolor{failred}" not in latex
    assert "N/A" in latex


def test_no_status_column_no_coloring():
    t = Table(
        headers=["Check", "Required"],
        rows=[["Pass", "10 kN"]],
        col_spec="ll",
    )
    latex = generate_table_latex(t)
    assert r"\cellcolor{passgreen}" not in latex
    assert r"\cellcolor{failred}" not in latex


def test_status_matching_is_case_insensitive():
    latex = generate_table_latex(_status_table("FAIL"))
    assert r"\cellcolor{failred}FAIL" in latex


def test_status_special_char_still_escaped():
    # Unrecognized status containing special chars: no color, but escaped.
    latex = generate_table_latex(_status_table("Fail & warn"))
    assert r"\cellcolor{failred}" not in latex
    assert r"Fail \& warn" in latex


def test_status_coloring_in_longtable():
    t = Table(
        headers=["Check", "Status"],
        rows=[["Weld shear", "Fail"], ["Bolt shear", "Pass"]],
        col_spec="ll",
        use_longtable=True,
    )
    latex = generate_table_latex(t)
    assert r"\cellcolor{passgreen}Pass" in latex
    assert r"\cellcolor{failred}Fail" in latex
=======
>>>>>>> 6d9d68f21fde00f29096fb7fa4988f597ca8d967
