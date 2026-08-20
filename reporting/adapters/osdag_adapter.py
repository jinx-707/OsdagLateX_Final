"""Adapter: Osdag uiObj + Design_Check -> reporting.models.report.Report."""

from __future__ import annotations
from typing import Any, Dict, List, Tuple

from reporting.models.report import Report, ReportConfig
from reporting.models.section import Section
from reporting.models.table import Table
from reporting.models.figure import Figure
from reporting.config import (
    DEFAULT_AUTHOR,
    TITLE_SUFFIX,
    HEADER_COLOR,
    DEFAULT_COL_SPEC,
    INPUT_COL_SPEC,
    DETAILS_COL_SPEC,
    INPUT_TABLE_HEADERS,
    DETAILS_TABLE_HEADERS,
    CHECKS_TABLE_HEADERS,
    SECTION_TITLE_INPUT,
    SECTION_TITLE_CHECKS,
)

# ── Osdag data-format sentinels ──────────────────────────────────────
_TITLE_SENTINEL = "TITLE"
_SUBSECTION_MARKER = "SubSection"

# ── Keys to skip in the input table ──────────────────────────────────
_SKIP_KEYS = {
    "Selected Section Details",
    "KEY_DISP_ANGLE_LIST",
    "KEY_DISP_TOPANGLE_LIST",
    "KEY_DISP_CLEAT_ANGLE_LIST",
}

# ── reportsummary dict keys ──────────────────────────────────────────
_PROFILE_SUMMARY_KEY = "ProfileSummary"
_DESIGNER_KEY = "Designer"

# ── Section details keys ─────────────────────────────────────────────
_SECTION_PROFILE_KEY = "Section Profile"


def build_report(
    uiObj: Dict[str, Any],
    design_check: List[Tuple],
    reportsummary: Dict[str, Any] | None = None,
    module_name: str = "",
    title: str | None = None,
    author: str | None = None,
) -> Report:
    """
    Convert Osdag's uiObj dict and Design_Check list into a Report model.

    Args:
        uiObj: Input parameter dict (report_input / self.report_input).
        design_check: Design check list (report_check / self.report_check).
        reportsummary: Optional report summary dict with ProfileSummary, etc.
        module_name: Module name string (e.g. 'Beam-to-Column End Plate Connection').
        title: Override report title. If None, derived from module_name.
        author: Override author. If None, from reportsummary or 'Osdag'.

    Returns:
        A fully populated Report object.
    """
    title = title or f"{module_name or DEFAULT_AUTHOR} {TITLE_SUFFIX}"
    author = author
    if not author and reportsummary:
        author = reportsummary.get(_PROFILE_SUMMARY_KEY, {}).get(_DESIGNER_KEY, DEFAULT_AUTHOR)
    author = author or DEFAULT_AUTHOR

    sections: List[Section] = []

    # 1. Input Parameters section
    sections.append(_build_input_section(uiObj))

    # 2. Design Checks section
    sections.append(_build_design_checks_section(design_check))

    config = ReportConfig(include_toc=True, include_list_of_figures=True, include_list_of_tables=True)

    return Report(
        title=title,
        author=author,
        sections=sections,
        config=config,
    )


