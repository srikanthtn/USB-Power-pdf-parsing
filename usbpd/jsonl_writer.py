import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Iterable, Any


class JSONLWriter:
    """Write iterable records to JSON Lines files."""

    def write(self, records: Iterable[Any], output_path: Path) -> None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open('w', encoding='utf-8') as handle:
            for item in records:
                payload = asdict(item) if is_dataclass(item) else item
                json.dump(payload, handle, ensure_ascii=False)
                handle.write('\n')


