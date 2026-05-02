# ros2-pqc-secure-comm Tutorial

This tutorial walks through the Docker image, build process, demo key generation, demo launch files, and benchmark CSV output. The target platform is arm64 and the ROS version is Humble.

## 1. Build the Development Image

Run this from the workspace root:

```bash
docker build --no-cache \
  --platform linux/arm64/v8 \
  -t ros2-pqc-dev:humble-arm64 .
```

The image is based on `ros:humble-ros-base-jammy` and installs:

- colcon
- build tools
- liboqs `0.14.0`
- liboqs-python
- Python test utilities

Check OQS:

```bash
docker run --rm --platform linux/arm64/v8 \
  ros2-pqc-dev:humble-arm64 \
  python3 -c "import oqs; print(oqs.oqs_version()); print(oqs.get_enabled_sig_mechanisms())"
```

The output should include:

```text
0.14.0
ML-DSA-44
```

## 2. Start the Container

```bash
docker run -it --rm \
  --platform linux/arm64/v8 \
  -v /Users/draganlegend/Documents/ros2_ws:/ros2_ws \
  -w /ros2_ws \
  ros2-pqc-dev:humble-arm64
```

If your workspace is somewhere else, replace the left side of the volume mount with your actual path.

## 3. Build the Workspace

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Check the packages:

```bash
ros2 pkg list | grep ros2_pqc
```

Expected packages:

```text
ros2_pqc_bench
ros2_pqc_bringup
ros2_pqc_crypto
ros2_pqc_demo
ros2_pqc_interfaces
ros2_pqc_signer
ros2_pqc_verifier
```

## 4. Generate Demo Keys

```bash
ros2 run ros2_pqc_crypto pqc_generate_demo_keys \
  --keys-dir /ros2_ws/src/keys \
  --overwrite
```

This creates:

```text
src/keys/signer/mldsa44_private.key
src/keys/trust/demo_source_mldsa44_pub.key
src/keys/trust/trust_store.yaml
```

`mldsa44_private.key` is a private key. It is for demos only and must not be committed.

## 5. Run Plain Mode

Plain mode does not sign, verify, reject replays, or check TTL. It is the benchmark baseline.

```bash
ros2 launch ros2_pqc_bringup plain.launch.py
```

Flow:

```text
raw_cmd_pub
  -> /cmd_vel/raw
  -> plain_cmd_echo
```

## 6. Run app_sig Mode

```bash
ros2 launch ros2_pqc_bringup app_sig.launch.py \
  keys_dir:=/ros2_ws/src/keys
```

Flow:

```text
raw_cmd_pub
  -> /cmd_vel/raw
  -> ros2_pqc_signer
  -> /cmd_vel/signed
  -> ros2_pqc_verifier
  -> /cmd_vel/verified
  -> verified_cmd_echo
```

The verifier publishes one event for every verification attempt:

```text
/pqc/verify_event
```

In another terminal, inspect the events:

```bash
source /opt/ros/humble/setup.bash
source /ros2_ws/install/setup.bash
ros2 topic echo /pqc/verify_event
```

## 7. Run Benchmarks

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

## 8. Troubleshooting

### `Unknown package 'ros2_pqc_interfaces'`

Make sure the workspace is rebuilt and sourced:

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### signer reports that the key file does not exist

Generate demo keys first:

```bash
ros2 run ros2_pqc_crypto pqc_generate_demo_keys \
  --keys-dir /ros2_ws/src/keys \
  --overwrite
```

### `sign_ns` is 0

The current `SignedTwist.msg` does not carry signer processing duration, so the MVP benchmark keeps the column and records `0`. To measure signing duration strictly, add a signer event or extend the message in a future version.
