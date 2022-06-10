from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Sequence

from newbial.slack.events import (
    MessageEvent,
    MessageChangedEvent,
)
from newbial.slack.structures import Message
from newbial.types.events import (
    MessageEventData,
    MessageEventPayload,
    MessageChangedEventPayload,
)

if TYPE_CHECKING:
    from newbial.core.bot import Bot
    from newbial.slack.clients import (
        SocketClient,
        WebClient,
    )
    from newbial.types.core import FuncT, DispatchFunc
    from newbial.types.events import EventPayload

__all__ = ('StateManager',)


def _flatten_parsers(_cls: Any) -> type[StateManager]:
    cls: type[StateManager] = _cls
    names: list[str]
    names = cls.__parser_names__ = []

    for base in cls.mro():
        for k, v in base.__dict__.items():
            if hasattr(v, '__sm_parser__'):
                names.append(k)

    return cls


def _parser(func: FuncT) -> FuncT:
    """Declare a function as an event parser."""
    func.__sm_parser__ = None

    return func


@_flatten_parsers
class StateManager:
    if TYPE_CHECKING:
        web: WebClient
        sock: SocketClient
        _logger: logging.Logger
        _dispatch: DispatchFunc
        _parsers: dict[str, Callable[[EventPayload], Any]]
        _messages: dict[str, dict[str, Message]]
        __parser_names__: ClassVar[Sequence[str]]

    def __init__(self, bot: Bot) -> None:
        self.web = bot.web
        self.sock = bot.sock

        self._logger = logging.getLogger(__name__)
        self._dispatch = bot.events.dispatch
        self._parsers = parsers = {}
        self._messages = {}
        self.sock.message_listeners.append(self._message_callback)

        # .__parser_names__ is set by @_flatten_parsers
        for name in self.__class__.__parser_names__:
            parser = getattr(self, name)  # get the bound method
            name = name[7:]  # remove "_parse_" prefix
            parsers[name] = parser

        self._logger.debug(f'Registered parsers: {list(parsers)}')

    # Called when a socket message is received
    async def _message_callback(self, *args: Any) -> None:
        # Arguments given are (SocketClient, dict, str | None)
        # We can safely ignore the first and last elements - we only need the data
        data: dict[str, Any] = args[1]

        # "data" (wrapper around event payload for socket mode) schema and other info:
        # https://api.slack.com/apis/connections/socket-implement#events

        if data.get('type') != 'events_api':
            self._logger.debug(f'Skipping event "{data}"')
            return

        payload: EventPayload = data['payload']

        event = payload['event']['type']
        try:
            parser = self._parsers[event]
        except KeyError:
            self._logger.warning(f'Parser not found for event "{event}"')
        else:
            self._logger.debug(f'Parsing event "{event}"')
            parser(payload)

    def get_message(self, channel_id: str, ts: str) -> Message | None:
        try:
            messages = self._messages[channel_id]
        except KeyError:
            pass
        else:
            return messages.get(ts)

    def _add_message(self, message: Message) -> None:
        messages = self._messages.setdefault(message.channel_id, {})
        messages[message.ts] = message

    ## Event parsing

    # https://api.slack.com/events/message
    @_parser
    def _parse_message(self, payload: MessageEventPayload) -> None:
        data = payload['event']

        try:
            subtype = data['subtype']
            parser = getattr(self, f'_parse_{subtype}')
        except (KeyError, AttributeError):
            message = Message(state=self, data=payload['event'])

            self._add_message(message)

            self._dispatch(MessageEvent(payload, message))
        else:
            parser(payload)

    # https://api.slack.com/events/message/message_changed
    def _parse_message_changed(self, payload: MessageChangedEventPayload) -> None:
        data = payload['event']
        d: MessageEventData = data['message'].copy().update(channel=data['channel'])  # type: ignore

        old_message = self.get_message(data['channel'], data['ts'])
        message = Message(state=self, data=d)

        self._dispatch(MessageChangedEvent(payload, old_message, message))

    # https://api.slack.com/events/message/message_deleted
    def _parse_message_deleted(self, payload: dict[str, Any]) -> None:
        ...
