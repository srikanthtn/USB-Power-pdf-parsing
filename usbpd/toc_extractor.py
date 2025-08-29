import logging
import re
from typing import List, Optional

import pdfplumber

from .models import TOCEntry


class TOCExtractor:
    """Extract the Table of Contents and hierarchy from a PDF."""

    def __init__(self, pdf_path: str, doc_title: str):
        self.pdf_path = pdf_path
        self.doc_title = doc_title
        self._logger = logging.getLogger(self.__class__.__name__)
        self._toc_pattern = re.compile(r'^(\d+(?:\.\d+)*)\s+(.+?)\s+(\d+)$')

    def extract_toc_text(self, start_page: int = 13, end_page: int = 34) -> List[str]:
        """Extract raw ToC lines from likely ToC pages.

        Bounds are inclusive-exclusive and 0-based in pdfplumber's list.
        """
        lines: List[str] = []
        with pdfplumber.open(self.pdf_path) as pdf:
            end = min(end_page, len(pdf.pages))
            for page in pdf.pages[start_page:end]:
                text = page.extract_text() or ""
                for raw_line in text.split('\n'):
                    line = raw_line.strip()
                    if (line and not line.lower().startswith(
                        ('table of contents', 'contents', 'page'))
                        and self._toc_pattern.match(line)):
                        lines.append(line)
        return lines

    def parse_toc_line(self, line: str) -> Optional[TOCEntry]:
        match = self._toc_pattern.match(line)
        if not match:
            return None
        section_id, title, page_str = match.groups()
        level = section_id.count('.') + 1
        parent_id = '.'.join(section_id.split('.')[:-1]) if '.' in section_id else None
        return TOCEntry(
            doc_title=self.doc_title,
            section_id=section_id,
            title=title.strip(),
            page=int(page_str),
            level=level,
            parent_id=parent_id,
            full_path=f"{section_id} {title.strip()}",
            tags=None,
        )

    def extract(self) -> List[TOCEntry]:
        lines = self.extract_toc_text()
        entries: List[TOCEntry] = []
        for line in lines:
            entry = self.parse_toc_line(line)
            if entry:
                entries.append(entry)
        return entries


