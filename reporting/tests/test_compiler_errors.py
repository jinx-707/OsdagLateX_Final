"""Tests for compiler/latex_compiler.py — full error taxonomy coverage.

Each test mocks subprocess.run and/or shutil.which so no real pdflatex
is needed.  Fake .log files are written to tmp_path to simulate the
various error conditions that pdflatex can produce.
"""

import os
import subprocess
from unittest.mock import patch, MagicMock

import pytest
from reporting.compiler.latex_compiler import compile_latex, CompileErrorType


# ── helpers ──────────────────────────────────────────────────────────

def _fake_process(stdout="", stderr="", returncode=0):
    """Build a mock subprocess.CompletedProcess."""
    p = MagicMock(spec=subprocess.CompletedProcess)
    p.stdout = stdout
    p.stderr = stderr
    p.returncode = returncode
    return p


def _write_log(tmp_path, tex_name, content):
    """Write a fake .log file next to where pdflatex would put one."""
    log = tmp_path / f"{tex_name}.log"
    log.write_text(content, encoding="utf-8")
    return log


def _write_tex(tmp_path, tex_name="test", body=r"\documentclass{article}\begin{document}hi\end{document}"):
    tex = tmp_path / f"{tex_name}.tex"
    tex.write_text(body, encoding="utf-8")
    return tex


# ── 1. COMPILER_NOT_FOUND — no subprocess call attempted ─────────────

class TestCompilerNotFound:
    def test_no_subprocess_call(self, tmp_path):
        """shutil.which returns None → COMPILER_NOT_FOUND, subprocess.run never called."""
        tex = _write_tex(tmp_path)
        with patch("reporting.compiler.latex_compiler.shutil.which", return_value=None), \
             patch("reporting.compiler.latex_compiler.subprocess.run") as mock_run:
            result = compile_latex(str(tex))

        assert not result.success
        assert result.error_type == CompileErrorType.COMPILER_NOT_FOUND
        assert "pdflatex not found" in result.error_message
        assert result.pdf_path is None
        assert result.warnings == []
        mock_run.assert_not_called()  # spec requirement


# ── 2. Valid .tex compiles → success=True ────────────────────────────

class TestValidCompilation:
    def test_success_with_pdf(self, tmp_path):
        """A valid .tex with a present PDF → success=True."""
        tex = _write_tex(tmp_path)
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")  # fake PDF

        with patch("reporting.compiler.latex_compiler.shutil.which", return_value="/usr/bin/pdflatex"), \
             patch("reporting.compiler.latex_compiler.subprocess.run", return_value=_fake_process()):
            result = compile_latex(str(tex))

        assert result.success
        assert result.pdf_path == str(pdf)
        assert result.error_type is None
        assert result.error_message is None


# ── 3. MISSING_IMAGE — log references a nonexistent file ─────────────

class TestMissingImage:
    def test_missing_image_error(self, tmp_path):
        tex = _write_tex(tmp_path)
        _write_log(tmp_path, "test", (
            "! LaTeX Error: File `diagram.png' not found.\n"
            "l.5 \\includegraphics{diagram.png}\n"
        ))
        # No PDF produced
        with patch("reporting.compiler.latex_compiler.shutil.which", return_value="/usr/bin/pdflatex"), \
             patch("reporting.compiler.latex_compiler.subprocess.run", return_value=_fake_process()):
            result = compile_latex(str(tex))

        assert not result.success
        assert result.error_type == CompileErrorType.MISSING_IMAGE
        assert "image" in result.error_message.lower()


# ── 4. MISSING_PACKAGE — log references missing .sty ──────────────────

class TestMissingPackage:
    def test_missing_sty_error(self, tmp_path):
        tex = _write_tex(tmp_path)
        _write_log(tmp_path, "test", (
            "! LaTeX Error: File `fancyhdr.sty' not found.\n"
            "l.10 \\usepackage{fancyhdr}\n"
        ))
        with patch("reporting.compiler.latex_compiler.shutil.which", return_value="/usr/bin/pdflatex"), \
             patch("reporting.compiler.latex_compiler.subprocess.run", return_value=_fake_process()):
            result = compile_latex(str(tex))

        assert not result.success
        assert result.error_type == CompileErrorType.MISSING_PACKAGE
        assert "package" in result.error_message.lower()


# ── 5. SYNTAX_ERROR — log has a generic ! error ──────────────────────

