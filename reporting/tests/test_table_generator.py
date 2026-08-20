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
