# ros2-pqc-secure-comm

`ros2-pqc-secure-comm` 是一個 ROS 2 Humble 的應用層命令保護 MVP。它示範如何用 ML-DSA-44 對 `geometry_msgs/Twist` 控制命令做簽章、驗章、SHA-256 digest 檢查、sequence replay protection、TTL 驗證，以及 benchmark CSV 輸出。

這個專案不是 SROS2，也不是 DDS-Security 的替代品。它只保護命令語意層，目標是讓下游控制節點仍然接收一般 `Twist`，同時在上游加入可量測的 post-quantum signature pipeline。

## 功能

- ROS 2 Humble
- Python-first implementation
- `geometry_msgs/Twist` command demo
- ML-DSA-44 signature and verification
- SHA-256 canonical payload digest
- static trust store
- sequence-based replay protection
- TTL / age validation
- plain mode and app_sig mode
- benchmark CSV output
- arm64 Docker development flow

## 專案結構

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

## 快速開始

建立 arm64 image：

```bash
docker build --no-cache \
  --platform linux/arm64/v8 \
  -t ros2-pqc-dev:humble-arm64 .
```

啟動 container：

```bash
docker run -it --rm \
  --platform linux/arm64/v8 \
  -v /Users/draganlegend/Documents/ros2_ws:/ros2_ws \
  -w /ros2_ws \
  ros2-pqc-dev:humble-arm64
```

在 container 內編譯：

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

確認 package：

```bash
ros2 pkg list | grep ros2_pqc
ros2 interface show ros2_pqc_interfaces/msg/SignedTwist
```

## 產生 demo keys

私鑰不應 commit。第一次執行 demo 前，在 container 內產生 demo key：

```bash
source /opt/ros/humble/setup.bash
source /ros2_ws/install/setup.bash

ros2 run ros2_pqc_crypto pqc_generate_demo_keys \
  --keys-dir /ros2_ws/src/keys \
  --overwrite
```

產生的私鑰位於：

```text
src/keys/signer/mldsa44_private.key
```

這只適合 demo，不可用於正式環境。

## 執行 demo

plain mode：

```bash
ros2 launch ros2_pqc_bringup plain.launch.py
```

app_sig mode：

```bash
ros2 launch ros2_pqc_bringup app_sig.launch.py \
  keys_dir:=/ros2_ws/src/keys
```

app_sig topic graph：

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

目前 `SignedTwist.msg` 沒有 signer processing duration 欄位，因此 MVP benchmark 保留 `sign_ns` 欄位並填 `0`。若要嚴格量測 `sign_ns`，可以在後續版本新增 signer event 或擴充 message。

## 安全注意事項

- demo keys 只用於展示。
- `src/keys/signer/*.key` 不應 commit。
- v1 不做 payload encryption。
- v1 不做 dynamic key exchange。
- v1 不取代 DDS-Security。
- static trust store 只適合 MVP 和實驗用途。

更多說明請看 [docs/tutorial_zh.md](docs/tutorial_zh.md)。
