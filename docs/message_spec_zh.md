# 訊息格式

## SignedTwist

`ros2_pqc_interfaces/msg/SignedTwist.msg`

```text
std_msgs/Header header
geometry_msgs/Twist command

uint8 payload_version
string payload_schema

builtin_interfaces/Time source_stamp
uint64 sequence
uint32 ttl_ms

string source_id
string key_id

uint8 sig_scheme
uint8 hash_scheme

uint8 SIG_SCHEME_UNKNOWN=0
uint8 SIG_SCHEME_ML_DSA_44=1

uint8 HASH_SCHEME_UNKNOWN=0
uint8 HASH_SCHEME_SHA256=1

uint8[] payload_digest
uint8[] signature
```

欄位語意：

- `command`: 被保護的 `geometry_msgs/Twist`
- `payload_version`: v1 固定為 `1`
- `payload_schema`: v1 固定為 `ros2_pqc.twist.v1`
- `source_stamp`: signer 產生簽章時的時間
- `sequence`: signer 端遞增序號
- `ttl_ms`: verifier 可接受的最大 age
- `source_id`: 命令來源識別
- `key_id`: trust store 中的 key 識別
- `sig_scheme`: v1 使用 `SIG_SCHEME_ML_DSA_44`
- `hash_scheme`: v1 使用 `HASH_SCHEME_SHA256`
- `payload_digest`: canonical bytes 的 SHA-256 digest
- `signature`: 對 digest 的 ML-DSA-44 signature

## VerificationEvent

`ros2_pqc_interfaces/msg/VerificationEvent.msg`

```text
std_msgs/Header header

bool ok
uint8 result_code
string reason

string source_id
string key_id
uint64 sequence

uint64 verify_ns
uint64 age_ns

uint8 RESULT_OK=0
uint8 RESULT_SCHEMA_ERROR=1
uint8 RESULT_ALG_UNSUPPORTED=2
uint8 RESULT_DIGEST_MISMATCH=3
uint8 RESULT_SIG_INVALID=4
uint8 RESULT_REPLAY=5
uint8 RESULT_EXPIRED=6
uint8 RESULT_KEY_NOT_TRUSTED=7
uint8 RESULT_INTERNAL_ERROR=8
```

規則：

- verifier 每次收到 `SignedTwist` 都必須發出一筆 `VerificationEvent`
- `result_code == RESULT_OK` 時 `ok=true`
- `result_code != RESULT_OK` 時 `ok=false`
- `reason` 只作為 debug 字串
- benchmark 與統計應依賴 `result_code`

## Canonical Payload

v1 使用 deterministic binary encoding，不使用 JSON，不使用 raw ROS serialization。

欄位順序：

```text
payload_version
payload_schema
topic_name
source_id
key_id
source_stamp_ns
sequence
ttl_ms
linear.x
linear.y
linear.z
angular.x
angular.y
angular.z
```

目前實作使用 little-endian binary packing：

- string: `uint32 length` + UTF-8 bytes
- integer: fixed-width little-endian
- float: IEEE-754 double little-endian

## Result Code

```text
0 RESULT_OK
1 RESULT_SCHEMA_ERROR
2 RESULT_ALG_UNSUPPORTED
3 RESULT_DIGEST_MISMATCH
4 RESULT_SIG_INVALID
5 RESULT_REPLAY
6 RESULT_EXPIRED
7 RESULT_KEY_NOT_TRUSTED
8 RESULT_INTERNAL_ERROR
```

只有 `RESULT_OK` 會發佈 `/cmd_vel/verified`。
