# Before/After Comparison: Osdag LaTeX Report Generator

## Honesty Statement

This comparison documents structural and behavioral differences between the
**original monolithic `save_latex()` method** (`reportGenerator_latex.py`, 487 lines)
and the **refactored `reporting/` package** (10 source files, ~400 lines of generators/templates).

**What was available for comparison:**
- Full source code of the original `reportGenerator_latex.py` (read, analyzed, documented)
- The original Osdag data structures (`uiObj`, `Design_Check`, `reportsummary`)
- `docs/before_state.md` with deep structural analysis

**What was NOT available:**
- No legacy-generated PDFs exist in the workspace
- No legacy-generated .tex files exist (old code writes ephemeral ones via pylatex)
- `pylatex` is not installed, so the old code cannot be executed
- No side-by-side PDF comparison is therefore possible

The regression tests in `test_regression.py` verify the **new pipeline faithfully
transfers data** from JSON → Report → .tex. They are structural tests, not
comparative tests against legacy output.

---

## Structural Before/After

### Original (`reportGenerator_latex.py`)

| Aspect | Before |
|--------|--------|
| Lines of code | 487 (single method `save_latex()`) |
| Architecture | Monolithic: one method builds entire PDF |
| LaTeX generation | pylatex library (Document, Section, Tabularx, LongTable, etc.) |
| Error handling | `except: pass` — all errors silently swallowed |
| LaTeX escaping | None — `NoEscape()` used everywhere |
| Template | Hardcoded in Python (no separate .tex template) |
| Config | None — all options hardcoded |
| Testability | Untestable — requires GUI, pylatex, pdflatex, images |
| Connection types | 22+ modules call `save_latex()` with same monolithic code |
| Code duplication | Subsection+LongTable pattern repeated per module |

### Refactored (`reporting/` package)

| Aspect | After |
|--------|-------|
| Lines of code | ~400 (generators + templates combined) |
| Architecture | Layered: models → generators → templates → compiler |
| LaTeX generation | Jinja2 templates + raw .tex string building |
| Error handling | Structured `CompileResult` with `CompileErrorType` enum |
| LaTeX escaping | Two-pass `escape_latex()` for all 10 special characters |
| Template | Separate `base.tex` Jinja2 template |
| Config | `ReportConfig` dataclass + `STYLE_REGISTRY` dict |
| Testability | 80 unit/integration/regression tests, no GUI needed |
| Connection types | Adapter pattern: `osdag_adapter.py` handles any connection type |
| Code duplication | Shared `generate_table_latex()` / `generate_figure_latex()` |

---

## Code Complexity Comparison

### Original: Key Patterns

The original `save_latex()` had these duplicated patterns:

1. **Input Parameters section** (~80 lines): Iterate `uiObj`, handle `"TITLE"` sentinels,
   render sub-dicts as section details with images, handle long strings >55 chars.

2. **Design Checks section** (~60 lines): Iterate `Design_Check`, handle `'SubSection'`,
   `'NewTable'`, `'Selected'` tuples, render rows with Pass/Fail color coding.

3. **3D Views section** (~30 lines): Hardcoded 4-view grid with image existence checks.

4. **Design Log section** (~20 lines): Color-coded log levels from `reportsummary`.

Each of these patterns was essentially copy-pasted across 22+ connection modules.

### Refactored: Shared Components

| Component | Lines | Used by |
|-----------|-------|---------|
| `generators/table_generator.py` | 86 | All table rendering (was duplicated 22+ times) |
| `generators/figure_generator.py` | 36 | All figure rendering (was duplicated) |
| `generators/latex_generator.py` | 89 | All section/document rendering |
| `templates/base.tex` | 48 | Document structure (was hardcoded in Python) |
| `adapters/osdag_adapter.py` | 224 | All connection types (was per-module) |

**Total shared code:** ~483 lines replacing ~487 × 22+ copies.

---

## Bug Fixes Made During Refactor

These are intentional differences from the old behavior:

1. **LaTeX escaping added**: Old code used `NoEscape()` for all text, meaning special
   characters (`\ & % $ # _ { } ~ ^`) would break compilation. New code escapes all
   text through `escape_latex()`.

