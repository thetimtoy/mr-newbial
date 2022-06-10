from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from newbial.core.bot import Bot

__all__ = ('TaskManager',)


class TaskManager:
    def __init__(self, bot: Bot | None = None) -> None:
        if bot is not None:
            self._loop = bot.loop
        else:
            self._loop = asyncio.get_event_loop()

    def add(self, callback: Callable[[], Any]) -> None:
        ...

    def remove(self, callback: Callable[[], Any]) -> None:
        ...
