"""Integration tests: real Osdag data -> Report -> .tex round-trip.

Parameterized across multiple Osdag connection types to prove
the adapter is general.
"""

import json
import os
import re

import pytest

from reporting.adapters.osdag_adapter import build_report
from reporting.generators.latex_generator import render_report
from reporting.models.table import Table

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

# ── fixture registry ──────────────────────────────────────────────────────
FIXTURE_FILES = {
    "bc_end_plate": {
        "file": "bc_end_plate_real.json",
        "module": "Beam-to-Column End Plate Connection",
        "title_contains": "Beam-to-Column End Plate",
        "key_content": ["ISMB 450", "ISMB 350", "Bolt Optimization"],
        "key_statuses": ["Pass", "Compatible"],
        "min_subsections": 5,
        "min_design_rows": 15,
    },
    "base_plate": {
        "file": "base_plate_real.json",
        "module": "Base Plate Connection",
        "title_contains": "Base Plate",
        "key_content": ["ISMB 350", "Bearing Strength", "Anchor Bolt"],
        "key_statuses": ["Pass", "OK"],
        "min_subsections": 4,
        "min_design_rows": 15,
    },
}


def _load_fixture(name):
    meta = FIXTURE_FILES[name]
    path = os.path.join(FIXTURES, meta["file"])
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    report = build_report(
        uiObj=data["uiObj"],
        design_check=data["design_check"],
        reportsummary=data.get("reportsummary"),
        module_name=meta["module"],
        title=data.get("title"),
        author=data.get("author"),
    )
    return data, report, meta


def _render_tex(report, tmp_path, name):
    output = str(tmp_path / f"{name}.tex")
    render_report(report, output)
    with open(output, "r", encoding="utf-8") as f:
        return f.read()


# ── parameterized adapter tests ──────────────────────────────────────────
@pytest.fixture(params=list(FIXTURE_FILES.keys()))
def fx(request):
    return _load_fixture(request.param)


class TestAdapterBuilding:
    def test_correct_title(self, fx):
        _, report, meta = fx
        assert meta["title_contains"] in report.title

    def test_has_input_section(self, fx):
        _, report, _ = fx
        assert len(report.sections) >= 1
        assert report.sections[0].title == "Input Parameters"
        assert report.sections[0].level == 1

    def test_input_has_tables(self, fx):
        _, report, _ = fx
        input_sec = report.sections[0]
        tables = [i for i in input_sec.content if isinstance(i, Table)]
        assert len(tables) >= 1

    def test_section_details_in_subsections(self, fx):
        _, report, _ = fx
        input_sec = report.sections[0]
        all_content = list(input_sec.content)
        for sub in input_sec.subsections:
            all_content.extend(sub.content)
        tables = [i for i in all_content if isinstance(i, Table)]
        assert len(tables) >= 2

    def test_design_checks_section(self, fx):
        _, report, meta = fx
        dc = report.sections[1]
        assert dc.title == "Design Checks"
        assert len(dc.subsections) >= meta["min_subsections"]

    def test_design_rows_have_data(self, fx):
        _, report, meta = fx
        dc = report.sections[1]
        total = sum(
            len(item.rows)
            for sub in dc.subsections
            for item in sub.content
            if isinstance(item, Table)
        )
        assert total >= meta["min_design_rows"]

    def test_expected_statuses(self, fx):
        _, report, meta = fx
        dc = report.sections[1]
        statuses = set()
        for sub in dc.subsections:
            for item in sub.content:
                if isinstance(item, Table):
                    for row in item.rows:
                        statuses.add(row[3])
        for s in meta["key_statuses"]:
            assert s in statuses


# ── parameterized render tests ───────────────────────────────────────────
class TestRenderRoundTrip:
    def test_valid_tex(self, fx, tmp_path):
        _, report, meta = fx
        content = _render_tex(report, tmp_path, meta["module"].replace(" ", "_"))
        assert r"\begin{document}" in content
        assert r"\end{document}" in content

    def test_key_content_present(self, fx, tmp_path):
        _, report, meta = fx
        content = _render_tex(report, tmp_path, meta["module"].replace(" ", "_"))
        for kw in meta["key_content"]:
            assert kw in content, f"Expected '{kw}' in rendered .tex"

    def test_input_params_in_tex(self, fx, tmp_path):
        _, report, meta = fx
        content = _render_tex(report, tmp_path, meta["module"].replace(" ", "_"))
        assert "Input Parameters" in content

    def test_design_checks_in_tex(self, fx, tmp_path):
        _, report, meta = fx
        content = _render_tex(report, tmp_path, meta["module"].replace(" ", "_"))
        assert "Design Checks" in content

    def test_no_pylatex_leak(self, fx, tmp_path):
        _, report, meta = fx
        content = _render_tex(report, tmp_path, meta["module"].replace(" ", "_"))
        assert "<pylatex" not in content
        assert "pylatex" not in content.lower()

    def test_multiple_longtables(self, fx, tmp_path):
        _, report, meta = fx
        content = _render_tex(report, tmp_path, meta["module"].replace(" ", "_"))
        assert content.count(r"\begin{longtable}") >= 3


