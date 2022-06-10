from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import aiohttp
from slack_sdk.web.async_client import AsyncWebClient

if TYPE_CHECKING:
    from newbial.core.bot import Bot

__all__ = ('WebClient',)


class WebClient(AsyncWebClient):
    def __init__(self, bot: Bot) -> None:
        super().__init__(
            token=bot.config.slack.bot_token,
        )

        self.__logger = logging.getLogger(__name__)

    async def connect(self) -> None:
        await self.close()
        self.session = aiohttp.ClientSession()

        await self.auth_test()

        self.__logger.debug('Auth test passed.')

    async def close(self) -> None:
        if self.session is not None:
            await self.session.close()

            self.__logger.debug('Closed.')
