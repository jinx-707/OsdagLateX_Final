"""LaTeX compilation wrapper with structured error handling."""

import logging
import os
import re
import subprocess
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, List

from reporting.config import LATEX_COMPILER, DEFAULT_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)

# ── Log-parsing markers (defined once, used in compile_latex) ─────────
LATEX_ERROR_MARKER = "! "
LATEX_WARNING_MARKER = "warning"
NOT_FOUND_MARKER = "not found"
STY_EXTENSION = ".sty"


class CompileErrorType(Enum):
    COMPILER_NOT_FOUND = "compiler_not_found"
    MISSING_PACKAGE = "missing_package"
    MISSING_IMAGE = "missing_image"
    SYNTAX_ERROR = "syntax_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class CompileResult:
    success: bool
    pdf_path: Optional[str]
    error_type: Optional[CompileErrorType]
    error_message: Optional[str]
    warnings: List[str]
    raw_log: Optional[str]


def _long_path(path: str) -> str:
    r"""Expand 8.3 short-path components (e.g. 'SAATVI~1') to long form.

    pdflatex treats '~' anywhere in its file-name argument as an active
    character (non-breaking space) and aborts, so short paths must never
    reach it.
    """
    if os.name != "nt" or "~" not in path:
        return path
    try:
        import ctypes

        buf = ctypes.create_unicode_buffer(32768)
        if ctypes.windll.kernel32.GetLongPathNameW(path, buf, len(buf)):
            return buf.value
    except Exception:  # pragma: no cover - best effort only
        pass
    return path


def compile_latex(tex_path: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> CompileResult:
    """
    Compile a .tex file to PDF using pdflatex.

    Args:
        tex_path: Path to the .tex file.
        timeout_seconds: Maximum compilation time.

    Returns:
        CompileResult with details.
    """
    if shutil.which(LATEX_COMPILER) is None:
        logger.error("%s not found on PATH", LATEX_COMPILER)
        return CompileResult(
            success=False,
            pdf_path=None,
            error_type=CompileErrorType.COMPILER_NOT_FOUND,
            error_message=f"{LATEX_COMPILER} not found. Please install a LaTeX distribution.",
            warnings=[],
            raw_log=None,
        )

    tex_dir = os.path.dirname(os.path.abspath(tex_path))
    tex_base = os.path.splitext(os.path.basename(tex_path))[0]
    pdf_path = os.path.join(tex_dir, f"{tex_base}.pdf")

    # pdflatex treats backslashes in arguments as control sequences,
    # so always hand it forward-slash paths.
    tex_path_arg = Path(_long_path(os.path.abspath(tex_path))).as_posix()
    tex_dir_arg = Path(_long_path(tex_dir)).as_posix()

    try:
        process = subprocess.run(
            [LATEX_COMPILER, "-interaction=nonstopmode", "-output-directory", tex_dir_arg, tex_path_arg],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return CompileResult(
            success=False,
            pdf_path=None,
            error_type=CompileErrorType.TIMEOUT,
            error_message=f"Compilation timed out after {timeout_seconds} seconds.",
            warnings=[],
            raw_log=None,
        )

    pdf_exists = os.path.isfile(pdf_path)

    log_path = os.path.join(tex_dir, f"{tex_base}.log")
    errors = []
    warnings = []
    raw_log = ""
    if os.path.isfile(log_path):
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_log = f.read()
            for line in raw_log.splitlines():
                if line.startswith(LATEX_ERROR_MARKER):
                    errors.append(line)
                elif LATEX_WARNING_MARKER in line.lower():
                    warnings.append(line)
    else:
        raw_log = process.stdout + "\n" + process.stderr

    # A PDF existing is not the same as compilation succeeding: in
    # nonstopmode pdflatex plows past fatal errors (e.g. a missing image)
    # and still writes a defective PDF.  If the log shows missing files,
    # report failure even when a PDF was produced.
    if errors and NOT_FOUND_MARKER in "\n".join(errors).lower():
        error_type, error_message = _classify_errors(errors)
        logger.error("PDF compilation failed for %s", tex_path)
        return CompileResult(
            success=False,
            pdf_path=None,
            error_type=error_type,
            error_message=error_message,
            warnings=warnings,
            raw_log=raw_log,
        )

    if pdf_exists:
        logger.info("PDF generated: %s", pdf_path)
        if warnings:
            logger.warning("Compilation warnings: %d", len(warnings))
        return CompileResult(
            success=True,
            pdf_path=pdf_path,
            error_type=None,
            error_message=None,
            warnings=warnings,
            raw_log=raw_log,
        )

    logger.error("PDF compilation failed for %s", tex_path)
    if errors:
        error_type, error_message = _classify_errors(errors)
    else:
        error_type = CompileErrorType.UNKNOWN
        error_message = "PDF not generated, but no obvious LaTeX errors found."

    return CompileResult(
        success=False,
        pdf_path=None,
        error_type=error_type,
        error_message=error_message,
        warnings=warnings,
        raw_log=raw_log,
    )


_MISSING_FILE_RE = re.compile(r"File [`'](.+?)' not found")


def _classify_errors(errors):
    """Map LaTeX log error lines to a (CompileErrorType, message) pair."""
    combined = "\n".join(errors)
    match = _MISSING_FILE_RE.search(combined)
    missing_name = match.group(1) if match else None

    if NOT_FOUND_MARKER in combined.lower():
        if STY_EXTENSION in combined:
            if missing_name:
                return (
                    CompileErrorType.MISSING_PACKAGE,
                    f"Required package '{missing_name}' not found.",
                )
            return (
                CompileErrorType.MISSING_PACKAGE,
                "Missing LaTeX package (sty file).",
            )
        if missing_name:
            return (
                CompileErrorType.MISSING_IMAGE,
                f"Figure at '{missing_name}' not found.",
            )
        return (
            CompileErrorType.MISSING_IMAGE,
            "Missing image file referenced in document.",
        )
    return (
        CompileErrorType.SYNTAX_ERROR,
        "LaTeX syntax error. Check log for details.",
    )
