import dataclasses
import json
import sys
from dataclasses import is_dataclass, fields
from enum import Enum
from types import GenericAlias, UnionType, GeneratorType, NoneType
from typing import Any, ForwardRef, _UnionGenericAlias, _eval_type

from PySide2 import QtCore, QtGui


def cast(typ: Any, value: Any, globalns: dict | None = None) -> Any:
    # casts a value to a type or a type hint

    if globalns is None:
        globalns = {}

    if typ in (None, NoneType):
        return None

    elif typ is Any:
        return value

    elif isinstance(typ, str):
        # check if string is a ForwardRef, such as 'InventoryItem'
        typ = _eval_type(ForwardRef(typ), globalns, globalns)
        return cast(typ, value)

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
        elif isinstance(value, (list, tuple)):
            # treat value as *args for a dataclass
            for field_, v in zip(fields(typ), value):
                kw_value = cast(field_.type, v, globalns)
                kwargs[field_.name] = kw_value
        else:
            return typ(value)
        return typ(**kwargs)

    elif isinstance(typ, type) and issubclass(typ, (tuple, set)):
        return typ(value)

    elif isinstance(typ, type) and issubclass(typ, Enum):
        # type hints such as enum.Enum
        try:
            enum = typ[value]
            return enum
        except KeyError:
            return len(typ) and list(typ)[0] or None

    else:
        # all other type hints
        if isinstance(value, (tuple, list)):
            return typ(*value)
        elif isinstance(value, Enum):
            return typ(value.value)
        else:
            return typ(value)

    raise TypeError(f'cannot cast to type ({typ})')


def cast_basic(obj: Any) -> Any:
    # returns a basic type that can be serialized by json

    if dataclasses.is_dataclass(obj):
        obj = dataclasses.asdict(obj)

    match obj:
        case str() | int() | float() | bool() | None:
            # basic types as defined in json library
            return obj
        case list() | GeneratorType():
            return type(obj)(cast_basic(v) for v in obj)
        case dict():
            return type(obj)((k, cast_basic(v)) for k, v in obj.items())
        case tuple():
            return type(obj)(cast_basic(v) for v in obj)
        case set():
            return [cast_basic(v) for v in obj]
        case Enum():
            return obj.name
        case QtCore.QPoint() | QtCore.QPointF():
            return [obj.x(), obj.y()]
        case QtCore.QSize() | QtCore.QSizeF():
            return [obj.width(), obj.height()]
        case QtCore.QRect() | QtCore.QRectF():
            return [obj.x(), obj.y(), obj.width(), obj.height()]
        case QtGui.QColor():
            return obj.getRgbF()

    try:
        # convert enum, flags to int
        if int(obj) == obj:
            return int(obj)
    except TypeError:
        pass

    raise TypeError(f'Cannot convert {obj.__class__} to basic type.')


def deep_field(obj) -> dataclasses.Field:
    return dataclasses.field(default_factory=lambda: obj.__class__(obj))


def hashable_dataclass(cls):
    def __hash__(self):
        json_data = cast_basic(self)
        return hash(json.dumps(json_data, sort_keys=True))

    cls.__hash__ = __hash__
    return dataclasses.dataclass(cls)


class HashableDict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))
