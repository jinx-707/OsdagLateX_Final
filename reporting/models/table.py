from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Table:
    """
    A table with headers, rows, and optional styling.

    Attributes:
        headers: Column headers (first row).
        rows: Data rows, each list must match len(headers).
        col_spec: LaTeX column specification (e.g., "lXlX").
        use_longtable: Whether to use longtable for multi-page tables.
        header_color: Optional color name (mapped to LaTeX).
        caption: Table caption.
        label: LaTeX label for cross-reference.
    """
    headers: List[str]
    rows: List[List[str]]
    col_spec: str = "l"
    use_longtable: bool = False
    header_color: Optional[str] = None
    caption: str = ""
    label: str = ""

    def __post_init__(self):
        if not self.headers:
            raise ValueError("Table must have at least one header.")
        if not self.rows:
            raise ValueError("Table must have at least one row.")
        expected = len(self.headers)
        for i, row in enumerate(self.rows):
            if len(row) != expected:
                raise ValueError(
                    f"Table row {i} has {len(row)} cells, expected {expected}."
                )
