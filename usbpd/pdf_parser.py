import logging
from pathlib import Path
from typing import Optional

import fitz


class PDFParser:
    """PDF text extraction utilities.

    Extracts raw text and metadata from PDFs. Provides small helpers
    used by higher-level extractors.
    """

    def __init__(self, pdf_path: Path):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")
        self._logger = logging.getLogger(self.__class__.__name__)

    def get_page_count(self) -> int:
        """Return total number of pages in the PDF."""
        with fitz.open(str(self.pdf_path)) as doc:
            return doc.page_count

    def extract_raw_text(self, start_page: int = 0,
                         end_page: Optional[int] = None) -> str:
        """Extract raw text from a page range [start_page, end_page).

        Pages are 0-indexed. If end_page is None, reads until EOF.
        """
        content_parts = []
        with fitz.open(str(self.pdf_path)) as doc:
            last = doc.page_count if end_page is None else min(end_page,
                                                              doc.page_count)
            for page_index in range(start_page, max(start_page, last)):
                page = doc.load_page(page_index)
                text = page.get_text("text") or ""
                if text:
                    content_parts.append(text)
        return "\n".join(content_parts)

    def extract_metadata(self) -> dict:
        """Return basic PDF metadata and file info."""
        with fitz.open(str(self.pdf_path)) as doc:
            meta = doc.metadata or {}
            return {
                "page_count": doc.page_count,
                "metadata": meta,
            }


