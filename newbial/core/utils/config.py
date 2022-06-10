from __future__ import annotations

import os
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Iterator

import yaml
from dotenv import load_dotenv

from newbial.core.utils.helpers import NULL

if TYPE_CHECKING:
    from typing_extensions import Self

__all__ = ('Config',)

load_dotenv()


# Setting up YAML SafeLoader to allow "!ENV" and "!REQUIRED-ENV" annotations
# In the config.yml file. This allows us to reference environment variables in
# Our config.yml file


def _env_constructor(loader: yaml.SafeLoader, node: yaml.ScalarNode | yaml.SequenceNode):
    """Constructor for optional env variables in the yaml doc.

    Usage is as follows:

    ```yaml
    field: !ENV "KEY"
    # or
    field: !ENV ["KEY", "default"]
    ```

    If a string is provided after `!ENV`` and `"KEY"` is not found in `os.environ`,
    `None` resolves as the value.
    """
    if isinstance(node, yaml.ScalarNode):
        key = str(
            loader.construct_scalar(node)
        )  # type is _Scalar (str subclass), cast to str
        default = None
    elif isinstance(node, yaml.SequenceNode):
        key, default = loader.construct_sequence(node)  # value is ["KEY", default]
    else:
        raise ValueError(f'Invalid node {node} with id {node.id!r}')

    return os.environ.get(key, default)


def _required_env_constructor(loader: yaml.SafeLoader, node: yaml.ScalarNode):
    """Constructor for required env variables in the yaml doc.

    Usage is as follows:

    ```yaml
    field: !REQUIRED-ENV "KEY"
    ```

    An error is thrown if `"KEY"` is not found in `os.environ`.
    """
    key = str(loader.construct_scalar(node))

    try:
        return os.environ[key]
    except KeyError:
        raise ValueError(f'Missing env key {key!r}') from None


yaml.SafeLoader.add_constructor('!ENV', _env_constructor)
yaml.SafeLoader.add_constructor('!REQUIRED-ENV', _required_env_constructor)

_config_instance: _ConfigImpl | None = None


def _recursive_dict_update(target: dict[str, Any], source: dict[str, Any]) -> None:
    for k, v in source.items():
        try:
            existing = target[k]
        except KeyError:
            target[k] = v
        else:
            assert (
                existing.__class__ is v.__class__
            ), f'Type of key {k} in source does not match the type in target'

            if existing.__class__ is dict and v.__class__ is dict:
                _recursive_dict_update(existing, v)
            else:
                target[k] = v


class _ConfigField(Mapping):
    __slots__ = ('__dict__',)

    def __repr__(self) -> str:
        return self.__dict__.__repr__()

    def __getattr__(self, name: str) -> Any:
        return NULL

    def __getitem__(self, item: str) -> Any:
        return self.__dict__.__getitem__(item)

    def __iter__(self) -> Iterator[str]:
        return self.__dict__.__iter__()

    def __len__(self) -> int:
        return self.__dict__.__len__()

    def _update(self, data: dict[str, Any]) -> None:
        d = self.__dict__

        for k, v in data.items():
            if v.__class__ is dict:
                try:
                    field = d[k]
                except KeyError:
                    field = _ConfigField()
                field._update(v)
                v = field

            d[k] = v


class _ConfigImpl(_ConfigField):
    __slots__ = (
        '__file',
        '__localfile',
    )

    def __new__(
        cls, file: str = 'config.yml', localfile: str = 'localconfig.yml'
    ) -> Self:
        global _config_instance

        if _config_instance is not None:
            return _config_instance

        self = super().__new__(cls)
        self.__file = file
        self.__localfile = localfile
        self.__load()
        _config_instance = self

        return self

    def __call__(self) -> Self:
        return self.__load()

    def __load(self) -> Self:
        with open(self.__file, 'r') as file:
            config: dict[str, Any] = yaml.safe_load(file)
            try:
                with open(self.__localfile, 'r') as localfile:
                    localconfig = yaml.safe_load(localfile)
            except FileNotFoundError:
                pass
            else:
                if localconfig.__class__ is dict:
                    _recursive_dict_update(config, localconfig)

            self._update(config)

        return self


if TYPE_CHECKING:
    from newbial.types.config import Config
else:
    Config = _ConfigImpl
