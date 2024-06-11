import json
import logging
import sys
from enum import Enum
from functools import partial

from PySide2 import QtWidgets

from qt_extensions import theme
from qt_extensions.parameters import (
    ParameterEditor,
    TabDataParameter,
    IntParameter,
    FloatParameter,
    PointParameter,
    PointFParameter,
    SizeParameter,
    SizeFParameter,
    BoolParameter,
    PathParameter,
    StringParameter,
    ColorParameter,
    EnumParameter,
)
from qt_extensions.parameters.editor import ParameterBox


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    theme.apply_theme(theme.monokai)

    editor = ParameterEditor()

    # default parameters
    box = editor.add_group('default')
    box.set_collapsed(False)
    box.set_box_style(ParameterBox.SIMPLE)
    form = box.form

    # action
    action = QtWidgets.QAction('Reset', form)
    action.triggered.connect(partial(form.reset, None))
    form.addAction(action)

    form.add_parameter(IntParameter('int'))
    form.add_parameter(FloatParameter('float'))
    form.add_parameter(StringParameter('string'))
    form.add_parameter(PathParameter('path'))
    form.add_parameter(BoolParameter('bool'))
    parm = EnumParameter('enum')
    enum = Enum('Number', ('one', 'two', 'three'))
    parm.set_enum(enum)
    form.add_parameter(parm)
    form.add_parameter(ColorParameter('color'))
    form.add_parameter(PointParameter('point'))
    form.add_parameter(PointFParameter('pointf'))
    form.add_parameter(SizeParameter('size'))
    form.add_parameter(SizeFParameter('sizef'))

    # attributes
    box = editor.add_group('attributes')
    box.set_collapsed(False)
    box.set_box_style(ParameterBox.SIMPLE)
    form = box.form

    parm = IntParameter('int')
    parm.set_default(5)
    parm.set_slider_min(2)
    parm.set_slider_max(8)
    parm.set_line_min(1)
    parm.set_line_max(7)
    parm.set_slider_visible(True)
    parm.set_commit_on_edit(True)
    form.add_parameter(parm)

    parm = FloatParameter('float')
    parm.set_default(5)
    parm.set_slider_min(2)
    parm.set_slider_max(12)
    parm.set_line_min(1)
    parm.set_line_max(20)
    parm.set_slider_visible(True)
    parm.set_commit_on_edit(True)
    parm.set_decimals(3)
    form.add_parameter(parm)

    parm = StringParameter('str')
    parm.set_default('Hello World')
    parm.set_menu({'parent': {'child 1': 'child_1', 'child 2': 'child_2'}})
    form.add_parameter(parm)

    parm = PathParameter('path')
    parm.set_default('c:/temp')
    parm.set_method(PathParameter.SAVE_FILE)
    parm.set_dir_fallback('c:/windows')
    form.add_parameter(parm)

    parm = EnumParameter('enum')
    parm.set_enum(enum)
    parm.set_default(enum['two'])
    parm.set_formatter(lambda s: s.upper())
    form.add_parameter(parm)

    parm = PointParameter('point')
    parm.set_default((5, 3))
    parm.set_line_min(1)
    parm.set_line_max(7)
    form.add_parameter(parm)

    parm = PointFParameter('pointf')
    parm.set_default((5, 3))
    parm.set_line_min(1)
    parm.set_line_max(7)
    parm.set_decimals(3)
    form.add_parameter(parm)

    parm = SizeParameter('size')
    parm.set_default((5, 3))
    parm.set_slider_min(2)
    parm.set_slider_max(8)
    parm.set_line_min(1)
    parm.set_line_max(7)
    parm.set_slider_visible(True)
    parm.set_commit_on_edit(True)
    parm.set_ratio_visible(True)
    parm.set_keep_ratio(False)
    form.add_parameter(parm)

    parm = SizeFParameter('sizef')
    parm.set_default((5, 3))
    parm.set_slider_min(2)
    parm.set_slider_max(8)
    parm.set_line_min(1)
    parm.set_line_max(7)
    parm.set_slider_visible(True)
    parm.set_commit_on_edit(True)
    parm.set_ratio_visible(True)
    parm.set_keep_ratio(False)
    parm.set_decimals(3)
    form.add_parameter(parm)

    # tabdata
    box = editor.add_group('tabdata')
    box.set_box_style(ParameterBox.BUTTON)
    form = box.form

    data = [
        ['Sun', 696000, 198],
        ['Earth', 6371, 5973.6],
        ['Moon', 1737, 73.5],
        ['Mars', 3390, 641.85],
        ['A really big Star', 406320, 339023452345.23450],
    ]
    parm = TabDataParameter('tabdata')
    parm.set_default(data)
    parm.set_headers(['Name', 'Radius', 'Weight'])
    parm.set_types([str, int, float])
    parm.set_start_index(4)
    parm.set_tooltip(
        'By default, labels display left-aligned, vertically-centered text and images, '
        'where any tabs in the text to be displayed are automatically expanded.'
        'However, the look of a QLabel can be adjusted and fine-tuned in several ways.'
    )
    form.add_parameter(parm)

    # tab widget
    tab = editor.add_tab_group(['tab_1', 'tab_2'])
    tab.tabs['tab_1'].add_parameter(IntParameter('int'))
    tab.tabs['tab_2'].add_parameter(IntParameter('int'))

    logging.debug(json.dumps(editor.values(), indent=4, default=lambda x: str(x)))
    editor.parameter_changed.connect(lambda p: logging.debug(p.value()))

    state = editor.state()
    editor.set_state(state)

    editor.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
