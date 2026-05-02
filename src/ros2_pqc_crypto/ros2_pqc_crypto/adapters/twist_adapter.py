from __future__ import annotations

import struct

from ..constants import PAYLOAD_SCHEMA_TWIST_V1, PAYLOAD_VERSION_V1
from .base import CommandAdapter


class TwistAdapter(CommandAdapter):
    def __init__(
        self,
        *,
        payload_schema: str = PAYLOAD_SCHEMA_TWIST_V1,
        payload_version: int = PAYLOAD_VERSION_V1,
    ) -> None:
        self._payload_schema = payload_schema
        self._payload_version = payload_version

    @property
    def payload_schema(self) -> str:
        return self._payload_schema

    @property
    def payload_version(self) -> int:
        return self._payload_version

    def build_canonical_bytes(
        self,
        command_msg,
        *,
        topic_name: str,
        source_id: str,
        key_id: str,
        source_stamp_ns: int,
        sequence: int,
        ttl_ms: int,
    ) -> bytes:
        parts = [
            struct.pack('<B', self.payload_version),
            _pack_string(self.payload_schema),
            _pack_string(topic_name),
            _pack_string(source_id),
            _pack_string(key_id),
            struct.pack('<Q', source_stamp_ns),
            struct.pack('<Q', sequence),
            struct.pack('<I', ttl_ms),
            struct.pack('<d', float(command_msg.linear.x)),
            struct.pack('<d', float(command_msg.linear.y)),
            struct.pack('<d', float(command_msg.linear.z)),
            struct.pack('<d', float(command_msg.angular.x)),
            struct.pack('<d', float(command_msg.angular.y)),
            struct.pack('<d', float(command_msg.angular.z)),
        ]
        return b''.join(parts)


def _pack_string(value: str) -> bytes:
    encoded = value.encode('utf-8')
    return struct.pack('<I', len(encoded)) + encoded
