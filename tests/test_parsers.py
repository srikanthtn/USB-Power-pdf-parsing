from pathlib import Path

import fitz

from usbpd.models import TOCEntry
from usbpd.pdf_parser import PDFParser
from usbpd.section_extractor import SectionExtractor
from usbpd.toc_extractor import TOCExtractor


def _make_pdf(tmp_path: Path, text: str = "Hello\n1 Intro 1\n") -> Path:
    p = tmp_path / "mini.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(str(p))
    doc.close()
    return p


def test_pdf_parser_extract(tmp_path):
    pdf_path = _make_pdf(tmp_path)
    parser = PDFParser(pdf_path)
    assert parser.get_page_count() == 1
    raw = parser.extract_raw_text(0, 1)
    assert "Hello" in raw
    meta = parser.extract_metadata()
    assert meta["page_count"] == 1


def test_toc_extractor_parse_line():
    extractor = TOCExtractor("/does/not/matter.pdf", "Doc")
    entry = extractor.parse_toc_line("1.2 Title 33")
    assert isinstance(entry, TOCEntry)
    assert entry.level == 2
    assert entry.parent_id == "1"


def test_section_extractor_with_min_pdf(tmp_path):
    pdf_path = _make_pdf(tmp_path, text="1 Intro 1\nBody text")
    toc = [TOCEntry("Doc", "1", "Intro", 1, 1, None, "1 Intro")]
    se = SectionExtractor(str(pdf_path), "Doc")
    sections = se.extract(toc)
    assert len(sections) == 1
    assert sections[0].section_id == "1"


