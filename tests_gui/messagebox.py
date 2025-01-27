from qtpy import QtWidgets

from qt_extensions.messagebox import MessageBox
from tests_gui import application


def main() -> None:
    with application():
        MessageBox.warning(QtWidgets.QWidget(), 'Title', 'text')
        MessageBox.question(QtWidgets.QWidget(), 'Title', 'text')
        MessageBox.information(QtWidgets.QWidget(), 'Title', 'text')
        MessageBox.critical(QtWidgets.QWidget(), 'Title', 'text')


if __name__ == '__main__':
    main()
