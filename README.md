
# Osdag LaTeX Report Generator

```
 .osi file ──▶ Adapter ──▶ Report Model ──▶ Generators ──▶ Templates ──▶ Compiler ──▶ PDF
 (Osdag data)   osdag_adapter   models/        generators/    jinja2 (.tex)   latex_compiler   pdflatex
                    │              ▲                              base.tex /
                    └── native JSON ┘                             compact.tex
```

A layered replacement for Osdag's per-module `save_latex()` report code.
One `Report` model serves every connection type; adapters translate Osdag's
raw `uiObj` / `Design_Check` data into that model; Jinja2 templates and a
structured compiler wrapper turn it into a PDF.

## Quickstart (5 minutes)

```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt      # jinja2, pytest, pypdf
venv\Scripts\python -m reporting.cli --input real_beam_column_report.json --output ./out
# -> out\Beam_Column_End_Plate_Connection_Design_Report.pdf
```

Requires a LaTeX distribution on PATH (TinyTeX recommended; on Windows also
`tlmgr install placeins`). To skip PDF compilation and only emit `.tex`:

```powershell
python -m reporting.cli --input sample_report.json --output ./out --tex-only
```

Other styles: add `--style compact`.

## What went wrong before (and how this fixes it)

The legacy generator (`design_report/reportGenerator_latex.py`, 487 lines)
built LaTeX strings inline, duplicated logic per module, and swallowed errors
with `except: pass`. Full narrative with the float-drift bug we caught in a
real compiled PDF: [docs/before_after_comparison.md](docs/before_after_comparison.md).

## Structured errors — actually triggered, not hypothetical

Each row below was produced by really running the trigger against
`reporting.compiler.latex_compiler.compile_latex()`:

| Trigger | Old behavior | New `CompileResult` |
|---|---|---|
| `pdflatex` not installed | Undefined behavior | `success=False, error_type=COMPILER_NOT_FOUND, error_message="definitely-not-a-real-latex-binary not found. Please install a LaTeX distribution."` |
| Missing `.sty` package | Cryptic pdflatex log, no user-facing message | `success=False, error_type=MISSING_PACKAGE, error_message="Required package 'definitely-not-a-real-sty-xyz.sty' not found."` |
| Missing image file | Silent crash / swallowed via `except: pass` | `success=False, error_type=MISSING_IMAGE, error_message="Figure at 'no_such_image_xyz.png' not found."` |

Note the missing-image case is subtle: in nonstopmode pdflatex *still writes a
PDF* after failing to find an image. The wrapper parses the log and reports
failure anyway, so a defective PDF is never presented as success.

## Extensibility proof: three connection types, zero adapter changes

| Connection type | Source | Fixture lines | Adapter changes |
|---|---|---|---|
| Beam-to-Column End Plate | `bc_ep_2.osi` | `reporting/tests/fixtures/bc_end_plate_real.json` | (initial build) |
| Base Plate | `baseplate_*.osi` | `reporting/tests/fixtures/base_plate_real.json` | 0 |
| Fin Plate | `fin1.osi` | `reporting/tests/fixtures/fin_plate_real.json` | **0** |

Fin Plate is structurally different — shear-only loads (no moment), pretensioned
bolts, no end-plate type, different check sequence (`Initial Section Check →
Load Consideration → Bolt Design → Section Design → Weld Design`) — yet it runs
through `osdag_adapter.build_report()` unmodified and is covered by the same
parameterized tests in `test_integration.py` and `test_regression.py`.
Adding it required one fixture file and one registry entry; no product code.

## Tests

```powershell
pytest reporting/tests -v --cov=reporting --cov-report=term-missing
```

128 tests. Pure-Python layers (models/generators/adapters/escaping) need no
LaTeX install — CI proves this by running them in a separate job without
TeXLive (`-m "not requires_latex"`). The full job additionally compiles real
PDFs and asserts float placement by extracting per-page text
(`test_pdf_structure_order.py`), so the section-ordering bug described above
can never silently return.

## Visual Polish

Reports now render with pass/fail status cells tinted green/red (opt-in per
table via a literal `Status` column header), a metadata block (module name,
report ID, generation date) under the title, a `\clearpage` before sections
flagged `force_page_break_before` (the Design Summary uses this), and a small
disclaimer footer on every content page (`config.REPORT_DISCLAIMER`, rendered
via `fancyhdr`; suppressed on the title page of the default style). Both the
`default` and `compact` templates support all four features.

Note: IS 800 clause references are **not** included — Osdag's calc engine
mentions clauses only inside source docstrings/comments; the design-check data
rows `(label, required, provided, status)` carry no clause field, so none are
cited rather than guessed.

## Known Limitations

- **No legacy-PDF diff comparison.** Running Osdag's original `save_latex()`
  for a side-by-side PDF comparison is blocked by circular imports in Osdag's
  internal modules (GUI-coupled). Instead, standalone `.tex` reconstruction
  from captured design data was used and verified for structural/data
  equivalence (see `docs/before_after_comparison.md`).
- **Cross-reference pass:** the compiler runs `pdflatex` once; documents with
  forward references may show "Label(s) may have changed" until a second run.
- **Windows short paths:** paths containing 8.3 components (`USER~1`) are
  expanded automatically before invoking pdflatex, but exotic TeX
  distributions that reject spaces may still need quoting at the shell level.
- **Adapter coverage:** the adapter handles the data shapes emitted by the
  traced modules (scalars, `TITLE` sentinels, section-detail dicts,
  `SubSection` tuples, 4-element check rows, `Image` tuples). Modules emitting
  other shapes would need small adapter extensions.

## Layout

```
reporting/
├── cli.py                  # argparse entry point (python -m reporting.cli)
├── config.py               # every previously-hardcoded value lives here
├── models/                 # Report / Section / Table / Figure dataclasses
├── adapters/osdag_adapter.py
├── generators/             # latex_generator, table_generator, figure_generator
├── compiler/latex_compiler.py   # structured CompileResult wrapper
├── utils/                  # escaping, formatting, paths
├── templates/              # base.tex, compact.tex (Jinja2)
└── tests/                  # 112 tests + real-data fixtures
```
