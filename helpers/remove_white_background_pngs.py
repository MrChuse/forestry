import os
from PIL import Image
import numpy as np
from helpers.helper_constants import assets_dir, bees_dir

#old_bees_dir = f'{assets_dir}/{bees_dir}'
old_bees_dir = f'{assets_dir}/elements'
new_bees_dir = f'{assets_dir}/elements'

if not os.path.exists(new_bees_dir):
    os.mkdir(new_bees_dir)
    print(f'created dir {new_bees_dir}')

pictures = os.listdir(old_bees_dir)
for filename in pictures:
    # crown_pixels = np.asarray(crown)
    if os.path.isdir(f'{old_bees_dir}/{filename}'): continue
    img = Image.open(f'{old_bees_dir}/{filename}')
    img = img.convert("RGBA")
    for i, row in enumerate(np.asarray(img)):
        for j, pixel in enumerate(row):
            # if 'COMMON' in filename:
            #     print(i, j, pixel)
            if np.array_equal(pixel, [255, 255, 255, 255]):
                # print(i, j, pixel)
                # print('put transparent')
                img.putpixel((j, i), (255,255,255,0))
    print('converted', f'{old_bees_dir}/' + filename, 'to', f'{new_bees_dir}/' + filename)
    img.save(f'{new_bees_dir}/' + filename)