from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Set, Tuple


@dataclass
class ReplayState:
    highest_sequence_seen: int = -1
    accepted_sequences: Set[int] = field(default_factory=set)


class ReplayWindow:
    def __init__(self, window_size: int = 64) -> None:
        if window_size <= 0:
            raise ValueError('replay_window_size must be a positive integer.')
        self._window_size = window_size
        self._states: Dict[Tuple[str, str], ReplayState] = {}

    def check_and_update(self, source_id: str, key_id: str, sequence: int) -> bool:
        state = self._states.setdefault((source_id, key_id), ReplayState())

        if sequence in state.accepted_sequences:
            return False

        if state.highest_sequence_seen >= 0:
            cutoff = state.highest_sequence_seen - self._window_size
            if sequence <= cutoff:
                return False

        state.accepted_sequences.add(sequence)
        if sequence > state.highest_sequence_seen:
            state.highest_sequence_seen = sequence

        cutoff = state.highest_sequence_seen - self._window_size
        state.accepted_sequences = {
            accepted for accepted in state.accepted_sequences if accepted > cutoff
        }
        return True
