from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TOCEntry:
    """Structure for Table of Contents entry."""

    doc_title: str
    section_id: str
    title: str
    page: int
    level: int
    parent_id: Optional[str]
    full_path: str
    tags: Optional[List[str]] = None


@dataclass
class Section:
    """Structure for document section."""

    doc_title: str
    section_id: str
    title: str
    page: int
    content: str
    tables: Optional[List[str]] = None
    figures: Optional[List[str]] = None