class TestSyntaxError:
    def test_undefined_control_sequence(self, tmp_path):
        tex = _write_tex(tmp_path)
        _write_log(tmp_path, "test", (
            "! Undefined control sequence.\n"
            "l.3 \\badcommand\n"
        ))
        with patch("reporting.compiler.latex_compiler.shutil.which", return_value="/usr/bin/pdflatex"), \
             patch("reporting.compiler.latex_compiler.subprocess.run", return_value=_fake_process()):
            result = compile_latex(str(tex))

        assert not result.success
        assert result.error_type == CompileErrorType.SYNTAX_ERROR
        assert "syntax" in result.error_message.lower()


# ── 6. Warnings only → success=True, warnings populated ──────────────

class TestWarningsOnly:
    def test_warnings_do_not_fail(self, tmp_path):
        tex = _write_tex(tmp_path)
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        _write_log(tmp_path, "test", (
            "LaTeX Warning: Reference `fig:missing' on page 1 undefined.\n"
            "LaTeX Warning: File `logo.png' not found on input line 7.\n"
        ))
        with patch("reporting.compiler.latex_compiler.shutil.which", return_value="/usr/bin/pdflatex"), \
             patch("reporting.compiler.latex_compiler.subprocess.run", return_value=_fake_process()):
            result = compile_latex(str(tex))

        assert result.success
        assert len(result.warnings) == 2
        assert result.error_type is None


# ── 7. TIMEOUT ───────────────────────────────────────────────────────

class TestTimeout:
    def test_timeout_error(self, tmp_path):
        tex = _write_tex(tmp_path)
        with patch("reporting.compiler.latex_compiler.shutil.which", return_value="/usr/bin/pdflatex"), \
             patch(
                 "reporting.compiler.latex_compiler.subprocess.run",
                 side_effect=subprocess.TimeoutExpired(cmd="pdflatex", timeout=60),
             ):
            result = compile_latex(str(tex), timeout_seconds=60)

        assert not result.success
        assert result.error_type == CompileErrorType.TIMEOUT
        assert "timed out" in result.error_message.lower()


# ── 8. Nonzero exit code + PDF exists → still success ────────────────
#    This mirrors a real Osdag bug: pdflatex exits non-zero but the PDF
#    was actually generated.  The old code would report "Latex Creation
#    Error"; the new code correctly checks for the PDF first.

class TestNonzeroExitWithPdf:
    def test_pdf_exists_trumps_exit_code(self, tmp_path):
        tex = _write_tex(tmp_path)
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        _write_log(tmp_path, "test", (
            "This is pdflatex, version 2023\n"
            "No errors in log.\n"
        ))
        with patch("reporting.compiler.latex_compiler.shutil.which", return_value="/usr/bin/pdflatex"), \
             patch(
                 "reporting.compiler.latex_compiler.subprocess.run",
                 return_value=_fake_process(returncode=1),
             ):
            result = compile_latex(str(tex))

        # PDF exists → success, even though exit code was 1
        assert result.success
        assert result.pdf_path == str(pdf)
        assert result.error_type is None


# ── 9. UNKNOWN — no PDF, no ! errors in log ─────────────────────────

class TestUnknownError:
    def test_no_pdf_no_errors(self, tmp_path):
        tex = _write_tex(tmp_path)
        _write_log(tmp_path, "test", (
            "This is pdflatex, version 2023\n"
            "No obvious error markers.\n"
        ))
        with patch("reporting.compiler.latex_compiler.shutil.which", return_value="/usr/bin/pdflatex"), \
             patch("reporting.compiler.latex_compiler.subprocess.run", return_value=_fake_process()):
            result = compile_latex(str(tex))

        assert not result.success
        assert result.error_type == CompileErrorType.UNKNOWN


# ── 10. Fallback to stdout/stderr when no .log file ──────────────────

class TestNoLogFile:
    def test_uses_stdout_when_no_log(self, tmp_path):
        tex = _write_tex(tmp_path)
        # No .log file written — compiler should fall back to stdout/stderr
        with patch("reporting.compiler.latex_compiler.shutil.which", return_value="/usr/bin/pdflatex"), \
             patch(
                 "reporting.compiler.latex_compiler.subprocess.run",
                 return_value=_fake_process(stdout="some output", stderr="some error"),
             ):
            result = compile_latex(str(tex))

        assert not result.success
        assert "some output" in result.raw_log
        assert "some error" in result.raw_log
