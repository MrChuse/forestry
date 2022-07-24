import os
from PIL import Image
import numpy as np

with open('assets/FOREST_Drone.png', 'rb') as f:
    original = f.read()


pictures = os.listdir('./assets')
princess_png = Image.open('./princess.body3.png')
queen_png = Image.open('./queen.body3.png')
for filename in pictures:
    if filename.find('Drone') != -1:
        continue
    if filename.find('Princess') != -1:
        crown = princess_png
    else:
        crown = queen_png
    crown_pixels = np.asarray(crown)
    img = Image.open('./assets/' + filename)
    for i, row in enumerate(crown_pixels):
        for j, pixel in enumerate(row):
            if not np.array_equal(pixel, [255, 255, 255, 255]):
                print(i, j, pixel)
                img.putpixel((j, i), tuple(pixel))    
    img.save('./assets/' + filename)