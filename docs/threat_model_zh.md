# 威脅模型

## 保護目標

v1 聚焦在 ROS 2 command topic 的應用層保護，尤其是 `/cmd_vel/raw` 到 `/cmd_vel/verified` 之間的命令語意。

保護目標：

- 命令完整性
- 命令來源真實性
- replay 防護
- 過期命令拒絕
- 驗證結果可觀測性

## 攻擊者能力

v1 假設攻擊者可能：

- 發佈偽造的 `SignedTwist`
- 修改 command payload
- 重送舊的 signed command
- 發送過期 command
- 使用未受信任 key id 或 source id

## 防護機制

### 完整性

Verifier 會重建 canonical payload，重算 SHA-256 digest，並與 message 中的 `payload_digest` 比對。payload 被改動會導致 `RESULT_DIGEST_MISMATCH`。

### 真實性

Verifier 只信任 static trust store 裡啟用的 `(source_id, key_id)`。簽章驗證失敗會導致 `RESULT_SIG_INVALID`。

### Replay Protection

Replay state 以 `(source_id, key_id)` 為單位維護。重複或過舊 sequence 會導致 `RESULT_REPLAY`。

### TTL / Age

Verifier 計算：

```text
age_ns = verifier_receive_time_ns - source_stamp_ns
```

若 `age_ns > ttl_ms * 1_000_000`，結果為 `RESULT_EXPIRED`。

## 非目標

v1 不防護：

- payload confidentiality
- DDS discovery metadata exposure
- network-level traffic analysis
- private key theft after host compromise
- dynamic key rotation
- Sybil identity management
- denial of service

## 安全注意事項

- demo keys 只適合教學與測試。
- private key 必須留在 signer 端。
- trust store 應由部署者明確管理。
- 正式系統仍應搭配 DDS-Security、網路隔離、主機安全與金鑰管理。
