# Hardcoded Values Removed — Refactor Log

**Summary:** 22 hardcoded values were found and centralized into `config.py` (15 cross-module
constants) and `compiler/latex_compiler.py` (4 log-parsing constants). All 85 tests pass with
no observable output changes. No test expected values needed to change.

**Deliberately left as-is:**
- Model defaults in `table.py`, `figure.py`, `section.py`, `report.py` — these are dataclass
  field defaults, not scattered literals. They live in one place already.
- LaTeX syntax strings in `table_generator.py` and `figure_generator.py` (e.g. `\begin{longtable}`,
  `\hline`, `\centering`) — these are LaTeX commands, not configurable values.
- Template-specific values in `base.tex` and `compact.tex` (margins, font sizes, colors) — these
  differ by design between templates and are not shared values.
- The escaping character mapping in `utils/escaping.py` — a single constant list, inherently fixed.
- `CompileErrorType` enum members — inherently constant.
- JSON key names in `cli.py` (e.g. `'uiObj'`, `'design_check'`, `'title'`) — these match the
  external data format and cannot be changed without breaking compatibility.
- Model-level defaults in `cli.py:_build_section()` (`'l'`, `r"0.8\textwidth"`, `'h'`) — these
  match the model dataclass defaults and serve as JSON-parsing fallbacks.

---

## Changes Log

| # | Value | Old location | New location | Why moved |
|---|-------|-------------|-------------|-----------|
| 1 | `"default"` (style name) | `cli.py:152`, `cli.py:93` | `config.DEFAULT_STYLE` | Used in 2 places; must match `ReportConfig` default |
| 2 | `"./out"` (output dir) | `cli.py:151` | `config.DEFAULT_OUTPUT_DIR` | CLI default should be a named constant |
| 3 | `5` (max warnings) | `cli.py:192` | `config.MAX_WARNINGS_DISPLAY` | Magic number → named constant |
| 4 | `60` (timeout seconds) | `latex_compiler.py:33` | `config.DEFAULT_TIMEOUT_SECONDS` | Used as function default; should be configurable |
| 5 | `"pdflatex"` (binary) | `latex_compiler.py:44,61` | `config.LATEX_COMPILER` | Used in 2 places; must stay consistent |
| 6 | `"base.tex"` (fallback) | `latex_generator.py:68` | `config.DEFAULT_TEMPLATE_FALLBACK` | Fallback when style not in registry |
| 7 | `r"\today"` (default date) | `latex_generator.py:77` | `config.DEFAULT_DATE` | LaTeX command used as default; should be named |
| 8 | `"Osdag"` (default author) | `osdag_adapter.py:45,48,49` | `config.DEFAULT_AUTHOR` | Used in 3 places; must stay consistent |
| 9 | `"Design Report"` (title suffix) | `osdag_adapter.py:45` | `config.TITLE_SUFFIX` | Part of title construction; should be named |
| 10 | `"OsdagGreen"` (header color) | `osdag_adapter.py:159,212` | `config.HEADER_COLOR` | Used in 2 places; must match LaTeX color name |
| 11 | `"l"` (default col spec) | `osdag_adapter.py:170` | `config.DEFAULT_COL_SPEC` | Fallback column alignment |
| 12 | `"p{7cm}\|X"` (input col spec) | `osdag_adapter.py:137` | `config.INPUT_COL_SPEC` | Table layout constant |
| 13 | `"p{5cm}\|X"` (details col spec) | `osdag_adapter.py:157` | `config.DETAILS_COL_SPEC` | Table layout constant |
| 14 | `["Parameter", "Value"]` | `osdag_adapter.py:135` | `config.INPUT_TABLE_HEADERS` | Table headers |
| 15 | `["Property", "Value"]` | `osdag_adapter.py:155` | `config.DETAILS_TABLE_HEADERS` | Table headers |
| 16 | `["Check", "Required", "Provided", "Remarks"]` | `osdag_adapter.py:208` | `config.CHECKS_TABLE_HEADERS` | Table headers |
| 17 | `"Input Parameters"` | `osdag_adapter.py:76,139` | `config.SECTION_TITLE_INPUT` | Section title used in 2 places |
| 18 | `"Design Checks"` | `osdag_adapter.py:167` | `config.SECTION_TITLE_CHECKS` | Section title |
| 19 | `"! "` (error marker) | `latex_compiler.py:86` | `compiler.latex_compiler.LATEX_ERROR_MARKER` | Log-parsing constant |
| 20 | `"warning"` (warning marker) | `latex_compiler.py:88` | `compiler.latex_compiler.LATEX_WARNING_MARKER` | Log-parsing constant |
| 21 | `"not found"` (error marker) | `latex_compiler.py:111` | `compiler.latex_compiler.NOT_FOUND_MARKER` | Log-parsing constant |
| 22 | `".sty"` (extension) | `latex_compiler.py:112` | `compiler.latex_compiler.STY_EXTENSION` | Log-parsing constant |

### Adapter sentinel strings (already centralized before this refactor)

These were already defined as module-level constants at the top of `osdag_adapter.py` and used
consistently — no change needed:

| Value | Constant | Status |
|-------|----------|--------|
| `"TITLE"` | `_TITLE_SENTINEL` | Already correct |
| `"SubSection"` | `_SUBSECTION_MARKER` | **New:** extracted to module constant |
| `"Selected Section Details"` etc. | `_SKIP_KEYS` | Already correct |
| `"Section Profile"` | `_SECTION_PROFILE_KEY` | **New:** extracted to module constant |
| `"ProfileSummary"` | `_PROFILE_SUMMARY_KEY` | **New:** extracted to module constant |
| `"Designer"` | `_DESIGNER_KEY` | **New:** extracted to module constant |

### Test impact

No test expected values changed. All 85 tests pass identically before and after this refactor.
The tests assert on output content (section titles, table data, LaTeX commands), not on the
location of constant definitions.
