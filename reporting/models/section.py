from dataclasses import dataclass, field
from typing import List, Union
from .table import Table
from .figure import Figure

ContentItem = Union[str, Table, Figure]


@dataclass
class Section:
    """
    A section or subsection of the report.

    Attributes:
        title: Section title.
        level: 1 = \\section, 2 = \\subsection, 3 = \\subsubsection.
        content: Ordered list of text, tables, and figures.
        subsections: Nested subsections (level+1).
<<<<<<< HEAD
        force_page_break_before: Emit \\clearpage before this section's heading.
=======
>>>>>>> 6d9d68f21fde00f29096fb7fa4988f597ca8d967
    """
    title: str
    level: int = 1
    content: List[ContentItem] = field(default_factory=list)
    subsections: List['Section'] = field(default_factory=list)
<<<<<<< HEAD
    force_page_break_before: bool = False
=======
>>>>>>> 6d9d68f21fde00f29096fb7fa4988f597ca8d967

    def __post_init__(self):
        if self.level not in (1, 2, 3):
            raise ValueError("Section level must be 1, 2, or 3.")
