from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from newbial.core.events import BaseEvent

if TYPE_CHECKING:
    from newbial.core.structures import Module

__all__ = (
    'ModuleLoadEvent',
    'ModuleUnloadEvent',
    'ModuleReloadEvent',
)


class ModuleEvent(BaseEvent, Protocol):
    __slots__ = ('module',)

    if TYPE_CHECKING:
        module: Module

    def __init__(self, module: Module) -> None:
        self.module = module

    _init = __init__


ModuleEvent.__init__ = ModuleEvent._init
del ModuleEvent._init


class ModuleLoadEvent(ModuleEvent):
    __slots__ = ()
    __event_name__ = 'module_load'


class ModuleUnloadEvent(ModuleEvent):
    __slots__ = ()
    __event_name__ = 'module_unload'


class ModuleReloadEvent(ModuleEvent):
    __slots__ = ('old_module',)
    __event_name__ = 'module_reload'

    if TYPE_CHECKING:
        old_module: Module

    def __init__(self, old_module: Module, module: Module) -> None:
        self.old_module = old_module

        super().__init__(module)
