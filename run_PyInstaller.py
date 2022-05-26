import PyInstaller.__main__
import os

PyInstaller.__main__.run([
    'gui.py',
    '--onefile',
    '--noconsole',
    '--add-data=theme.json;.'
])
#  + [f'--add-data=assets\\{filename};assets' for filename in os.listdir('./assets')])