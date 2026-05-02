# ros2-pqc-secure-comm

`ros2-pqc-secure-comm` is a ROS 2 Humble MVP for application-layer command protection. It demonstrates ML-DSA-44 signing and verification for `geometry_msgs/Twist`, SHA-256 payload digests, sequence-based replay protection, TTL validation, and benchmark CSV output.

This project is not SROS2 and does not replace DDS-Security. It protects the command semantics at the application layer while keeping the downstream controller interface as a normal `Twist` topic.

## Features

- ROS 2 Humble
- Python-first implementation
- `geometry_msgs/Twist` command demo
- ML-DSA-44 signing and verification
- SHA-256 canonical payload digest
- static trust store
- sequence-based replay protection
- TTL / age validation
- plain mode and app_sig mode
- benchmark CSV output
- arm64 Docker development flow

## Repository Layout

```text
src/
├── ros2_pqc_interfaces   # SignedTwist / VerificationEvent messages
├── ros2_pqc_crypto       # adapter, OQS backend, key store, replay window
├── ros2_pqc_signer       # /cmd_vel/raw -> /cmd_vel/signed
├── ros2_pqc_verifier     # /cmd_vel/signed -> /cmd_vel/verified + events
├── ros2_pqc_demo         # demo publisher and echo nodes
├── ros2_pqc_bench        # benchmark runner and CSV summary
├── ros2_pqc_bringup      # launch files and configs
└── keys                  # demo key material and trust store
```

## Quick Start

Build the arm64 image:

```bash
docker build --no-cache \
  --platform linux/arm64/v8 \
  -t ros2-pqc-dev:humble-arm64 .
```

Start the container:

```bash
docker run -it --rm \
  --platform linux/arm64/v8 \
  -v /Users/draganlegend/Documents/ros2_ws:/ros2_ws \
  -w /ros2_ws \
  ros2-pqc-dev:humble-arm64
```

Build inside the container:

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Check the packages:

```bash
ros2 pkg list | grep ros2_pqc
ros2 interface show ros2_pqc_interfaces/msg/SignedTwist
```

## Generate Demo Keys

Private keys must not be committed. Before running the demo for the first time, generate demo key material inside the container:

```bash
source /opt/ros/humble/setup.bash
source /ros2_ws/install/setup.bash

ros2 run ros2_pqc_crypto pqc_generate_demo_keys \
  --keys-dir /ros2_ws/src/keys \
  --overwrite
```

The generated private key is:

```text
src/keys/signer/mldsa44_private.key
```

It is for demos only and must not be used in production.

## Run the Demo

Plain mode:

```bash
ros2 launch ros2_pqc_bringup plain.launch.py
```

app_sig mode:

```bash
ros2 launch ros2_pqc_bringup app_sig.launch.py \
  keys_dir:=/ros2_ws/src/keys
```

app_sig topic graph:

```text
/cmd_vel/raw
  -> ros2_pqc_signer
  -> /cmd_vel/signed
  -> ros2_pqc_verifier
  -> /cmd_vel/verified
  -> verified_cmd_echo

ros2_pqc_verifier
  -> /pqc/verify_event
```

## Benchmark

Plain benchmark:

```bash
ros2 launch ros2_pqc_bringup bench_plain.launch.py \
  count:=100 \
  rate_hz:=20 \
  output_csv:=/tmp/ros2_pqc_plain.csv
```

app_sig benchmark:

```bash
ros2 launch ros2_pqc_bringup bench_app_sig.launch.py \
  count:=100 \
  rate_hz:=20 \
  output_csv:=/tmp/ros2_pqc_app_sig.csv \
  keys_dir:=/ros2_ws/src/keys
```

Summarize the CSV:

```bash
ros2 run ros2_pqc_bench pqc_bench_summary /tmp/ros2_pqc_app_sig.csv
```

CSV columns:

```text
run_id,mode,sequence,sign_ns,verify_ns,age_ns,e2e_ns,result_code
```

The current `SignedTwist.msg` does not carry signer processing duration, so the MVP benchmark keeps the `sign_ns` column and records `0`. To measure `sign_ns` strictly, add a signer event or extend the message in a future version.

## Security Notes

- Demo keys are for demonstration only.
- `src/keys/signer/*.key` must not be committed.
- v1 does not encrypt payloads.
- v1 does not perform dynamic key exchange.
- v1 does not replace DDS-Security.
- The static trust store is intended for MVP and experiments.

See [docs/tutorial_en.md](docs/tutorial_en.md) for the full walkthrough.
