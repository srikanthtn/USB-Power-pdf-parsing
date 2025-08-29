from pathlib import Path

import pandas as pd

from usbpd.jsonl_writer import JSONLWriter
from usbpd.models import TOCEntry, Section
from usbpd.validator import Validator


def test_jsonl_writer(tmp_path):
    writer = JSONLWriter()
    data = [
        TOCEntry('Doc', '1', 'Intro', 1, 1, None, '1 Intro'),
        TOCEntry('Doc', '1.1', 'Scope', 2, 2, '1', '1.1 Scope'),
    ]
    out = tmp_path / 'toc.jsonl'
    writer.write(data, out)
    assert out.exists()
    assert out.read_text(encoding='utf-8').count('\n') == 2


def test_validator_compare_and_export(tmp_path):
    toc = [
        TOCEntry('Doc', '1', 'Intro', 1, 1, None, '1 Intro'),
        TOCEntry('Doc', '2', 'Spec', 3, 1, None, '2 Spec'),
    ]
    sections = [
        Section('Doc', '1', 'Intro', 1, '...'),
        Section('Doc', '2.1', 'Part', 4, '...'),
    ]
    v = Validator()
    df = v.compare(toc, sections)
    assert isinstance(df, pd.DataFrame)
    assert {'section_id', 'status'}.issubset(df.columns)
    xlsx = tmp_path / 'report.xlsx'
    v.export_excel(df, str(xlsx))
    assert xlsx.exists()


