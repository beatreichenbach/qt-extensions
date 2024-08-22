from PySide2 import QtWidgets

from qt_extensions import testing
from qt_extensions.elementbrowser import ElementBrowser, Field


@testing.gui
def main() -> QtWidgets.QWidget:
    widget = ElementBrowser([Field('name'), Field('focal')])
    # widget.model.element_added.connect(lambda data: logging.info(data))
    # widget.model.element_removed.connect(lambda data: logging.info(data))
    # widget.model.element_changed.connect(
    #     lambda data, data2: logging.info([data, data2])
    # )
    # widget.model.element_moved.connect(
    #     lambda data, parent: logging.info([data, parent])
    # )

    widget.show()
    return widget


if __name__ == '__main__':
    main()
