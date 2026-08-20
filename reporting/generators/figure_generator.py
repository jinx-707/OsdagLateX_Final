"""Generate LaTeX code for Figure objects."""

import logging
import os
from reporting.models.figure import Figure
from reporting.utils.escaping import escape_latex

logger = logging.getLogger(__name__)


def generate_figure_latex(figure: Figure) -> str:
    """
    Convert a Figure model into a LaTeX figure environment.

    Args:
        figure: Figure object.

    Returns:
        LaTeX string.

    Raises:
        FileNotFoundError: If image path does not exist.
    """
    if not os.path.isfile(figure.path):
        raise FileNotFoundError(f"Image file not found: {figure.path}")

    lines = []
    lines.append(r"\begin{figure}[" + figure.placement + "]")
    lines.append(r"\centering")
    lines.append(r"\includegraphics[width=" + figure.width + "]{" + figure.path + "}")
    if figure.caption:
        lines.append(r"\caption{" + escape_latex(figure.caption) + "}")
    if figure.label:
        lines.append(r"\label{" + figure.label + "}")
    lines.append(r"\end{figure}")
    return "\n".join(lines)
