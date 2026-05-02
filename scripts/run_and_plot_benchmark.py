#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'ros2_pqc_matplotlib'))
os.environ.setdefault('XDG_CACHE_HOME', str(Path(tempfile.gettempdir()) / 'ros2_pqc_cache'))

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd


RESULT_OK = 0
REQUIRED_COLUMNS = {
    'run_id',
    'mode',
    'sequence',
    'sign_ns',
    'verify_ns',
    'age_ns',
    'e2e_ns',
    'result_code',
}


class BenchmarkError(RuntimeError):
    pass


def log(message: str) -> None:
    print(f'[benchmark] {message}', flush=True)


def run_command(command: list[str]) -> None:
    log('Running: ' + ' '.join(command))
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise BenchmarkError(
            f'Command failed with exit code {completed.returncode}: {" ".join(command)}'
        )


def remove_stale_csv(path: Path) -> None:
    if path.exists():
        log(f'Removing stale CSV: {path}')
        path.unlink()


def load_csv(path: Path, expected_mode: str) -> pd.DataFrame:
    log(f'Loading CSV: {path}')
    if not path.exists():
        raise BenchmarkError(f'Missing CSV: {path}')
    if path.stat().st_size == 0:
        raise BenchmarkError(f'Empty CSV: {path}')

    try:
        frame = pd.read_csv(path)
    except pd.errors.EmptyDataError as exc:
        raise BenchmarkError(f'Empty CSV: {path}') from exc

    if frame.empty:
        raise BenchmarkError(f'CSV has no benchmark rows: {path}')

    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        missing_list = ', '.join(sorted(missing))
        raise BenchmarkError(f'CSV is missing required columns ({missing_list}): {path}')

    frame = frame.copy()
    frame['mode'] = frame['mode'].fillna(expected_mode)
    for column in ('sequence', 'sign_ns', 'verify_ns', 'age_ns', 'e2e_ns', 'result_code'):
        frame[column] = pd.to_numeric(frame[column], errors='coerce')

    invalid_numeric = frame[['e2e_ns', 'result_code']].isna().any(axis=1)
    if invalid_numeric.any():
        raise BenchmarkError(f'CSV contains non-numeric e2e_ns or result_code values: {path}')

    frame['e2e_ms'] = frame['e2e_ns'] / 1_000_000.0
    return frame


def positive_latency(frame: pd.DataFrame) -> pd.Series:
    values = frame.loc[frame['e2e_ns'] > 0, 'e2e_ms'].dropna()
    if values.empty:
        raise BenchmarkError('No positive e2e_ns samples are available for plotting')
    return values


def save_no_data_plot(output_path: Path, title: str, message: str) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.set_title(title)
    ax.text(0.5, 0.5, message, ha='center', va='center', transform=ax.transAxes)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    log(f'Saved: {output_path}')


