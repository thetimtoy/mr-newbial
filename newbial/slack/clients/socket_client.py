from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

import aiohttp
from slack_sdk.socket_mode.aiohttp import SocketModeClient

from newbial.core.events import ReadyEvent

if TYPE_CHECKING:
    from newbial.core.bot import Bot

__all__ = ('SocketClient',)


class SocketClient(SocketModeClient):
    if TYPE_CHECKING:
        _bot: Bot

    def __init__(self, bot: Bot) -> None:
        self._bot = bot
        self._logger = logging.getLogger(__name__)

        super().__init__(
            web_client=bot.web,
            app_token=bot.config.slack.socket_token,
        )

        self.message_listeners.append(self._message_callback)

    async def connect(self):
        if self.aiohttp_client_session.closed:
            self.aiohttp_client_session = aiohttp.ClientSession()

        await super().connect()

        self._logger.debug('Connected.')

        self._bot.events.dispatch(ReadyEvent())

        assert self.current_session_monitor is not None

        try:
            await self.current_session_monitor
        except asyncio.CancelledError:
            pass

    async def _message_callback(self, *args: Any) -> None:
        d: dict[str, Any] = args[1]

        envelope_id: int = d['envelope_id']

        self._logger.debug(f'Sending ack for envelope "{envelope_id}"')
        await self.send_socket_mode_response({'envelope_id': envelope_id})
