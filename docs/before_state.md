# Before State: Osdag LaTeX Report Generation

## Recon Date: 2026-08-20 (Updated with deep analysis of actual codebase)

---

## 1. Input Parameters of `save_latex` (line 29)

**File:** `Osdag/src/osdag/design_report/reportGenerator_latex.py`

```python
def save_latex(self, uiObj, Design_Check, reportsummary, filename, rel_path,
               Disp_2d_image, Disp_3d_image, module=''):
```

| Parameter | Python Type | Source | Contains Actual Design Data? |
|---|---|---|---|
| `uiObj` | `dict` | `self.report_input` from each module's `save_design()` | **YES** — all input parameters (loads, section sizes, bolt details, plate dimensions). Keys are `KEY_DISP_*` display labels; values are strings/numbers or sub-dicts for section details. A `"TITLE"` sentinel value marks subsection breaks. |
| `Design_Check` | `list[tuple]` | `self.report_check` from each module's `save_design()` | **YES** — all calculation results, pass/fail flags, required/provided values. Each tuple is either a section control tuple `('SubSection', title, table_spec)` or a check row `(label, required, provided, 'Pass'/'Fail')`. The `provided` value can be a `pylatex.Math` equation object from `Report_functions.py`. |
| `reportsummary` | `dict` | `popup_summary` from the GUI summary dialog | **Metadata only** — `ProfileSummary` (CompanyName, CompanyLogo, Group/TeamName, Designer), ProjectTitle, Subtitle, JobNumber, Client, `does_design_exist` (bool), `logger_messages` (str). |
| `filename` | `str` | File dialog in summary popup | **No** — output file path (without `.pdf` extension). |
| `rel_path` | `str` | `sys.path[0]` with backslashes replaced | **No** — base path for resolving image files. |
| `Disp_2d_image` | `list[str]` | Module-specific | **Image paths** — list of 2D drawing filenames (e.g. weld details, detailing, stiffener details). |
| `Disp_3d_image` | `str` | Module-specific | **Image path** — single 3D view filename (e.g. `"/ResourceFiles/images/BasePlate.jpeg"`). |
| `module` | `str` | `self.module` | **Control flow** — module display name (e.g. `KEY_DISP_BCENDPLATE`). Drives conditional logic for which 2D drawings to render. |

**Key finding:** `uiObj` and `Design_Check` contain all the actual design-calculation data (numbers, units, pass/fail). The rest are metadata, paths, or control flags.

---

## 2. Report Structure — How Sections Are Created

The report is built as a single 487-line method using pylatex's `doc.create(Section(...))` context manager pattern. Sections are always the same regardless of `module`:

| Section # | Title | Created At (line) | Content |
|---|---|---|---|
| 1 | `Input Parameters` | Line 92 | LongTable iterating over `uiObj` dict. Handles sub-dicts (section details with images via MultiRow), "TITLE" sentinels (bold header rows), long text wrapping, and angle list subsections. |
| 2 | `Design Checks` | Line 209 | Tabularx with pass/fail status header, then iterates `Design_Check` list. Each `'SubSection'`/`'NewTable'`/`'Selected'` tuple opens a new subsection with a LongTable. Regular check tuples render as table rows with color-coded pass/fail. |
| 3 | `2D Drawings (Typical)` | Line 360/386 | **Conditional on module** — different image sets for BC End Plate vs Base Plate. Each image is a `Figure` with `add_image` + `add_caption`. |
| 4 | `3D Views` | Line 422/451 | Always present. 4-view grid (3D, top, side, front) in a Tabularx. Falls back to `broken.png` if no 3D image. |
| 5 | `Design Log` | Line 467 | Iterates `logger_messages` string, coloring each line by log level (WARNING=blue, INFO=green, ERROR=red). |

**Sections are always the same structure** — they do NOT depend on `module`. Only the 2D drawings section has module-dependent branching (line 353: `if module == KEY_DISP_BCENDPLATE` vs line 377: `elif module == KEY_DISP_BASE_PLATE`).

---

## 3. Tables — Where Headers, Rows, Captions Are Built

