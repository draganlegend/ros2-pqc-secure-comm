from abc import ABC, abstractmethod


class CommandAdapter(ABC):
    @property
    @abstractmethod
    def payload_schema(self) -> str:
        ...

    @property
    @abstractmethod
    def payload_version(self) -> int:
        ...

    @abstractmethod
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
        ...