2. **Error handling**: Old code had `except: pass` blocks that silently swallowed
   compilation errors, missing images, and other failures. New code raises exceptions
   and returns structured `CompileResult` objects.

3. **Figure validation**: New code raises `FileNotFoundError` when an image path
   doesn't exist, before attempting compilation. Old code would silently skip or
   pass a broken path to pylatex.

4. **Compiler error classification**: New code classifies compilation failures into
   6 categories (`COMPILER_NOT_FOUND`, `MISSING_PACKAGE`, `MISSING_IMAGE`,
   `SYNTAX_ERROR`, `TIMEOUT`, `UNKNOWN`). Old code showed a generic "Latex Creation
   Error" dialog for all failures.

---

## Concrete Artifact: New Pipeline Output

A sample `.tex` file was generated from `bc_end_plate_real.json` using the new pipeline:

**Output:** `C:\Users\SAATVI~1\AppData\Local\Temp\opencode\new_pipeline_output.tex`

### Document structure produced by new pipeline:

```latex
\documentclass[12pt]{article}
\usepackage{geometry}
\geometry{a4paper, margin=1in}
\usepackage{graphicx}
\usepackage{longtable}
\usepackage{tabularx}
\usepackage{multirow}
\usepackage{colortbl}
\usepackage{hyperref}
\definecolor{OsdagGreen}{RGB}{0,128,0}
...
\title{\textbf{{ Beam-to-Column End Plate Connection Design Report }}}
\author{{ Engineer }}
\date{{ \today }}
\begin{document}
\maketitle
\tableofcontents
\newpage
\listoftables
\newpage
\section{Input Parameters}
... (6 subsections with longtable input tables)
\section{Design Checks}
... (9 subsections with design check tables)
\end{document}
```

### What the old `save_latex()` would have produced (reconstructed from code analysis):

The old code used pylatex to build a `Document` object. The equivalent .tex
would have included the same sections but with these differences:

```latex
% OLD: pylatex-generated preamble (reconstructed)
\documentclass{article}
\usepackage[margin=1.0in]{geometry}
\usepackage{graphicx}
\usepackage{longtable}
\usepackage{tabularx}
\usepackage{colortbl}
% ... (no hyperref, no multirow in old code)
% OLD: Custom colors defined differently
\definecolor{OsdagGreen}{RGB}{0,128,0}
\definecolor{PassColor}{RGB}{0,128,0}
\definecolor{FailColor}{RGB}{255,0,0}
\definecolor{Red}{RGB}{255,0,0}
\definecolor{Green}{RGB}{0,128,0}
% OLD: No \title/\author/\date — header built manually via Tabularx
\begin{document}
% OLD: Page header with company logo + Osdag header (hardcoded Tabularx)
% OLD: \section{Input Parameters} — same structure
% OLD: \section{Design Checks} — same structure
% OLD: \section{2D Drawings} — module-specific, NOT in new pipeline
% OLD: \section{3D Views} — hardcoded 4-view grid, NOT in new pipeline
% OLD: \section{Design Log} — from reportsummary, NOT in new pipeline
\end{document}
```

### Key differences (text diff summary):

| Aspect | Old (save_latex) | New (reporting/) |
|--------|-----------------|-------------------|
| Preamble | pylatex-managed, no `hyperref`/`multirow` | Explicit in template, includes all needed packages |
| Title | Hardcoded Tabularx header with logo | `\title{}` + `\maketitle` |
| Colors | 5 colors (OsdagGreen, PassColor, FailColor, Red, Green) | 3 colors (OsdagGreen, OsdagRed, OsdagBlue) |
| Escaping | None (`NoEscape` everywhere) | All text through `escape_latex()` |
| 2D/3D sections | Present (module-specific) | Not included (out of scope for core model) |
| Design Log | Present (from reportsummary) | Not included (out of scope for core model) |
| Sections | 5 fixed sections | Model-driven (Input + Design Checks) |
| Tables | pylatex LongTable/Tabularx | Raw `\begin{longtable}` via Jinja2 |

**Note:** The 2D Drawings, 3D Views, and Design Log sections were intentionally
omitted from the new pipeline's core model. They can be added via the `Figure`
model and string content when needed, but were not part of the core structural
report refactoring scope.
