import os
from PIL import Image, ImageChops
import numpy as np
from helpers.helper_constants import assets_dir, bees_dir, genders

pictures_dir = f'{assets_dir}/{bees_dir}'
new_pictures_dir = f'{assets_dir}/bees3'
if not os.path.exists(new_pictures_dir):
    os.mkdir(new_pictures_dir)
    print('created dir', new_pictures_dir)
pictures = os.listdir(pictures_dir)

princess_crown = Image.open(f'{assets_dir}/CROWN_Princess.png')
queen_crown = Image.open(f'{assets_dir}/CROWN_Queen.png')

for filename in pictures:
    if filename.find('Drone') != -1:
        continue
    elif filename.find('Princess') != -1:
        crown = princess_crown
    elif filename.find('Queen') != -1:
        crown = queen_crown
    else:
        continue
    crown_pixels = np.asarray(crown)
    img = Image.open(pictures_dir + '/' + filename)
    for i, row in enumerate(crown_pixels):
        for j, pixel in enumerate(row):
            if not np.array_equal(pixel, [255, 255, 255, 255]):
                #print(i, j, pixel)
                img.putpixel((j, i), tuple(pixel))
    img.save(new_pictures_dir + '/' + filename)
    print('saved image to', new_pictures_dir + '/' + filename)