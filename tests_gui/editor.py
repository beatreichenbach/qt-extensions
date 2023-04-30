import logging
import sys
from PySide2 import QtWidgets

from qt_extensions import theme
from qt_extensions.box import CollapsibleBox
from qt_extensions.properties import PropertyEditor, TabDataProperty
from qt_extensions import properties
from qt_extensions.typeutils import cast_basic


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    theme.apply_theme(theme.monokai)

    editor = PropertyEditor()

    editor.add_property(properties.IntProperty('int'))
    editor.add_property(properties.FloatProperty('float'))
    editor.add_separator()
    editor.add_property(properties.PointProperty('point'))
    editor.add_property(properties.PointFProperty('pointf'))
    editor.add_property(properties.SizeProperty('size'))
    editor.add_property(properties.SizeFProperty('sizef'))
    editor.add_property(properties.BoolProperty('bool'))
    editor.add_property(properties.PathProperty('path'))
    editor.add_property(properties.StringProperty('string'))
    editor.add_property(properties.ColorProperty('color'))
    # editor.add_property(
    #     properties.EnumProperty('enum', enum=enum.Enum('Number', ('one', 'two', 'three')))
    # )

    group1 = editor.add_group(
        'group_1', collapsible=True, style=CollapsibleBox.Style.BUTTON
    )

    group1.add_property(properties.IntProperty('int'))
    group1.add_property(properties.FloatProperty('float'))

    action = QtWidgets.QAction('Save', group1)
    group1.addAction(action)
    group1.addAction(QtWidgets.QAction('Save1', group1))
    group1.addAction(QtWidgets.QAction('Save2', group1))

    group2 = editor.add_group(
        'group_2', collapsible=False, style=CollapsibleBox.Style.SIMPLE
    )

    group2.add_property(properties.IntProperty('int'))
    group2.add_property(properties.FloatProperty('float'))

    group1_nested = group2.add_group(
        'group_1_nested', collapsible=True, style=CollapsibleBox.Style.BUTTON
    )
    group1_nested.add_property(properties.IntProperty('int'))
    group1_nested.add_property(properties.FloatProperty('float'))
    nested_prop_tooltip = properties.StringProperty('nested_tooltip')
    nested_prop_tooltip.tooltip = (
        'asdfasdfasdf asdf asdf asdf asdfa fdadsfa sdfadfadfasdfadf'
    )
    group1_nested.add_property(nested_prop_tooltip)

    group3 = editor.add_tab_group(('tab_1', 'tab_2'))

    group3.tabs['tab_1'].add_property(properties.IntProperty('int4'))
    group3.tabs['tab_1'].add_property(properties.FloatProperty('float4'))

    group4 = editor.add_group(
        'group_4', collapsible=True, style=CollapsibleBox.Style.SIMPLE
    )

    group4.add_property(properties.IntProperty('int'))
    group4.add_property(properties.FloatProperty('float'))

    group4.addAction(QtWidgets.QAction('Save', group4))
    group4.addAction(QtWidgets.QAction('Save1', group4))
    group4.addAction(QtWidgets.QAction('Save2', group4))

    prop = properties.StringProperty('text')
    prop.area = True
    editor.add_property(prop)

    data = [
        ['Sun', 696000, 198],
        ['Earth', 6371, 5973.6],
        ['Moon', 1737, 73.5],
        ['Mars', 3390, 641.85],
        ['A really big Star', 406320, 339023452345.23450],
    ]
    prop = TabDataProperty('tabdata')
    prop.default = data
    prop.headers = ['Name', 'Radius', 'Weight']
    prop.types = [str, int, float]
    prop.start_index = 4
    prop.tooltip = 'By default, labels display left-aligned, vertically-centered text and images, where any tabs in the text to be displayed are automatically expanded. However, the look of a QLabel can be adjusted and fine-tuned in several ways.'
    editor.add_property(prop)

    # editor.values_changed.connect(logging.debug)
    # logging.debug(json.dumps(editor.values(), indent=4, default=lambda x: str(x)))
    editor.property_changed.connect(logging.debug)

    editor.show()
    state = editor.state
    editor.state = cast_basic(state)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
