import dataclasses
import json
import logging
import sys
from dataclasses import is_dataclass, fields
from enum import Enum
from types import GenericAlias, UnionType, GeneratorType, NoneType
from typing import Any, ForwardRef, _UnionGenericAlias, _eval_type

from PySide2 import QtCore, QtGui


def cast_basic(obj: Any) -> Any:
    # returns a basic type that can be serialized by json
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


def cast(typ: type, value: Any, globalns: dict | None = None) -> Any:
    # casts a value to a type or a type hint
    if typ == str:
        pass

    if globalns is None:
        globalns = {}

    if typ in (None, NoneType):
        return None

    elif typ is Any:
        return value

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
        # iterate through all types until one works
        for arg in typ.__args__:
            try:
                return cast(arg, value, globalns)
            except TypeError:
                continue

    elif isinstance(typ, ForwardRef):
        typ = _eval_type(typ, globalns, globalns)
        return cast(typ, value)

    elif isinstance(typ, str):
        typ = _eval_type(ForwardRef(typ), globalns, globalns)
        return cast(typ, value)

    elif issubclass(typ, Enum):
        try:
            enum = typ[value]
            return enum
        except KeyError:
            return len(typ) and list(typ)[0] or None

    elif is_dataclass(typ):
        # types that are dataclasses

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

    else:
        if isinstance(value, (tuple, list)):
            return typ(*value)
        elif isinstance(value, Enum):
            return typ(value.value)
        else:
            return typ(value)

    raise TypeError(f'cannot cast to type ({typ})')


def _asdict_inner(obj):
    # dataclasses.asdict without deepcopy
    if dataclasses.is_dataclass(obj):
        result = []
        for f in fields(obj):
            value = _asdict_inner(getattr(obj, f.name))
            result.append((f.name, value))
        return dict(result)
    elif isinstance(obj, tuple) and hasattr(obj, '_fields'):
        return type(obj)(*[_asdict_inner(v) for v in obj])
    elif isinstance(obj, (list, tuple)):
        return type(obj)(_asdict_inner(v) for v in obj)
    elif isinstance(obj, dict):
        return type(obj)((_asdict_inner(k), _asdict_inner(v)) for k, v in obj.items())
    else:
        return obj


def cast_json(value: Any) -> dict:
    # TODO: implement __deepcopy__ instead of this gabaghoou
    if dataclasses.is_dataclass(value):
        value = _asdict_inner(value)
    data = cast_basic(value)
    return data


def hash_dataclass(cls):
    def __hash__(self):
        json_data = cast_json(self)
        return hash(json.dumps(json_data, sort_keys=True))

    cls.__hash__ = __hash__
    return dataclasses.dataclass(cls)