### Input Parameters Table (lines 93–196)
- **Format:** `LongTable('|p{5cm}|p{2.5cm}|p{1.5cm}|p{3cm}|p{3.5cm}|')` — 5 fixed-width columns
- **No headers** — the table is a key-value layout
- **Built inside a `for i in uiObj:` loop** — iterates every key in the dict
- Special handling for:
  - Sub-dicts (section details): renders with `StandAloneGraphic` image + `MultiRow` + `MultiColumn`
  - `"TITLE"` sentinel: renders bold section header spanning all columns
  - Long strings (>55 chars): splits across multiple rows
  - Angle lists: rendered in a separate `Tabularx` subsection below

### Design Checks Tables (lines 222–303)
- **Format:** Varies per subsection (passed as `check[2]` in the tuple, e.g. `'|p{4cm}|p{5cm}|p{5.5cm}|p{1.5cm}|'`)
- **Standard header row:** `('Check', 'Required', 'Provided', 'Remarks')` — hardcoded at line 230
- **Built inside `for check in Design_Check:` loop**
- Pass/fail coloring: `TextColor("Red", bold(check[3]))` for fail, `TextColor("OsdagGreen", bold(check[3]))` for pass

### 3D Views Table (lines 423–465)
- **Format:** `Tabularx(r'|>{\centering}X|>{\centering\arraybackslash}X|')` — 2 centered columns
- **No headers** — just images with labels like "(a) 3D View", "(b) Top View"

---

## 4. Figures — How Images Are Inserted

**2D Drawings** (lines 351–411):
- Module-dependent: BC End Plate gets 3 images (weld, detailing, stiffener), Base Plate gets 4-5 images (sketch, detailing, weld, anchor, optional shear key)
- Images use `Figure()` context manager with `add_image(path, width=NoEscape(r'0.7\textwidth'))` and `add_caption()`
- **No path validation** — if the file doesn't exist, pdflatex will fail at compile time
- All paths are constructed as `rel_path + Disp_2d_image[i]`

**3D Views** (lines 413–465):
- Uses `StandAloneGraphic` inside a `Tabularx` grid (not `Figure`)
- **No path validation** — falls back to `broken.png` if `Disp_3d_image` is empty, but doesn't check if `broken.png` exists
- Paths constructed as `rel_path + Disp_3d_image`

---

## 5. Special Characters — No Escaping Whatsoever

**There is NO call to `escape_latex()` or any similar function anywhere in the file.**

Searching for `escape` in the file:
- `NoEscape` is used extensively (lines 80, 125–126, 128, 154, 198, 206, 226, 238, 251, 298–302, 363, 368, 373, 388, 393, 398, 403, 409, 468) — but this is pylatex's `NoEscape` which does the **opposite** of escaping (it prevents pylatex from escaping the content)
- No `escape_latex` function exists
- No character replacement or escaping logic exists

**This means:** User-supplied data (company names, project titles, designer names, check labels) is inserted directly into LaTeX without escaping. Characters like `&`, `%`, `$`, `#`, `_`, `{`, `}` in input data will cause LaTeX compilation errors.

---

## 6. Error Handling — Bare `except: pass`

Lines 480–483:
```python
try:
    doc.generate_pdf(filename, compiler='pdflatex', clean_tex=False)
except:
    pass
```

- **Bare `except:` clause** catches ALL exceptions including `KeyboardInterrupt` and `SystemExit`
- **`pass`** silently swallows every error — the user gets no feedback at all
- **No log file parsing** — the `.log` file generated by pdflatex is never read
- **No error classification** — missing packages, missing images, syntax errors all look the same (nothing)
- **No exit code check** — relies entirely on pylatex's `generate_pdf` which internally calls subprocess

This is the root cause of the known "Latex Creation Error" false positive bug — sometimes `generate_pdf` raises an exception even when the PDF was actually written to disk.

---

## 7. Duplicated Code — Evidence

### Duplication 1: Subsection + LongTable + Header Pattern

The same pattern repeats for every subsection in `Design_Check`:

**Bolt Check (lines 228–234):**
```python
with doc.create(Subsection(check[1])):
    with doc.create(LongTable(check[2], row_height=1.2)) as table:
        table.add_hline()
        table.add_row(('Check', 'Required', 'Provided', 'Remarks'), color='OsdagGreen')
        table.add_hline()
        table.end_table_header()
        table.add_hline()
        count = count + 1
```

