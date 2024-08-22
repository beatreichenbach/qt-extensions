import numpy as np
from PySide2 import QtWidgets

from qt_extensions import testing
from qt_extensions.viewer import Viewer


@testing.gui
def main() -> QtWidgets.QWidget:
    array = np.tile(
        np.linspace(start=0, stop=2, num=512, dtype=np.float32), reps=(512, 1)
    )
    array = np.swapaxes(array, 0, 1)
    image_array = np.dstack((array, array, np.zeros((512, 512), np.float64)))

    widget = Viewer()
    widget.set_array(image_array)
    widget.show()
    return widget


if __name__ == '__main__':
    main()
