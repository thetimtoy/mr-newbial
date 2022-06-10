from __future__ import annotations

from typing import Any, Mapping

__all__ = (
    'Config',
    'Slack',
    'Ipc',
    'Logging',
    'LoggingLevels',
    'Modules',
    'ModulesList',
    'Module',
    'CoreModule',
    'CoreModuleConfig',
)


# * -> not required


class Config(Mapping[str, Any]):
    slack: Slack
    ipc: Ipc
    logging: Logging
    modules: Modules


# config.slack
class Slack(Mapping[str, str]):
    bot_token: str
    socket_token: str


# config.ipc
class Ipc(Mapping[str, Any]):
    host: str
    port: int


# config.logging
class Logging(Mapping[str, Any]):
    enabled: bool
    levels: LoggingLevels


# config.logging.levels
class LoggingLevels(Mapping[str, str]):
    root: str
    newbial: str
    slack: str


# config.modules
class Modules(Mapping[str, Any]):
    path: str
    list: ModulesList


# config.modules.list
class ModulesList(Mapping[str, 'Module']):
    core: CoreModule
    util: Module


# config.modules.list.x
class Module(Mapping[str, Any]):
    config: Any  # *
    address: tuple[str, int]  # *


# config.modules.list.core
class CoreModule(Module, Mapping[str, Any]):
    config: CoreModuleConfig


# config.modules.list.core.config
class CoreModuleConfig(Mapping[str, Any]):
    command_prefixes: list[str]
