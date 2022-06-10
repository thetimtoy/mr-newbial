def main():
    try:
        import asyncio

        from newbial.core.bot import Bot
        from newbial.core.utils import logging

        async def runner():
            async with Bot() as bot:
                await bot.connect()

        with logging.setup():
            asyncio.run(runner())
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
