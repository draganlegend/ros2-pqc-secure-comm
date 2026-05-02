# 架構說明

## 目標

v1 的目標是在 ROS 2 應用層保護控制命令：

- 驗證命令來源
- 保護命令完整性
- 防止 sequence replay
- 檢查命令是否過期
- 輸出可量測的驗證事件與 benchmark CSV

v1 不提供 payload encryption，不做 dynamic key exchange，也不保證跨 DDS vendor 的安全協定相容性。

## Package 職責

```text
ros2_pqc_interfaces
  SignedTwist.msg
  VerificationEvent.msg

ros2_pqc_crypto
  SignatureBackend abstraction
  OqsMlDsa44Backend
  TwistAdapter
  TrustStore
  ReplayWindow
  demo key generator

ros2_pqc_signer
  subscribe /cmd_vel/raw
  build canonical payload
  SHA-256 digest
  ML-DSA-44 sign
  publish /cmd_vel/signed

ros2_pqc_verifier
  subscribe /cmd_vel/signed
  schema / algorithm / trust checks
  recompute digest
  verify signature
  TTL check
  replay check
  publish /cmd_vel/verified on success
  always publish /pqc/verify_event

ros2_pqc_demo
  raw command publisher
  verified command echo

ros2_pqc_bench
  benchmark runner
  CSV writer
  summary command

ros2_pqc_bringup
  launch files
  YAML configs
```

## app_sig 資料流

```text
/cmd_vel/raw
  -> ros2_pqc_signer
  -> /cmd_vel/signed
  -> ros2_pqc_verifier
  -> /cmd_vel/verified

ros2_pqc_verifier
  -> /pqc/verify_event
```

## Canonical Payload

`TwistAdapter` 建立 deterministic binary payload，不使用 JSON，也不使用 raw ROS serialization。v1 canonical payload 包含：

- `payload_version`
- `payload_schema`
- `topic_name`
- `source_id`
- `key_id`
- `source_stamp_ns`
- `sequence`
- `ttl_ms`
- `linear.x`
- `linear.y`
- `linear.z`
- `angular.x`
- `angular.y`
- `angular.z`

Signer 與 verifier 都透過同一個 adapter 建立 canonical bytes，避免 canonicalization 邏輯散落在 node 裡。

## 驗證順序

Verifier 對每筆 `SignedTwist` 執行：

1. payload version 檢查
2. payload schema 檢查
3. signature / hash algorithm 檢查
4. trust store 查詢
5. canonical bytes 重建
6. SHA-256 digest 重算
7. digest 比對
8. ML-DSA-44 signature verification
9. TTL / age 檢查
10. replay window 檢查
11. 發佈 `VerificationEvent`

只有 `RESULT_OK` 才會發佈 `/cmd_vel/verified`。

## 已知 MVP 限制

- v1 只支援 `geometry_msgs/Twist`
- v1 只支援 ML-DSA-44
- v1 只支援 SHA-256
- `sign_ns` 目前沒有從 signer node 暴露，benchmark 先填 `0`
- trust store 是靜態 YAML
- demo key 不適合正式環境
