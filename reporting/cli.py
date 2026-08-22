"""Command-line interface for report generation.

Supports two JSON input formats:

1. Osdag format (auto-detected when ``uiObj`` key is present):
   { "uiObj": {...}, "design_check": [...], "reportsummary": {...} }

2. Native reporting format:
   { "title": "...", "author": "...", "sections": [...] }
"""

import argparse
import json
import logging
import sys
import os

from reporting.models.report import Report, ReportConfig
from reporting.models.section import Section
from reporting.models.table import Table
from reporting.models.figure import Figure
from reporting.generators.latex_generator import render_report
from reporting.compiler.latex_compiler import compile_latex
from reporting.config import STYLE_REGISTRY, DEFAULT_OUTPUT_DIR, DEFAULT_STYLE, MAX_WARNINGS_DISPLAY


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def validate_report(report: Report, output_dir: str):
    """Pre-flight validation. Returns list of error strings (empty = pass)."""
    errors = []
    if not report.title:
        errors.append("Report title is empty.")
    if not report.author:
        errors.append("Report author is empty.")
    if report.config.style not in STYLE_REGISTRY:
        errors.append(f"Style '{report.config.style}' not found in registry.")

    def check_figure_paths(section: Section):
        for item in section.content:
            if isinstance(item, Figure):
                if not os.path.isfile(item.path):
                    errors.append(f"Image file not found: {item.path}")
        for sub in section.subsections:
            check_figure_paths(sub)

    for sec in report.sections:
        check_figure_paths(sec)

    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            errors.append(f"Cannot create output directory: {e}")
    elif not os.access(output_dir, os.W_OK):
        errors.append(f"Output directory {output_dir} is not writable.")

    return errors


def load_report_from_json(json_path: str) -> Report:
    """Load a Report from a JSON file.

    Auto-detects Osdag format (has ``uiObj`` key) vs native format.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # --- Osdag format ---
    if 'uiObj' in data:
        from reporting.adapters.osdag_adapter import build_report
        return build_report(
            uiObj=data['uiObj'],
            design_check=data.get('design_check', []),
            reportsummary=data.get('reportsummary'),
            module_name=data.get('module', ''),
            title=data.get('title'),
            author=data.get('author'),
        )

    # --- Native reporting format ---
    config_data = data.get('config', {})
    config = ReportConfig(
        include_toc=config_data.get('include_toc', True),
        include_list_of_figures=config_data.get('include_list_of_figures', False),
        include_list_of_tables=config_data.get('include_list_of_tables', False),
        include_appendix=config_data.get('include_appendix', False),
        style=config_data.get('style', DEFAULT_STYLE),
    )

    sections = [_build_section(s) for s in data.get('sections', [])]

    return Report(
        title=data['title'],
        author=data['author'],
        sections=sections,
        config=config,
        subtitle=data.get('subtitle'),
        date=data.get('date'),
<<<<<<< HEAD
        module_name=data.get('module'),
        report_id=data.get('report_id'),
=======
>>>>>>> 6d9d68f21fde00f29096fb7fa4988f597ca8d967
    )


def _build_section(s_data: dict) -> Section:
    """Recursively build Section from dict."""
    content = []
    for item in s_data.get('content', []):
        if isinstance(item, str):
            content.append(item)
        elif isinstance(item, dict):
            if item.get('type') == 'table':
                content.append(Table(
                    headers=item['headers'],
                    rows=item['rows'],
                    col_spec=item.get('col_spec', 'l'),
                    use_longtable=item.get('use_longtable', False),
                    header_color=item.get('header_color'),
                    caption=item.get('caption', ''),
                    label=item.get('label', ''),
                ))
            elif item.get('type') == 'figure':
                content.append(Figure(
                    path=item['path'],
                    caption=item.get('caption', ''),
                    label=item.get('label', ''),
                    width=item.get('width', r"0.8\textwidth"),
                    placement=item.get('placement', 'h'),
                ))
            else:
                content.append(str(item))
        else:
            content.append(str(item))

    return Section(
        title=s_data['title'],
        level=s_data.get('level', 1),
        content=content,
        subsections=[_build_section(sub) for sub in s_data.get('subsections', [])],
<<<<<<< HEAD
        force_page_break_before=s_data.get('force_page_break_before', False),
=======
>>>>>>> 6d9d68f21fde00f29096fb7fa4988f597ca8d967
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate a LaTeX report from JSON input."
    )
    parser.add_argument('--input', required=True, help="JSON file with report data.")
    parser.add_argument('--output', default=DEFAULT_OUTPUT_DIR, help="Output directory for .tex and .pdf.")
    parser.add_argument('--style', default=DEFAULT_STYLE, help="Report style.")
    parser.add_argument('--tex-only', action='store_true',
                        help="Generate .tex only, skip PDF compilation.")
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        report = load_report_from_json(args.input)
        if args.style:
            report.config.style = args.style
    except Exception as e:
        logger.error(f"Failed to load input JSON: {e}")
        sys.exit(1)

    errors = validate_report(report, args.output)
    if errors:
        logger.error("Validation failed:")
        for err in errors:
            logger.error(f"  - {err}")
        sys.exit(1)

    tex_filename = f"{report.title.replace(' ', '_')}.tex"
    tex_path = os.path.join(args.output, tex_filename)
    try:
        render_report(report, tex_path)
        logger.info(f"LaTeX source written to {tex_path}")
    except Exception as e:
        logger.error(f"Failed to generate LaTeX: {e}")
        sys.exit(1)

    if args.tex_only:
        logger.info("Skipping PDF compilation (--tex-only).")
        sys.exit(0)

    result = compile_latex(tex_path)
    if result.success:
        logger.info(f"PDF generated successfully: {result.pdf_path}")
        if result.warnings:
            for w in result.warnings[:MAX_WARNINGS_DISPLAY]:
                logger.warning(f"  {w}")
        sys.exit(0)
    else:
        logger.error(
            f"Compilation failed: {result.error_message} "
            f"(type={result.error_type})"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
