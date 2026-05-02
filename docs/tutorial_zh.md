# ros2-pqc-secure-comm 教學

這份教學帶你從 Docker image、編譯、產生 demo key、執行 demo，到輸出 benchmark CSV。目標平台是 arm64，ROS 版本是 Humble。

## 1. 建立開發 image

在 workspace 根目錄執行：

```bash
docker build --no-cache \
  --platform linux/arm64/v8 \
  -t ros2-pqc-dev:humble-arm64 .
```

這個 image 以 `ros:humble-ros-base-jammy` 為基底，並安裝：

- colcon
- build tools
- liboqs `0.14.0`
- liboqs-python
- Python test utilities

確認 OQS：

```bash
docker run --rm --platform linux/arm64/v8 \
  ros2-pqc-dev:humble-arm64 \
  python3 -c "import oqs; print(oqs.oqs_version()); print(oqs.get_enabled_sig_mechanisms())"
```

輸出應包含：

```text
0.14.0
ML-DSA-44
```

## 2. 進入 container

```bash
docker run -it --rm \
  --platform linux/arm64/v8 \
  -v /Users/draganlegend/Documents/ros2_ws:/ros2_ws \
  -w /ros2_ws \
  ros2-pqc-dev:humble-arm64
```

如果你的 workspace 不在這個路徑，請把 volume 左側改成你的實際路徑。

## 3. 編譯 workspace

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

檢查 package：

```bash
ros2 pkg list | grep ros2_pqc
```

應看到：

```text
ros2_pqc_bench
ros2_pqc_bringup
ros2_pqc_crypto
ros2_pqc_demo
ros2_pqc_interfaces
ros2_pqc_signer
ros2_pqc_verifier
```

## 4. 產生 demo keys

```bash
ros2 run ros2_pqc_crypto pqc_generate_demo_keys \
  --keys-dir /ros2_ws/src/keys \
  --overwrite
```

這會產生：

```text
src/keys/signer/mldsa44_private.key
src/keys/trust/demo_source_mldsa44_pub.key
src/keys/trust/trust_store.yaml
```

注意：`mldsa44_private.key` 是私鑰，只能用於 demo，不可 commit。

## 5. 執行 plain mode

plain mode 不做簽章、驗章、防重放或 TTL 檢查，用來當 benchmark baseline。

```bash
ros2 launch ros2_pqc_bringup plain.launch.py
```

流程：

```text
raw_cmd_pub
  -> /cmd_vel/raw
  -> plain_cmd_echo
```

## 6. 執行 app_sig mode

```bash
ros2 launch ros2_pqc_bringup app_sig.launch.py \
  keys_dir:=/ros2_ws/src/keys
```

流程：

```text
raw_cmd_pub
  -> /cmd_vel/raw
  -> ros2_pqc_signer
  -> /cmd_vel/signed
  -> ros2_pqc_verifier
  -> /cmd_vel/verified
  -> verified_cmd_echo
```

Verifier 會對每次驗證發佈：

```text
/pqc/verify_event
```

你可以另外開一個 terminal 看事件：

```bash
source /opt/ros/humble/setup.bash
source /ros2_ws/install/setup.bash
ros2 topic echo /pqc/verify_event
```

## 7. 執行 benchmark

plain benchmark：

```bash
ros2 launch ros2_pqc_bringup bench_plain.launch.py \
  count:=100 \
  rate_hz:=20 \
  output_csv:=/tmp/ros2_pqc_plain.csv
```

app_sig benchmark：

```bash
ros2 launch ros2_pqc_bringup bench_app_sig.launch.py \
  count:=100 \
  rate_hz:=20 \
  output_csv:=/tmp/ros2_pqc_app_sig.csv \
  keys_dir:=/ros2_ws/src/keys
```

輸出摘要：

```bash
ros2 run ros2_pqc_bench pqc_bench_summary /tmp/ros2_pqc_app_sig.csv
```

CSV 欄位：

```text
run_id,mode,sequence,sign_ns,verify_ns,age_ns,e2e_ns,result_code
```

## 8. 常見問題

### `Unknown package 'ros2_pqc_interfaces'`

請確認你已經重新編譯並 source：

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### signer 顯示 key file does not exist

請先產生 demo keys：

```bash
ros2 run ros2_pqc_crypto pqc_generate_demo_keys \
  --keys-dir /ros2_ws/src/keys \
  --overwrite
```

### `sign_ns` 為 0

目前 `SignedTwist.msg` 沒有 signer processing duration 欄位，因此 MVP benchmark 保留欄位並填 `0`。若要嚴格量測簽章耗時，後續版本可以新增 signer event 或擴充 message。
