from collections import defaultdict
from config import BeeSpecies, config_production_modifier, ResourceTypes, local
from forestry import (Apiary, ApiaryProblems, Bestiary, Drone, Inventory, MatingHistory, Princess,
                      Queen, Slot, construct_achievements, generate_die_after)

CURRENT_BACK_VERSION = 14

def update_bee(slot: Slot):
    bee, amount = slot.take_all()
    if isinstance(bee, Princess):
        bee = Princess(bee.genes, bee.inspected, generation=bee.generation, die_after=generate_die_after())
    elif isinstance(bee, Drone):
        bee = Drone(bee.genes, bee.inspected)
    elif isinstance(bee, Queen):
        bee = Queen(bee.parent1, bee.parent2, bee.inspected, die_after=generate_die_after())
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
    for i, inventory in enumerate(state['inventories'].values()):
        update_bees_in_inventory(inventory)
    for i, apiary in enumerate(state['apiaries'].values()):
        apiary.add_mating_entry = state['mating_history'].append
        update_bees_in_apiary(apiary)
    for i, alveary in enumerate(state['alvearies'].values()):
        alveary.add_mating_entry = state['mating_history'].append
        update_bees_in_apiary(alveary)
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

def update_achievements_split_text(state: dict) -> dict:
    if 'achievements' not in state:
        state['achievements'] = construct_achievements()

    for achievement in state['achievements']:
        for ach in local.values():
            if isinstance(ach, dict):
                if 'requirement' in ach and ach['requirement'] in achievement.text:
                    achievement.requirement_str = ach['requirement']
                    achievement.reward_str = ach['reward']
                    achievement.comment_str = ach['comment']
    return state

def update_bestiary_known_bees(state: dict) -> dict:
    old = state['bestiary'].known_bees
    state['bestiary'].known_bees = defaultdict(int)
    state['bestiary'].known_bees.update(old)
    return state

def update_apiaries_to_dict(state: dict) -> dict:
    if not isinstance(state['apiaries'], list):
        raise ValueError(f'State update cancelled: apiaries was not a list, but {type(state["apiaries"])}')
    state['apiaries'] = {
        api.name: api for api in state['apiaries']
    }
    if 'alvearies' not in state:
        state['alvearies'] = {}
    return state

def update_bestiary_to_use_resourcetypes(state: dict) -> dict:
    b : Bestiary = state['bestiary']
    b.produced_resources = {beetype: {ResourceTypes[res.upper() if res != 'pollen cluster' else 'POLLEN_CLUSTER']: amt}
                            for beetype, things in b.produced_resources.items()
                            for res, amt in things.items()}
    return state

def add_all_bees_to_bestiary(state: dict) -> dict:
    b: Bestiary = state['bestiary']
    for i in BeeSpecies:
        b.produced_resources[i] = b.produced_resources.get(i, {})
    return state

def update_bestiary_produced_resources(state: dict) -> dict:
    b: Bestiary = state['bestiary']
    for i in BeeSpecies:
        old = b.produced_resources.get(i, {})
        b.produced_resources[i] = defaultdict(int)
        b.produced_resources[i].update(old)
    return state


def check_dict_have_current_keys(state):
    for key in current_keys:
        if key not in state:
            return False
    return True

current_keys = [
    'back_version'
    'current_tutorial_stage',
    'resources',
    'inventories',
    'apiaries',
    'bestiary',
    'mating_history',
    'total_inspections'
    'achievements',
]

update_back_versions = [update_back_state_0_1,
                        update_back_state_1_2,
                        update_back_state_2_3,
                        update_back_state_3_4,
                        update_bees_in_state,
                        update_back_state_5_6,
                        update_back_state_6_7,
                        update_achievements_split_text,
                        update_bestiary_known_bees,
                        update_apiaries_to_dict,
                        update_bestiary_to_use_resourcetypes,
                        add_all_bees_to_bestiary,
                        update_bestiary_produced_resources,
                        update_bees_in_state,
                        ]
