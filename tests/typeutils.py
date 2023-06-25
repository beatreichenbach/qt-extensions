from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import Enum
from typing import Union

from PySide2 import QtGui, QtCore

from qt_extensions.typeutils import (
    hashable_dataclass,
    HashableDict,
    cast,
    basic,
    deep_field,
)


@dataclass
class ProductNumber:
    number: int


@dataclass
class InventoryItem:
    name: str
    unit_price: float
    product_number: ProductNumber
    color: QtGui.QColor
    quantity_on_hand: int = 0


def test_cast():
    assert cast(None, 'test') is None
    assert cast(bool, 'False') is True
    assert cast(str, 3.141) == '3.141'
    assert cast(int, 3.141) == 3
    assert cast(float, 3) == 3.0
    assert cast(tuple, [1, 2]) == (1, 2)
    assert cast(tuple[str, ...], [1, 2]) == ('1', '2')
    assert cast(list[str], (1, 2)) == ['1', '2']
    assert cast(dict[str, int], {1: 2.3, 2: 3.4}) == {'1': 2, '2': 3}

    assert cast(Union[int, str], '1.234') == '1.234'

    enum = Enum('Color', 'Red, Green, Blue')
    assert cast(enum, 'Red') == enum['Red']

    item = InventoryItem('Apple', 2, ProductNumber(2), QtGui.QColor(1, 2, 3))
    assert (
        cast(
            InventoryItem,
            {
                'name': 'Apple',
                'unit_price': '2',
                'color': [1, 2, 3],
                'product_number': 2,
            },
        )
        == item
    )

    assert cast(QtGui.QColor, (1, 2, 3)) == QtGui.QColor(1, 2, 3)
    assert cast(QtCore.QPointF, (1, 2)) == QtCore.QPointF(1, 2)


def test_cast_basic():
    item = InventoryItem('Apple', 2, ProductNumber(2), QtGui.QColor(1, 2, 3))
    assert basic(item) == {
        'name': 'Apple',
        'unit_price': 2,
        'color': (1, 2, 3, 255),
        'product_number': {'number': 2},
        'quantity_on_hand': 0,
    }


def test_hashable_dataclass():
    @hashable_dataclass
    class TestClass:
        name: str
        count: int

    test = TestClass('Apple', 2)
    hash(test)


def test_hashable_dict():
    test = HashableDict([(0, 'a'), (1, 'b')])
    hash(test)


def test_deep_field():
    @dataclasses.dataclass
    class Test:
        color: QtGui.QColor = deep_field(QtGui.QColor(255, 255, 255))

    test1 = Test()
    test1.color.setRed(0)

    test2 = Test()
    assert test1 != test2
