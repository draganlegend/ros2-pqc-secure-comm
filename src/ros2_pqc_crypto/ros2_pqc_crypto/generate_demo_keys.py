from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from ros2_pqc_crypto.oqs_backend import oqs


def generate_demo_keys(
    *,
    keys_dir: str | Path,
    source_id: str,
    key_id: str,
    overwrite: bool,
) -> None:
    if oqs is None:
        raise RuntimeError('Python package "oqs" is required to generate ML-DSA-44 demo keys.')

    root = Path(keys_dir).expanduser()
    signer_dir = root / 'signer'
    trust_dir = root / 'trust'
    private_key_path = signer_dir / 'mldsa44_private.key'
    public_key_path = trust_dir / 'demo_source_mldsa44_pub.key'
    trust_store_path = trust_dir / 'trust_store.yaml'

    signer_dir.mkdir(parents=True, exist_ok=True)
    trust_dir.mkdir(parents=True, exist_ok=True)

    if not overwrite:
        existing = [path for path in (private_key_path, public_key_path, trust_store_path) if path.exists()]
        if existing:
            formatted = ', '.join(str(path) for path in existing)
            raise FileExistsError(f'Key material already exists; pass --overwrite to replace: {formatted}')

    with oqs.Signature('ML-DSA-44') as signer:
        public_key = signer.generate_keypair()
        private_key = signer.export_secret_key()

    private_key_path.write_bytes(private_key)
    private_key_path.chmod(0o600)
    public_key_path.write_bytes(public_key)

    trust_store = {
        'trusted_keys': [
            {
                'source_id': source_id,
                'key_id': key_id,
                'sig_scheme': 'ML_DSA_44',
                'public_key_path': public_key_path.name,
                'enabled': True,
            }
        ]
    }
    trust_store_path.write_text(yaml.safe_dump(trust_store, sort_keys=False), encoding='utf-8')

    print(f'wrote private key: {private_key_path}')
    print(f'wrote public key: {public_key_path}')
    print(f'wrote trust store: {trust_store_path}')


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description='Generate demo ML-DSA-44 keys for ros2-pqc-secure-comm.')
    parser.add_argument('--keys-dir', default='/ros2_ws/src/keys')
    parser.add_argument('--source-id', default='demo_source')
    parser.add_argument('--key-id', default='demo_mldsa44_key_1')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(argv)

    generate_demo_keys(
        keys_dir=args.keys_dir,
        source_id=args.source_id,
        key_id=args.key_id,
        overwrite=args.overwrite,
    )
