import os
from PIL import Image
import numpy as np
from helpers.helper_constants import assets_dir, bees_dir
new_bees_dir = 'bees3'
if not os.path.exists(f'{assets_dir}/{new_bees_dir}'):
    os.mkdir(f'{assets_dir}/{new_bees_dir}')
    print(f'created dir {assets_dir}/{new_bees_dir}')

pictures = os.listdir(f'{assets_dir}/{bees_dir}')
for filename in pictures:
    # crown_pixels = np.asarray(crown)
    img = Image.open(f'{assets_dir}/{bees_dir}/' + filename)
    img = img.convert("RGBA")
    for i, row in enumerate(np.asarray(img)):
        for j, pixel in enumerate(row):
            # if 'COMMON' in filename:
            #     print(i, j, pixel)
            if np.array_equal(pixel, [255, 255, 255, 255]):
                # print(i, j, pixel)
                # print('put transparent')
                img.putpixel((j, i), (255,255,255,0))
    print('converted', f'{assets_dir}/{bees_dir}/' + filename, 'to', f'{assets_dir}/{new_bees_dir}/' + filename)
    img.save(f'{assets_dir}/{new_bees_dir}/' + filename)