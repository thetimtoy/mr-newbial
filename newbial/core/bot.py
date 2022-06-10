from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, overload

from newbial.core.events import ReadyEvent
from newbial.core.managers import (
    EventManager,
    IPCManager,
    StateManager,
    ModuleManager,
    TaskManager,
)
from newbial.slack.clients import (
    SocketClient,
    WebClient,
)
from newbial.core.utils import Config

if TYPE_CHECKING:
    from types import TracebackType
    from typing_extensions import Self

    from newbial.types.core import BaseExcT

__all__ = ('Bot',)


class Bot:
    if TYPE_CHECKING:
        closed: bool
        config: Config
        events: EventManager
        ipc: IPCManager
        logger: logging.Logger
        loop: asyncio.AbstractEventLoop
        modules: ModuleManager
        sock: SocketClient
        state: StateManager
        tasks: TaskManager
        web: WebClient

    def __init__(self) -> None:
        self.closed = True
        self.loop = asyncio.get_event_loop()
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.web = WebClient(self)
        self.sock = SocketClient(self)
        self.ipc = IPCManager(self)
        self.events = EventManager(self)
        self.tasks = TaskManager(self)
        self.state = StateManager(self)
        self.modules = ModuleManager(self)

        self.events.add_callback(ReadyEvent, self._on_ready)

    def __repr__(self) -> str:
        return f'<Bot closed={self.closed}>'

    async def __aenter__(self) -> Self:
        return self

    @overload
    async def __aexit__(
        self,
        exc_tp: None,
        exc: None,
        tb: None,
    ) -> None:
        ...

    @overload
    async def __aexit__(
        self,
        exc_tp: type[BaseExcT],
        exc: BaseExcT,
        tb: TracebackType,
    ) -> None:
        ...

    async def __aexit__(
        self,
        exc_tp: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if not self.closed:
            await self.close()

    async def connect(self) -> None:
        if not self.closed:
            return

        self.closed = False

        try:
            self.logger.info('Connecting...')
            await self.ipc.connect()
            await self.modules.load()

            await asyncio.gather(
                self.web.connect(),
                self.sock.connect(),
            )
            self.logger.info('Connected.')
        except Exception as exc:
            self.logger.error('Something went wrong.', exc_info=exc)

    async def close(self) -> None:
        if self.closed:
            return

        self.closed = True

        self.logger.info('Closing, please wait... (CTRL+C to force-quit)')
        for result in await asyncio.gather(
            self.ipc.close(),
            self.web.close(),
            self.sock.close(),
            self.modules.unload(),
            return_exceptions=True,
        ):
            if isinstance(result, Exception):
                self.logger.error(
                    'Something went wrong during close().',
                    exc_info=result,
                )

        self.logger.info('Closed.')

    def _on_ready(self, event: ReadyEvent) -> None:
        self.logger.info('Ready.')
