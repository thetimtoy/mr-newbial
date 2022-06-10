from __future__ import annotations

import asyncio
import importlib
import logging
import os
import sys
from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Coroutine,
    Iterator,
    NamedTuple,
    Sequence,
)

from ipc import rpc

from newbial.core.events import (
    ModuleLoadEvent,
    ModuleUnloadEvent,
    ModuleReloadEvent,
)
from newbial.core.structures import Module, RemoteModule
from newbial.core.utils import NULL

if TYPE_CHECKING:
    from types import ModuleType

    import ipc

    from newbial.core.bot import Bot
    from newbial.types.core import DispatchFunc

__all__ = ('ModuleManager',)


class ModuleInfo(NamedTuple):
    name: str
    address: tuple[str, int] = NULL
    connection: ipc.Connection = NULL


class ModuleManager(Mapping):
    if TYPE_CHECKING:
        _bot: Bot
        _dispatch: DispatchFunc
        _modules: dict[str, Module]
        _logger: logging.Logger

    def __init__(self, bot: Bot) -> None:
        self._bot = bot
        self._dispatch = bot.events.dispatch
        self._modules = {}
        self._logger = logging.getLogger(__name__)
        self._bot.ipc.register('load_module', self._load_remote)

    def __repr__(self) -> str:
        return f'<ModuleManager modules={list(self._modules)}>'

    def __len__(self) -> int:
        return self._modules.__len__()

    def __iter__(self) -> Iterator[str]:
        return self._modules.__iter__()

    def __getitem__(self, item: str) -> Module:
        return self._modules.__getitem__(item)

    def load(self, *modules: str) -> Coroutine[Any, Any, int]:
        return self._aggregate_helper(self._load_single, modules)

    def unload(self, *modules: str) -> Coroutine[Any, Any, int]:
        return self._aggregate_helper(self._unload_single, modules)

    def reload(self, *modules: str) -> Coroutine[Any, Any, int]:
        return self._aggregate_helper(self._reload_single, modules)

    async def _load_single(self, info: ModuleInfo) -> bool:
        if info.name in self._modules:
            return False

        if info.address:
            if not info.connection:
                host, port = self._bot.config.modules.list[info.name].address
                self._logger.debug(f'Attempting to load remote module "{info.name}"...')
                try:
                    await rpc.invoke(host, port, 'hello')
                except OSError as exc:
                    if exc.errno == 61:
                        self._logger.debug(f'Remote module "{info.name}" is offline.')
                        return False
                    raise exc
                assert info.name in self._modules  # this should not fail
                return True
            else:
                module_cls = RemoteModule
        else:
            py_module = importlib.import_module(self._module_path(info.name))

            try:
                module_cls = getattr(py_module, py_module.__all__[0])
            except AttributeError:
                raise ValueError(
                    f"Module {info.name!r} must specify '__all__'"
                    "with the module class's name as the first element"
                )

            assert issubclass(module_cls, Module)

        module = await self._load_module_from_cls(info, module_cls)

        self._dispatch(ModuleLoadEvent(module))

        return True

    async def _unload_single(self, info: ModuleInfo) -> bool:
        if not info.address:
            path = self._module_path(info.name)

            # Remove (now) stale entries from sys.modules
            for k in tuple(sys.modules):
                if k.startswith(path):
                    del sys.modules[k]

        # Check if we have the module instance after removing
        # sys.modules entries to allow self._reload_single() to work
        # even if the module was removed from the mapping
        try:
            module = self._modules[info.name]
        except KeyError:
            return False

        await module.teardown()

        if info.address:
            self._logger.debug(f'Unloaded remote module "{info.name}"')
        else:
            self._logger.debug(f'Unloaded module "{info.name}"')

        del self._modules[info.name]

        self._dispatch(ModuleUnloadEvent(module))

        return True

    async def _reload_single(self, info: ModuleInfo) -> bool:
        old_module: Module
        old_modules_state: dict[str, ModuleType]

        # Get state of the already loaded module (if it exists)
        try:
            old_module = self._modules[info.name]
        except KeyError:
            old_module = NULL
            old_modules_state = NULL  # prevent type checker warning
        else:
            # self._unload_single() deletes these entries so we want to keep a copy
            # if loading the new module goes wrong and we want to revert back.
            path = self._module_path(info.name)
            old_modules_state = {k: v for k, v in sys.modules.copy().items() if path in k}

        await self._unload_single(info)

        try:
            await self._load_single(info)
        except Exception:
            # Something went wrong with loading the updated module
            # We have to revert back (if possible) and re-raise the exception
            if old_module is not NULL:
                # Revert sys.modules
                if not info.address:
                    sys.modules.update(old_modules_state)

                # Load the previous *working* version of the module
                cls = old_module.__class__
                await self._load_module_from_cls(info, cls)

            raise

        module = self._modules[info.name]

        self._dispatch(ModuleReloadEvent(old_module, module))

        return True

    async def _load_remote(
        self, ctx: rpc.Context[rpc.Server, ipc.Connection], data: dict[str, Any]
    ) -> int:
        if (
            not isinstance(data, dict)
            or not isinstance(data.get('host'), str)
            or not isinstance(data.get('port'), int)
        ):
            self._logger.error(
                f'Invalid data received from remote load_module call: {data}'
            )
            return -1

        info = ModuleInfo(
            name=data['name'],
            address=(data['host'], data['port']),
            connection=ctx.connection,
        )

        self._logger.debug(f'Received remote load_module call for module "{info.name}"')

        if await self._load_single(info):
            return 1

        self._logger.debug(f'Remote load_module call failed for module "{info.name}".')

        return -1

    async def _aggregate_helper(
        self,
        method: Callable[[ModuleInfo], Coroutine[Any, Any, bool]],
        modules: Sequence[str],
    ) -> int:
        coros: list[Coroutine[Any, Any, bool]] = []
        module_infos: list[ModuleInfo] = []

        if not len(modules):
            module_infos = self._list_modules()
        else:
            module_infos = list(map(lambda s: ModuleInfo(name=s), modules))

        for info in module_infos:
            coros.append(method(info))

        ret = 0
        for ok in await asyncio.gather(*coros):
            if ok:
                ret += 1

        return ret

    async def _load_module_from_cls(self, info: ModuleInfo, cls: type[Module]) -> Module:
        if info.address:
            assert issubclass(cls, RemoteModule)
            module = cls(self._bot, info)
        else:
            module = cls(self._bot)

        await module.setup()

        if info.address:
            self._logger.debug(f'Loaded remote module "{info.name}"')
        else:
            self._logger.debug(f'Loaded module "{info.name}"')

        self._modules[info.name] = module

        return module

    def _module_path(self, module_name: str) -> str:
        path = os.path.join(self._bot.config.modules.path, module_name)

        return path.replace('/', '.')

    def _list_modules(self) -> list[ModuleInfo]:
        modules = []

        files = list(
            map(
                lambda s: s.removesuffix('.py'),
                os.listdir(self._bot.config.modules.path),
            )
        )

        if '__pycache__' in files:
            files.remove('__pycache__')

        for file in files:
            modules.append(ModuleInfo(name=file))

        for name, module in self._bot.config.modules.list.items():
            modules.append(ModuleInfo(name=name, address=module.address))

        return modules
