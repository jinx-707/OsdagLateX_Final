"""Regenerate + verify polish PDFs: 3 modules x 2 styles."""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from reporting.cli import load_report_from_json
from reporting.generators.latex_generator import render_report
from reporting.compiler.latex_compiler import compile_latex

MODULES = {
    "beam_column": os.path.join(".", "real_beam_column_report.json"),
    "base_plate": os.path.join("reporting", "tests", "fixtures", "base_plate_real.json"),
    "fin_plate": os.path.join("reporting", "tests", "fixtures", "fin_plate_real.json"),
}
STYLES = ["default", "compact"]
OUT = os.path.join(".", "out", "polish")

failures = []

for mod, path in MODULES.items():
    for style in STYLES:
        report = load_report_from_json(path)
        report.config.style = style
        tex_path = os.path.join(OUT, f"{mod}_{style}.tex")
        render_report(report, tex_path)

        with open(tex_path, encoding="utf-8") as f:
            tex = f.read()

        # --- .tex structural checks ---
        checks = {
            "metadata Report ID row": r"\textbf{Report ID:}" in tex,
            "metadata Generated row": r"\textbf{Generated:}" in tex,
            "status coloring used": (r"\cellcolor{passgreen}" in tex
                                     or r"\cellcolor{failred}" in tex),
            "fancyfoot disclaimer cmd": r"\fancyfoot[L]" in tex,
            "no raw None literal": "None" not in tex,
        }
        if mod == "beam_column":
            checks["clearpage before Design Summary"] = (
                "\\clearpage\n\\section{Design Summary}" in tex
            )

        result = compile_latex(tex_path)
        checks["pdf compiled"] = bool(result.success)

        if result.success:
            from pypdf import PdfReader
            reader = PdfReader(result.pdf_path)
            pages = [(p.extract_text() or "") for p in reader.pages]
            norm = lambda s: " ".join(s.split())
            pages_n = [norm(p) for p in pages]

            checks["page1 has metadata"] = (
                "Report ID:" in pages_n[0]
                and "OSDAG-" in pages_n[0]
                and "Generated:" in pages_n[0]
            )
            footer_needle = "design guidance only"
            if style == "default":
                checks["footer absent on title page"] = footer_needle not in pages_n[0]
                checks["footer present on later pages"] = all(
                    footer_needle in pg for pg in pages_n[1:]
                )
            else:
                checks["footer present all pages (compact)"] = all(
                    footer_needle in pg for pg in pages_n
                )

            if mod == "beam_column":
                ds_pages = [i for i, pg in enumerate(pages_n) if "Design Summary" in pg]
                last_ds = ds_pages[-1] if ds_pages else None
                conn_caption = next(
                    (c.caption for sec in report.sections
                     if sec.title == "Connection Details"
                     for c in sec.content if getattr(c, "caption", None)),
                    None,
                )
                if conn_caption and last_ds is not None:
                    leaked = norm(conn_caption).replace("_", " ") in pages_n[last_ds]
                    checks["Design Summary page free of upstream floats"] = not leaked

        bad = [k for k, v in checks.items() if not v]
        status = "OK " if not bad and result.success else "FAIL"
        print(f"[{status}] {mod:11s} {style:8s} pdf={result.pdf_path and os.path.basename(result.pdf_path)}")
        if bad:
            failures.append((mod, style, bad))
            for b in bad:
                print(f"         !! {b}")

print()
if failures:
    print(f"{len(failures)} verification failure(s)")
    sys.exit(1)
print("All verifications passed.")
