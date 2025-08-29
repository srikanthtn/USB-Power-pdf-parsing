import argparse
import logging
from pathlib import Path
from typing import Dict, Tuple, List

from .jsonl_writer import JSONLWriter
from .models import TOCEntry, Section
from .toc_extractor import TOCExtractor
from .section_extractor import SectionExtractor
from .validator import Validator


class USBPDParserApp:
    """Orchestrator for parsing, exporting, and validating USB PD specs."""

    def __init__(self, pdf_path: str, output_dir: str = ".", doc_title: str = "USB Power Delivery Specification"):
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.doc_title = doc_title
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self) -> Tuple[List[TOCEntry], List[Section], Dict]:
        self.logger.info("Starting parsing pipeline")
        self.logger.info(f"PDF: {self.pdf_path}")
        self.logger.info("Step 1/5: Extracting Table of Contents...")
        toc_entries = TOCExtractor(self.pdf_path, self.doc_title).extract()
        self.logger.info(f"ToC entries: {len(toc_entries)}")

        self.logger.info("Step 2/5: Extracting sections from PDF...")
        sections = SectionExtractor(self.pdf_path, self.doc_title).extract(toc_entries)
        self.logger.info(f"Sections extracted: {len(sections)}")

        writer = JSONLWriter()
        toc_path = self.output_dir / 'usb_pd_toc.jsonl'
        sec_path = self.output_dir / 'usb_pd_spec.jsonl'
        self.logger.info("Step 3/5: Writing JSONL outputs...")
        self.logger.info(f"Writing ToC JSONL -> {toc_path}")
        writer.write(toc_entries, toc_path)
        self.logger.info(f"Writing Sections JSONL -> {sec_path}")
        writer.write(sections, sec_path)

        validator = Validator()
        self.logger.info("Step 4/5: Comparing ToC vs Sections and exporting Excel...")
        df = validator.compare(toc_entries, sections)
        xlsx_path = self.output_dir / 'validation_report.xlsx'
        validator.export_excel(df, str(xlsx_path))
        self.logger.info(f"Validation report -> {xlsx_path}")
        summary = validator.to_summary(df)
        self.logger.info(
            f"Validation summary: total={summary['total_ids']}, "
            f"matches={summary['matches']}, mismatches={summary['mismatches']}"
        )

        # basic metadata
        metadata = {
            'doc_title': self.doc_title,
            'pdf_path': str(self.pdf_path),
            'toc_entries': len(toc_entries),
            'sections': len(sections),
            'validation': summary,
        }
        meta_path = self.output_dir / 'usb_pd_metadata.jsonl'
        self.logger.info(f"Step 5/5: Writing metadata JSONL -> {meta_path}")
        JSONLWriter().write([metadata], meta_path)

        self.logger.info("Pipeline completed successfully")

        return toc_entries, sections, metadata

    @staticmethod
    def build_cli(argv: List[str] = None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description='USB PD OOP Parser')
        parser.add_argument('--pdf', required=True, help='Path to the PDF file')
        parser.add_argument('--output', default='.', help='Output directory')
        parser.add_argument('--title', default='USB Power Delivery Specification', help='Document title')
        parser.add_argument('-v', '--verbose', action='count', default=0,
                            help='Increase verbosity (-v for INFO, -vv for DEBUG)')
        return parser.parse_args(argv)

    @classmethod
    def main(cls, argv: List[str] = None) -> int:
        args = cls.build_cli(argv)
        # Configure root logger to print to console
        level = logging.WARNING
        if args.verbose == 1:
            level = logging.INFO
        elif args.verbose >= 2:
            level = logging.DEBUG
        logging.basicConfig(
            level=level,
            format='%(asctime)s | %(levelname)-7s | %(name)s | %(message)s'
        )
        logging.getLogger('pdfplumber').setLevel(logging.ERROR)
        logging.getLogger('fitz').setLevel(logging.ERROR)
        app = cls(args.pdf, args.output, args.title)
        app.run()
        return 0


