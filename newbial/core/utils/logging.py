from __future__ import annotations

import logging
import logging.handlers
import queue
import sys
from contextlib import contextmanager

import coloredlogs

from newbial.core.utils import Config

__all__ = ('setup',)


@contextmanager
def setup():
    config = Config()

    if not config.logging.enabled:
        try:
            yield
        finally:
            pass

        return

    _queue = queue.Queue(-1)
    handler = logging.StreamHandler(sys.stdout)
    queue_handler = logging.handlers.QueueHandler(_queue)
    listener = logging.handlers.QueueListener(_queue, handler)

    handler.setFormatter(
        coloredlogs.ColoredFormatter(
            fmt='[{asctime}.{msecs:0<3.0f}] [{name}] [{levelname}]: {message}',
            style='{',
            datefmt='%Y-%m-%d %H:%M:%S',
            field_styles=dict(
                asctime=dict(color='white'),
                levelname=dict(color='black', bold=True),
                name=dict(color='white'),
            ),
            level_styles=dict(
                debug=dict(color='cyan', faint=True),
                info=dict(color='green'),
                warning=dict(color='yellow'),
                error=dict(color='red', bold=True),
                critical=dict(color='red', bold=True, bright=True),
            ),
        )
    )

    for k, v in config.logging.levels.items():
        logger = logging.getLogger(k)
        logger.setLevel(v.upper())
        logger.addHandler(handler)

    try:
        listener.start()

        yield
    finally:
        handler.close()
        queue_handler.close()
        listener.stop()
