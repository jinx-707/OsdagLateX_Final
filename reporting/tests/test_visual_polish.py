"""Visual polish pass tests.

Covers:
- Item 2: metadata block (module_name / report_id) under the title.
- Item 3: force_page_break_before -> \\clearpage before a section heading.
- Item 5: disclaimer footer sourced from config.REPORT_DISCLAIMER.
"""

import os

from unittest.mock import patch

from reporting.models.report import Report
from reporting.models.section import Section
from reporting.generators.latex_generator import render_report


def _render(report: Report, tmp_path, name="out.tex") -> str:
    path = str(tmp_path / name)
    render_report(report, path)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _simple_report(**report_kwargs) -> Report:
    section = Section(title="Design Checks", level=1, content=["Some prose."])
    return Report(
        title="Test Report",
        author="Osdag",
        sections=[section],
        **report_kwargs,
    )


# ── Item 2: metadata block ───────────────────────────────────────────────

def test_module_name_none_omits_row_and_none_literal(tmp_path):
    report = _simple_report()  # module_name not set -> None
    content = _render(report, tmp_path)

    assert "Module:" not in content
    assert "None" not in content


def test_module_name_present_renders(tmp_path):
    report = _simple_report(module_name="Beam-to-Column End Plate Connection")
    content = _render(report, tmp_path)

    assert r"\textbf{Module:}" in content
    assert "Beam-to-Column End Plate Connection" in content


def test_report_id_stable_across_two_renders(tmp_path):
    report = _simple_report()
    first = _render(report, tmp_path, name="first.tex")
    second = _render(report, tmp_path, name="second.tex")

    assert report.report_id is not None
    assert report.report_id.startswith("OSDAG-")
    assert report.report_id in first
    assert report.report_id in second
    assert first == second


def test_report_id_explicit_value_respected(tmp_path):
    report = _simple_report(report_id="OSDAG-FIXED42")
    assert report.report_id == "OSDAG-FIXED42"
    content = _render(report, tmp_path)
    assert "OSDAG-FIXED42" in content


# ── Item 3: forced page break before a section ──────────────────────────

def test_force_page_break_emits_clearpage_before_heading(tmp_path):
    flagged = Section(title="Design Summary", level=1,
                      content=["Summary text."],
                      force_page_break_before=True)
    report = Report(title="T", author="Osdag", sections=[
        Section(title="Intro", level=1, content=["Intro text."]),
        flagged,
    ])
    content = _render(report, tmp_path)

    assert "\\clearpage\n\\section{Design Summary}" in content


def test_no_flag_no_clearpage(tmp_path):
    section = Section(title="Design Checks", level=1, content=["Text."])
    report = Report(title="T", author="Osdag", sections=[section])
    content = _render(report, tmp_path)

    assert "\\clearpage" not in content


def test_native_json_design_summary_gets_clearpage():
    """The beam-column fixture's Design Summary is flagged via JSON data."""
    import json

    fixture = os.path.join(
        os.path.dirname(__file__), "..", "..", "real_beam_column_report.json"
    )
    with open(fixture, "r", encoding="utf-8") as f:
        data = json.load(f)
    summary_sections = [
        s for s in data["sections"]
        if s.get("title") == "Design Summary"
        and s.get("force_page_break_before")
    ]
    assert summary_sections, (
        "real_beam_column_report.json should flag Design Summary with "
        "force_page_break_before=true"
    )


# ── Item 5: disclaimer footer ────────────────────────────────────────────

def test_disclaimer_rendered_from_config_constant(tmp_path):
    report = _simple_report()
    content = _render(report, tmp_path)

    from reporting.config import REPORT_DISCLAIMER as real_value
    assert real_value in content


def test_disclaimer_not_hardcoded_in_template_path(tmp_path):
    """Patching the generator's config constant must change the output —
    proving the string flows through config rather than being duplicated
    inside the template."""
    sentinel = "PATCHED-DISCLAIMER-SENTINEL-1234"
    report = _simple_report()

    with patch("reporting.generators.latex_generator.REPORT_DISCLAIMER", sentinel):
        content = _render(report, tmp_path)

    assert sentinel in content
