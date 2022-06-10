import traceback
from typing import Any

from newbial.core.events import BaseEvent

__all__ = ('ErrorEvent',)


def _exception_toJSON(exc: Exception) -> dict[str, Any]:
    tb_fmt = traceback.format_exception(
        exc.__class__,
        exc,
        exc.__traceback__,
    )
    return {'name': exc.__class__.__name__, 'tb': tb_fmt}


class ErrorEvent(BaseEvent):
    __slots__ = ('error',)
    __event_name__ = 'error'

    def __init__(self, error: Exception) -> None:
        self.error = error
        self.error.toJSON = lambda: _exception_toJSON(error)  # type: ignore
