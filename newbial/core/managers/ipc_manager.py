from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import ipc
from ipc import rpc

if TYPE_CHECKING:

    from newbial.core.bot import Bot

__all__ = ('IPCManager',)


class IPCManager(rpc.Server[ipc.Connection]):
    if TYPE_CHECKING:
        _bot: Bot
        _logger: logging.Logger

    def __init__(self, bot: Bot) -> None:
        self._bot = bot
        self._logger = logging.getLogger(__name__)

        super().__init__(
            bot.config.ipc.host,
            bot.config.ipc.port,
            commands={'api_call': self._api_call_command},
        )

    def on_ready(self) -> None:
        self._logger.debug('Ready.')

    def on_close(self) -> None:
        self._logger.debug('Closed.')

    async def _api_call_command(
        self,
        ctx: rpc.Context,
        method: str,
        kwargs: dict[str, Any] = {},
    ) -> None:
        func = getattr(self._bot.web, method)

        self._logger.debug(
            f'Calling Slack API method {method} with kwargs {kwargs}',
        )
        await func(**kwargs)
