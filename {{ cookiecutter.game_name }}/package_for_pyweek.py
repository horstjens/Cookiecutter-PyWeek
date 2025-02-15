#!/usr/bin/env python3
"""
Utility script to package game for PyWeek.
"""
import os
import shutil
import subprocess
from pathlib import Path
import argparse
import zipfile

parser = argparse.ArgumentParser(description='Package the game for PyWeek')
parser.add_argument('--convert-icons', action='store_true', help='Convert appicon.png to ICNS/ICO')
parser.add_argument('--smoketest', action='store_true', help='Run the game before packaging')
parser.add_argument('--macos-bundle', action='store_true', help='Build macOS app bundle (on macOS)')
parser.add_argument('--windows-exe', action='store_true', help='Build Windows .exe (on Windows)')

args = parser.parse_args()

githash = subprocess.check_output(
    ["git", "describe", "--always", "--tags", "--long"], encoding="utf-8"
).strip()

if args.convert_icons:
    # Use ImageMagick to convert PNG icon to Win32/macOS icon formats
    print('Using ImageMagick to convert app icon...')
    subprocess.check_call(['convert', 'package_for_pyweek/appicon.png', 'package_for_pyweek/appicon.ico'])
    subprocess.check_call(['convert', 'package_for_pyweek/appicon.png', 'package_for_pyweek/appicon.icns'])

# Configuration
GAME_NAME = "{{ cookiecutter.game_name }}"
PACKAGE_NAME = f"{GAME_NAME}-{githash}"
RESOURCES = [
    "data",
    "run_game.py",
    "requirements.txt",
    "ARTWORK.txt",
    "LICENSE.txt",
]
HERE = os.path.dirname(__file__)
DST = "sdist"
README = open(os.path.join(HERE, "README.dist.md"), "r").read()

target_folder = Path(HERE) / DST / PACKAGE_NAME
zip_archive = Path(HERE) / DST / (PACKAGE_NAME + ".zip")

# remove eventually existing files in sdist
print("Removing outdates files and folders.")
shutil.rmtree(target_folder, ignore_errors=True)

# copy listed resources
print("Copying resources.")
target_folder.mkdir(exist_ok=True)
for resource in RESOURCES:
    print(resource)
    src = Path(HERE) / resource
    dst = target_folder / resource
    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        shutil.copy(src, dst)

# write README
readme = target_folder / "README.md"
readme.write_text(README)

if args.smoketest:
    print('Running smoketest... (close the game after testing)')
    subprocess.check_call(['python3', 'run_game.py'], cwd=target_folder)

if args.macos_bundle:
    # macOS package
    subprocess.check_call([
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--noconfirm',
        '--add-data', 'data:data',
        '--icon', 'package_for_pyweek/appicon.icns',
        '--osx-bundle-identifier', 'at.pyugat.pyweek34',
        '--name', GAME_NAME,
        '--distpath', 'pyi-dist',
        '--workpath', 'pyi-build',
        'run_game.py',
    ])
    os.chdir('pyi-dist')
    with open('README.md', 'w') as fp:
        fp.write(README)
    shutil.copy('../ARTWORK.txt', '.')
    shutil.copy('../LICENSE.txt', '.')
    subprocess.check_call(['zip', '-r', f'../sdist/{GAME_NAME}-{githash}-macOS.zip',
        f'{GAME_NAME}.app',
        'README.md',
        'ARTWORK.txt',
        'LICENSE.txt',
    ])
    os.chdir('..')

if args.windows_exe:
    # macOS package
    subprocess.check_call([
        'pyinstaller.exe',
        '--onefile',
        '--windowed',
        '--noconfirm',
        '--add-data', 'data;data',
        '--icon', 'package_for_pyweek/appicon.ico',
        '--name', GAME_NAME,
        '--distpath', 'pyi-dist',
        '--workpath', 'pyi-build',
        'run_game.py',
    ])

    with zipfile.ZipFile(os.path.join('sdist', f'{GAME_NAME}-{githash}-Windows.zip'), 'w',
                         compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.writestr('README.md', README)
        zf.write('ARTWORK.txt')
        zf.write('LICENSE.txt')
        zf.write(os.path.join('pyi-dist', f'{GAME_NAME}.exe'), f'{GAME_NAME}.exe')

print("Creating ZIP...")
shutil.make_archive(target_folder, "zip", target_folder)
print(r"Created ZIP archive! \o/")
