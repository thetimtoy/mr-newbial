from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from newbial.core.managers import StateManager


class User:
    __slots__ = ()

    def __init__(self, state: StateManager, data: dict[str, Any]) -> None:
        self._state = state
        self.id = data['id']
