from __future__ import annotations

from inspect import isawaitable
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    overload,
)

if TYPE_CHECKING:
    from typing_extensions import NoReturn

    from newbial.types.core import P, T

__all__ = (
    'NULL',
    'maybe_awaitable',
)


@overload
async def maybe_awaitable(
    func: Callable[P, Awaitable[T]], *args: P.args, **kwargs: P.kwargs
) -> T:
    ...


@overload
async def maybe_awaitable(func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    ...


async def maybe_awaitable(
    func: Callable[P, Any], *args: P.args, **kwargs: P.kwargs
) -> Any:
    ret = func(*args, **kwargs)

    if isawaitable(ret):
        ret = await ret

    return ret


class _NullType:
    __slots__ = ()

    def __repr__(self) -> str:
        return '<NULL>'

    def __bool__(self) -> bool:
        return False

    # presence of this method makes NULL unhashable
    def __eq__(self, other: Any) -> bool:
        return self is other

    def __getattribute__(self, name: str) -> NoReturn:
        raise AttributeError(f'NULL does not support attribute access ({name!r})')


# A sentinel value that is ignored by type checker
NULL: Any = _NullType()
