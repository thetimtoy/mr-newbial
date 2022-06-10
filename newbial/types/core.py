from __future__ import annotations

from typing import (
    Any,
    Callable,
    Protocol,
    TypeVar,
    TYPE_CHECKING,
)
from typing_extensions import ParamSpec

if TYPE_CHECKING:
    from newbial.core.structures import Module
    from newbial.types.events import Event, EventT

__all__ = (
    'P',
    'T',
    'T2',
    'FuncT',
    'TypeT',
    'ModuleT',
    'BaseExcT',
    'DispatchFunc',
    'EventCallback',
)

P = ParamSpec('P')
T = TypeVar('T')
T2 = TypeVar('T2')
FuncT = TypeVar('FuncT', bound=Callable[..., Any])
TypeT = TypeVar('TypeT', bound=type)
ModuleT = TypeVar('ModuleT', bound='Module')
BaseExcT = TypeVar('BaseExcT', bound=BaseException)


class DispatchFunc(Protocol):
    def __call__(self, event: Event, *, handle_errors: bool = ...) -> None:
        ...


EventCallback = Callable[['EventT'], Any]
