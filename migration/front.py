import pygame

from forestry import Slot

CURRENT_FRONT_VERSION = 2

def update_front_state_0_1(state: dict) -> dict:
    state['inspect_windows'] = []
    state['inspect_slots'] = [state.get('inspect_slot', Slot())]
    state.pop('inspect_slot', None)
    return state

def update_front_state_1_2(state: dict) -> dict:
    state['current_tutorial_stage'] = 4 # INSPECT_AVAILABLE, last stage possible for now
    state['apiary_list_opened'] = True
    return state

update_front_versions = [update_front_state_0_1, update_front_state_1_2]