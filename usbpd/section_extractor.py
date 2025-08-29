import logging
from typing import List

import pdfplumber

from .models import TOCEntry, Section


class SectionExtractor:
    """Extract sections' content based on ToC entries."""

    def __init__(self, pdf_path: str, doc_title: str):
        self.pdf_path = pdf_path
        self.doc_title = doc_title
        self._logger = logging.getLogger(self.__class__.__name__)

    def _extract_page_range(self, pdf, start_page: int, end_page: int) -> str:
        contents: List[str] = []
        for page_index in range(start_page, min(end_page, len(pdf.pages))):
            page = pdf.pages[page_index]
            text = page.extract_text() or ""
            if text:
                contents.append(text)
        return "\n".join(contents)

    def extract(self, toc_entries: List[TOCEntry],
                start_page: int = 0, end_page: int = None) -> List[Section]:
        sections: List[Section] = []
        with pdfplumber.open(self.pdf_path) as pdf:
            max_page = len(pdf.pages) if end_page is None else min(end_page, len(pdf.pages))
            for i, entry in enumerate(toc_entries):
                section_start = max(start_page, entry.page - 1)
                section_end = toc_entries[i + 1].page - 1 if i + 1 < len(toc_entries) else max_page
                section_end = min(section_end, max_page)
                content = self._extract_page_range(pdf, section_start, section_end)
                sections.append(Section(
                    doc_title=self.doc_title,
                    section_id=entry.section_id,
                    title=entry.title,
                    page=entry.page,
                    content=content[:1000] if content else "",
                ))
        return sections


