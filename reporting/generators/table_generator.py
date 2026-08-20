"""Generate LaTeX code for Table objects."""

from reporting.models.table import Table
from reporting.utils.escaping import escape_latex


def generate_table_latex(table: Table) -> str:
    """
    Convert a Table model into a LaTeX tabular/longtable environment.

    Args:
        table: Table object.

    Returns:
        LaTeX string for the table.
    """
    col_spec = table.col_spec
    if len(col_spec) != len(table.headers):
        col_spec = 'l' * len(table.headers)

    header_cells = [escape_latex(h) for h in table.headers]

    if table.use_longtable:
        return _build_longtable(col_spec, header_cells, table)
    else:
        return _build_tabular(col_spec, header_cells, table)


def _build_tabular(col_spec: str, header_cells: list, table: Table) -> str:
    """Build a tabular environment wrapped in a table float."""
    lines = []
    lines.append(r"\begin{table}[h]")
    lines.append(r"\centering")
    if table.caption:
        lines.append(r"\caption{" + escape_latex(table.caption) + "}")
    if table.label:
        lines.append(r"\label{" + table.label + "}")
    lines.append(r"\begin{tabular}{" + col_spec + "}")

    if table.header_color:
        color_cmd = r"\cellcolor{" + table.header_color + "}"
        header_row = " & ".join(f"{color_cmd} {c}" for c in header_cells)
    else:
        header_row = " & ".join(header_cells)
    lines.append(header_row + r" \\ \hline")

    for row in table.rows:
        escaped = [escape_latex(cell) for cell in row]
        lines.append(" & ".join(escaped) + r" \\")
        lines.append(r"\hline")

    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")
    return "\n".join(lines)


def _build_longtable(col_spec: str, header_cells: list, table: Table) -> str:
    """Build a longtable environment with repeating headers."""
    lines = []
    lines.append(r"\begin{longtable}{" + col_spec + "}")
    if table.caption:
        lines.append(r"\caption{" + escape_latex(table.caption) + "}")
    if table.label:
        lines.append(r"\label{" + table.label + "}")

    if table.header_color:
        color_cmd = r"\cellcolor{" + table.header_color + "}"
        header_row = " & ".join(f"{color_cmd} {c}" for c in header_cells)
    else:
        header_row = " & ".join(header_cells)
    lines.append(header_row + r" \\ \hline")
    lines.append(r"\endfirsthead")

    n = len(table.headers)
    lines.append(r"\multicolumn{" + str(n) + r"}{c}{{\bfseries \tablename\ \thetable{} -- continued from previous page}} \\")
    lines.append(r"\endhead")
    lines.append(r"\endfoot")
    lines.append(r"\endlastfoot")

    for row in table.rows:
        escaped = [escape_latex(cell) for cell in row]
        lines.append(" & ".join(escaped) + r" \\")
        lines.append(r"\hline")

    lines.append(r"\end{longtable}")
    return "\n".join(lines)
