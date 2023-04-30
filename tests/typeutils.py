from dataclasses import dataclass, asdict
from enum import Enum

from PySide2 import QtGui, QtCore

from qt_extensions.typeutils import hash_dataclass, hashable_dict, cast, cast_basic


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
    assert cast(None, 'test') == None
    assert cast(str, 3.141) == '3.141'
    assert cast(bool, 'False') == True
    assert cast(int, 3.141) == 3
    assert cast(float, 3) == 3.0
    assert cast(tuple, [1, 2]) == (1, 2)
    assert cast(tuple[str, ...], [1, 2]) == ('1', '2')
    assert cast(list[str], (1, 2)) == ['1', '2']
    assert cast(dict[str, int], {1: 2.3, 2: 3.4}) == {'1': 2, '2': 3}

    assert cast(int | str, '1.234') == '1.234'

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
    assert cast_basic(item) == {
        'name': 'Apple',
        'unit_price': 2,
        'color': [1, 2, 3],
        'product_number': {'number': 2},
        'quantity_on_hand': 0,
    }
