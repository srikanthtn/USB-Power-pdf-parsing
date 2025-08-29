from typing import Any, Dict, List

import pandas as pd

from .models import TOCEntry, Section


class Validator:
    """Generate validation report and Excel comparing ToC vs sections."""

    def compare(self, toc: List[TOCEntry], sections: List[Section]) -> pd.DataFrame:
        toc_ids = {e.section_id for e in toc}
        sec_ids = {s.section_id for s in sections}
        all_ids = sorted(toc_ids | sec_ids, key=lambda s: [int(x) for x in s.split('.')])
        rows = []
        for sid in all_ids:
            in_toc = sid in toc_ids
            in_sec = sid in sec_ids
            rows.append({
                'section_id': sid,
                'in_toc': in_toc,
                'in_sections': in_sec,
                'status': 'MATCH' if in_toc and in_sec else 'MISMATCH'
            })
        return pd.DataFrame(rows)

    def to_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        return {
            'total_ids': int(df.shape[0]),
            'matches': int((df['status'] == 'MATCH').sum()),
            'mismatches': int((df['status'] == 'MISMATCH').sum()),
        }

    def export_excel(self, df: pd.DataFrame, output_path: str) -> None:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='validation')


