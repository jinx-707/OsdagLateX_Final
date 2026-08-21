# Before / After — and the Float-Placement Bug We Caught in a Real PDF

## The bug: floats drifting out of section order

### Symptom

The first full PDF compiled from real Osdag data (`bc_ep_2.osi`, a
Beam-to-Column End Plate connection) *looked* fine at a glance — until it was
read against the Table of Contents. Tables belonging to section 4 ("Design
Checks") were typeset on pages after section 5's heading, and figures declared
inside "Connection Details" drifted into "Design Summary". The ToC promised one
document order; the body delivered another.

### Root cause

LaTeX gives no guarantee that a `\begin{table}[h]` float is typeset where it is
declared. When a `[h]` float does not fit on the current page, LaTeX defers it
into a float queue and places it at the top of a *later* page — often after the
next section heading has already been typeset. With many consecutive tables
(exactly what a design-check report is), the queue backs up and entire tables
leak across section boundaries:

```latex
\section{Design Checks}          % typeset immediately
\begin{table}[h] ... \end{table} % doesn't fit -> deferred
\begin{table}[h] ... \end{table} % queued behind it
\section{Connection Details}     % typeset BEFORE the queued tables appear
```

This is correct LaTeX behaviour and entirely invisible to unit tests that only
inspect the generated `.tex` source — the `.tex` file was perfectly ordered.
Only the *rendered* output was wrong.

### Diagnosis

The compiled PDF's page order was compared against the source `Report` model:
for every section, the page number of each table/figure caption was checked
against the page numbers of its own heading and of the following section's
heading. Captions appearing on later pages than the next section's heading
proved the drift. (Manual, one-off — which is exactly why it is now automated,
see below.)

### Fix

`reporting/generators/latex_generator.render_section()` now emits
`\FloatBarrier` after each section's content (before rendering subsections),
and both templates load the `placeins` package. A barrier flushes all pending
floats before the next heading may appear, so a section's tables and figures
are always typeset inside that section:

```latex
\usepackage{placeins}   % templates/base.tex, templates/compact.tex
```

```python
# latex_generator.render_section()
lines.append("\\FloatBarrier")   # after content, before subsections
```

### Locked in with a regression test

`reporting/tests/test_pdf_structure_order.py` compiles documents to real PDFs,
extracts per-page text with `pypdf`, and asserts three invariants against the
source model:

1. a caption never appears on an earlier page than its parent section heading;
2. headings appear in non-decreasing page order;
3. **no caption appears on a later page than the next section heading** — the
   exact failure mode described above.

The test suite was verified both ways (red/green): with `\FloatBarrier`
temporarily removed from the generator, both ordering tests fail loudly —

```
Float drifted out of order: caption 'Stress table for section 2' found on
page 5, but the next section heading is already on page 2 - floats have
drifted out of order. Check that \FloatBarrier is emitted after each section.
```

— and with the fix restored, all tests pass. Because the short fixture alone
never overflows a page, the suite also compiles a dense 6-section stress
document (35-row tables + figures) that forces float reflow when unbarriered;
that is what makes the test genuinely able to catch the bug rather than
vacuously pass.

## Architecture before / after

| | Before (`Osdag/design_report/`) | After (`reporting/`) |
|---|---|---|
| Structure | One 487-line `save_latex()` per report generator, duplicated across modules | Layered package: models → adapters → generators → compiler |
| Input coupling | Reads GUI widget objects directly | Plain-data `uiObj` dict via adapter; native JSON also supported |
| Error handling | Silent failures (`except: pass`), cryptic pdflatex logs | Structured `CompileResult` with typed `error_type` |
| Float placement | Unmanaged `[h]` floats; ordering bugs only found by reading PDFs | `\FloatBarrier` per section, enforced by automated PDF-order regression tests |
| Styles | Hardcoded preamble strings | Jinja2 templates (`base`, `compact`) selected via style registry |
| Testing | None | 88 tests incl. end-to-end compile-and-inspect-PDF checks |

## Honest metrics

The rewrite is a modest line-count increase (≈735 lines of legacy generator
code → ≈1,032 lines across the package). That increase buys maintainability
(one model, N modules), safety (structured errors instead of silent ones), and
extensibility (a new connection type is fixture data, not new code — see the
three-connection-type proof in the README).
