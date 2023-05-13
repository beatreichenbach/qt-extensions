from enum import Enum

from PySide2 import QtWidgets, QtCore

from qt_extensions.parameters import (
    IntParameter,
    FloatParameter,
    StringParameter,
    PathParameter,
    ColorParameter,
    PointParameter,
    PointFParameter,
    SizeParameter,
    SizeFParameter,
    BoolParameter,
    EnumParameter,
    TabDataParameter,
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

    int_parameter = IntParameter('int')
    int_parameter.value = 9
    int_parameter.slider_max = 50
    widget.layout().addWidget(int_parameter)

    float_parameter = FloatParameter('float')
    float_parameter.decimals = 2
    float_parameter.value = 13.5234
    float_parameter.slider_min = 300
    float_parameter.slider_max = 700
    widget.layout().addWidget(float_parameter)

    string_parameter = StringParameter('string')
    string_parameter.value = 'asd'
    string_parameter.area = True
    widget.layout().addWidget(string_parameter)

    string_parameter = StringParameter('string_menu')
    string_parameter.value = '$PATH/file.json'
    string_parameter.menu = {
        'Presets': {'File': 'file.json', 'Empty': ''},
        'Bob': 'bob.txt',
    }
    widget.layout().addWidget(string_parameter)

    path_parameter = PathParameter('path')
    path_parameter.value = 'asd'
    path_parameter.method = PathParameter.Method.EXISTING_DIR
    widget.layout().addWidget(path_parameter)

    widget.layout().addWidget(ColorParameter('color'))

    point_parameter = PointParameter('point')
    widget.layout().addWidget(point_parameter)

    widget.layout().addWidget(PointFParameter('pointf'))

    size_parameter = SizeParameter('size')
    size_parameter.value = QtCore.QSize(17, 56)
    widget.layout().addWidget(size_parameter)

    widget.layout().addWidget(SizeFParameter('sizef'))

    widget.layout().addWidget(BoolParameter('bool'))

    enum_parameter = EnumParameter('enum')
    enum_parameter.enum = Enum('Number', ('one', 'two', 'three'))
    widget.layout().addWidget(enum_parameter)

    data = [
        ['Sun', 696000, 198],
        ['Earth', 6371, 5973.6],
        ['Moon', 1737, 73.5],
        ['Mars', 3390, 641.85],
        ['A really big Star', 406320, 339023452345.23450],
    ]
    tab_data_parameter = TabDataParameter('TabData')
    tab_data_parameter.default = data
    tab_data_parameter.headers = ['Name', 'Radius', 'Weight']
    tab_data_parameter.types = [str, int, float]
    tab_data_parameter.start_index = 4
    widget.layout().addWidget(tab_data_parameter)

    widget.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    widgets()
