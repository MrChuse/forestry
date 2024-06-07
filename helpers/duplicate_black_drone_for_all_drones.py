import os
import shutil

from config import BeeSpecies
from helpers.helper_constants import assets_dir, bees_dir, genders

files = os.listdir(f'{assets_dir}/{bees_dir}')

gender = 'Drone'
for species in BeeSpecies:
    filename = f'{species.name}_{gender}.png'
    if filename not in files:
        shutil.copy(f'{assets_dir}/{bees_dir}/black_drone.png', f'{assets_dir}/{bees_dir}/{filename}')
        print(f'copied black_drone to {filename}')