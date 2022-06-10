from newbial.core.events import BaseEvent

__all__ = ('ReadyEvent',)


# Not sure about adding any data to this event
# but it may be done in the future
class ReadyEvent(BaseEvent):
    __slots__ = ()
    __event_name__ = 'ready'
