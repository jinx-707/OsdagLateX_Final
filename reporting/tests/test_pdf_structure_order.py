"""PDF structure regression test: floats must never drift out of section order.

Background
----------
A real bug was found by manually reading a compiled PDF built from Osdag's
``bc_ep_2.osi`` data: tables and figures declared inside a section were
typeset on pages *after* the following section's heading, because LaTeX is
free to reflow ``[h]`` floats to the top of later pages.  The fix was to
emit ``\\FloatBarrier`` (``placeins`` package) after every section's content
in ``latex_generator.render_section``.

This test locks that fix in.  It compiles a known fixture to a real PDF,
extracts per-page text, and asserts:

1. Every section heading appears on an equal-or-earlier page than every
   content item (table/figure caption) declared inside it (recursively).
2. Headings appear in non-decreasing page order across the whole document.
3. No content item may appear on a LATER page than the next heading that
   follows it in document order - i.e. a section's floats may never leak
   into a later section.

If a float drifts past the next heading, the test fails loudly and names
the offending item and pages.
"""

import os
import shutil

import pytest

from reporting.cli import load_report_from_json
from reporting.generators.latex_generator import render_report
from reporting.compiler.latex_compiler import compile_latex

pytestmark = pytest.mark.requires_latex

requires_pdflatex = pytest.mark.skipif(
    shutil.which("pdflatex") is None,
    reason="pdflatex not on PATH - install a LaTeX distribution to run this test",
)

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "..")
FIXTURE = os.path.join(FIXTURES, "real_beam_column_report.json")


def _norm(text: str) -> str:
    """Collapse whitespace and unify underscores so line wraps and pypdf's
    underscore-as-space quirk don't break matching."""
    return " ".join(text.replace("_", " ").split())


def _page_texts(pdf_path: str):
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    return [_norm(page.extract_text() or "") for page in reader.pages]


def _last_page_with(pages, needle: str):
    """1-based page number of the LAST occurrence of needle.

    The last occurrence skips the front matter (ToC / LoF / LoT repeat every
    heading and caption on early pages); the real body occurrence always
    comes later.
    """
    needle = _norm(needle)
    hits = [i + 1 for i, text in enumerate(pages) if needle in text]
    return hits[-1] if hits else None


def _walk(report):
    """Yield ('heading', title) and ('caption', text) items in document order,
    flattened depth-first, annotated with their ancestor headings."""
    def visit(section, ancestors):
        entry = {"kind": "heading", "title": section.title.strip(),
                 "ancestors": list(ancestors)}
        yield entry
        for item in section.content:
            caption = getattr(item, "caption", None)
            if isinstance(item, str) or not caption:
                continue
            yield {"kind": "caption", "title": str(caption).strip(),
                   "ancestors": ancestors + [section.title.strip()]}
        for sub in section.subsections:
            yield from visit(sub, ancestors + [section.title.strip()])

    for sec in report.sections:
        yield from visit(sec, [])


@requires_pdflatex
def test_floats_stay_within_their_sections(tmp_path):
    report = load_report_from_json(FIXTURE)

    tex_path = str(tmp_path / "order_check.tex")
    render_report(report, tex_path)

    result = compile_latex(tex_path)
    assert result.success, (
        f"Fixture PDF failed to compile: {result.error_type}: "
        f"{result.error_message}"
    )

    pages = _page_texts(result.pdf_path)
    items = list(_walk(report))

    # Resolve every heading/caption to its real body page.
    located = []
    for item in items:
        page = _last_page_with(pages, item["title"])
        assert page is not None, (
            f"Could not find {item['kind']} '{item['title']}' anywhere in the "
            f"compiled PDF - the needle text or extraction is broken."
        )
        located.append((item, page))

    # Rule 1: a section's content may never appear before its own heading
    # (or before any ancestor heading).
    for item, page in located:
        if item["kind"] != "caption":
            continue
        for ancestor in item["ancestors"]:
            anc_page = _last_page_with(pages, ancestor)
            assert anc_page is not None, f"Ancestor heading '{ancestor}' not found in PDF"
            assert page >= anc_page, (
                f"Float drifted out of order: caption '{item['title']}' found "
                f"on page {page}, but its parent section '{ancestor}' heading "
                f"is on page {anc_page} - floats have drifted out of order. "
                f"Check that \\FloatBarrier is emitted after each section."
            )

    # Rule 2: headings must appear in non-decreasing page order.
    headings = [(it, pg) for it, pg in located if it["kind"] == "heading"]
    for (cur, cur_pg), (nxt, nxt_pg) in zip(headings, headings[1:]):
        assert nxt_pg >= cur_pg, (
            f"Section drift: heading '{nxt['title']}' found on page {nxt_pg}, "
            f"but the earlier heading '{cur['title']}' is on page {cur_pg}. "
            f"Document structure does not match source model order."
        )

    # Rule 3: a section's content may never land after the next heading
    # that follows it - that is exactly the float-drift bug this suite
    # exists to prevent.
    for idx, (item, page) in enumerate(located):
        if item["kind"] != "caption":
            continue
        following = located[idx + 1:]
        next_heading = next((pg for it, pg in following if it["kind"] == "heading"), None)
        if next_heading is None:
            continue  # last content in the document
        assert page <= next_heading, (
            f"Float drifted out of order: caption '{item['title']}' found on "
            f"page {page}, but the next section heading is already on page "
            f"{next_heading} - floats have drifted out of order. Check that "
            f"\\FloatBarrier is emitted after each section."
        )


