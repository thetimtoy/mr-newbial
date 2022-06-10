from __future__ import annotations

from typing import TYPE_CHECKING

from newbial.slack.events.base_event import BaseEvent

if TYPE_CHECKING:
    from newbial.slack.structures import Message
    from newbial.types.events import (
        MessageEventPayload,
        MessageChangedEventPayload,
    )

__all__ = (
    'MessageEvent',
    'MessageChangedEvent',
)


class MessageEvent(BaseEvent):
    __slots__ = ('message', 'subtype')
    __event_name__ = 'message'

    def __init__(
        self,
        payload: MessageEventPayload,
        message: Message,
    ) -> None:
        self.message = message
        self.subtype = payload['event'].get('subtype')

        super().__init__(payload['event'])

    @property
    def text(self) -> str:
        return self.message.text

    @property
    def is_bot(self) -> bool:
        return self.message.bot_id is not None


class MessageChangedEvent(BaseEvent):
    __slots__ = ('old_message', 'message')
    __event_name__ = 'message_changed'

    def __init__(
        self,
        payload: MessageChangedEventPayload,
        old_message: Message | None,
        message: Message,
    ) -> None:
        self.old_message = old_message
        self.message = message

        super().__init__(payload['event'])
