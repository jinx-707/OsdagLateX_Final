"""Assemble a Report object into a full LaTeX document."""

import os
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from reporting.models.report import Report, ReportConfig
from reporting.models.section import Section
from reporting.models.table import Table
from reporting.models.figure import Figure
from reporting.generators.table_generator import generate_table_latex
from reporting.generators.figure_generator import generate_figure_latex
from reporting.utils.escaping import escape_latex
from reporting.config import (
    STYLE_REGISTRY,
    DEFAULT_TEMPLATE_FALLBACK,
    DEFAULT_DATE,
    REPORT_DISCLAIMER,
)

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates')
_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), keep_trailing_newline=True)


def render_section(section: Section) -> str:
    """
    Render a section (recursively) to LaTeX.

    Args:
        section: Section object.

    Returns:
        LaTeX string.
    """
    lines = []
    # Optional forced page break (e.g. Design Summary starts on its own page)
    if section.force_page_break_before:
        lines.append("\\clearpage")
    # Section command
    if section.level == 1:
        cmd = "section"
    elif section.level == 2:
        cmd = "subsection"
    else:
        cmd = "subsubsection"
    lines.append(f"\\{cmd}{{{escape_latex(section.title)}}}")
    lines.append("")

    # Render content
    for item in section.content:
        if isinstance(item, str):
            lines.append(escape_latex(item) + "\\\\")
        elif isinstance(item, Table):
            lines.append(generate_table_latex(item))
        elif isinstance(item, Figure):
            lines.append(generate_figure_latex(item))
        else:
            raise TypeError(f"Unsupported content item: {type(item)}")
        lines.append("")

    # Force floats to stay in this section
    lines.append("\\FloatBarrier")
    lines.append("")

    # Render subsections
    for sub in section.subsections:
        lines.append(render_section(sub))

    return "\n".join(lines)


def render_report(report: Report, output_path: str) -> str:
    """
    Walk the Report model and generate a .tex file.

    Args:
        report: Report object.
        output_path: Path where .tex file will be written.

    Returns:
        Path to the written .tex file.

    Raises:
        ValueError: If required fields missing (title/author).
    """
    # Select the template for this style (base.tex / compact.tex / ...)
    template_name = STYLE_REGISTRY.get(report.config.style, DEFAULT_TEMPLATE_FALLBACK)
    template = _env.get_template(template_name)

    # Render all sections
    sections_tex = "\n".join(render_section(s) for s in report.sections)

    # Build context for template
    context = {
        "title": "{" + escape_latex(report.title) + "}",
        "subtitle": "{" + escape_latex(report.subtitle) + "}" if report.subtitle else "",
        "author": "{" + escape_latex(report.author) + "}",
        "date": "{" + (report.date or DEFAULT_DATE) + "}",
        "module_name": escape_latex(report.module_name) if report.module_name else "",
        "report_id": escape_latex(report.report_id) if report.report_id else "",
        "disclaimer": REPORT_DISCLAIMER,
        "include_toc": report.config.include_toc,
        "include_lof": report.config.include_list_of_figures,
        "include_lot": report.config.include_list_of_tables,
        "sections": sections_tex,
    }

    # Render full document
    tex_content = template.render(**context)

    # Write to file (creating the output directory if needed)
    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(tex_content)

    logger.info(f"LaTeX source written to {output_path} ({len(tex_content)} bytes)")
    return output_path
