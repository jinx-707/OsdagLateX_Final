from dataclasses import dataclass, field
from typing import List, Optional
from .section import Section


@dataclass
class ReportConfig:
    """Configuration flags for report generation."""
    include_toc: bool = True
    include_list_of_figures: bool = False
    include_list_of_tables: bool = False
    include_appendix: bool = False
    style: str = "default"


@dataclass
class Report:
    """
    Complete report document.

    Attributes:
        title: Main title.
        author: Author name.
        sections: List of top-level sections.
        config: Generation options.
        subtitle: Optional subtitle.
        date: Optional date string (if None, \\today is used).
    """
    title: str
    author: str
    sections: List[Section]
    config: ReportConfig = field(default_factory=ReportConfig)
    subtitle: Optional[str] = None
    date: Optional[str] = None
