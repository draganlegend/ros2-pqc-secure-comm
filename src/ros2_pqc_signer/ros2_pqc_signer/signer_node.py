from __future__ import annotations

import hashlib
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from rclpy.time import Time

from ros2_pqc_crypto.constants import (
    HASH_SCHEME_SHA256,
    PAYLOAD_SCHEMA_TWIST_V1,
    PAYLOAD_VERSION_V1,
    SIG_SCHEME_ML_DSA_44,
)
from ros2_pqc_crypto.key_store import load_key_bytes
from ros2_pqc_crypto.oqs_backend import OqsMlDsa44Backend
from ros2_pqc_crypto.adapters import TwistAdapter
from ros2_pqc_interfaces.msg import SignedTwist


class SignerNode(Node):
    def __init__(self) -> None:
        super().__init__('ros2_pqc_signer')

        self.declare_parameter('source_id', 'demo_source')
        self.declare_parameter('key_id', 'demo_mldsa44_key_1')
        self.declare_parameter('private_key_path', 'keys/signer/mldsa44_private.key')
        self.declare_parameter('sig_scheme', SIG_SCHEME_ML_DSA_44)
        self.declare_parameter('hash_scheme', HASH_SCHEME_SHA256)
        self.declare_parameter('ttl_ms', 500)
        self.declare_parameter('topic_name', '/cmd_vel/raw')
        self.declare_parameter('payload_schema', PAYLOAD_SCHEMA_TWIST_V1)

        self._source_id = self.get_parameter('source_id').value
        self._key_id = self.get_parameter('key_id').value
        self._private_key_path = self.get_parameter('private_key_path').value
        self._sig_scheme = int(self.get_parameter('sig_scheme').value)
        self._hash_scheme = int(self.get_parameter('hash_scheme').value)
        self._ttl_ms = int(self.get_parameter('ttl_ms').value)
        self._topic_name = self.get_parameter('topic_name').value
        payload_schema = self.get_parameter('payload_schema').value

        self._sequence = 0
        self._adapter = TwistAdapter(
            payload_schema=payload_schema,
            payload_version=PAYLOAD_VERSION_V1,
        )

        try:
            self._private_key = load_key_bytes(self._private_key_path)
            self._backend = OqsMlDsa44Backend()
        except Exception as exc:
            self._private_key = None
            self._backend = None
            self.get_logger().error(f'Failed to initialize signer backend: {exc}')

        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self._subscription = self.create_subscription(
            Twist,
            self._topic_name,
            self._on_raw_twist,
            qos,
        )
        self._publisher = self.create_publisher(SignedTwist, '/cmd_vel/signed', qos)

    def _on_raw_twist(self, msg: Twist) -> None:
        if self._backend is None or self._private_key is None:
            return
        if self._sig_scheme != SIG_SCHEME_ML_DSA_44 or self._hash_scheme != HASH_SCHEME_SHA256:
            self.get_logger().error(
                'Unsupported signer configuration; v1 only supports ML-DSA-44 with SHA-256.'
            )
            return

        try:
            now = self.get_clock().now()
            source_stamp_ns = now.nanoseconds
            canonical_bytes = self._adapter.build_canonical_bytes(
                msg,
                topic_name=self._topic_name,
                source_id=self._source_id,
                key_id=self._key_id,
                source_stamp_ns=source_stamp_ns,
                sequence=self._sequence,
                ttl_ms=self._ttl_ms,
            )
            payload_digest = hashlib.sha256(canonical_bytes).digest()
            signature = self._backend.sign(self._private_key, payload_digest)

            signed_msg = SignedTwist()
            signed_msg.header.stamp = now.to_msg()
            signed_msg.command = msg
            signed_msg.payload_version = self._adapter.payload_version
            signed_msg.payload_schema = self._adapter.payload_schema
            signed_msg.source_stamp = now.to_msg()
            signed_msg.sequence = self._sequence
            signed_msg.ttl_ms = self._ttl_ms
            signed_msg.source_id = self._source_id
            signed_msg.key_id = self._key_id
            signed_msg.sig_scheme = self._sig_scheme
            signed_msg.hash_scheme = self._hash_scheme
            signed_msg.payload_digest = list(payload_digest)
            signed_msg.signature = list(signature)

            self._publisher.publish(signed_msg)
            self._sequence += 1
        except Exception as exc:
            self.get_logger().error(f'Signing failed, dropping message: {exc}')


def main(args=None) -> None:
    rclpy.init(args=args)
    node = SignerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
