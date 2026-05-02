from __future__ import annotations

import hashlib
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

from ros2_pqc_crypto.adapters import TwistAdapter
from ros2_pqc_crypto.constants import (
    HASH_SCHEME_SHA256,
    PAYLOAD_SCHEMA_TWIST_V1,
    PAYLOAD_VERSION_V1,
    RESULT_ALG_UNSUPPORTED,
    RESULT_DIGEST_MISMATCH,
    RESULT_EXPIRED,
    RESULT_INTERNAL_ERROR,
    RESULT_KEY_NOT_TRUSTED,
    RESULT_OK,
    RESULT_REPLAY,
    RESULT_SCHEMA_ERROR,
    RESULT_SIG_INVALID,
    SIG_SCHEME_ML_DSA_44,
)
from ros2_pqc_crypto.key_store import TrustStore
from ros2_pqc_crypto.oqs_backend import OqsMlDsa44Backend
from ros2_pqc_crypto.replay_window import ReplayWindow
from ros2_pqc_interfaces.msg import SignedTwist, VerificationEvent


class VerifierNode(Node):
    def __init__(self) -> None:
        super().__init__('ros2_pqc_verifier')

        self.declare_parameter('trust_store_path', 'keys/trust/trust_store.yaml')
        self.declare_parameter('expected_payload_schema', PAYLOAD_SCHEMA_TWIST_V1)
        self.declare_parameter('expected_payload_version', PAYLOAD_VERSION_V1)
        self.declare_parameter('replay_window_size', 64)
        self.declare_parameter('topic_name', '/cmd_vel/raw')

        self._trust_store_path = self.get_parameter('trust_store_path').value
        self._expected_payload_schema = self.get_parameter('expected_payload_schema').value
        self._expected_payload_version = int(self.get_parameter('expected_payload_version').value)
        self._topic_name = self.get_parameter('topic_name').value

        self._adapter = TwistAdapter(
            payload_schema=self._expected_payload_schema,
            payload_version=self._expected_payload_version,
        )
        self._replay_window = ReplayWindow(int(self.get_parameter('replay_window_size').value))

        try:
            self._trust_store = TrustStore.from_file(self._trust_store_path)
            self._backend = OqsMlDsa44Backend()
        except Exception as exc:
            self._trust_store = None
            self._backend = None
            self.get_logger().error(f'Failed to initialize verifier backend: {exc}')

        secure_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        event_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=100,
        )

        self._subscription = self.create_subscription(
            SignedTwist,
            '/cmd_vel/signed',
            self._on_signed_twist,
            secure_qos,
        )
        self._verified_publisher = self.create_publisher(Twist, '/cmd_vel/verified', secure_qos)
        self._event_publisher = self.create_publisher(
            VerificationEvent,
            '/pqc/verify_event',
            event_qos,
        )

    def _on_signed_twist(self, msg: SignedTwist) -> None:
        start_ns = time.perf_counter_ns()
        now_ns = self.get_clock().now().nanoseconds
        source_stamp_ns = (int(msg.source_stamp.sec) * 1_000_000_000) + int(msg.source_stamp.nanosec)
        age_ns = max(0, now_ns - source_stamp_ns)

        result_code = RESULT_INTERNAL_ERROR
        reason = ''
        ok = False

        try:
            if msg.payload_version != PAYLOAD_VERSION_V1 or msg.payload_version != self._expected_payload_version:
                result_code = RESULT_SCHEMA_ERROR
                reason = f'Unsupported payload_version: {msg.payload_version}'
            elif msg.payload_schema != self._expected_payload_schema:
                result_code = RESULT_SCHEMA_ERROR
                reason = f'Unexpected payload_schema: {msg.payload_schema}'
            elif msg.sig_scheme != SIG_SCHEME_ML_DSA_44 or msg.hash_scheme != HASH_SCHEME_SHA256:
                result_code = RESULT_ALG_UNSUPPORTED
                reason = (
                    f'Unsupported algorithms sig_scheme={msg.sig_scheme} '
                    f'hash_scheme={msg.hash_scheme}'
                )
            elif self._trust_store is None or self._backend is None:
                result_code = RESULT_INTERNAL_ERROR
                reason = 'Verifier backend is not initialized.'
            else:
                public_key = self._trust_store.get_public_key(
                    source_id=msg.source_id,
                    key_id=msg.key_id,
                    sig_scheme=msg.sig_scheme,
                )
                if public_key is None:
                    result_code = RESULT_KEY_NOT_TRUSTED
                    reason = f'Key not trusted for source_id={msg.source_id}, key_id={msg.key_id}'
                else:
                    canonical_bytes = self._adapter.build_canonical_bytes(
                        msg.command,
                        topic_name=self._topic_name,
                        source_id=msg.source_id,
                        key_id=msg.key_id,
                        source_stamp_ns=source_stamp_ns,
                        sequence=msg.sequence,
                        ttl_ms=msg.ttl_ms,
                    )
                    expected_digest = hashlib.sha256(canonical_bytes).digest()
                    if expected_digest != bytes(msg.payload_digest):
                        result_code = RESULT_DIGEST_MISMATCH
                        reason = 'payload_digest does not match recomputed SHA-256 digest.'
                    elif not self._backend.verify(public_key, expected_digest, bytes(msg.signature)):
                        result_code = RESULT_SIG_INVALID
                        reason = 'ML-DSA-44 signature verification failed.'
                    elif age_ns > int(msg.ttl_ms) * 1_000_000:
                        result_code = RESULT_EXPIRED
                        reason = f'Message age {age_ns} ns exceeds ttl_ms={msg.ttl_ms}'
                    elif not self._replay_window.check_and_update(msg.source_id, msg.key_id, msg.sequence):
                        result_code = RESULT_REPLAY
                        reason = f'Replayed or stale sequence detected: {msg.sequence}'
                    else:
                        result_code = RESULT_OK
                        ok = True
                        self._verified_publisher.publish(msg.command)
        except Exception as exc:
            result_code = RESULT_INTERNAL_ERROR
            reason = f'Internal verification error: {exc}'

        verify_ns = time.perf_counter_ns() - start_ns

        event = VerificationEvent()
        event.header.stamp = self.get_clock().now().to_msg()
        event.ok = (result_code == RESULT_OK)
        event.result_code = result_code
        event.reason = reason
        event.source_id = msg.source_id
        event.key_id = msg.key_id
        event.sequence = msg.sequence
        event.verify_ns = verify_ns
        event.age_ns = age_ns
        self._event_publisher.publish(event)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = VerifierNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
