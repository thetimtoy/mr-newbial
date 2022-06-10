from typing import Any, Protocol, Sequence

from newbial.types.events import Event

__all__ = (
    'EVENT_MAPPING',
    'BaseEvent',
)


EVENT_MAPPING: dict[str, Event] = {}


class BaseEvent(Event, Protocol):
    __slots__ = ()

    def __repr__(self) -> str:
        attrs = ''.join(
            tuple(
                f' {attr}={getattr(self, attr)}'
                for attr in self._get_attr_names()
                if not attr.startswith('_')
            )
        )

        return f'<{self.__class__.__name__}{attrs}>'

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        try:
            event_name = cls.__event_name__
        except AttributeError:
            pass
        else:
            EVENT_MAPPING[event_name] = cls

    def _get_attr_names(self) -> tuple[str, ...]:
        attr_names: list[str] = []

        for cls in self.__class__.mro():
            try:
                slots: Sequence[str] = cls.__slots__  # type: ignore
            except AttributeError:
                pass
            else:
                attr_names.extend(slots)

        try:
            d = self.__dict__
        except AttributeError:
            pass
        else:
            attr_names.extend(d)

        return tuple(set(attr_names))

    def toJSON(self) -> dict[str, Any]:
        d: dict[str, Any] = {}

        for k in self._get_attr_names():
            v = getattr(self, k)
            try:
                toJSON = v.toJSON
            except AttributeError:
                pass
            else:
                v = toJSON()

            d[k] = v

        return d