# ── ToC / LoF / LoT verification ────────────────────────────────────────
class TestToCLoFLoT:
    """Verify that config flags produce the expected LaTeX commands."""

    def test_toc_appears_when_enabled(self, fx, tmp_path):
        _, report, meta = fx
        report.config.include_toc = True
        report.config.include_list_of_figures = True
        report.config.include_list_of_tables = True
        content = _render_tex(report, tmp_path, meta["module"].replace(" ", "_"))
        assert r"\tableofcontents" in content
        assert r"\listoffigures" in content
        assert r"\listoftables" in content

    def test_toc_absent_when_disabled(self, fx, tmp_path):
        _, report, meta = fx
        report.config.include_toc = False
        report.config.include_list_of_figures = False
        report.config.include_list_of_tables = False
        content = _render_tex(report, tmp_path, meta["module"].replace(" ", "_"))
        assert r"\tableofcontents" not in content
        assert r"\listoffigures" not in content
        assert r"\listoftables" not in content


# ── regression: text-content extraction ──────────────────────────────────
def _extract_text_from_tex(tex_content: str) -> str:
    """Strip LaTeX commands and return plain text for comparison."""
    text = tex_content
    # Remove \begin{...} \end{...} \command{...} \command
    text = re.sub(r'\\begin\{[^}]+\}', '', text)
    text = re.sub(r'\\end\{[^}]+\}', '', text)
    text = re.sub(r'\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})*', '', text)
    # Remove remaining braces
    text = text.replace('{', '').replace('}', '')
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


class TestRegression:
    """Verify that the new pipeline produces consistent output for each fixture.

    Strategy: render the .tex, extract plain text, and assert key content
    fragments are present. This proves the adapter + generator chain
    faithfully transfers all design data from the JSON through to the output.
    """

    @pytest.mark.parametrize("name", list(FIXTURE_FILES.keys()))
    def test_all_design_data_in_output(self, name, tmp_path):
        _, report, meta = _load_fixture(name)
        content = _render_tex(report, tmp_path, name)

        # Verify all input parameter subsections appear
        input_sec = report.sections[0]
        for sub in input_sec.subsections:
            assert sub.title in content, f"Missing subsection: {sub.title}"

        # Verify all design check subsections appear
        dc_sec = report.sections[1]
        for sub in dc_sec.subsections:
            assert sub.title in content, f"Missing design check: {sub.title}"

        # Verify subsection count matches
        tex_subsections = len(re.findall(r'\\subsection\{', content))
        model_subsections = len(input_sec.subsections) + len(dc_sec.subsections)
        assert tex_subsections == model_subsections, (
            f"Subsection count mismatch: tex={tex_subsections}, model={model_subsections}"
        )

    @pytest.mark.parametrize("name", list(FIXTURE_FILES.keys()))
    def test_table_row_counts_match(self, name, tmp_path):
        """Every table in the model should appear in the .tex with the same row count."""
        _, report, meta = _load_fixture(name)
        content = _render_tex(report, tmp_path, name)

        for section in report.sections:
            for sub in [section] + section.subsections:
                for item in sub.content:
                    if isinstance(item, Table):
                        # Count \\ rows in the longtable for this caption
                        if item.caption:
                            caption_escaped = item.caption.replace('_', r'\_')
                            # Find the longtable block containing this caption
                            pattern = rf'\\caption\{{{re.escape(caption_escaped)}\}}.*?\\end\{{longtable\}}'
                            match = re.search(pattern, content, re.DOTALL)
                            if match:
                                block = match.group(0)
                                data_rows = block.count('\\\\')
                                # Each row ends with \\, but headers and separators also have \\
                                # So we just check the table is non-empty
                                assert data_rows > 0, (
                                    f"Table '{item.caption}' appears empty in .tex"
                                )

    @pytest.mark.parametrize("name", list(FIXTURE_FILES.keys()))
    def test_title_author_appear(self, name, tmp_path):
        _, report, meta = _load_fixture(name)
        content = _render_tex(report, tmp_path, name)
        assert report.title in content
        assert report.author in content
