from dataclasses import dataclass, field
from typing import List, Optional
<<<<<<< HEAD
from uuid import uuid4
from .section import Section


def _generate_report_id() -> str:
    """Generate a short report ID once, at Report construction time."""
    return f"OSDAG-{uuid4().hex[:8].upper()}"


=======
from .section import Section


>>>>>>> 6d9d68f21fde00f29096fb7fa4988f597ca8d967
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
<<<<<<< HEAD
        module_name: Optional module name for the metadata block
            (e.g. "Beam-to-Column End Plate Connection").
        report_id: Optional report identifier; auto-generated at construction
            when omitted, and stable across re-renders of the same instance.
=======
>>>>>>> 6d9d68f21fde00f29096fb7fa4988f597ca8d967
    """
    title: str
    author: str
    sections: List[Section]
    config: ReportConfig = field(default_factory=ReportConfig)
    subtitle: Optional[str] = None
    date: Optional[str] = None
<<<<<<< HEAD
    module_name: Optional[str] = None
    report_id: Optional[str] = field(default_factory=_generate_report_id)

    def __post_init__(self):
        # Callers (e.g. CLI) may pass report_id=None explicitly;
        # still generate a stable ID for this instance.
        if not self.report_id:
            self.report_id = _generate_report_id()
=======
>>>>>>> 6d9d68f21fde00f29096fb7fa4988f597ca8d967
