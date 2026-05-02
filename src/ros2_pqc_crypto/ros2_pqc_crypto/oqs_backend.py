from __future__ import annotations

from .backend_base import SignatureBackend
from .errors import BackendUnavailableError

try:
    import oqs
except ImportError:  # pragma: no cover - depends on local environment
    oqs = None


class OqsMlDsa44Backend(SignatureBackend):
    algorithm_name = 'ML-DSA-44'

    def __init__(self) -> None:
        if oqs is None:
            raise BackendUnavailableError(
                'Python package "oqs" is required for ML-DSA-44 signing and verification.'
            )

        enabled = set(oqs.get_enabled_sig_mechanisms())
        if self.algorithm_name not in enabled:
            raise BackendUnavailableError(
                f'{self.algorithm_name} is not enabled in the installed liboqs build.'
            )

    def sign(self, private_key: bytes, message: bytes) -> bytes:
        with oqs.Signature(self.algorithm_name, secret_key=private_key) as signer:
            return signer.sign(message)

    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        with oqs.Signature(self.algorithm_name) as verifier:
            return verifier.verify(message, signature, public_key)
