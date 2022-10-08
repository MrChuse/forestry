import pygame

from forestry import Slot

CURRENT_FRONT_VERSION = 1

def update_front_state_0_1(state: dict):
    state['inspect_windows'] = [pygame.Rect(0,0,0,0)]
    state['inspect_slots'] = [state.get('inspect_slot', Slot())]
    state.pop('inspect_slot', None)
    return state

update_front_versions = [update_front_state_0_1]