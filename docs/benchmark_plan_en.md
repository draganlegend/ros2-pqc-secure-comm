# Benchmark Plan

## Goal

The benchmark compares:

- `plain`: native ROS 2 command flow
- `app_sig`: ML-DSA-44 signing, verification, digest, TTL, and replay protection flow

## Run Plain Benchmark

```bash
ros2 launch ros2_pqc_bringup bench_plain.launch.py \
  count:=100 \
  rate_hz:=20 \
  output_csv:=/tmp/ros2_pqc_plain.csv
```

Plain mode publishes `Twist` messages to `/cmd_vel/raw` and subscribes to the same topic to measure a baseline publish-to-receive latency.

## Run app_sig Benchmark

```bash
ros2 launch ros2_pqc_bringup bench_app_sig.launch.py \
  count:=100 \
  rate_hz:=20 \
  output_csv:=/tmp/ros2_pqc_app_sig.csv \
  keys_dir:=/ros2_ws/src/keys
```

app_sig mode starts:

- `ros2_pqc_signer`
- `ros2_pqc_verifier`
- `latency_runner`

`latency_runner` publishes `/cmd_vel/raw` and subscribes to `/pqc/verify_event` to produce the CSV.

## CSV Format

```text
run_id,mode,sequence,sign_ns,verify_ns,age_ns,e2e_ns,result_code
```

Fields:

- `run_id`: short ID for each benchmark run
- `mode`: `plain` or `app_sig`
- `sequence`: command sequence
- `sign_ns`: signer processing time, currently `0` in the MVP
- `verify_ns`: verifier processing time
- `age_ns`: difference between verifier receive time and signer source stamp
- `e2e_ns`: end-to-end time on success, `0` on failure
- `result_code`: verification result code

## Summary

```bash
ros2 run ros2_pqc_bench pqc_bench_summary /tmp/ros2_pqc_app_sig.csv
```

The summary prints:

- rows
- ok
- failed
- verify mean / median / p95
- e2e mean / median / p95

## Suggested Runs

```bash
ros2 launch ros2_pqc_bringup bench_plain.launch.py count:=100 rate_hz:=10 output_csv:=/tmp/plain_10hz.csv
ros2 launch ros2_pqc_bringup bench_plain.launch.py count:=100 rate_hz:=20 output_csv:=/tmp/plain_20hz.csv
ros2 launch ros2_pqc_bringup bench_app_sig.launch.py count:=100 rate_hz:=10 output_csv:=/tmp/app_sig_10hz.csv keys_dir:=/ros2_ws/src/keys
ros2 launch ros2_pqc_bringup bench_app_sig.launch.py count:=100 rate_hz:=20 output_csv:=/tmp/app_sig_20hz.csv keys_dir:=/ros2_ws/src/keys
```

## MVP Limit

The current `SignedTwist.msg` does not carry signer processing duration, so `sign_ns` is `0`. This does not affect verifier latency, age, e2e, or result-code statistics. To fully measure signer timing, add a signer-side event or add `sign_ns` to `SignedTwist`.
