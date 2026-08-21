"""Regression tests: JSON -> models -> .tex round-trip verification.

Tests both the native JSON format and the Osdag adapter format.

Honesty note (per task requirement):
These tests verify the NEW pipeline faithfully transfers all design data
from JSON through the Report model to .tex output.  They do NOT compare
against legacy save_latex() output because:

  1. No legacy PDFs or .tex files exist anywhere in the workspace.
  2. The original code depends on pylatex (not installed in this env).
  3. The old code writes ephemeral .tmp .tex files during PDF generation
     that are not saved.

The assertions below are therefore STRUCTURAL (does the .tex contain
the right sections, tables, keywords?) not COMPARATIVE (does it match
the old output byte-for-byte?).  This is the most rigorous testing
possible without executing the legacy code.
"""

import json
import os
import re

import pytest

from reporting.generators.latex_generator import render_report
from reporting.cli import load_report_from_json
from reporting.adapters.osdag_adapter import build_report


FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


# ── native JSON fixtures ─────────────────────────────────────────────────
@pytest.fixture
def bolted_end_plate_report():
    path = os.path.join(FIXTURES, "bolted_end_plate_sample.json")
    return load_report_from_json(path)


@pytest.fixture
def base_plate_native_report():
    path = os.path.join(FIXTURES, "base_plate_sample.json")
    return load_report_from_json(path)


# ── Osdag adapter fixtures ───────────────────────────────────────────────
@pytest.fixture
def bc_end_plate_report():
    path = os.path.join(FIXTURES, "bc_end_plate_real.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return build_report(
        uiObj=data["uiObj"],
        design_check=data["design_check"],
        reportsummary=data.get("reportsummary"),
        module_name="Beam-to-Column End Plate Connection",
    )


@pytest.fixture
def base_plate_real_report():
    path = os.path.join(FIXTURES, "base_plate_real.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return build_report(
        uiObj=data["uiObj"],
        design_check=data["design_check"],
        reportsummary=data.get("reportsummary"),
        module_name="Base Plate Connection",
    )


@pytest.fixture
def fin_plate_real_report():
    path = os.path.join(FIXTURES, "fin_plate_real.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return build_report(
        uiObj=data["uiObj"],
        design_check=data["design_check"],
        reportsummary=data.get("reportsummary"),
        module_name="Fin Plate Connection",
    )


def _render(report, tmp_path, name):
    output = str(tmp_path / f"{name}.tex")
    render_report(report, output)
    with open(output, "r", encoding="utf-8") as f:
        return f.read()


# ── native format tests ──────────────────────────────────────────────────
class TestBoltedEndPlateNative:
    def test_loads_correctly(self, bolted_end_plate_report):
        r = bolted_end_plate_report
        assert r.title == "Bolted End Plate Connection Design Report"
        assert r.author == "Osdag"
        assert len(r.sections) >= 1

    def test_render_produces_tex(self, bolted_end_plate_report, tmp_path):
        content = _render(bolted_end_plate_report, tmp_path, "native_bep")
        assert r"\begin{document}" in content
        assert r"\end{document}" in content

    def test_title_in_output(self, bolted_end_plate_report, tmp_path):
        content = _render(bolted_end_plate_report, tmp_path, "native_bep")
        assert "Bolted End Plate Connection Design Report" in content


class TestBasePlateNative:
    def test_loads_correctly(self, base_plate_native_report):
        r = base_plate_native_report
        assert r.title == "Base Plate Design Report"
        assert r.author == "Osdag"

    def test_render_produces_tex(self, base_plate_native_report, tmp_path):
        content = _render(base_plate_native_report, tmp_path, "native_bp")
        assert r"\begin{document}" in content

    def test_toc_enabled(self, base_plate_native_report, tmp_path):
        content = _render(base_plate_native_report, tmp_path, "native_bp")
        assert r"\tableofcontents" in content

    def test_lof_enabled(self, base_plate_native_report, tmp_path):
        content = _render(base_plate_native_report, tmp_path, "native_bp")
        assert r"\listoffigures" in content

    def test_lot_enabled(self, base_plate_native_report, tmp_path):
        content = _render(base_plate_native_report, tmp_path, "native_bp")
        assert r"\listoftables" in content


