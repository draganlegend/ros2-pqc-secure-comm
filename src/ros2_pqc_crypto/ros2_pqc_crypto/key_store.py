from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import yaml

from .constants import SIG_SCHEME_NAME_TO_ID
from .errors import KeyStoreError


def load_key_bytes(path: str | Path) -> bytes:
    key_path = Path(path).expanduser()
    if not key_path.is_file():
        raise KeyStoreError(f'Key file does not exist: {key_path}')
    return key_path.read_bytes()


@dataclass(frozen=True)
class TrustedKey:
    source_id: str
    key_id: str
    sig_scheme: int
    public_key_path: Path
    enabled: bool


class TrustStore:
    def __init__(self, keys: Dict[Tuple[str, str], TrustedKey]) -> None:
        self._keys = keys

    @classmethod
    def from_file(cls, trust_store_path: str | Path) -> 'TrustStore':
        store_path = Path(trust_store_path).expanduser()
        if not store_path.is_file():
            raise KeyStoreError(f'Trust store does not exist: {store_path}')

        with store_path.open('r', encoding='utf-8') as handle:
            payload = yaml.safe_load(handle) or {}

        trusted_keys = payload.get('trusted_keys', [])
        if not isinstance(trusted_keys, list):
            raise KeyStoreError('trust_store.yaml must contain a "trusted_keys" list.')

        keys: Dict[Tuple[str, str], TrustedKey] = {}
        for entry in trusted_keys:
            if not isinstance(entry, dict):
                raise KeyStoreError('Each trust store entry must be a mapping.')

            source_id = entry.get('source_id')
            key_id = entry.get('key_id')
            sig_scheme = _parse_sig_scheme(entry.get('sig_scheme'))
            public_key_path = _resolve_relative_path(store_path.parent, entry.get('public_key_path'))
            enabled = bool(entry.get('enabled', False))

            if not source_id or not key_id:
                raise KeyStoreError('Each trust store entry must define source_id and key_id.')

            keys[(source_id, key_id)] = TrustedKey(
                source_id=source_id,
                key_id=key_id,
                sig_scheme=sig_scheme,
                public_key_path=public_key_path,
                enabled=enabled,
            )

        return cls(keys)

    def get_public_key(
        self,
        *,
        source_id: str,
        key_id: str,
        sig_scheme: int,
    ) -> Optional[bytes]:
        entry = self._keys.get((source_id, key_id))
        if entry is None or not entry.enabled or entry.sig_scheme != sig_scheme:
            return None
        return load_key_bytes(entry.public_key_path)


def _parse_sig_scheme(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value in SIG_SCHEME_NAME_TO_ID:
        return SIG_SCHEME_NAME_TO_ID[value]
    raise KeyStoreError(f'Unsupported trust-store sig_scheme: {value!r}')


def _resolve_relative_path(base_dir: Path, raw_path: object) -> Path:
    if not isinstance(raw_path, str) or not raw_path:
        raise KeyStoreError('public_key_path must be a non-empty string.')

    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate

    return (base_dir / candidate).resolve()