@requires_pdflatex
def test_compiled_pdf_has_expected_section_sequence(tmp_path):
    """The exact ordering confirmed against the bc_ep_2-derived fixture."""
    report = load_report_from_json(FIXTURE)

    tex_path = str(tmp_path / "sequence_check.tex")
    render_report(report, tex_path)
    result = compile_latex(tex_path)
    assert result.success, f"{result.error_type}: {result.error_message}"

    pages = _page_texts(result.pdf_path)
    expected = ["Design Input", "Bolt Data", "Weld Data", "Design Checks",
                "Connection Details", "Design Summary"]
    seq = [_last_page_with(pages, t) for t in expected]
    assert all(p is not None for p in seq), f"Missing headings in PDF: {expected}"
    assert seq == sorted(seq), (
        f"Section sequence wrong: "
        f"{list(zip(expected, seq))} - expected ToC order preserved in body"
    )


# ── stress document ──────────────────────────────────────────────────────
# The fixture above is too short to force LaTeX to reflow floats even
# without barriers.  This synthetic document (6 sections x 35-row table +
# figure) is dense enough that an unbarriered [h] float queue overflows
# and drifts - it is what makes this regression test actually bite.

_STRESS_SECTIONS = 6
_STRESS_ROWS = 35

_STRESS_IMAGES = [
    "C:/Users/Saatvika Reddy/Osdag_Vault/Osdag/src/osdag/data/ResourceFiles/images/endplate.png",
    "C:/Users/Saatvika Reddy/Osdag_Vault/Osdag/src/osdag/data/ResourceFiles/images/extended.png",
]


def _build_stress_report():
    from reporting.models.report import Report, ReportConfig
    from reporting.models.section import Section
    from reporting.models.table import Table
    from reporting.models.figure import Figure

    sections = []
    for i in range(1, _STRESS_SECTIONS + 1):
        rows = [[f"Parameter {j}", f"{j * 3}.25 kN", f"{j * 3}.40 kN"]
                for j in range(1, _STRESS_ROWS + 1)]
        table = Table(
            headers=["Check", "Required", "Provided"],
            rows=rows,
            col_spec="lll",
            caption=f"Stress table for section {i}",
            label=f"tab:stress-{i}",
        )
        figure = Figure(
            path=_STRESS_IMAGES[i % 2],
            caption=f"Stress figure for section {i}",
            label=f"fig:stress-{i}",
        )
        sections.append(Section(
            title=f"Stress Section {i}",
            level=1,
            content=[
                f"Intro text for stress section {i} with filler prose long "
                "enough to occupy a line on the page and influence layout.",
                table,
                figure,
            ],
        ))
    return Report(
        title="Float Stress Report",
        author="Osdag",
        sections=sections,
        config=ReportConfig(include_toc=False, include_list_of_figures=False,
                            include_list_of_tables=False),
    )


@requires_pdflatex
def test_floats_stay_in_sections_under_page_pressure(tmp_path):
    """Dense document: every caption must land before the next heading."""
    report = _build_stress_report()

    tex_path = str(tmp_path / "stress_check.tex")
    render_report(report, tex_path)
    result = compile_latex(tex_path)
    assert result.success, f"{result.error_type}: {result.error_message}"

    pages = _page_texts(result.pdf_path)
    located = []
    for item in _walk(report):
        page = _last_page_with(pages, item["title"])
        assert page is not None, f"'{item['title']}' not found in compiled PDF"
        located.append((item, page))

    for idx, (item, page) in enumerate(located):
        if item["kind"] != "caption":
            continue
        next_heading = next(
            (pg for it, pg in located[idx + 1:] if it["kind"] == "heading"), None)
        if next_heading is None:
            continue
        assert page <= next_heading, (
            f"Float drifted out of order: caption '{item['title']}' found on "
            f"page {page}, but the next section heading is already on page "
            f"{next_heading} - floats have drifted out of order. Check that "
            f"\\FloatBarrier is emitted after each section."
        )
