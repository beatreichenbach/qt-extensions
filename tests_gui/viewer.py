import logging
import sys

import numpy as np
from PySide2 import QtWidgets, QtGui

from qt_extensions import theme
from qt_extensions.viewer import Viewer


def main():
    app = QtWidgets.QApplication(sys.argv)
    theme.apply_theme(theme.monokai)

    array = np.tile(
        np.linspace(start=0, stop=2, num=512, dtype=np.float32), reps=(512, 1)
    )
    array = np.swapaxes(array, 0, 1)
    image_array = np.dstack((array, array, np.zeros((512, 512), np.float64)))

    viewer = Viewer()
    viewer.set_array(image_array)
    viewer.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