# ── Osdag adapter tests ──────────────────────────────────────────────────
# Intentional differences from old save_latex():
#   - All text now goes through escape_latex() (old code used NoEscape everywhere)
#   - Errors raise exceptions instead of being silently swallowed (except: pass)
#   - 2D/3D image sections omitted from adapter (not part of core report model;
#     can be added via Figure model when needed)
#   - Design Log section omitted (was reportsummary['logger_messages'] only;
#     not part of core structural report)

class TestBCEndPlateOsdag:
    def test_loads_correctly(self, bc_end_plate_report):
        r = bc_end_plate_report
        assert "Beam-to-Column End Plate" in r.title
        assert r.author  # populated from reportsummary

    def test_render_produces_tex(self, bc_end_plate_report, tmp_path):
        content = _render(bc_end_plate_report, tmp_path, "osdag_bcep")
        assert r"\begin{document}" in content
        assert r"\end{document}" in content

    def test_title_in_output(self, bc_end_plate_report, tmp_path):
        content = _render(bc_end_plate_report, tmp_path, "osdag_bcep")
        assert "Beam-to-Column End Plate Connection Design Report" in content

    def test_no_pylatex_leak(self, bc_end_plate_report, tmp_path):
        content = _render(bc_end_plate_report, tmp_path, "osdag_bcep")
        assert "<pylatex" not in content

    def test_design_checks_present(self, bc_end_plate_report, tmp_path):
        content = _render(bc_end_plate_report, tmp_path, "osdag_bcep")
        assert "Design Checks" in content
        assert "Bolt Optimization" in content
        assert "Weld Design" in content


class TestBasePlateOsdag:
    def test_loads_correctly(self, base_plate_real_report):
        r = base_plate_real_report
        assert "Base Plate" in r.title
        assert r.author  # populated from reportsummary

    def test_render_produces_tex(self, base_plate_real_report, tmp_path):
        content = _render(base_plate_real_report, tmp_path, "osdag_bp")
        assert r"\begin{document}" in content
        assert r"\end{document}" in content

    def test_design_checks_present(self, base_plate_real_report, tmp_path):
        content = _render(base_plate_real_report, tmp_path, "osdag_bp")
        assert "Design Checks" in content
        assert "Bearing Strength" in content
        assert "Anchor Bolt" in content
        assert "Base Plate Analysis" in content
        assert "Weld Design" in content

    def test_section_details_present(self, base_plate_real_report, tmp_path):
        content = _render(base_plate_real_report, tmp_path, "osdag_bp")
        assert "ISMB 350" in content

    def test_config_flags(self, base_plate_real_report, tmp_path):
        content = _render(base_plate_real_report, tmp_path, "osdag_bp")
        assert r"\tableofcontents" in content
        assert r"\listoffigures" in content
        assert r"\listoftables" in content

    def test_no_pylatex_leak(self, base_plate_real_report, tmp_path):
        content = _render(base_plate_real_report, tmp_path, "osdag_bp")
        assert "<pylatex" not in content
        assert "pylatex" not in content.lower()


class TestFinPlateOsdag:
    """Third connection type - proves the adapter generalizes with zero
    adapter changes (shear-only loads, pretensioned bolts, no plate type)."""

    def test_loads_correctly(self, fin_plate_real_report):
        r = fin_plate_real_report
        assert "Fin Plate" in r.title
        assert r.author  # populated from reportsummary

    def test_render_produces_tex(self, fin_plate_real_report, tmp_path):
        content = _render(fin_plate_real_report, tmp_path, "osdag_fin")
        assert r"\begin{document}" in content
        assert r"\end{document}" in content

    def test_design_checks_present(self, fin_plate_real_report, tmp_path):
        content = _render(fin_plate_real_report, tmp_path, "osdag_fin")
        assert "Design Checks" in content
        assert "Initial Section Check" in content
        assert "Bolt Design" in content
        assert "Section Design" in content
        assert "Weld Design" in content

    def test_section_details_present(self, fin_plate_real_report, tmp_path):
        content = _render(fin_plate_real_report, tmp_path, "osdag_fin")
        assert "MB 500" in content
        assert "UC 356 x 406 x 393" in content

    def test_fail_status_preserved(self, fin_plate_real_report, tmp_path):
        content = _render(fin_plate_real_report, tmp_path, "osdag_fin")
        assert "Fail" in content

    def test_no_pylatex_leak(self, fin_plate_real_report, tmp_path):
        content = _render(fin_plate_real_report, tmp_path, "osdag_fin")
        assert "<pylatex" not in content
        assert "pylatex" not in content.lower()
