from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Sequence,
)

from newbial.core.utils import NULL
from newbial.types.core import T, ModuleT

if TYPE_CHECKING:
    from typing_extensions import Self

    from newbial.core.structures import Context

__all__ = ('Command',)


class _CommandOptions:
    __slots__ = (
        'name',
        'aliases',
        'module',
        'func',
    )


class Command(Generic[ModuleT, T]):
    """Represents a bot command.

    This should be used as a decorator.

    Examples
    --------
    ```py
    # Create a command named "foo", with a
    # single "bar" alias.
    @Command(name='foo', aliases=['bar'])
    def qux(ctx):
        ...

    ```"""

    __slots__ = (
        '_options',
        'module',
    )

    if TYPE_CHECKING:
        name: str
        aliases: Sequence[str] | None
        module: ModuleT
        func: Callable[[ModuleT, Context], T]

    def __init__(self, *, name: str, aliases: Sequence[str] | None = None) -> None:
        opts = _CommandOptions()
        opts.name = name
        opts.aliases = aliases
        opts.func = NULL  # set in self.__call__()
        self.module = NULL
        self._options = opts

    def __call__(self, func: Callable[[ModuleT, Context], T]) -> Self:
        if self._options.func is not NULL:
            raise RuntimeError(f'Command {self!r} already has a callback registered.')

        self._options.func = func

        return self

    def __getattr__(self, name: str) -> Any:
        opts = self._options
        try:
            return getattr(opts, name)
        except AttributeError:
            raise AttributeError(
                f'{self.__class__.__name__!r} object has no attribute {name!r}'
            )

    def _bind(self, module: ModuleT) -> Self:
        cls = self.__class__
        copy = cls.__new__(cls)

        copy._options = self._options
        copy.module = module

        return copy
