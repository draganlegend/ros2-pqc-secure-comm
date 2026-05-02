# Benchmark 計畫

## 目標

benchmark 目標是比較：

- `plain`: 原生 ROS 2 command flow
- `app_sig`: ML-DSA-44 簽章、驗章、digest、TTL、replay protection flow

## 執行 plain benchmark

```bash
ros2 launch ros2_pqc_bringup bench_plain.launch.py \
  count:=100 \
  rate_hz:=20 \
  output_csv:=/tmp/ros2_pqc_plain.csv
```

plain mode 會發佈 `Twist` 到 `/cmd_vel/raw`，同一個 node 訂閱該 topic 取得 publish-to-receive 的基準延遲。

## 執行 app_sig benchmark

```bash
ros2 launch ros2_pqc_bringup bench_app_sig.launch.py \
  count:=100 \
  rate_hz:=20 \
  output_csv:=/tmp/ros2_pqc_app_sig.csv \
  keys_dir:=/ros2_ws/src/keys
```

app_sig mode 會啟動：

- `ros2_pqc_signer`
- `ros2_pqc_verifier`
- `latency_runner`

`latency_runner` 發佈 `/cmd_vel/raw`，並訂閱 `/pqc/verify_event` 產出 CSV。

## CSV 格式

```text
run_id,mode,sequence,sign_ns,verify_ns,age_ns,e2e_ns,result_code
```

欄位：

- `run_id`: 每次 benchmark 的短 ID
- `mode`: `plain` 或 `app_sig`
- `sequence`: command sequence
- `sign_ns`: signer processing time，MVP 目前填 `0`
- `verify_ns`: verifier processing time
- `age_ns`: verifier receive time 與 signer source stamp 的差距
- `e2e_ns`: 成功時的端到端時間，失敗時為 `0`
- `result_code`: 驗證結果代碼

## 摘要

```bash
ros2 run ros2_pqc_bench pqc_bench_summary /tmp/ros2_pqc_app_sig.csv
```

摘要輸出：

- rows
- ok
- failed
- verify mean / median / p95
- e2e mean / median / p95

## 建議測試組合

```bash
ros2 launch ros2_pqc_bringup bench_plain.launch.py count:=100 rate_hz:=10 output_csv:=/tmp/plain_10hz.csv
ros2 launch ros2_pqc_bringup bench_plain.launch.py count:=100 rate_hz:=20 output_csv:=/tmp/plain_20hz.csv
ros2 launch ros2_pqc_bringup bench_app_sig.launch.py count:=100 rate_hz:=10 output_csv:=/tmp/app_sig_10hz.csv keys_dir:=/ros2_ws/src/keys
ros2 launch ros2_pqc_bringup bench_app_sig.launch.py count:=100 rate_hz:=20 output_csv:=/tmp/app_sig_20hz.csv keys_dir:=/ros2_ws/src/keys
```

## MVP 限制

目前 `SignedTwist.msg` 沒有 signer processing duration，因此 `sign_ns` 會是 `0`。這不影響 verifier latency、age、e2e 與 result_code 統計。若要完整符合 sign timing 定義，建議新增 signer-side event 或在 `SignedTwist` 增加 `sign_ns` 欄位。
