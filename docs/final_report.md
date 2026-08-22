# Osdag LaTeX Report Generator — Final Report

*One coherent account of what was wrong, what was built, how it was validated,
and what it costs.*

---

## 1. The problem

Every Osdag connection module carried its own ~500-line `save_latex()` that
built a PDF report by concatenating LaTeX strings. Three consequences:

1. **Copy-paste drift.** Table headers, column widths, colors, and section
   titles were re-typed per module; the same concept ("Input Parameters")
   appeared with different spellings and layouts.
2. **Silent failure.** Errors were wrapped in `except: pass`; a user could get
   no report, half a report, or a corrupt `.tmp` file with no explanation.
3. **Untestable coupling.** Report code read GUI widget objects directly, so
   nothing could be exercised without launching the Qt interface.

## 2. What was built

A six-layer pipeline, each layer independently testable:

```
 .osi file ──▶ Adapter ──▶ Report Model ──▶ Generators ──▶ Templates ──▶ Compiler ──▶ PDF
```

- **Model** (`reporting/models/`): `Report`, `Section`, `Table`, `Figure`
  dataclasses. Knows nothing about Osdag or LaTeX.
- **Adapter** (`adapters/osdag_adapter.py`): translates raw `uiObj` /
  `Design_Check` data (including `TITLE` sentinels, section-detail dicts,
  `SubSection` tuples, and `Image` entries) into the model.
- **Generators** (`generators/`): walk the model and emit LaTeX; tables,
  figures, and section assembly are separate units.
- **Templates** (`templates/base.tex`, `compact.tex`): Jinja2 documents;
  styles are selected from a registry.
- **Compiler** (`compiler/latex_compiler.py`): subprocess wrapper returning a
  structured `CompileResult` with typed errors.
- **CLI** (`cli.py`): loads native JSON *or* Osdag-format JSON (auto-detected),
  validates pre-flight, renders, compiles.

## 3. The bug we caught in a real PDF

The first end-to-end PDF compiled from real `bc_ep_2.osi` data looked correct
in the source and wrong on paper: tables declared inside "Design Checks"
appeared after the next section's heading. Cause: `\begin{table}[h]` floats
that don't fit are deferred by LaTeX into later pages; nothing in the legacy
code (or our first generator) constrained them. Diagnosis compared each
caption's page number against its section heading's page in the extracted PDF
text. Fix: `\FloatBarrier` (`placeins`) after every section's content.

The important part is not the fix — it is that the diagnosis method became a
test. `reporting/tests/test_pdf_structure_order.py` compiles documents, extracts
per-page text with `pypdf`, and asserts three ordering invariants against the
source model. It was verified red (barrier removed → both ordering tests fail
with *"floats have drifted out of order"* messages naming the caption and
pages) and green (fix restored). A dense 6-section stress document makes the
test genuinely able to trigger the reflow it guards against. Full narrative:
[`before_after_comparison.md`](before_after_comparison.md).

## 4. Proof the abstraction is real: three connection types

| Connection type | Source | Adapter changes |
|---|---|---|
| Beam-to-Column End Plate | `bc_ep_2.osi` | (initial build) |
| Base Plate | `baseplate_*.osi` | 0 |
| Fin Plate | `fin1.osi` | **0** |

Fin Plate differs structurally — shear-only loading, pretensioned bolts, no
end-plate geometry, a five-stage check sequence — yet required only a fixture
file (`fin_plate_real.json`) and one entry in the test registry. It runs
through the same parameterized integration and regression tests as the other
two types. This is the extensibility argument in its strongest form: *new
module = new data, not new code.*

## 5. Errors you can read

The compiler wrapper turns pdflatex's opaque log into typed results. These are
real captured outputs from triggering each case:

| Trigger | Old behavior | New `CompileResult` |
|---|---|---|
| `pdflatex` missing | Undefined | `COMPILER_NOT_FOUND` — "...not found. Please install a LaTeX distribution." |
| Missing `.sty` | Cryptic log | `MISSING_PACKAGE` — "Required package 'x.sty' not found." |
| Missing image | Silent / swallowed | `MISSING_IMAGE` — "Figure at 'no_such_image_xyz.png' not found." |

Subtlety worth knowing: nonstopmode pdflatex still writes a PDF after failing
to find an image. The wrapper parses the log and reports failure anyway, so a
defective PDF is never presented as success.

## 6. Configuration over duplication

Fourteen classes of hardcoded values — colors, column specs, table headers,
section titles, compiler name, timeouts, sentinels — moved to named homes
(`config.py`, templates, model defaults). Full ledger with rationale:
[`hardcoded_values_removed.md`](hardcoded_values_removed.md).

## 7. Honest metrics

≈735 lines of legacy generator code became ≈1,032 lines across the package.
That is a modest increase, not a reduction — and it should be framed as one:
the extra lines buy maintainability (one model serves N modules), safety
(structured errors instead of silent ones), and extensibility (a new
connection type is fixture data). Line counts alone were never the point.

## 8. Validation summary

- **112 tests**, all passing: unit (models, escaping, generators), adapter
  round-trips against three real-data fixtures, compiler error taxonomy
  (mocked), and end-to-end compile-and-inspect-PDF checks.
- CI runs two jobs on every push: pure-Python tests without any LaTeX
  installed (proving layer independence), and the full suite with TeXLive +
  coverage.
- CLI verified end-to-end on Windows (TinyTeX): ToC/LoF/LoT, longtables,
  figures, styles, and structured failures all exercised against real output.

## 9. Known limitations

- No byte-for-byte comparison against legacy PDFs: Osdag's internal modules
  cannot be imported standalone (GUI-coupled circular imports), so equivalence
  was established structurally on reconstructed `.tex` output.
- Single `pdflatex` pass: forward references may need a second run.
- Adapter covers the data shapes emitted by the traced modules; novel shapes
  would need small extensions (by design, they fail loudly rather than silently).
