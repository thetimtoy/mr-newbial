from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from newbial.core.managers import StateManager
    from newbial.types.events import MessageEventData

__all__ = ('Message',)


class Message:
    if TYPE_CHECKING:
        _state: StateManager
        ts: str
        text: str
        user_id: str
        channel_id: str
        bot_id: str | None
        hidden: bool

    __slots__ = (
        '_state',
        'ts',
        'text',
        'user_id',
        'channel_id',
        'bot_id',
        'hidden',
    )

    def __init__(self, *, state: StateManager, data: MessageEventData) -> None:
        self._state = state
        self.ts = data['ts']
        self.text = data['text']
        self.user_id = data['user']
        self.channel_id = data['channel']
        self.bot_id = data.get('bot_id')
        self.hidden = data.get('hidden', False)

    def toJSON(self) -> dict[str, Any]:
        return {
            k: getattr(self, k) for k in self.__class__.__slots__ if not k.startswith('_')
        }
