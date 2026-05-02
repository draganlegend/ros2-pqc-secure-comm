# Benchmark Summary

Units: milliseconds.

| mode | samples | p50_ms | p95_ms | p99_ms | max_ms | success_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| plain | 100 | 0.745 | 1.119 | 1.231 | 1.262 | 100.0% |
| app_sig | 99 | 3.269 | 7.456 | 116.083 | 162.747 | 100.0% |

Verification success rate: 100.0% (99/99)

Interpretation: the main app_sig latency distribution is low, but tail latency exists. Do not interpret this run as app_sig always staying under 10 ms.
