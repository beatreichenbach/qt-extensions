from PySide2 import QtWidgets

from qt_extensions import testing
from qt_extensions.messagebox import MessageBox


@testing.gui
def main() -> None:
    MessageBox.warning(QtWidgets.QWidget(), 'Title', 'text')
    MessageBox.question(QtWidgets.QWidget(), 'Title', 'text')
    MessageBox.information(QtWidgets.QWidget(), 'Title', 'text')
    MessageBox.critical(QtWidgets.QWidget(), 'Title', 'text')


if __name__ == '__main__':
    main()
