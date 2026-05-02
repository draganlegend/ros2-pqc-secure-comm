from pathlib import Path

import pytest
import yaml
from geometry_msgs.msg import Twist

from ros2_pqc_crypto.adapters.twist_adapter import TwistAdapter
from ros2_pqc_crypto.constants import SIG_SCHEME_ML_DSA_44
from ros2_pqc_crypto.replay_window import ReplayWindow
from ros2_pqc_crypto.key_store import TrustStore


def _twist(linear_x: float = 1.0, angular_z: float = 0.1) -> Twist:
    msg = Twist()
    msg.linear.x = linear_x
    msg.angular.z = angular_z
    return msg


def _canonical(adapter: TwistAdapter, msg: Twist, *, sequence: int = 1) -> bytes:
    return adapter.build_canonical_bytes(
        msg,
        topic_name='/cmd_vel/raw',
        source_id='demo_source',
        key_id='demo_key',
        source_stamp_ns=123456789,
        sequence=sequence,
        ttl_ms=250,
    )


def test_twist_adapter_builds_deterministic_canonical_bytes() -> None:
    adapter = TwistAdapter()
    msg = _twist()

    first = _canonical(adapter, msg)
    second = _canonical(adapter, msg)

    assert first == second
    assert _canonical(adapter, msg, sequence=2) != first
    assert _canonical(adapter, _twist(linear_x=2.0)) != first


def test_replay_window_accepts_new_sequences_and_rejects_replays() -> None:
    window = ReplayWindow(window_size=3)

    assert window.check_and_update('source', 'key', 10)
    assert not window.check_and_update('source', 'key', 10)
    assert window.check_and_update('source', 'key', 11)
    assert window.check_and_update('source', 'key', 12)
    assert window.check_and_update('source', 'key', 13)
    assert not window.check_and_update('source', 'key', 9)


def test_replay_window_tracks_source_key_pairs_independently() -> None:
    window = ReplayWindow(window_size=3)

    assert window.check_and_update('source-a', 'key-a', 1)
    assert not window.check_and_update('source-a', 'key-a', 1)
    assert window.check_and_update('source-b', 'key-a', 1)
    assert window.check_and_update('source-a', 'key-b', 1)


def test_trust_store_loads_enabled_keys_and_rejects_disabled_or_unknown_keys(tmp_path: Path) -> None:
    enabled_key = tmp_path / 'enabled.pub'
    disabled_key = tmp_path / 'disabled.pub'
    enabled_key.write_bytes(b'enabled-public-key')
    disabled_key.write_bytes(b'disabled-public-key')

    trust_store_path = tmp_path / 'trust_store.yaml'
    trust_store_path.write_text(
        yaml.safe_dump(
            {
                'trusted_keys': [
                    {
                        'source_id': 'demo_source',
                        'key_id': 'enabled_key',
                        'sig_scheme': 'ML-DSA-44',
                        'public_key_path': enabled_key.name,
                        'enabled': True,
                    },
                    {
                        'source_id': 'demo_source',
                        'key_id': 'disabled_key',
                        'sig_scheme': 'ML-DSA-44',
                        'public_key_path': disabled_key.name,
                        'enabled': False,
                    },
                ]
            }
        ),
        encoding='utf-8',
    )

    store = TrustStore.from_file(trust_store_path)

    assert (
        store.get_public_key(
            source_id='demo_source',
            key_id='enabled_key',
            sig_scheme=SIG_SCHEME_ML_DSA_44,
        )
        == b'enabled-public-key'
    )
    assert (
        store.get_public_key(
            source_id='demo_source',
            key_id='disabled_key',
            sig_scheme=SIG_SCHEME_ML_DSA_44,
        )
        is None
    )
    assert (
        store.get_public_key(
            source_id='demo_source',
            key_id='missing_key',
            sig_scheme=SIG_SCHEME_ML_DSA_44,
        )
        is None
    )
