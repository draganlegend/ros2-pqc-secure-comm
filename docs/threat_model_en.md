# Threat Model

## Protected Asset

v1 focuses on application-layer protection for ROS 2 command topics, especially the command semantics between `/cmd_vel/raw` and `/cmd_vel/verified`.

Protected goals:

- command integrity
- command source authenticity
- replay protection
- expired command rejection
- observable verification results

## Attacker Capabilities

v1 assumes an attacker may:

- publish forged `SignedTwist` messages
- modify command payloads
- replay old signed commands
- send expired commands
- use an untrusted key id or source id

## Protections

### Integrity

The verifier rebuilds the canonical payload, recomputes the SHA-256 digest, and compares it with `payload_digest`. A modified payload causes `RESULT_DIGEST_MISMATCH`.

### Authenticity

The verifier trusts only enabled `(source_id, key_id)` pairs from the static trust store. Signature verification failure causes `RESULT_SIG_INVALID`.

### Replay Protection

Replay state is tracked per `(source_id, key_id)`. Duplicate or stale sequences cause `RESULT_REPLAY`.

### TTL / Age

The verifier computes:

```text
age_ns = verifier_receive_time_ns - source_stamp_ns
```

If `age_ns > ttl_ms * 1_000_000`, the result is `RESULT_EXPIRED`.

## Non-Goals

v1 does not protect against:

- payload confidentiality loss
- DDS discovery metadata exposure
- network-level traffic analysis
- private key theft after host compromise
- dynamic key rotation
- Sybil identity management
- denial of service

## Security Notes

- demo keys are for tutorials and tests only.
- the private key must stay on the signer side.
- the trust store should be explicitly managed by the deployer.
- production systems should still use DDS-Security, network isolation, host hardening, and key management.
