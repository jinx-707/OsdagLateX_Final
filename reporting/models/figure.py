from dataclasses import dataclass


@dataclass
class Figure:
    """
    A figure (image) to be included in the report.

    Attributes:
        path: Filesystem path to the image.
        caption: Figure caption.
        label: LaTeX label for cross-reference.
        width: LaTeX width specification (e.g., "0.8\\textwidth").
        placement: Float placement ('h', 't', 'b', 'H').
    """
    path: str
    caption: str = ""
    label: str = ""
    width: str = r"0.8\textwidth"
    placement: str = "h"
