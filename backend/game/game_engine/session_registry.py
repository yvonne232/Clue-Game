"""In-memory registry for active GameManager instances."""

from __future__ import annotations

import threading
from typing import Dict, Optional

if False:  # pragma: nocover
    from .game_manager import GameManager

_lock = threading.RLock()
_sessions: Dict[str, "GameManager"] = {}


def register_session(game_name: str, manager: "GameManager") -> None:
    with _lock:
        _sessions[game_name] = manager


def get_session(game_name: str) -> Optional["GameManager"]:
    with _lock:
        return _sessions.get(game_name)


def remove_session(game_name: str) -> None:
    with _lock:
        _sessions.pop(game_name, None)


def list_sessions() -> Dict[str, "GameManager"]:
    with _lock:
        return dict(_sessions)