**Weld Check (same pattern, lines 240–247):**
```python
with doc.create(Subsection(check[1])):
    with doc.create(LongTable(check[2], row_height=1.2)) as table:
        table.add_hline()
        table.add_row(('Axes', 'Buckling Class', 'Imperfection Factor', ''), color='OsdagGreen')
        table.add_hline()
        table.end_table_header()
        table.add_hline()
        count = count + 1
```

**Selected Section Details (lines 252–294):**
```python
with doc.create(Subsection(check[1])):
    with doc.create(LongTable(check[2], row_height=1.2)) as table:
        table.add_hline()
        # ... same MultiRow/MultiColumn image rendering ...
        table.add_hline()
    count = count + 1
```

The only difference is the header row content (`('Check', 'Required', 'Provided', 'Remarks')` vs `('Axes', 'Buckling Class', ...)`). The table creation, hlines, header, end_table_header, and count increment are identical.

### Duplication 2: Section Details Image Rendering

The code that renders a section's properties with its profile image appears **twice** — once for the "Input Parameters" section (lines 100–130) and once for the "Selected" section details (lines 259–292). Both blocks:
1. Check `type(uiObj[i]) == dict`
2. Extract `image_name = sectiondetails[KEY_DISP_SEC_PROFILE]`
3. Build `Img_path` from package images
4. Calculate `merge_rows` based on dict length parity
5. Loop through keys rendering `MultiRow` + `MultiColumn` rows
6. Add `table.add_hline(2, 5)` after each row

### Duplication 3: 3D Views Grid

The 3D views table (lines 423–465) is duplicated almost verbatim between the "has image" branch and the "broken image" fallback — same Tabularx format, same 4-view grid layout, same row labels.

---

## 8. Data Flow Chain

```
GUI (ui_template.py)
  │ User enters loads, sections, bolts, plates
  │ Each design module stores results in:
  │   self.report_input (dict)
  │   self.report_check (list of tuples)
  │   self.report_supporting (dict with section properties)
  │   self.report_supported (dict with section properties)
  ▼
Module's save_design() method
  │ Builds report_input dict with KEY_DISP_* keys
  │ Builds report_check list with ('SubSection',...) and (label, req, prov, 'Pass'/'Fail') tuples
  │ Calls Report_functions.py functions to build pylatex.Math equations for "Provided" column
  │ Calls: CreateLatex.save_latex(CreateLatex(), self.report_input, self.report_check, ...)
  ▼
CreateLatex.save_latex() [reportGenerator_latex.py]
  │ Iterates uiObj → builds "Input Parameters" LongTable
  │ Iterates Design_Check → builds "Design Checks" section with subsections
  │ Renders 2D drawings (module-dependent)
  │ Renders 3D views (4-view grid)
  │ Renders Design Log (colored logger messages)
  │ Calls: doc.generate_pdf(filename, compiler='pdflatex')
  ▼
pylatex Document.generate_pdf()
  │ Writes .tex file to disk
  │ Spawns pdflatex subprocess
  │ Returns (or raises exception — silently caught)
  ▼
PDF file on disk
```

### Key files in the chain:

| File | Role |
|---|---|
| `Common.py` | All `KEY_DISP_*` constants (300+ definitions) |
| `Report_functions.py` | ~100+ functions returning `pylatex.Math` equation objects |
| `utils/common/common_calculation.py` | `round_up()` and other math helpers |
| `design_report/reportGenerator_latex.py` | The monolithic 487-line `save_latex()` method |
| `design_report/report_generator_base_plate.py` | Base Plate module's `save_design()` building `report_check` |
| `gui/ui_summary_popup.py` | GUI dialog that collects metadata and triggers report generation |

---

## 9. Workspace State (Updated)

The real Osdag codebase **IS present** at `C:\Users\Saatvika Reddy\Osdag_Vault\Osdag\`. The reporting package we built is at `C:\Users\Saatvika Reddy\Osdag_Vault\reporting\`.

### What We Can Now Do

- **Trace real data shapes** from `save_design()` methods to build accurate test fixtures
- **Identify all 22+ modules** that call `save_latex` and catalog their `report_check` tuple patterns
- **Build regression tests** comparing old vs new output for real report types
- **Migrate the most-duplicated patterns** (subsection+table, section details image rendering) into the new generator architecture
