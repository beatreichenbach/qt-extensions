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
    int_parameter.set_value(9)
    int_parameter.set_line_min(2)
    int_parameter.set_slider_max(50)
    widget.layout().addWidget(int_parameter)

    float_parameter = FloatParameter('float')
    float_parameter.set_decimals(2)
    float_parameter.set_value(13.5234)
    float_parameter.set_slider_min(300)
    float_parameter.set_slider_max(700)
    widget.layout().addWidget(float_parameter)

    string_parameter = StringParameter('string')
    string_parameter.set_value('asd')
    string_parameter.set_area(True)
    widget.layout().addWidget(string_parameter)

    string_parameter = StringParameter('string_menu')
    string_parameter.set_value('$PATH/file.json')
    string_parameter.set_menu(
        {
            'Presets': {'File': 'file.json', 'Empty': ''},
            'Bob': 'bob.txt',
        }
    )
    widget.layout().addWidget(string_parameter)

    path_parameter = PathParameter('path')
    path_parameter.set_value('asd')
    path_parameter.set_method(PathParameter.EXISTING_DIR)
    widget.layout().addWidget(path_parameter)

    widget.layout().addWidget(ColorParameter('color'))

    point_parameter = PointParameter('point')
    widget.layout().addWidget(point_parameter)

    widget.layout().addWidget(PointFParameter('pointf'))

    size_parameter = SizeParameter('size')
    size_parameter.set_value(QtCore.QSize(17, 56))
    widget.layout().addWidget(size_parameter)

    sizef_parameter = SizeFParameter('sizef')
    widget.layout().addWidget(sizef_parameter)

    widget.layout().addWidget(BoolParameter('bool'))

    enum_parameter = EnumParameter('enum')
    enum_parameter.set_enum(Enum('Number', ('one', 'two', 'three')))
    widget.layout().addWidget(enum_parameter)

    data = [
        ['Sun', 696000, 198],
        ['Earth', 6371, 5973.6],
        ['Moon', 1737, 73.5],
        ['Mars', 3390, 641.85],
        ['A really big Star', 406320, 339023452345.23450],
    ]
    tab_data_parameter = TabDataParameter('TabData')
    tab_data_parameter.set_default(data)
    tab_data_parameter.set_headers(['Name', 'Radius', 'Weight'])
    tab_data_parameter.set_types([str, int, float])
    tab_data_parameter.set_start_index(4)
    widget.layout().addWidget(tab_data_parameter)

    widget.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    widgets()
