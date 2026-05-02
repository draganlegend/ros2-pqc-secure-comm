# Architecture

## Goal

v1 protects ROS 2 control commands at the application layer:

- authenticate command source
- protect command integrity
- reject sequence replays
- reject expired commands
- emit measurable verification events and benchmark CSV output

v1 does not provide payload encryption, dynamic key exchange, or cross-DDS-vendor security protocol compatibility.

## Package Responsibilities

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

## app_sig Data Flow

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

`TwistAdapter` builds deterministic binary payload bytes. It does not use JSON and does not use raw ROS serialization. The v1 canonical payload includes:

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

Both signer and verifier use the same adapter to build canonical bytes, keeping canonicalization out of node-specific logic.

## Verification Order

For every `SignedTwist`, the verifier performs:

1. payload version check
2. payload schema check
3. signature / hash algorithm check
4. trust store lookup
5. canonical bytes rebuild
6. SHA-256 digest recomputation
7. digest comparison
8. ML-DSA-44 signature verification
9. TTL / age check
10. replay window check
11. publish `VerificationEvent`

Only `RESULT_OK` publishes `/cmd_vel/verified`.

## Known MVP Limits

- v1 supports only `geometry_msgs/Twist`
- v1 supports only ML-DSA-44
- v1 supports only SHA-256
- `sign_ns` is not currently exposed by the signer node, so benchmarks record `0`
- the trust store is static YAML
- demo keys are not suitable for production
