from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Coroutine

from ipc import rpc

from newbial.core.events import EVENT_MAPPING, BaseEvent
from newbial.core.structures import Command
from newbial.core.utils import NULL, maybe_awaitable

if TYPE_CHECKING:
    from typing_extensions import Self

    import ipc

    from newbial.core.bot import Bot
    from newbial.core.managers.module_manager import ModuleInfo
    from newbial.types.core import Event, EventT, EventCallback

__all__ = (
    'Module',
    'RemoteModule',
)


class ModuleMeta(type):
    __module_commands__: tuple[Command, ...]

    def __new__(
        cls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> Self:
        self = super().__new__(cls, name, bases, namespace)

        commands: dict[str, Command] = {}

        for base in reversed(self.__mro__[:-1]):
            for k, v in base.__dict__.items():
                if k in commands:
                    del commands[k]

                if isinstance(v, Command):
                    commands[k] = v

        self.__module_commands__ = tuple(commands.values())

        return self


class Module(metaclass=ModuleMeta):
    if TYPE_CHECKING:
        bot: Bot
        name: str
        logger: logging.Logger
        commands: list[Command]
        _bound_commands: list[Command] | None
        _bound_listeners: list[tuple[type[Event], EventCallback]] | None

    name = NULL
    tasks = None  # TODO
    _bound_commands = None
    _bound_listeners = None

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        self = super().__new__(cls)

        self.commands = list(cls.__module_commands__)

        return self

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        if self.name is NULL:
            self.name = self.__class__.__name__.lower()

        self.logger = logging.getLogger(f'newbial.modules.{self.name}')

    async def setup(self) -> None:
        bot = self.bot

        await maybe_awaitable(self.setup_hook)

        if self.commands is not None:
            bound_commands = self._bound_commands
            for command in self.commands:
                bound = command._bind(self)

                if bound_commands is None:
                    bound_commands = self._bound_commands = []

                bound_commands.append(bound)
                ...  # TODO: Register command

    async def teardown(self) -> None:
        bot = self.bot

        await maybe_awaitable(self.teardown_hook)

        if self._bound_commands is not None:
            for command in self._bound_commands:
                ...  # TODO: Unregister command

        if self._bound_listeners is not None:
            for event, listener in self._bound_listeners:
                bot.events.remove_callback(event, listener)

    def setup_hook(self) -> None:
        pass

    def teardown_hook(self) -> None:
        pass

    def add_listener(
        self,
        event: type[EventT],
        callback: EventCallback[EventT],
    ) -> None:
        if self._bound_listeners is None:
            self._bound_listeners = []

        self._bound_listeners.append((event, callback))

        self.bot.events.add_callback(event, callback)

    def remove_listener(
        self, event: type[EventT], callback: EventCallback[EventT]
    ) -> None:
        if self._bound_listeners is not None:
            try:
                self._bound_listeners.remove((event, callback))
            except ValueError:
                pass

        self.bot.events.remove_callback(event, callback)

    def toJSON(self) -> dict[str, Any]:
        return {'name': self.name}


class RemoteModule(Module):
    if TYPE_CHECKING:
        rpc: rpc.Client

    def __init__(self, bot: Bot, info: ModuleInfo) -> None:
        self.bot = bot
        self.name = info.name
        self.logger = logging.getLogger(f'newbial.remote_modules.{info.name}')
        self.address = host, port = info.address
        self.rpc = rpc.Client(host, port)
        self.connection = info.connection

    async def setup_hook(self) -> None:
        await self._connect()

    async def teardown_hook(self) -> None:
        if self.rpc.connected:
            await self.rpc.commands.teardown()
            await self.rpc.close()

    async def _connect(self) -> None:
        await self.rpc.connect()

        self.logger.debug('Online.')
        self.connection.add_listener('message', self._on_message)
        self.connection.add_listener('disconnect', self._on_remote_disconnect)

        data = await self.rpc.commands.setup()

        cb = self._send_event
        for event_name in data.get('events', ()):
            self.add_listener(EVENT_MAPPING[event_name], cb)  # type: ignore

    async def _on_remote_disconnect(self, exc: Exception | None) -> None:
        msg = 'Offline.'
        level = logging.DEBUG
        if exc is not None:
            msg += f" Exception: {exc.__class__.__name__}({''.join(exc.args)}"
            level = logging.INFO
        self.logger.log(level, msg)
        await self.bot.modules.unload(self.name)

    def _send_event(self, event: BaseEvent) -> Coroutine[Any, Any, Any]:
        data = {'t': event.__class__.__event_name__, 'd': event.toJSON()}
        return self.rpc.invoke('event', data)

    def _on_message(self, data: Any) -> None:
        if rpc.utils.is_command(data):
            return

        assert data.__class__ is dict

        method = getattr(self.logger, data['level'])
        method(data['message'])

    def toJSON(self) -> dict[str, Any]:
        d = super().toJSON()
        d['address'] = self.address
        return d
