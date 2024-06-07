import os
import shutil

from config import ResourceTypes
from helpers.helper_constants import assets_dir, icons_dir

files = os.listdir(f'{assets_dir}/{icons_dir}')
forced = False

for resource in ResourceTypes:
    filename_from = f'HONEY.png'
    filename_to = f'{resource}.png'
    if filename_to in files and not forced: continue
    shutil.copy(f'{assets_dir}/{icons_dir}/{filename_from}', f'{assets_dir}/{icons_dir}/{filename_to}')
    print(f'copied {filename_from} to {filename_to}')