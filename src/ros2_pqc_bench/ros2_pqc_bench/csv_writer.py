from __future__ import annotations

import csv
from pathlib import Path
from typing import Mapping


FIELDNAMES = [
    'run_id',
    'mode',
    'sequence',
    'sign_ns',
    'verify_ns',
    'age_ns',
    'e2e_ns',
    'result_code',
]


class BenchmarkCsvWriter:
    def __init__(self, output_path: str | Path) -> None:
        self.output_path = Path(output_path).expanduser()
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.output_path.open('w', newline='', encoding='utf-8')
        self._writer = csv.DictWriter(self._handle, fieldnames=FIELDNAMES)
        self._writer.writeheader()

    def write_row(self, row: Mapping[str, object]) -> None:
        self._writer.writerow({field: row.get(field, '') for field in FIELDNAMES})
        self._handle.flush()

    def close(self) -> None:
        self._handle.close()
