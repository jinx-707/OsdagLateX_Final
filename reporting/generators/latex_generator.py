"""Assemble a Report object into a full LaTeX document."""

import logging
import os

from jinja2 import Environment, FileSystemLoader
from reporting.models.report import Report, ReportConfig
from reporting.models.section import Section
from reporting.models.table import Table
from reporting.models.figure import Figure
from reporting.generators.table_generator import generate_table_latex
from reporting.generators.figure_generator import generate_figure_latex
from reporting.utils.escaping import escape_latex
from reporting.config import STYLE_REGISTRY, DEFAULT_TEMPLATE_FALLBACK, DEFAULT_DATE

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates')
_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), keep_trailing_newline=True)


def render_section(section: Section, depth: int = 0) -> str:
    """
    Render a section (recursively) to LaTeX.

    Args:
        section: Section object.
        depth: Nested depth (unused but could be used for indentation).

    Returns:
        LaTeX string.
    """
    lines = []
    cmd = {1: "section", 2: "subsection", 3: "subsubsection"}.get(
        section.level, "section"
    )
    lines.append("\\" + cmd + "{" + escape_latex(section.title) + "}")
    lines.append("")

    for item in section.content:
        if isinstance(item, str):
            lines.append(escape_latex(item))
        elif isinstance(item, Table):
            lines.append(generate_table_latex(item))
        elif isinstance(item, Figure):
            lines.append(generate_figure_latex(item))
        else:
            raise TypeError(f"Unsupported content item: {type(item)}")
        lines.append("")

    for sub in section.subsections:
        lines.append(render_section(sub, depth + 1))

    return "\n".join(lines)


def render_report(report: Report, output_path: str) -> str:
    """
    Walk the Report model and generate a .tex file.

    Args:
        report: Report object.
        output_path: Path where .tex file will be written.

    Returns:
        Path to the written .tex file.
    """
    template_name = STYLE_REGISTRY.get(report.config.style, DEFAULT_TEMPLATE_FALLBACK)
    template = _env.get_template(template_name)

    sections_tex = "\n".join(render_section(s) for s in report.sections)

    context = {
        "title": "{" + escape_latex(report.title) + "}",
        "subtitle": "{" + escape_latex(report.subtitle) + "}" if report.subtitle else "",
        "author": "{" + escape_latex(report.author) + "}",
        "date": "{" + (report.date or DEFAULT_DATE) + "}",
        "include_toc": report.config.include_toc,
        "include_lof": report.config.include_list_of_figures,
        "include_lot": report.config.include_list_of_tables,
        "sections": sections_tex,
    }

    tex_content = template.render(**context)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(tex_content)

    logger.info("LaTeX source written to %s (%d bytes)", output_path, len(tex_content))
    return output_path
