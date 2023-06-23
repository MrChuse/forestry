from config import config_production_modifier, ResourceTypes
from forestry import (Apiary, ApiaryProblems, Bestiary, Drone, Inventory, MatingHistory, Princess,
                      Queen, Slot)

CURRENT_BACK_VERSION = 7

def update_bee(slot: Slot):
    bee, amount = slot.take_all()
    if isinstance(bee, Princess):
        bee = Princess(bee.genes, bee.inspected)
    elif isinstance(bee, Drone):
        bee = Drone(bee.genes, bee.inspected)
    elif isinstance(bee, Queen):
        bee = Queen(bee.parent1, bee.parent2, bee.inspected)
    else:
        raise TypeError(f'Update failed, bee was not a Princess, Drone or Queen but {type(bee)}')
    slot.put(bee, amount)

def update_bees_in_inventory(inventory: Inventory):
    for j, slot in enumerate(inventory.storage):
        if not slot.is_empty():
            update_bee(slot)

def update_bees_in_apiary(apiary: Apiary):
    if not apiary.princess.is_empty():
        update_bee(apiary.princess)
    if not apiary.drone.is_empty():
        update_bee(apiary.drone)
    for j, slot in enumerate(apiary.inv):
        if not slot.is_empty():
            update_bee(slot)

def update_bees_in_state(state: dict) -> dict:
    for i, inventory in enumerate(state['inventories']):
        update_bees_in_inventory(inventory)
    for i, apiary in enumerate(state['apiaries']):
        apiary.add_mating_entry = state['mating_history'].append
        update_bees_in_apiary(apiary)
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

def update_back_state_5_6(state: dict) -> dict:
    if not isinstance(state['inventories'], list):
        raise ValueError(f'State update cancelled: inventories was not a list, but {type(state["inventories"])}')
    state['inventories'] = update_inventories(state['inventories'])
    state['inventories'] = {
        inv.name: inv for inv in state['inventories']
    }
    return state

def update_inventories(invs):
    new_invs = []
    for inv in invs:
        new_inv = Inventory(inv.capacity, inv.name)
        new_inv.place_bees(inv.storage)
        new_invs.append(new_inv)
    return new_invs

def update_back_state_6_7(state: dict) -> dict:
    r = {'pollen cluster': 'POLLEN_CLUSTER', 'royal jelly': 'ROYAL_JELLY'}
    state['resources'].res = {ResourceTypes[r.get(res, res.upper())]: amt for res, amt in state['resources'].items()}
    return state

update_back_versions = [update_back_state_0_1,
                        update_back_state_1_2,
                        update_back_state_2_3,
                        update_back_state_3_4,
                        update_bees_in_state,
                        update_back_state_5_6,
                        update_back_state_6_7]