def _build_input_section(uiObj: Dict[str, Any]) -> Section:
    """Parse uiObj into an 'Input Parameters' section.

    uiObj keys that map to 'TITLE' act as subsection headers.
    Sub-dicts (section details) are rendered as sub-tables with a
    cross-section profile image reference.
    """
    top_section = Section(title=SECTION_TITLE_INPUT, level=1)
    current_sub: Section | None = None
    rows: List[List[str]] = []

    for key, value in uiObj.items():
        if key in _SKIP_KEYS:
            continue

        # Subsection header sentinel
        if value == _TITLE_SENTINEL:
            # Flush any accumulated rows into a table on the current sub
            if rows:
                if current_sub is not None:
                    current_sub.content.append(_make_input_table(rows))
                    rows = []
                else:
                    top_section.content.append(_make_input_table(rows))
                    rows = []
            # Save the previous subsection before starting a new one
            if current_sub is not None:
                top_section.subsections.append(current_sub)
            current_sub = Section(title=key, level=2)
            continue

        # Sub-dict => section details table
        if isinstance(value, dict):
            if rows:
                if current_sub is not None:
                    current_sub.content.append(_make_input_table(rows))
                    rows = []
                else:
                    top_section.content.append(_make_input_table(rows))
                    rows = []
            detail_table = _make_section_details_table(key, value)
            if current_sub is not None:
                current_sub.content.append(detail_table)
            else:
                top_section.content.append(detail_table)
            continue

        # Normal key-value row
        rows.append([str(key), _format_value(value)])

    # Flush remaining rows
    if rows:
        if current_sub is not None:
            current_sub.content.append(_make_input_table(rows))
        else:
            top_section.content.append(_make_input_table(rows))

    # Attach accumulated subsections
    if current_sub is not None:
        top_section.subsections.append(current_sub)

    return top_section


def _make_input_table(rows: List[List[str]]) -> Table:
    return Table(
        headers=INPUT_TABLE_HEADERS,
        rows=rows,
        col_spec=INPUT_COL_SPEC,
        use_longtable=True,
        caption=SECTION_TITLE_INPUT,
        label="tab:input",
    )


def _make_section_details_table(section_label: str, details: Dict[str, Any]) -> Table:
    """Build a table from a section-details sub-dict."""
    rows = []
    for k, v in details.items():
        if k == _SECTION_PROFILE_KEY:
            continue  # shown as header context, not as a row
        rows.append([str(k), str(v)])
    profile_name = details.get(_SECTION_PROFILE_KEY, section_label)
    caption = f"{section_label.strip()} - {profile_name}"
    label = f"tab:{section_label.strip().lower().replace(' ', '-')}"
    return Table(
        headers=DETAILS_TABLE_HEADERS,
        rows=rows,
        col_spec=DETAILS_COL_SPEC,
        use_longtable=True,
        header_color=HEADER_COLOR,
        caption=caption,
        label=label,
    )


def _build_design_checks_section(design_check: List[Tuple]) -> Section:
    """Parse Design_Check list into a 'Design Checks' section with subsections."""
    top = Section(title=SECTION_TITLE_CHECKS, level=1)
    current_sub: Section | None = None
    current_rows: List[List[str]] = []
    current_col_spec = DEFAULT_COL_SPEC

    for item in design_check:
        if not isinstance(item, (list, tuple)):
            continue

        # SubSection header
        if len(item) == 3 and item[0] == _SUBSECTION_MARKER:
            # Flush previous
            if current_sub is not None and current_rows:
                current_sub.content.append(_make_checks_table(current_rows, current_col_spec))
                top.subsections.append(current_sub)
            title = item[1]
            current_col_spec = item[2]
            current_sub = Section(title=title, level=2)
            current_rows = []
            continue

        # Data row: (label, required, provided, status)
        if len(item) == 4:
            label, req, prov, status = item
            prov_str = _format_value(prov)
            req_str = _format_value(req)
            current_rows.append([str(label), req_str, prov_str, str(status)])
        elif len(item) == 3 and item[0] != _SUBSECTION_MARKER:
            # Some modules emit 3-element data rows
            current_rows.append([str(item[0]), str(item[1]), str(item[2]), ""])

    # Flush last subsection
    if current_sub is not None and current_rows:
        current_sub.content.append(_make_checks_table(current_rows, current_col_spec))
        top.subsections.append(current_sub)

    return top


def _make_checks_table(rows: List[List[str]], col_spec: str) -> Table:
    return Table(
        headers=CHECKS_TABLE_HEADERS,
        rows=rows,
        col_spec=col_spec,
        use_longtable=True,
        header_color=HEADER_COLOR,
    )


def _format_value(v: Any) -> str:
    """Convert a value to a displayable string.

    pylatex.Math objects stringify to their LaTeX source; we preserve that.
    Numbers and strings pass through as-is.
    """
    if v is None:
        return ""
    return str(v)
