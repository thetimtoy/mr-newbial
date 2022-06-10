from typing import ClassVar, Literal, Protocol, TypedDict, TypeVar
from typing_extensions import NotRequired

__all__ = (
    'Event',
    'SlackEvent',
    'EventT',
    'EventData',
    'EventDataT',
    'EventPayload',
    'MessageEventData',
    'MessageEventPayload',
    'MessageChangedEventData',
    'MessageChangedEventPayload',
)

EventT = TypeVar('EventT', bound='Event')
EventDataT = TypeVar('EventDataT', bound='EventData')


## Base event data & payload types
# https://api.slack.com/types/event


class _BaseEventData(TypedDict):
    event_ts: str
    # subclasses should implement "type" field


class _BaseEventPayload(TypedDict):
    token: str
    team_id: str
    api_app_id: str
    type: Literal['event_callback']
    event_id: str
    event_time: int
    # subclasses should implement "event" field and
    # that should be a subclass of _BaseEventData


## Various sub-fields


class _MessageEditedField(TypedDict):
    user: str
    ts: str


class _ChangedMessage(TypedDict):
    type: Literal['message']
    user: str
    text: str
    ts: str
    edited: _MessageEditedField


## Abstract event types


class Event(Protocol):
    __event_name__: ClassVar[str]


class SlackEvent(Event, Protocol):
    type: str
    ts: str


## Abstract event data & payload types


class EventData(_BaseEventData):
    type: str


class EventPayload(_BaseEventPayload):
    event: EventData


## Message event
# https://api.slack.com/events/message


class MessageEventData(_BaseEventData):
    type: Literal['message']
    subtype: NotRequired[str]
    channel: str
    user: str
    text: str
    ts: str
    edited: NotRequired[_MessageEditedField]
    bot_id: NotRequired[str]
    hidden: NotRequired[bool]


class MessageEventPayload(_BaseEventPayload):
    event: MessageEventData


## Message changed event
# https://api.slack.com/events/message/message_changed


class MessageChangedEventData(_BaseEventData):
    type: Literal['message']
    subtype: NotRequired[str]
    hidden: NotRequired[bool]
    channel: str
    ts: str
    message: _ChangedMessage


class MessageChangedEventPayload(_BaseEventPayload):
    event: MessageChangedEventData
