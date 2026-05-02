class Ros2PqcError(Exception):
    """Base error for the ros2-pqc-secure-comm crypto layer."""


class BackendUnavailableError(Ros2PqcError):
    """Raised when the ML-DSA backend is unavailable."""


class KeyStoreError(Ros2PqcError):
    """Raised when key or trust-store files are invalid."""
