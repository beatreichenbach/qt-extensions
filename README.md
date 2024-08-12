# qt-extensions

This is a collection of widgets and utility functions to extend Qt.
Some example usages can be found in gui_tests.

<!-- TOC -->
* [qt-extensions](#qt-extensions)
  * [Installation](#installation)
  * [Usage](#usage)
  * [Modules](#modules)
    * [parameters](#parameters)
    * [box](#box)
    * [buttons](#buttons)
    * [elementbrowser](#elementbrowser)
    * [filebrowser](#filebrowser)
    * [flexview](#flexview)
    * [icons](#icons)
    * [logger](#logger)
    * [mainwindow](#mainwindow)
    * [messagebox](#messagebox)
    * [resizegrip](#resizegrip)
    * [scrollarea](#scrollarea)
    * [theme](#theme)
    * [typeutils](#typeutils)
    * [viewer](#viewer)
  * [Contributing](#contributing)
<!-- TOC -->

## Installation

Install using pip:
```shell
pip install qt-extensions
```

## Usage

For usage see `tests_gui` directory.

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

### icons
A module that provides easy creation of QIcons based on
[Google Material Symbols & Icons]. Initially using the icons they are now using the new
symbols.

![Screenshot of the icons](/.github/assets/icons.png)

[Google Material Symbols & Icons]: https://fonts.google.com/icons

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

Create a venv:
```shell
python3 -m venv venv
```
Install `qt-extensions` in editable mode:
```shell
python3 -m pip install -e .[dev]
```

To version up using [python-semantic-release]:
```shell
semantic-release version
```

[python-semantic-release]: https://github.com/python-semantic-release/python-semantic-release