from typing import Protocol

from newbial.core.events import BaseEvent as BaseCoreEvent
from newbial.types.events import SlackEvent, EventData


class BaseEvent(BaseCoreEvent, SlackEvent, Protocol):
    __slots__ = ('type', 'ts')

    def __init__(self, data: EventData) -> None:
        self.type = data['type']
        self.ts = data['event_ts']

    # https://github.com/python/cpython/pull/31628
    # typing.Protocol replaces __init__() (patched in 3.11)
    # So we are going to monkey-patch it to use our __init__()
    # Note, __init__() is declared explicitly for type-checkers
    _init = __init__


BaseEvent.__init__ = BaseEvent._init
del BaseEvent._init
