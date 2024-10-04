# Initially https://github.com/marella/material-design-icons/ was used to get SVG icons.
# However, Google Material Design Symbols replaced the Icons.

import os
import subprocess

from qt_extensions.icons import MaterialIcon


def clone_repo() -> None:
    repo = 'material-design-icons'

    if not os.path.exists(repo):
        os.makedirs(repo)
        subprocess.run('git init', cwd=repo, shell=True)
        subprocess.run(
            'git remote add -f origin https://github.com/google/material-design-icons',
            cwd=repo,
            shell=True,
        )
        subprocess.run('git config core.sparseCheckout true', cwd=repo, shell=True)
        with open(os.path.join(repo, '.git', 'info', 'sparse-checkout'), 'a') as f:
            f.write('symbols/web/')

    subprocess.run('git pull origin master', cwd=repo, shell=True)


def collect_files() -> None:
    for style in MaterialIcon.Style:
        files = []
        root = os.path.join('material-design-icons', 'symbols', 'web')
        for icon in os.listdir(root):
            style_path = os.path.join(root, icon, f'materialsymbols{style.value}')
            files.append(os.path.join(style_path, f'{icon}_24px.svg'))
            files.append(os.path.join(style_path, f'{icon}_fill1_24px.svg'))

        qrc_path = f'material_design_icons_{style.value}.qrc'
        with open(qrc_path, 'w') as f:
            f.write('<!DOCTYPE RCC>\n<RCC version="1.0">\n')
            f.write('<qresource>\n')
            for file in files:
                path = file.replace('\\', '/')
                f.write(f'<file>{path}</file>\n')
            f.write('</qresource>\n')
            f.write('</RCC>\n')


def build_resource() -> None:
    for style in MaterialIcon.Style:
        qrc_path = f'material_design_icons_{style.value}.qrc'
        resource_path = os.path.join(
            'qt_extensions', f'icons_resource_{style.value}.py'
        )
        subprocess.run(['pyside2-rcc', qrc_path, '-o', resource_path])
        os.remove(qrc_path)


def main() -> None:
    clone_repo()
    collect_files()
    build_resource()


if __name__ == '__main__':
    main()
