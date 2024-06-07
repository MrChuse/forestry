import os
import shutil

from config import BeeSpecies
from helpers.helper_constants import assets_dir, bees_dir, genders

files = os.listdir(f'{assets_dir}/{bees_dir}')
forced = False

drone = genders[0]
for species in BeeSpecies:
    for gender in genders[1:]:
        filename_from = f'{species.name}_{drone}.png'
        filename_to = f'{species.name}_{gender}.png'
        if filename_to in files and not forced: continue
        shutil.copy(f'{assets_dir}/{bees_dir}/{filename_from}', f'{assets_dir}/{bees_dir}/{filename_to}')
        print(f'copied {filename_from} to {filename_to}')