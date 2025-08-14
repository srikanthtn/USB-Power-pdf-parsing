import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pdfplumber
from dataclasses import dataclass, asdict
import fitz  # PyMuPDF


@dataclass
class TOCEntry:
    """Structure for Table of Contents entry"""
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
    """Structure for document section"""
    doc_title: str
    section_id: str
    title: str
    page: int
    content: str
    tables: Optional[List[str]] = None
    figures: Optional[List[str]] = None


class USBPDParser:
    """Main parser class for USB PD specification documents"""
    
    def __init__(self, pdf_path: str, doc_title: str = "USB Power Delivery Specification"):
        self.pdf_path = Path(pdf_path)
        self.doc_title = doc_title
        self.toc_pattern = re.compile(r'^(\d+(?:\.\d+)*)\s+(.+?)\s+(\d+)$')
        
    def extract_toc_text(self) -> List[str]:
        """Extract raw text lines from ToC pages"""
        toc_lines = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages[13:34]:  # ToC usually in first 10 pages
                text = page.extract_text()
                if not text:
                    continue
                    
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    # Skip headers, footers, and empty lines
                    if (line and 
                        not line.lower().startswith(('table of contents', 'contents', 'page')) and
                        self.toc_pattern.match(line)):
                        toc_lines.append(line)
        
        return toc_lines
    
    def parse_toc_line(self, line: str) -> Optional[TOCEntry]:
        """Parse a single ToC line into structured data"""
        match = self.toc_pattern.match(line)
        if not match:
            return None
            
        section_id, title, page_str = match.groups()
        
        # Calculate hierarchy level
        level = section_id.count('.') + 1
        
        # Determine parent_id
        parent_id = None
        if '.' in section_id:
            parent_id = '.'.join(section_id.split('.')[:-1])
        
        # Generate tags from title keywords
        tags = self._extract_tags(title)
        
        return TOCEntry(
            doc_title=self.doc_title,
            section_id=section_id,
            title=title.strip(),
            page=int(page_str),
            level=level,
            parent_id=parent_id,
            full_path=f"{section_id} {title.strip()}",
            tags=tags
        )
    
    def _extract_tags(self, title: str) -> List[str]:
        """Extract relevant tags from section title"""
        keywords = {
            'power': ['power', 'voltage', 'current', 'supply'],
            'delivery': ['delivery', 'transport', 'transmission'],
            'contract': ['contract', 'negotiation', 'agreement'],
            'protocol': ['protocol', 'communication', 'message'],
            'cable': ['cable', 'connector', 'wire'],
            'device': ['device', 'source', 'sink'],
            'charging': ['charging', 'charge', 'battery'],
            'testing': ['test', 'compliance', 'verification']
        }
        
        title_lower = title.lower()
        tags = []
        
        for tag, words in keywords.items():
            if any(word in title_lower for word in words):
                tags.append(tag)
        
        return tags if tags else None
    
    def parse_toc(self) -> List[TOCEntry]:
        """Parse complete Table of Contents"""
        toc_lines = self.extract_toc_text()
        entries = []
        
        for line in toc_lines:
            entry = self.parse_toc_line(line)
            if entry:
                entries.append(entry)
        
        return entries
    
    def extract_sections(self, toc_entries: List[TOCEntry]) -> List[Section]:
        """Extract content sections from PDF"""
        sections = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for i, entry in enumerate(toc_entries):
                # Determine page range for this section
                start_page = entry.page - 1  # 0-indexed
                end_page = (toc_entries[i + 1].page - 1 
                           if i + 1 < len(toc_entries) 
                           else len(pdf.pages))
                
                # Extract content from pages
                content = self._extract_page_range(pdf, start_page, end_page)
                
                section = Section(
                    doc_title=self.doc_title,
                    section_id=entry.section_id,
                    title=entry.title,
                    page=entry.page,
                    content=content[:1000] if content else ""  # Truncate for demo
                )
                sections.append(section)
        
        return sections
    
    def _extract_page_range(self, pdf, start_page: int, end_page: int) -> str:
        """Extract text content from a range of pages"""
        content = []
        
        for page_num in range(start_page, min(end_page, len(pdf.pages))):
            page = pdf.pages[page_num]
            text = page.extract_text()
            if text:
                content.append(text)
        
        return '\n'.join(content)
    
    def save_jsonl(self, data: List, filename: str):
        """Save data to JSONL file"""
        with open(filename, 'w', encoding='utf-8') as f:
            for item in data:
                if hasattr(item, '__dict__'):
                    json.dump(asdict(item), f, ensure_ascii=False)
                else:
                    json.dump(item, f, ensure_ascii=False)
                f.write('\n')
    
    def generate_validation_report(self, toc_entries: List[TOCEntry], 
                                 sections: List[Section]) -> Dict[str, Any]:
        """Generate validation report comparing ToC vs parsed sections"""
        # Create comparison data
        toc_ids = {entry.section_id for entry in toc_entries}
        section_ids = {section.section_id for section in sections}
        
        # Find mismatches
        missing_in_sections = toc_ids - section_ids
        extra_in_sections = section_ids - toc_ids
        
        # Create report data
        report_data = {
            'Metric': [
                'Total ToC Entries',
                'Total Parsed Sections',
                'Matching Sections',
                'Missing in Sections',
                'Extra in Sections'
            ],
            'Count': [
                len(toc_entries),
                len(sections),
                len(toc_ids & section_ids),
                len(missing_in_sections),
                len(extra_in_sections)
            ],
            'Details': [
                ', '.join([f"{e.section_id}: {e.title}" for e in toc_entries[:5]]) + '...',
                ', '.join([f"{s.section_id}: {s.title}" for s in sections[:5]]) + '...',
                ', '.join(list(toc_ids & section_ids)[:10]),
                ', '.join(missing_in_sections),
                ', '.join(extra_in_sections)
            ]
        }
        
        return report_data
    
    def process_pdf(self) -> Tuple[List[TOCEntry], List[Section], Dict[str, Any]]:
        """Main processing pipeline"""
        print(f"Processing PDF: {self.pdf_path}")
        
        # Parse ToC
        print("Extracting Table of Contents...")
        toc_entries = self.parse_toc()
        print(f"Found {len(toc_entries)} ToC entries")
        
        # Extract sections
        print("Extracting sections...")
        sections = self.extract_sections(toc_entries)
        print(f"Extracted {len(sections)} sections")
        
        # Generate validation report
        print("Generating validation report...")
        validation_report = self.generate_validation_report(toc_entries, sections)
        
        # Save TOC to JSONL
        with open('usb_pd_toc.jsonl', 'w', encoding='utf-8') as f:
            for entry in toc_entries:
                json.dump(entry.__dict__, f)
                f.write('\n')

        # Save sections to JSONL
        with open('usb_pd_spec.jsonl', 'w', encoding='utf-8') as f:
            for section in sections:
                json.dump(section.__dict__, f)
                f.write('\n')
        
        return toc_entries, sections, validation_report

    def parse_pdf(self, pdf_path: str, start_page: int = 1, end_page: Optional[int] = None) -> Tuple[List[TOCEntry], List[Section]]:
        doc = fitz.open(pdf_path)
        
        # Validate page range
        if end_page is None:
            end_page = doc.page_count
        
        if start_page < 1 or start_page > doc.page_count:
            raise ValueError(f"Start page must be between 1 and {doc.page_count}")
        if end_page < start_page or end_page > doc.page_count:
            raise ValueError(f"End page must be between {start_page} and {doc.page_count}")
            
        # Adjust page range to 0-based index
        start_page -= 1
        end_page -= 1
        
        # Modify your existing parsing logic to use the page range
        # Only process pages within the specified range
        with pdfplumber.open(self.pdf_path) as pdf:
            for i, entry in enumerate(toc_entries):
                # Determine page range for this section
                section_start_page = max(start_page, entry.page - 1)  # 0-indexed
                section_end_page = (toc_entries[i + 1].page - 1 
                                   if i + 1 < len(toc_entries) 
                                   else len(pdf.pages))
                
                # Extract content from pages
                content = self._extract_page_range(pdf, section_start_page, section_end_page)
                
                section = Section(
                    doc_title=self.doc_title,
                    section_id=entry.section_id,
                    title=entry.title,
                    page=entry.page,
                    content=content[:1000] if content else ""  # Truncate for demo
                )
                sections.append(section)
        
        return sections
    
def main():
    """Main execution function"""
    # Configuration
    PDF_PATH = "USB_PD_R3_2 V1.1 2024-10.pdf"  # Replace with actual path
    DOC_TITLE = "USB Power Delivery Specification Rev 3.1"
    
    # Initialize parser
    parser = USBPDParser(PDF_PATH, DOC_TITLE)
    
    try:
        # Process PDF
        toc_entries, sections, validation_report = parser.process_pdf()
        
        # Save outputs
        print("Saving outputs...")
        parser.save_jsonl(toc_entries, "usb_pd_toc.jsonl")
        parser.save_jsonl(sections, "usb_pd_spec.jsonl")
        
        # Save validation report
        with open("validation_report.json", "w") as f:
            json.dump(validation_report, f, indent=2)
        
        print("Processing completed successfully!")
        print(f"Generated files:")
        print(f"  - usb_pd_toc.jsonl ({len(toc_entries)} entries)")
        print(f"  - usb_pd_spec.jsonl ({len(sections)} sections)")
        print(f"  - validation_report.json")
        
        # Print sample data
        if toc_entries:
            print(f"\nSample ToC entry:")
            print(json.dumps(asdict(toc_entries[0]), indent=2))
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        raise


if __name__ == "__main__":
    main()