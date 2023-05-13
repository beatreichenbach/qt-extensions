import logging
import sys
from PySide2 import QtWidgets

from qt_extensions import theme
from qt_extensions.box import CollapsibleBox
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
)


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    theme.apply_theme(theme.monokai)

    editor = ParameterEditor()

    editor.add_parameter(IntParameter('int'))
    editor.add_parameter(FloatParameter('float'))
    editor.add_separator()
    editor.add_parameter(PointParameter('point'))
    editor.add_parameter(PointFParameter('pointf'))
    editor.add_parameter(SizeParameter('size'))
    editor.add_parameter(SizeFParameter('sizef'))
    editor.add_parameter(BoolParameter('bool'))
    editor.add_parameter(PathParameter('path'))
    editor.add_parameter(StringParameter('string'))
    editor.add_parameter(ColorParameter('color'))
    # editor.add_parameter(
    #     EnumParameter('enum', enum=enum.Enum('Number', ('one', 'two', 'three')))
    # )

    group1 = editor.add_group(
        'group_1', collapsible=True, style=CollapsibleBox.Style.BUTTON
    )

    group1.add_parameter(IntParameter('int'))
    group1.add_parameter(FloatParameter('float'))

    action = QtWidgets.QAction('Save', group1)
    group1.addAction(action)
    group1.addAction(QtWidgets.QAction('Save1', group1))
    group1.addAction(QtWidgets.QAction('Save2', group1))

    group2 = editor.add_group(
        'group_2', collapsible=False, style=CollapsibleBox.Style.SIMPLE
    )

    group2.add_parameter(IntParameter('int'))
    group2.add_parameter(FloatParameter('float'))

    group1_nested = group2.add_group(
        'group_1_nested', collapsible=True, style=CollapsibleBox.Style.BUTTON
    )
    group1_nested.add_parameter(IntParameter('int'))
    group1_nested.add_parameter(FloatParameter('float'))
    nested_prop_tooltip = StringParameter('nested_tooltip')
    nested_prop_tooltip.tooltip = (
        'asdfasdfasdf asdf asdf asdf asdfa fdadsfa sdfadfadfasdfadf'
    )
    group1_nested.add_parameter(nested_prop_tooltip)

    group3 = editor.add_tab_group(('tab_1', 'tab_2'))

    parm = IntParameter('int4')
    parm.setEnabled(False)
    group3.tabs['tab_1'].add_parameter(parm)
    parm = FloatParameter('float4')
    parm.setEnabled(False)
    group3.tabs['tab_1'].add_parameter(parm)

    group4 = editor.add_group(
        'group_4', collapsible=True, style=CollapsibleBox.Style.SIMPLE
    )

    group4.add_parameter(IntParameter('int'))
    group4.add_parameter(FloatParameter('float'))

    group4.addAction(QtWidgets.QAction('Save', group4))
    group4.addAction(QtWidgets.QAction('Save1', group4))
    group4.addAction(QtWidgets.QAction('Save2', group4))

    parm = StringParameter('text')
    parm.area = True
    editor.add_parameter(parm)

    data = [
        ['Sun', 696000, 198],
        ['Earth', 6371, 5973.6],
        ['Moon', 1737, 73.5],
        ['Mars', 3390, 641.85],
        ['A really big Star', 406320, 339023452345.23450],
    ]
    parm = TabDataParameter('tabdata')
    parm.default = data
    parm.headers = ['Name', 'Radius', 'Weight']
    parm.types = [str, int, float]
    parm.start_index = 4
    parm.tooltip = 'By default, labels display left-aligned, vertically-centered text and images, where any tabs in the text to be displayed are automatically expanded. However, the look of a QLabel can be adjusted and fine-tuned in several ways.'
    editor.add_parameter(parm)

    # editor.values_changed.connect(logging.debug)
    # logging.debug(json.dumps(editor.values(), indent=4, default=lambda x: str(x)))
    editor.parameter_changed.connect(logging.debug)

    editor.show()

    state = editor.state()
    editor.set_state(state)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
