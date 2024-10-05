# qt-extensions

This is a collection of widgets and utility functions to extend Qt.
This package uses Material Icons from
[qt-material-icons](https://github.com/beatreichenbach/qt-material-icons).

## Installation

Install using pip:
```shell
pip install qt-extensions
```

## Usage

For examples see the [tests_gui](tests_gui) directory.

## Modules

### parameters
A collection of modules for a unified parameter editor. It has widgets for most common variable types similar to the Nuke knobs.

![Screenshot of the box widget](/.github/assets/parameter_editor.png)

### box
A collapsible box with multiple styles.

![Screenshot of the box widget](/.github/assets/box.png)

### buttons
A helper module to create styled buttons.

![Screenshot of the buttons widget](/.github/assets/buttons.png)

### elementbrowser
An abstract element browser that can display complex objects with multiple columns.

### filebrowser
A browser based on the ElementBrowser widget to display files.

![Screenshot of the filebrowser widget](/.github/assets/filebrowser.png)

### flexview
A StandardItemView that displays items in a flex view.

### logger
A status bar and log viewer that provides a gui interface for the logging module.

![Screenshot of the logbar and logviewer widget](/.github/assets/logger.png)

### mainwindow
A main window widget that allows the docking of panels.

![Screenshot of the mainwindow widget](/.github/assets/mainwindow.png)

### messagebox
A QMessageBox with icons from the MaterialIcon module.

![Screenshot of the messagebox widget](/.github/assets/messagebox.png)

### resizegrip
A resize grip that can be added to any widget to make it resizable.

![Screenshot of a QPlainTextEdit field with the resize grip widget](/.github/assets/resizegrip.png)

### scrollarea
A scrollArea widget that has a minimum width based on its content.

### theme
Allows to style Qt Applications based on color schemes. Also provides some dark color schemes.

### typeutils
A module for helping with types. For example cast a dictionary to a dataclass.

### viewer
A viewer for numpy array images. It has an exposure slider zoom, pan and shows pixel information.

![Screenshot of the viewer widget](/.github/assets/viewer.png)


## Contributing

To contribute please refer to the [Contributing Guide](CONTRIBUTING.md).

## License

MIT License. Copyright 2024 - Beat Reichenbach.
See the [License file](LICENSE) for details.
