"""Generate LaTeX code for Table objects."""

from reporting.models.table import Table
from reporting.utils.escaping import escape_latex

# ── Status-column coloring (opt-in: fires only when a header literally
#    named "Status" is present) ─────────────────────────────────────────
_STATUS_HEADER = "status"
_PASS_COLOR = "passgreen"
_FAIL_COLOR = "failred"


def _status_column_index(table: Table):
    """Return the index of the 'Status' column, or None if absent."""
    for i, header in enumerate(table.headers):
        if str(header).strip().lower() == _STATUS_HEADER:
            return i
    return None


def _render_cell(cell, status_idx, col_idx) -> str:
    """Escape a cell, optionally wrapping recognized statuses in \\cellcolor.

    The \\cellcolor command is prepended to the already-escaped text — the
    escaped text itself must never include the color command (escaping the
    combined string would break the LaTeX command).
    """
    text = str(cell)
    if col_idx == status_idx:
        stripped = text.strip().lower()
        if stripped == "pass":
            return r"\cellcolor{passgreen}" + escape_latex(text)
        if stripped == "fail":
            return r"\cellcolor{failred}" + escape_latex(text)
        # Unknown status in a Status column: leave unstyled.
    return escape_latex(text)


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


def _render_rows(table: Table, status_idx) -> list:
    """Render data rows with per-cell escaping and optional Status coloring."""
    lines = []
    for row in table.rows:
        cells = [
            _render_cell(cell, status_idx, col_idx)
            for col_idx, cell in enumerate(row)
        ]
        lines.append(" & ".join(cells) + r" \\")
        lines.append(r"\hline")
    return lines


def _build_tabular(col_spec: str, header_cells: list, table: Table) -> str:
    """Build a tabular environment wrapped in a table float."""
    status_idx = _status_column_index(table)
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

    lines.extend(_render_rows(table, status_idx))

    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")
    return "\n".join(lines)


def _build_longtable(col_spec: str, header_cells: list, table: Table) -> str:
    """Build a longtable environment with repeating headers."""
    status_idx = _status_column_index(table)
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

    lines.extend(_render_rows(table, status_idx))

    lines.append(r"\end{longtable}")
    return "\n".join(lines)
