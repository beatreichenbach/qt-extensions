import numpy as np

from qt_extensions.viewer import Viewer
from tests_gui import application


def main() -> None:
    with application():
        array = np.tile(
            np.linspace(start=0, stop=2, num=512, dtype=np.float32), reps=(512, 1)
        )
        array = np.swapaxes(array, 0, 1)
        image_array = np.dstack((array, array, np.zeros((512, 512), np.float64)))

        widget = Viewer()
        widget.set_array(image_array)
        widget.show()


if __name__ == '__main__':
    main()
