import os
from PIL import Image
import numpy as np

pictures = os.listdir('./assets/bees2')
for filename in pictures:
    # crown_pixels = np.asarray(crown)
    img = Image.open('./assets/bees2/' + filename)
    img = img.convert("RGBA")
    for i, row in enumerate(np.asarray(img)):
        for j, pixel in enumerate(row):
            # if 'COMMON' in filename:
            #     print(i, j, pixel)
            if np.array_equal(pixel, [255, 255, 255, 255]):
                # print(i, j, pixel)
                # print('put transparent')
                img.putpixel((j, i), (255,255,255,0))
    img.save('./assets/bees3/' + filename)