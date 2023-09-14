import os
from PIL import Image
import numpy as np

def blackout(img):
    img = img.convert("RGBA")
    for i, row in enumerate(np.asarray(img)):
        for j, pixel in enumerate(row):
            if not np.array_equal(pixel, [255, 255, 255, 255]) and not np.array_equal(pixel, [255,255,255,0]):
                # print(i, j, pixel)
                # print('put')
                img.putpixel((j, i), (0,0,0,255))
    # arr = img.load()
    # print(arr[1,1])
    return img

blackout(Image.open('./assets/bees2/COMMON_Drone.png')).save('assets/bees2/black_drone.png')
blackout(Image.open('./assets/bees2/COMMON_Princess.png')).save('assets/bees2/black_princess.png')