def plot_latency_box(
    plain: pd.DataFrame,
    app_sig: pd.DataFrame,
    output_path: Path,
    *,
    title: str,
    ylim: tuple[float, float] | None = None,
    note: str | None = None,
) -> None:
    log(f'Generating latency comparison box plot: {output_path}')
    plain_values = positive_latency(plain)
    app_sig_values = positive_latency(app_sig)
    labels = [f'plain (n={len(plain_values)})', f'app_sig (n={len(app_sig_values)})']

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.boxplot(
        [plain_values, app_sig_values],
        tick_labels=labels,
        showmeans=True,
        patch_artist=True,
        boxprops={'facecolor': '#e0f2fe', 'edgecolor': '#475569'},
        medianprops={'color': '#0f172a', 'linewidth': 2},
        meanprops={
            'marker': 'o',
            'markerfacecolor': '#f97316',
            'markeredgecolor': '#f97316',
        },
        whiskerprops={'color': '#475569'},
        capprops={'color': '#475569'},
    )
    ax.set_title(title)
    ax.set_ylabel('Latency (ms)')
    if ylim is not None:
        ax.set_ylim(*ylim)
    if note:
        ax.text(
            0.01,
            0.98,
            note,
            transform=ax.transAxes,
            ha='left',
            va='top',
            fontsize=9,
            color='#64748b',
        )
    ax.grid(axis='y', color='#e2e8f0', linewidth=0.8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    log(f'Saved: {output_path}')


def percentile_series(values: pd.Series) -> pd.DataFrame:
    sorted_values = values.sort_values(ignore_index=True)
    count = len(sorted_values)
    percentiles = [(index + 1) / count * 100.0 for index in range(count)]
    return pd.DataFrame({'latency_ms': sorted_values, 'percentile': percentiles})


def plot_latency_cdf(app_sig: pd.DataFrame, output_path: Path) -> None:
    log('Generating app_sig latency CDF')
    values = positive_latency(app_sig)
    cdf = percentile_series(values)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(cdf['latency_ms'], cdf['percentile'], color='#2563eb', linewidth=2)
    for label_y, (percentile, color) in zip(
        (52, 66, 80),
        ((50, '#64748b'), (95, '#f97316'), (99, '#dc2626')),
    ):
        latency = values.quantile(percentile / 100.0)
        ax.axvline(latency, color=color, linestyle='--', linewidth=1)
        ax.text(
            latency,
            label_y,
            f'p{percentile}: {latency:.3f} ms',
            color=color,
            fontsize=9,
            rotation=90,
            va='center',
            ha='right',
        )

    ax.set_title('End-to-End Latency CDF')
    ax.text(
        0.01,
        0.96,
        'Note: p99 is affected by observed tail latency/outliers.',
        transform=ax.transAxes,
        ha='left',
        va='top',
        fontsize=9,
        color='#64748b',
    )
    ax.set_xlabel('Latency (ms)')
    ax.set_ylabel('Percentile')
    ax.set_ylim(0, 100)
    ax.grid(color='#e2e8f0', linewidth=0.8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    log(f'Saved: {output_path}')


def plot_success_rate(app_sig: pd.DataFrame, output_path: Path) -> None:
    log('Generating verification success-rate chart')
    total = len(app_sig)
    if total == 0:
        save_no_data_plot(output_path, 'Verification Success Rate', 'No app_sig rows available')
        return

    ok_count = int((app_sig['result_code'] == RESULT_OK).sum())
    fail_count = total - ok_count
    ok_rate = ok_count / total * 100.0

    fig, ax = plt.subplots(figsize=(8, 2.6))
    ax.barh(['Verification success'], [ok_rate], color='#16a34a', edgecolor='#475569', linewidth=1)
    ax.text(
        min(ok_rate + 2, 98),
        0,
        f'{ok_rate:.1f}% ({ok_count}/{total})',
        ha='right' if ok_rate > 96 else 'left',
        va='center',
        fontsize=12,
        fontweight='bold',
        color='#0f172a',
    )
    if fail_count:
        ax.text(
            0.01,
            0.12,
            f'Non-OK results: {fail_count}/{total}',
            transform=ax.transAxes,
            ha='left',
            va='bottom',
            fontsize=9,
            color='#64748b',
        )

    ax.set_title('Verification Success Rate')
    ax.set_xlabel('Share of app_sig samples (%)')
    ax.set_xlim(0, 100)
    ax.grid(axis='x', color='#e2e8f0', linewidth=0.8)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    log(f'Saved: {output_path}')


def summarize_mode(mode: str, frame: pd.DataFrame) -> dict[str, object]:
    values = positive_latency(frame)
    total = len(frame)
    ok_count = int((frame['result_code'] == RESULT_OK).sum())
    return {
        'mode': mode,
        'samples': total,
        'p50_ms': values.quantile(0.50),
        'p95_ms': values.quantile(0.95),
        'p99_ms': values.quantile(0.99),
        'max_ms': values.max(),
        'success_rate': ok_count / total * 100.0 if total else 0.0,
    }


def build_summary(plain: pd.DataFrame, app_sig: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            summarize_mode('plain', plain),
            summarize_mode('app_sig', app_sig),
        ]
    )


def print_summary(summary: pd.DataFrame) -> None:
    display = summary.copy()
    for column in ('p50_ms', 'p95_ms', 'p99_ms', 'max_ms', 'success_rate'):
        display[column] = display[column].map(lambda value: f'{value:.3f}')
    log('Summary table:')
    print(display.to_string(index=False), flush=True)


def save_summary_markdown(summary: pd.DataFrame, output_path: Path) -> None:
    lines = [
        '# Benchmark Summary',
        '',
        'Units: milliseconds.',
        '',
        '| mode | samples | p50_ms | p95_ms | p99_ms | max_ms | success_rate |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |',
    ]
    for row in summary.to_dict('records'):
        lines.append(
            '| {mode} | {samples} | {p50_ms:.3f} | {p95_ms:.3f} | {p99_ms:.3f} | '
            '{max_ms:.3f} | {success_rate:.1f}% |'.format(**row)
        )
    app_sig = summary.loc[summary['mode'] == 'app_sig'].iloc[0]
    lines.extend(
        [
            '',
            'Verification success rate: {:.1f}% ({}/{})'.format(
                app_sig['success_rate'],
                int(round(app_sig['samples'] * app_sig['success_rate'] / 100.0)),
                int(app_sig['samples']),
            ),
            '',
            (
                'Interpretation: the main app_sig latency distribution is low, '
                'but tail latency exists. Do not interpret this run as app_sig '
                'always staying under 10 ms.'
            ),
            '',
        ]
    )
    output_path.write_text('\n'.join(lines), encoding='utf-8')
    log(f'Saved: {output_path}')


def ensure_parent_dirs(paths: Iterable[Path]) -> None:
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run ROS 2 PQC benchmarks and generate latency plots.'
    )
    parser.add_argument('--count', type=int, default=100)
    parser.add_argument('--rate-hz', type=float, default=20.0)
    parser.add_argument('--plain-csv', type=Path, default=Path('/tmp/plain.csv'))
    parser.add_argument('--app-sig-csv', type=Path, default=Path('/tmp/app_sig.csv'))
    parser.add_argument('--keys-dir', default='./src/keys')
    parser.add_argument('--output-dir', type=Path, default=Path('docs'))
    parser.add_argument(
        '--plot-only',
        action='store_true',
        help='Skip ROS 2 benchmark execution and regenerate plots from existing CSV files.',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plain_csv = args.plain_csv.expanduser()
    app_sig_csv = args.app_sig_csv.expanduser()
    output_dir = args.output_dir.expanduser()
    latency_box_full = output_dir / 'fig_latency_box_full.png'
    latency_box_zoom = output_dir / 'fig_latency_box_zoom.png'
    latency_cdf = output_dir / 'fig_latency_cdf.png'
    success_rate = output_dir / 'fig_success_rate.png'
    summary_md = output_dir / 'benchmark_summary.md'

    try:
        ensure_parent_dirs(
            [plain_csv, app_sig_csv, latency_box_full, latency_box_zoom, latency_cdf, success_rate, summary_md]
        )
        if args.plot_only:
            log('Plot-only mode: using existing CSV files and skipping ROS 2 launch commands')
        else:
            remove_stale_csv(plain_csv)
            remove_stale_csv(app_sig_csv)

            run_command(
                [
                    'ros2',
                    'launch',
                    'ros2_pqc_bringup',
                    'bench_plain.launch.py',
                    f'count:={args.count}',
                    f'rate_hz:={args.rate_hz:g}',
                    f'output_csv:={plain_csv}',
                ]
            )
            run_command(
                [
                    'ros2',
                    'launch',
                    'ros2_pqc_bringup',
                    'bench_app_sig.launch.py',
                    f'count:={args.count}',
                    f'rate_hz:={args.rate_hz:g}',
                    f'output_csv:={app_sig_csv}',
                    f'keys_dir:={args.keys_dir}',
                ]
            )

        plain = load_csv(plain_csv, 'plain')
        app_sig = load_csv(app_sig_csv, 'app_sig')
        combined = pd.concat([plain, app_sig], ignore_index=True)
        log(f'Loaded {len(combined)} samples: plain={len(plain)}, app_sig={len(app_sig)}')

        summary = build_summary(plain, app_sig)
        print_summary(summary)
        save_summary_markdown(summary, summary_md)
        plot_latency_box(
            plain,
            app_sig,
            latency_box_full,
            title='End-to-End Latency Comparison (Full Range)',
            note='Full range includes all observed outliers.',
        )
        plot_latency_box(
            plain,
            app_sig,
            latency_box_zoom,
            title='End-to-End Latency Comparison (0-15 ms Zoom)',
            ylim=(0, 15),
            note='Zoomed view improves readability of the main distribution.',
        )
        plot_latency_cdf(app_sig, latency_cdf)
        plot_success_rate(app_sig, success_rate)
        log('Benchmark pipeline complete')
        return 0
    except BenchmarkError as exc:
        print(f'[benchmark] ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
