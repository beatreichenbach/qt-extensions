from __future__ import annotations

import dataclasses
import json
import sys
from collections.abc import Sequence, Iterator
from dataclasses import is_dataclass, fields
from enum import Enum
from types import GenericAlias
from typing import Any, Callable, ForwardRef, TypeVar
from typing import _eval_type, _UnionGenericAlias  # noqa

from PySide2 import QtCore, QtGui

try:
    from types import UnionType, NoneType
except ImportError:
    # python 3.9
    from typing import Union

    UnionType = type(Union)
    NoneType = None


T = TypeVar('T')


def cast(typ: type[T], value: Any, globalns: dict | None = None) -> T:
    """Casts a value to a type or a type hint.

    Raises TypeError when failed.
    """

    if globalns is None:
        globalns = {}

    if typ in (None, NoneType):
        return None

    elif typ is Any:
        return value

    elif isinstance(typ, type) and isinstance(value, typ):
        return value

    elif isinstance(typ, str):
        # check if string is a ForwardRef, such as 'InventoryItem'
        typ = _eval_type(ForwardRef(typ), globalns, globalns)
        return cast(typ, value)

    elif isinstance(typ, type) and issubclass(typ, (list, tuple, set)):
        return typ(value)

    elif isinstance(typ, type) and issubclass(typ, Enum):
        # type hints such as enum.Enum
        if isinstance(value, typ):
            # value is Enum
            return value
        try:
            enum = typ[value]
            return enum
        except KeyError:
            return len(typ) and list(typ)[0] or None

    elif isinstance(typ, GenericAlias):
        # type hints such as list[int], dict[str, int] etc.
        origin = typ.__origin__
        args = typ.__args__
        if issubclass(origin, list):
            try:
                arg = args[0]
                return origin(cast(arg, v, globalns) for v in value)
            except IndexError:
                return origin(value)
            except TypeError:
                return value

        elif issubclass(origin, tuple):
            if len(args) == 2 and args[1] is Ellipsis:
                return origin(cast(args[0], v, globalns) for v in value)
            try:
                return origin(cast(args[i], v, globalns) for i, v in enumerate(value))
            except IndexError:
                return origin(value)

        elif issubclass(origin, dict):
            try:
                key_arg = args[0]
                value_arg = args[1]
                return origin(
                    (cast(key_arg, k, globalns), cast(value_arg, v, globalns))
                    for k, v in value.items()
                )
            except IndexError:
                return dict(**value)

    elif isinstance(typ, (UnionType, _UnionGenericAlias)):
        # type hints such as int | str, Optional[int]

        if type(value) in typ.__args__:
            # don't convert if current type comes later in list
            return value
        # iterate through all types until one works
        for arg in typ.__args__:
            try:
                return cast(arg, value, globalns)
            except (ValueError, TypeError):
                continue

    elif isinstance(typ, ForwardRef):
        typ = _eval_type(typ, globalns, globalns)
        return cast(typ, value)

    elif is_dataclass(typ):
        # types hints that are dataclasses

        # update globals (see typing module)
        base_globals = getattr(sys.modules.get(typ.__module__, None), '__dict__', {})
        globalns.update(base_globals)

        kwargs = {}
        if isinstance(value, dict):
            # treat value as kwargs for dataclass
            for field_ in fields(typ):
                if field_.name not in value:
                    continue
                kw_value = cast(field_.type, value[field_.name], globalns)
                kwargs[field_.name] = kw_value
        elif isinstance(value, Sequence):
            # treat value as *args for a dataclass
            for field_, v in zip(fields(typ), value):
                kw_value = cast(field_.type, v, globalns)
                kwargs[field_.name] = kw_value
        else:
            return typ(value)
        return typ(**kwargs)

    else:
        # all other type hints
        if isinstance(value, (tuple, list)):
            return typ(*value)
        elif isinstance(value, Enum):
            return typ(value.value)
        else:
            return typ(value)

    raise TypeError(f'cannot cast to type ({typ})')


def basic(obj: Any) -> tuple | list | dict | str | int | float | bool | None:
    """Returns a basic type that can be serialized by json."""

    if obj is None:
        return
    elif isinstance(obj, (str, int, float, bool)):
        # basic types as defined in json library
        return obj
    elif dataclasses.is_dataclass(obj):
        return basic(dataclasses.asdict(obj))
    elif isinstance(obj, Iterator):
        return tuple(basic(v) for v in obj)
    elif isinstance(obj, dict):
        return {k: basic(v) for k, v in obj.items()}
    elif isinstance(obj, Enum):
        return obj.name
    elif isinstance(obj, (QtCore.QPoint, QtCore.QPointF)):
        return obj.x(), obj.y()
    elif isinstance(obj, (QtCore.QSize, QtCore.QSizeF)):
        return obj.width(), obj.height()
    elif isinstance(obj, (QtCore.QRect, QtCore.QRectF)):
        return obj.x(), obj.y(), obj.width(), obj.height()
    elif isinstance(obj, QtGui.QColor):
        return obj.getRgb()
    else:
        # convert enum, flags to int
        try:
            if int(obj) == obj:
                return int(obj)
        except TypeError:
            pass

    raise TypeError(f'cannot convert {obj.__class__} to basic type')


def deep_field(obj) -> dataclasses.Field:
    return dataclasses.field(default_factory=lambda: obj.__class__(obj))


def hashable_dataclass(cls) -> Callable:
    def __hash__(self) -> int:
        if self._hash is None:
            data = basic(self)
            _hash = hash(json.dumps(data, sort_keys=True))
            super(cls, self).__setattr__('_hash', _hash)
        return self._hash

    def __setattr__(self, name: str, value: Any) -> None:
        super(cls, self).__setattr__(name, value)
        super(cls, self).__setattr__('_hash', None)

    cls._hash = None
    cls.__setattr__ = __setattr__
    cls.__hash__ = __hash__
    return dataclasses.dataclass(cls)


class HashableDict(dict):
    def __hash__(self) -> int:
        return hash(tuple(sorted(self.items())))
