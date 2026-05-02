from abc import ABC, abstractmethod


class SignatureBackend(ABC):
    @abstractmethod
    def sign(self, private_key: bytes, message: bytes) -> bytes:
        """Sign the provided message bytes."""

    @abstractmethod
    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        """Verify the provided signature."""
