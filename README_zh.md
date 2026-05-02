# ros2-pqc-secure-comm

語言：
[English](README.md) | [繁體中文](README_zh.md)

## 🔐 專案概述

一個 ROS 2 應用層安全通訊 pipeline，使用 post-quantum signature
（ML-DSA-44）保護控制命令。

這個專案確保：

- 命令完整性（SHA-256 digest）
- 來源真實性（ML-DSA signature）
- 重送防護（sequence window）
- 過期控制（TTL validation）
- 可量測延遲（benchmark CSV）

它運作在應用層，不取代 DDS-Security 或 SROS2。

## 🏗 系統架構

![architecture](docs/architecture.png)

## 📊 效能測試結果

benchmark 比較 plain ROS 2 command path 與 application-layer signed command
pipeline。延遲以端到端命令傳遞時間計算。

| Mode | Samples | p50 e2e | p95 e2e | p99 e2e | Max | Success Rate |
|------|--------:|--------:|--------:|--------:|----:|-------------:|
| plain | 100 | 0.745 ms | 1.119 ms | 1.231 ms | 1.262 ms | 100% |
| app_sig | 99 | 3.269 ms | 7.456 ms | 116.083 ms | 162.747 ms | 100% |

`app_sig` 路徑加入預期中的簽章與驗章 overhead，同時主要延遲分布仍維持在低範圍。
大多數 `app_sig` 樣本會在個位數毫秒內完成，但少數 outliers 造成 long-tail latency
distribution。因此 p99 受到 tail latency 影響，不應解讀成「永遠低於 10 ms」。

### 延遲分布（主要範圍）

![latency](docs/fig_latency_box_zoom.png)

### 端到端延遲 CDF

![cdf](docs/fig_latency_cdf.png)

<details>
<summary>完整延遲範圍（包含 outliers）</summary>

![full](docs/fig_latency_box_full.png)

</details>

## 重現 Benchmark

完整 benchmark 執行：

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash

python3 scripts/run_and_plot_benchmark.py \
  --count 100 \
  --rate-hz 20 \
  --keys-dir ./src/keys \
  --output-dir docs
```

plot-only mode 會使用既有 CSV 檔重新產生圖表，不重新執行 ROS 2 benchmark launch files：

```bash
python3 scripts/run_and_plot_benchmark.py \
  --plot-only \
  --plain-csv docs/benchmark_plain.csv \
  --app-sig-csv docs/benchmark_app_sig.csv \
  --output-dir docs
```

## Benchmark 環境

- ROS 2 Humble
- 本機單機 benchmark
- Count: 100
- Publish rate: 20 Hz
- Metric: 端到端命令傳遞延遲
- Mode comparison: plain vs app_sig

## 文件連結

- [Tutorial](docs/tutorial_en.md) / [繁體中文教學](docs/tutorial_zh.md)
- [架構說明](docs/architecture_zh.md) / [Architecture](docs/architecture_en.md)
- [威脅模型](docs/threat_model_zh.md) / [Threat model](docs/threat_model_en.md)
- [訊息格式](docs/message_spec_zh.md) / [Message spec](docs/message_spec_en.md)
- [Benchmark 說明](docs/benchmark_plan_zh.md) / [Benchmark plan](docs/benchmark_plan_en.md)
