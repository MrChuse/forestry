import os
from pprint import pprint

import pygame

from helpers.helper_constants import assets_dir, bees_dir
# from config import colors
from config import BeeSpecies

def changColor(image: pygame.Surface, color):
    colouredImage = pygame.Surface(image.get_size())
    colouredImage.fill(color)

    finalImage = image.copy()
    finalImage.blit(colouredImage, (0, 0), special_flags = pygame.BLEND_MULT)
    return finalImage

def screen_blend(color1, color2):
    return pygame.Color(
        256 - (256 - color1.r)*(256 - color2.r) / 256,
        256 - (256 - color1.g)*(256 - color2.g) / 256,
        256 - (256 - color1.b)*(256 - color2.b) / 256,
        256 - (256 - color1.a)*(256 - color2.a) / 256,
    )

def type0(bs):
    return pygame.image.load(f'{assets_dir}/{bees_dir}/{bs.name}_Drone.png')

def type1(color):
    color = pygame.Color(color)
    res = changColor(drone, color)
    # wing_color = color
    wing_color = screen_blend(color, pygame.Color(128,128,128))
    wing_color = screen_blend(wing_color, pygame.Color(128,128,128))
    colored_wing = changColor(wing, wing_color)
    print(color, wing_color)
    res.blit(colored_wing, (0, 0))
    return res

elements_dir = f'{assets_dir}/elements'
# elements
border = pygame.image.load(f'{elements_dir}/border.png')
drone = pygame.image.load(f'{elements_dir}/drone.png')
wing = pygame.image.load(f'{elements_dir}/wing.png')
CROWN_Princess = pygame.image.load(f'{elements_dir}/CROWN_Princess.png')
CROWN_Queen = pygame.image.load(f'{elements_dir}/CROWN_Queen.png')

for bee_species in BeeSpecies:
    res = type0(bee_species)

    res.blit(border, (0, 0))
    pygame.image.save(res, f'{elements_dir}/new_bees/{bee_species.name}_Drone.png')

    res.blit(CROWN_Princess, (0, 0))
    pygame.image.save(res, f'{elements_dir}/new_bees/{bee_species.name}_Princess.png')

    res.blit(CROWN_Queen, (0, 0))
    pygame.image.save(res, f'{elements_dir}/new_bees/{bee_species.name}_Queen.png')

# pprint(sorted(pygame.Color(color).hsla for color in list(colors.values())[:10]))