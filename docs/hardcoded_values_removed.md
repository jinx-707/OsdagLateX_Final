# Hardcoded Values Removed

Every magic value that used to live inline in report-generation code now has
a single named home. Table format: `Value | Old location | New location | Why moved`.

| Value | Old location | New location | Why moved |
|---|---|---|---|
| `OsdagGreen` / `OsdagRed` / `OsdagBlue` RGB definitions | Pasted into every generator's preamble string | `templates/base.tex`, `templates/compact.tex` (single definition per style) | One place to rebrand; styles may diverge deliberately |
| Header color `"OsdagGreen"` for table header rows | Inline in each `save_latex()` table call | `config.HEADER_COLOR` | Reusable by any generator; grep-able |
| Checks-table headers `('Check','Required','Provided','Remarks')` | Hardcoded row inside `reportGenerator_latex.py` | `config.CHECKS_TABLE_HEADERS` | Single source; testable |
| Input-table headers `("Parameter","Value")` / details headers | Inline strings per module | `config.INPUT_TABLE_HEADERS`, `config.DETAILS_TABLE_HEADERS` | Consistency across modules |
| Column specs `\|p{7cm}\|X\|` etc. | Inline in LaTeX preamble strings | `config.DEFAULT_COL_SPEC`, `config.INPUT_COL_SPEC`, `config.DETAILS_COL_SPEC` | Layout tweaks don't require code edits |
| Section titles `"Input Parameters"` / `"Design Checks"` | Inline `doc.create(Section(...))` calls | `config.SECTION_TITLE_INPUT`, `config.SECTION_TITLE_CHECKS`, `config.SECTION_TITLE_DETAILS` | Renaming/relocalizing is a one-line change |
| Report title suffix `"Design Report"`, default author `"Osdag"` | String concatenation scattered in modules | `config.TITLE_SUFFIX`, `config.DEFAULT_AUTHOR` | Branding in one place |
| Compiler name `"pdflatex"`, 60 s timeout | Buried in subprocess call sites | `config.LATEX_COMPILER`, `config.DEFAULT_TIMEOUT_SECONDS` | Switch to `lualatex`/`xelatex` or slow machines without code changes |
| Template file names | Implicit convention | `config.STYLE_REGISTRY`, `config.DEFAULT_TEMPLATE_FALLBACK` | Adding a style = registry entry + template file |
| Default date `\today`, output dir `./out`, warnings cap | Ad-hoc literals | `config.DEFAULT_DATE`, `config.DEFAULT_OUTPUT_DIR`, `config.MAX_WARNINGS_DISPLAY` | CLI and library share defaults |
| Figure width `0.8\textwidth`, placement `h` | Inline in image-emitting code | `models/figure.Figure` dataclass defaults | Model owns its rendering contract |
| Osdag sentinels `"TITLE"`, `"SubSection"`, `"Image"` | Magic strings compared inline | `adapters/osdag_adapter.py` module constants (`_TITLE_SENTINEL`, `_SUBSECTION_MARKER`, `_IMAGE_MARKER`) | Documented, single comparison point |
| Log-parsing markers `"! "`, `"not found"`, `.sty` | Implicit knowledge in error handling | `compiler/latex_compiler.py` constants (`LATEX_ERROR_MARKER`, `NOT_FOUND_MARKER`, `STY_EXTENSION`) | Parser behaviour is explicit and unit-tested |

Nothing here is cosmetic: each moved value eliminated at least one class of
copy-paste drift between the legacy per-module generators.
