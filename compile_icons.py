import glob
import os
import subprocess


def main():
    files = glob.glob('material-design-icons/svg/**/*.svg', recursive=True)

    qrc_path = 'material_design_icons.qrc'
    with open(qrc_path, 'w') as f:
        f.write('<!DOCTYPE RCC>\n<RCC version="1.0">\n')
        f.write('<qresource>\n')
        for file in files:
            path = file.replace('\\', '/')
            f.write(f'<file>{path}</file>\n')
        f.write('</qresource>\n')
        f.write('</RCC>\n')

    subprocess.run(
        [
            'pyside2-rcc',
            qrc_path,
            '-o',
            f'qt_extensions/icons_resource.py',
        ]
    )
    os.remove(qrc_path)


if __name__ == '__main__':
    main()
