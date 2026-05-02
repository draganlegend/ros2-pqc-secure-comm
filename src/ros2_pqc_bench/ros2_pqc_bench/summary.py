from __future__ import annotations

import argparse
import csv
from pathlib import Path
from statistics import mean, median


def _percentile(values: list[int], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((percentile / 100.0) * (len(ordered) - 1))))
    return float(ordered[index])


def summarize(csv_path: str | Path) -> dict[str, object]:
    path = Path(csv_path).expanduser()
    rows = list(csv.DictReader(path.open('r', encoding='utf-8')))
    ok_rows = [row for row in rows if int(row['result_code']) == 0]
    verify_ns = [int(row['verify_ns']) for row in ok_rows]
    e2e_ns = [int(row['e2e_ns']) for row in ok_rows]

    return {
        'rows': len(rows),
        'ok': len(ok_rows),
        'failed': len(rows) - len(ok_rows),
        'verify_mean_ns': int(mean(verify_ns)) if verify_ns else 0,
        'verify_median_ns': int(median(verify_ns)) if verify_ns else 0,
        'verify_p95_ns': int(_percentile(verify_ns, 95)) if verify_ns else 0,
        'e2e_mean_ns': int(mean(e2e_ns)) if e2e_ns else 0,
        'e2e_median_ns': int(median(e2e_ns)) if e2e_ns else 0,
        'e2e_p95_ns': int(_percentile(e2e_ns, 95)) if e2e_ns else 0,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description='Summarize ros2-pqc benchmark CSV output.')
    parser.add_argument('csv_path')
    args = parser.parse_args(argv)

    result = summarize(args.csv_path)
    for key, value in result.items():
        print(f'{key}: {value}')
