from enum import Enum

from PySide2 import QtWidgets, QtCore

from qt_extensions.properties import (
    IntProperty,
    FloatProperty,
    StringProperty,
    PathProperty,
    ColorProperty,
    PointProperty,
    PointFProperty,
    SizeProperty,
    SizeFProperty,
    BoolProperty,
    EnumProperty,
)


def widgets():
    import sys
    import logging
    from qt_extensions import theme

    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication()
    theme.apply_theme(theme.monokai)

    widget = QtWidgets.QWidget()
    widget.setLayout(QtWidgets.QVBoxLayout())

    int_property = IntProperty('int')
    int_property.value = 9
    int_property.slider_max = 50
    widget.layout().addWidget(int_property)

    float_property = FloatProperty('float')
    float_property.decimals = 2
    float_property.value = 13.5234
    float_property.slider_min = 300
    float_property.slider_max = 700
    widget.layout().addWidget(float_property)

    string_property = StringProperty('string')
    string_property.value = 'asd'
    string_property.area = True
    widget.layout().addWidget(string_property)

    string_property = StringProperty('string_menu')
    string_property.value = '$PATH/file.json'
    string_property.menu = {
        'Presets': {'File': 'file.json', 'Empty': ''},
        'Bob': 'bob.txt',
    }
    widget.layout().addWidget(string_property)

    path_property = PathProperty('path')
    path_property.value = 'asd'
    path_property.method = PathProperty.Method.EXISTING_DIR
    widget.layout().addWidget(path_property)

    widget.layout().addWidget(ColorProperty('color'))

    point_property = PointProperty('point')
    widget.layout().addWidget(point_property)

    widget.layout().addWidget(PointFProperty('pointf'))

    size_property = SizeProperty('size')
    size_property.value = QtCore.QSize(17, 56)
    widget.layout().addWidget(size_property)

    widget.layout().addWidget(SizeFProperty('sizef'))

    widget.layout().addWidget(BoolProperty('bool'))

    enum_property = EnumProperty('enum')
    enum_property.enum = Enum('Number', ('one', 'two', 'three'))
    widget.layout().addWidget(enum_property)

    widget.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    widgets()
