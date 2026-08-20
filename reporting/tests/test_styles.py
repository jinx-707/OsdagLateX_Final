"""Style integration tests: render the same Report through multiple styles."""

import pytest

from reporting.models.report import Report, ReportConfig
from reporting.models.section import Section
from reporting.models.table import Table
from reporting.generators.latex_generator import render_report


def _sample_report(style="default"):
    """Build a minimal but realistic Report for style testing."""
    table = Table(
        headers=["Parameter", "Value"],
        rows=[["Yield Strength", "250 MPa"], ["Ultimate Strength", "410 MPa"]],
        col_spec="l|l",
        use_longtable=True,
        header_color="OsdagGreen",
        caption="Material Properties",
        label="tab:material",
    )
    section = Section(
        title="Input Parameters",
        level=1,
        content=["Grade: E250", table],
        subsections=[
            Section(title="Beam Section", level=2, content=["ISMB 350"])
        ],
    )
    checks = Section(
        title="Design Checks",
        level=1,
        content=[],
        subsections=[
            Section(
                title="Bending Strength",
                level=2,
                content=["M_d = 150.2 kN-m > M_a = 120.0 kN-m => Pass"],
            )
        ],
    )
    return Report(
        title="Test Connection Design Report",
        author="Test Engineer",
        sections=[section, checks],
        config=ReportConfig(
            style=style,
            include_toc=True,
            include_list_of_figures=False,
            include_list_of_tables=True,
        ),
        subtitle="Structural Engineering",
    )


class TestStyleRendering:
    """Both styles must produce valid, compilable .tex from the same Report."""

    @pytest.mark.parametrize("style", ["default", "compact"])
    def test_produces_valid_tex(self, style, tmp_path):
        report = _sample_report(style=style)
        out = str(tmp_path / f"test_{style}.tex")
        render_report(report, out)

        with open(out, "r", encoding="utf-8") as f:
            content = f.read()

        assert r"\begin{document}" in content
        assert r"\end{document}" in content
        assert "Test Connection Design Report" in content
        assert "Test Engineer" in content

    def test_default_has_maketitle(self, tmp_path):
        report = _sample_report(style="default")
        out = str(tmp_path / "default.tex")
        render_report(report, out)
        with open(out, "r", encoding="utf-8") as f:
            content = f.read()
        assert r"\maketitle" in content

    def test_compact_has_no_maketitle(self, tmp_path):
        report = _sample_report(style="compact")
        out = str(tmp_path / "compact.tex")
        render_report(report, out)
        with open(out, "r", encoding="utf-8") as f:
            content = f.read()
        assert r"\maketitle" not in content
        assert r"\begin{center}" in content

    def test_different_margins(self, tmp_path):
        default_report = _sample_report(style="default")
        compact_report = _sample_report(style="compact")

        d_out = str(tmp_path / "default.tex")
        c_out = str(tmp_path / "compact.tex")
        render_report(default_report, d_out)
        render_report(compact_report, c_out)

        with open(d_out, "r", encoding="utf-8") as f:
            d_content = f.read()
        with open(c_out, "r", encoding="utf-8") as f:
            c_content = f.read()

        assert "margin=1in" in d_content
        assert "margin=0.75in" in c_content

    def test_both_preserve_sections(self, tmp_path):
        for style in ["default", "compact"]:
            report = _sample_report(style=style)
            out = str(tmp_path / f"sections_{style}.tex")
            render_report(report, out)
            with open(out, "r", encoding="utf-8") as f:
                content = f.read()
            assert r"\section{Input Parameters}" in content
            assert r"\subsection{Beam Section}" in content
            assert r"\section{Design Checks}" in content
            assert r"\subsection{Bending Strength}" in content

    def test_both_preserve_tables(self, tmp_path):
        for style in ["default", "compact"]:
            report = _sample_report(style=style)
            out = str(tmp_path / f"tables_{style}.tex")
            render_report(report, out)
            with open(out, "r", encoding="utf-8") as f:
                content = f.read()
            assert r"\begin{longtable}" in content
            assert "Yield Strength" in content
            assert "250 MPa" in content
