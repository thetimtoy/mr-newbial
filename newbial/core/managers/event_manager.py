from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from newbial.core.events import ErrorEvent
from newbial.core.utils import maybe_awaitable

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from typing_extensions import Self

    from newbial.core.bot import Bot
    from newbial.types.core import EventT, EventCallback
    from newbial.types.events import Event

__all__ = ('EventManager',)


class EventManager:
    if TYPE_CHECKING:
        _loop: AbstractEventLoop
        _logger: logging.Logger
        _events: dict[type[Event], list[EventCallback]]

    def __init__(self, bot: Bot | None = None) -> None:
        if bot is not None:
            self._loop = bot.loop
        else:
            self._loop = asyncio.get_event_loop()
        self._logger = logging.getLogger(__name__)
        self._events = {}

    def __repr__(self) -> str:
        events = list(e.__event_name__ for e in self._events)
        return f"<EventManager events={events}>"

    def dispatch(self, event: Event, *, handle_errors: bool = True) -> None:
        try:
            callbacks = self._events[event.__class__]
        except KeyError:
            pass
        else:
            create_task = self._loop.create_task
            event_info = repr(event)

            for callback in callbacks:
                if handle_errors:
                    coro = self._wrapped_callback(callback, event)
                else:
                    # Not handling errors here, they will propagate
                    coro = maybe_awaitable(callback, event)

                details = f'{event_info} @ {callback}'
                create_task(coro, name=details)
                self._logger.debug(f'Dispatching: {details}')

    async def _wrapped_callback(
        self,
        callback: EventCallback,
        event: Event,
    ) -> None:
        """Invokes `callback` with `event` and handles any
        exceptions raised by the callback.
        """
        try:
            await maybe_awaitable(callback, event)
        except Exception as exc:
            self._logger.error(
                'Something went wrong while dispatching a callback '
                f'for event {event} ("{event.__class__.__event_name__}")',
                exc_info=exc,
            )

            # Dispatch an "error" event without handling errors to
            # Prevent recursion and to expose faulty error handlers
            self.dispatch(ErrorEvent(exc), handle_errors=False)

    def add_callback(
        self,
        event: type[EventT],
        callback: EventCallback[EventT],
    ) -> Self:
        callbacks: list[EventCallback]

        try:
            callbacks = self._events[event]
        except KeyError:
            callbacks = self._events[event] = []

        callbacks.append(callback)
        self._logger.debug(f'Added callback for event {event.__event_name__}: {callback}')

        return self

    def remove_callback(
        self,
        event: type[EventT],
        callback: EventCallback[EventT],
    ) -> Self:
        try:
            callbacks = self._events[event]
        except KeyError:
            pass
        else:
            try:
                callbacks.remove(callback)
            except ValueError:
                pass
            else:
                self._logger.debug(
                    f'Removed callback for event {event.__event_name__}: {callback}'
                )

            if not len(callbacks):
                del self._events[event]

        return self
