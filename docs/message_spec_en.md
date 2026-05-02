# Message Spec

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

Field semantics:

- `command`: protected `geometry_msgs/Twist`
- `payload_version`: fixed to `1` in v1
- `payload_schema`: fixed to `ros2_pqc.twist.v1` in v1
- `source_stamp`: signer timestamp
- `sequence`: monotonically increasing signer-side sequence
- `ttl_ms`: maximum acceptable age at the verifier
- `source_id`: command source identity
- `key_id`: key identity in the trust store
- `sig_scheme`: v1 uses `SIG_SCHEME_ML_DSA_44`
- `hash_scheme`: v1 uses `HASH_SCHEME_SHA256`
- `payload_digest`: SHA-256 digest of the canonical bytes
- `signature`: ML-DSA-44 signature over the digest

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

Rules:

- the verifier must publish one `VerificationEvent` for every received `SignedTwist`
- `result_code == RESULT_OK` means `ok=true`
- `result_code != RESULT_OK` means `ok=false`
- `reason` is a debug string only
- benchmark and statistics should depend on `result_code`

## Canonical Payload

v1 uses deterministic binary encoding. It does not use JSON and does not use raw ROS serialization.

Field order:

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

The current implementation uses little-endian binary packing:

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

Only `RESULT_OK` publishes `/cmd_vel/verified`.
