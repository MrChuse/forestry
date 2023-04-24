from config import config_production_modifier
from forestry import (ApiaryProblems, Bestiary, Drone, MatingHistory, Princess,
                      Queen)

CURRENT_BACK_VERSION = 4

def update_bee(bee):
    if isinstance(bee, Princess):
        return Princess(bee.genes, bee.inspected)
    elif isinstance(bee, Drone):
        return Drone(bee.genes, bee.inspected)
    elif isinstance(bee, Queen):
        return Queen(bee.parent1, bee.parent2, bee.inspected)
    else:
        raise TypeError(f'Update failed, bee was not a Princess, Drone or Queen but {type(bee)}')

def update_bees_in_state(state):
    for i, inventory in enumerate(state['inventories']):
        for j, slot in enumerate(inventory):
            if not slot.is_empty():
                state['inventories'][i][j].slot = update_bee(slot.slot)
    for i, apiary in enumerate(state['apiaries']):
        apiary.add_mating_entry = state['mating_history'].append
        if not apiary.princess.is_empty():
            state['apiaries'][i].princess.slot = update_bee(apiary.princess.slot)
        if not apiary.drone.is_empty():
            state['apiaries'][i].drone.slot = update_bee(apiary.drone.slot)
        for j, slot in enumerate(apiary.inv):
            if not slot.is_empty():
                state['apiaries'][i].inv[j] = update_bee(slot.slot)
    return state

def update_back_state_0_1(state: dict) -> dict:
    state['total_inspections'] = state.get('total_inspections', 0)
    state['mating_history'] = state.get('mating_history', MatingHistory())
    return state

def update_back_state_1_2(state: dict) -> dict:
    for i, apiary in enumerate(state['apiaries']):
        apiary.problem = ApiaryProblems.NO_QUEEN
        state['apiaries'][i] = apiary
    return state

def update_back_state_2_3(state: dict) -> dict:
    for k in state['resources'].res:
        state['resources'].res[k] *= config_production_modifier
    return state

def update_back_state_3_4(state: dict) -> dict:
    state['bestiary'] = state.get('bestiary', Bestiary())
    for i, apiary in enumerate(state['apiaries']):
        apiary.bestiary = state['bestiary']
        state['apiaries'][i] = apiary
    return state

update_back_versions = [update_back_state_0_1, update_back_state_1_2, update_back_state_2_3, update_back_state_3_4]
update_back_versions.append(update_bees_in_state)