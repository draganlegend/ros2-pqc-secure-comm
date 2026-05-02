# ros2-pqc-secure-comm

## 🔐 Project Overview

A ROS 2 application-layer secure communication pipeline using post-quantum
signature (ML-DSA-44) to protect control commands.

This project ensures:

- Command integrity (SHA-256 digest)
- Authenticity (ML-DSA signature)
- Replay protection (sequence window)
- Expiration control (TTL validation)
- Measurable latency (benchmark CSV)

It operates at the application layer and does not replace DDS-Security or SROS2.

## 🏗 Architecture

![architecture](docs/architecture.png)

## 📊 Benchmark Results

The benchmark compares a plain ROS 2 command path with the application-layer
signed command pipeline. Latency is measured as end-to-end command delivery time.

| Mode | Samples | p50 e2e | p95 e2e | p99 e2e | Max | Success Rate |
|------|--------:|--------:|--------:|--------:|----:|-------------:|
| plain | 100 | 0.745 ms | 1.119 ms | 1.231 ms | 1.262 ms | 100% |
| app_sig | 99 | 3.269 ms | 7.456 ms | 116.083 ms | 162.747 ms | 100% |

The `app_sig` path adds the expected signing and verification overhead while
keeping the main latency distribution low. Most `app_sig` samples complete
within single-digit milliseconds, while a small number of outliers introduce a
long-tail latency distribution. The p99 value is therefore affected by tail
latency and should not be interpreted as "always under 10 ms."

### Latency Distribution (Main Range)

![latency](docs/fig_latency_box_zoom.png)

### End-to-End Latency CDF

![cdf](docs/fig_latency_cdf.png)

<details>
<summary>Full Range Latency (including outliers)</summary>

![full](docs/fig_latency_box_full.png)

</details>

Language / 語言:

- [繁體中文 README](README_zh.md)
- [English README](README_en.md)

Documentation / 文件:

- [繁體中文教學](docs/tutorial_zh.md)
- [English tutorial](docs/tutorial_en.md)
- [架構說明](docs/architecture_zh.md) / [Architecture](docs/architecture_en.md)
- [威脅模型](docs/threat_model_zh.md) / [Threat model](docs/threat_model_en.md)
- [訊息格式](docs/message_spec_zh.md) / [Message spec](docs/message_spec_en.md)
- [Benchmark 說明](docs/benchmark_plan_zh.md) / [Benchmark plan](docs/benchmark_plan_en.md)
