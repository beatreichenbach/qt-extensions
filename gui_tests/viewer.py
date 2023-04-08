import logging
import sys

import numpy as np
from PySide2 import QtWidgets

from qt_extensions import theme
from qt_extensions.viewer import Viewer


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    theme.apply_theme(theme.monokai)

    viewer = Viewer()
    array = np.tile(np.linspace(0, 1, 512), (512, 1))
    image = np.dstack((array, array, array))
    viewer.update_image(image)

    viewer.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
