import dataclasses
import logging
import os
import pickle
import random
import textwrap
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, fields
from enum import Enum, IntEnum, auto
from pprint import pprint
from traceback import print_exc
from typing import Any, Callable, List, Tuple, Union

from config import (BeeFertility, BeeLifespan, BeeSpecies, BeeSpeed,
                    ResourceTypes, config_production_modifier, dominant,
                    helper_text, local, mendel_text, mutations, products)


def weighted_if(weight, out1, out2):
    return out1 if random.random() < weight else out2

bs = BeeSpecies
bf = BeeFertility
bl = BeeLifespan
bS = BeeSpeed

default_genes = {
    bs.FOREST: {
        'species': bs.FOREST,
        'fertility': bf(3),
        'lifespan': bl.SHORTER,
        'speed': bS.SLOWEST,
    },
    bs.MEADOWS: {
        'species': bs.MEADOWS,
        'fertility': bf(2),
        'lifespan': bl.SHORTER,
        'speed': bS.SLOWEST,
    },
    bs.COMMON: {
        'species': bs.COMMON,
        'fertility': bf(2),
        'lifespan': bl.SHORTER,
        'speed': bS.SLOWER,
    },
    bs.CULTIVATED: {
        'species': bs.CULTIVATED,
        'fertility': bf(2),
        'lifespan': bl.SHORTEST,
        'speed': bS.FAST,
    },
    bs.NOBLE: {
        'species': bs.NOBLE,
        'fertility': bf(2),
        'lifespan': bl.SHORT,
        'speed': bS.SLOWER,
    },
    bs.MAJESTIC: {
        'species': bs.MAJESTIC,
        'fertility': bf(4),
        'lifespan': bl.SHORTENED,
        'speed': bS.NORMAL,
    },
    bs.IMPERIAL: {
        'species': bs.IMPERIAL,
        'fertility': bf(2),
        'lifespan': bl.NORMAL,
        'speed': bS.SLOWER,
    },
    bs.DILIGENT: {
        'species': bs.DILIGENT,
        'fertility': bf(2),
        'lifespan': bl.SHORT,
        'speed': bS.SLOWER,
    },
    bs.UNWEARY: {
        'species': bs.UNWEARY,
        'fertility': bf(2),
        'lifespan': bl.SHORTENED,
        'speed': bS.NORMAL,
    },
    bs.INDUSTRIOUS: {
        'species': bs.INDUSTRIOUS,
        'fertility': bf(2),
        'lifespan': bl.NORMAL,
        'speed': bS.SLOWER,
    },
}


basic_species = [bs.FOREST, bs.MEADOWS]

class SlotOccupiedError(RuntimeError):
    pass


Allele = Union[BeeSpecies, BeeFertility, BeeLifespan, BeeSpeed]
Gene = Tuple[Allele, Allele]


@dataclass(eq=True, frozen=True)
class Genes:
    species: Gene
    fertility: Gene = None
    lifespan: Gene = None
    speed: Gene = None

    def asdict(self):
        d = dataclasses.asdict(self)
        d = dict(filter(lambda x: x[1] is not None, d.items()))
        return d

    @staticmethod
    def mutate(allele1, allele2):
        mut = mutations.get((allele1, allele2))
        if mut is not None:  # mutation found in mutation map
            allele = random.choices(mut[0], weights=mut[1])[
                0
            ]  # sample with weights from mutation map
            if allele is not None:
                return weighted_if(
                    0.5, (allele, allele2), (allele1, allele)
                )  # gene from mutation
        return (allele1, allele2)  # same genes if not mutated

    def crossingover(self, genes2: 'Genes'):
        spec1 = weighted_if(0.5, *(self.species))
        spec2 = weighted_if(0.5, *(genes2.species))
        new_spec1, new_spec2 = Genes.mutate(spec1, spec2)
        species = None
        mutated_1 = False
        mutated_2 = False
        if new_spec1 != spec1:
            genes = default_genes[new_spec1]
            mutated_1 = True
        elif new_spec2 != spec2:
            genes = default_genes[new_spec2]
            mutated_2 = True

        l = []
        genes1_dict = self.asdict()
        genes2_dict = genes2.asdict()
        for key, key2 in zip(genes1_dict, genes2_dict):
            assert key == key2, 'fields should be equal...'
            g1 = genes1_dict[key]
            g2 = genes2_dict[key2]

            allele1 = weighted_if(0.5, *g1)
            allele2 = weighted_if(0.5, *g2)
            if mutated_1:
                allele1 = genes[key]
            elif mutated_2:
                allele2 = genes[key]

            if dominant[allele1] and not dominant[allele2]:
                l.append((allele1, allele2))
            elif not dominant[allele1] and dominant[allele2]:
                l.append((allele2, allele1))
            else:
                l.append(weighted_if(0.5, (allele1, allele2), (allele2, allele1)))
        return Genes(*l)

    @staticmethod
    def sample(basic=True):
        if basic:
            species = random.sample(basic_species, 1)[0]
            genes = default_genes[species]
            return Genes(**{k: (g, g) for k, g in genes.items()})

def dom_local(allele, dom):
    return allele.upper() if dom else allele.lower()
class Bee:
    type_str = 'unknown'
    def __init__(self, genes: Genes, inspected: bool = False):
        self.genes = genes
        self.inspected = inspected
        self.mating_entries = []
        super().__init__()

    def __str__(self):
        res = []
        if not self.inspected:
            res.append(self.small_str())
            return '\n'.join(res)
        name, bee_species_index = local[self.type_str]
        res.append(name)
        genes = vars(self.genes)
        res.append(local['trait'])
        for key in genes:
            try:
                allele0 = local[genes[key][0]][bee_species_index]
                allele1 = local[genes[key][1]][bee_species_index]
            except IndexError:
                allele0 = local[genes[key][0]][0] # TODO: remove [0]
                allele1 = local[genes[key][1]][0]
            dom0 = dominant[genes[key][0]]
            dom1 = dominant[genes[key][1]]
            res.append(f'  {local[key]} : {dom_local(allele0, dom0)}, {dom_local(allele1, dom1)}')
        return '\n'.join(res)

    def __hash__(self):
        return hash(self.genes)

    def __eq__(self, other: 'Bee'):
        return type(self) == type(other) and self.genes == other.genes and self.inspected == other.inspected

    def small_str(self):
        name, bee_species_index = local[self.type_str]
        if not self.inspected or self.genes.species[0] == self.genes.species[1]:
            try:
                allele = local[self.genes.species[0]][bee_species_index]
            except IndexError:
                allele = local[self.genes.species[0]][0]
            dom = dominant[self.genes.species[0]]
            return dom_local(allele, dom) + ' ' + name
        else:
            try:
                allele0 = local[self.genes.species[0]][bee_species_index]
                allele1 = local[self.genes.species[1]][bee_species_index]
            except IndexError:
                allele0 = local[self.genes.species[0]][0]
                allele1 = local[self.genes.species[1]][0]
            dom0 = dominant[self.genes.species[0]]
            dom1 = dominant[self.genes.species[1]]
            return dom_local(allele0, dom0) + '-' + dom_local(allele1, dom1) + ' Hybrid'

    def inspect(self):
        self.inspected = True
        for set_inspected in self.mating_entries:
            set_inspected()
        self.mating_entries.clear()


class Queen(Bee):
    type_str = 'Queen'
    def __init__(self, parent1: 'Princess', parent2: 'Drone', inspected: bool = False):
        self.parent1 = parent1
        self.parent2 = parent2
        self.generation = self.parent1.generation
        super().__init__(parent1.genes, inspected)
        self.lifespan = parent1.genes.lifespan[0].value
        self.remaining_lifespan = self.lifespan
        self.children = None

    def small_str(self):
        return super().small_str() + ', rem: ' + str(self.remaining_lifespan)

    def die(self):
        if self.children is None:
            self.children = [Princess(self.parent1.genes.crossingover(self.parent2.genes), generation=self.generation+1)] + [
                Drone(self.parent1.genes.crossingover(self.parent2.genes)) for i in range(self.genes.fertility[0].value)
            ]
        return self.children


class Princess(Bee):
    type_str = 'Princess'
    def __init__(self, genes, inspected: bool = False, generation: int = 0):
        self.generation = generation
        super().__init__(genes, inspected)

    def mate(self, other: 'Drone') -> Queen:
        if not isinstance(other, Drone):
            raise TypeError('Princesses can only mate drones')
        return Queen(self, other)


class Drone(Bee):
    type_str = 'Drone'
    def __init__(self, genes, inspected: bool = False):
        super().__init__(genes, inspected)

class NotEnoughResourcesError(Exception):
    pass
class Resources:
    def __init__(self, dictlike={}):
        self.res = {}
        self.res.update(dictlike)
        super().__init__()

    def __contains__(self, key):
        return key in self.res

    def __len__(self):
        return len(self.res)

    def __str__(self):
        res = ['------ RESOURCES ------']
        for k in self.res:
            res.append(k + ': ' + str(self.res[k]))
        if len(res) == 1:
            res.append('  Empty...')
        return '\n'.join(res)

    def __getitem__(self, key):
        return self.res.get(key, 0)

    def __eq__(self, __o: object) -> bool:
        if __o is None: return False
        return __o.res == self.res

    def copy(self):
        return Resources(self.res)

    def add_resources(self, resources):
        for k in resources:
            self.res[k] = self[k] + resources[k]

    def remove_resources(self, resources):
        s = ''
        for k in resources:
            need_resources = resources[k] * config_production_modifier
            if self[k] - need_resources < 0:
                s += local['notenough'].format(local[k], self.res[k], need_resources) + '\n'
        if s != '':
            raise NotEnoughResourcesError(s)
        for k in resources:
            self.res[k] -= resources[k] * config_production_modifier

    def check_enough(self, resources):
        for k in resources:
            if k not in self:
                return False
        return True

    def items(self):
        return self.res.items()

class Bestiary:
    def __init__(self):
        self.produced_resources = {species: defaultdict(int) for species in BeeSpecies}
        self.known_bees = defaultdict(int)

    def add_produced_resources(self, bee_species, resources):
        for res in resources:
            self.produced_resources[bee_species][res] += resources[res]

    def add_offspring(self, bee_species: BeeSpecies, amount=1):
        self.known_bees[bee_species] += amount

    def copy(self):
        new_bestiary = Bestiary()
        new_bestiary.produced_resources = {species: d.copy() for species, d in self.produced_resources.items()}
        new_bestiary.known_bees = self.known_bees.copy()
        return new_bestiary

    def __eq__(self, other: 'Bestiary') -> bool:
        if not isinstance(other, Bestiary):
            return False
        return self.produced_resources == other.produced_resources and self.known_bees == other.known_bees

class Achievement:
    string = ''
    def __init__(self, requirement: str, reward: str, comment: str, achieved: bool = False):
        self.requirement_str = requirement
        self.reward_str = reward
        self.comment_str = comment
        self.achieved = achieved

    def check(self, game: 'Game'):
        return False

    def reward(self, game: 'Game'):
        pass

class ProducedProducts(Achievement):
    def __init__(self, products, reward_resources, requirement: str, reward: str, comment: str, achieved: bool = False):
        self.products = products
        self.reward_resources = reward_resources
        super().__init__(requirement, reward, comment, achieved)

    def check(self, game: 'Game'):
        per_product = []
        for product, n in self.products.items():
            b = sum(map(lambda x: x.get(product, 0), game.bestiary.produced_resources.values())) >= n
            per_product.append(b)
        return all(per_product)

    def reward(self, game: 'Game'):
        game.resources.add_resources(self.reward_resources)

class BredSpecies(Achievement):
    def __init__(self, species: BeeSpecies, requirement: str, reward: str, comment: str, achieved: bool = False):
        self.species = species
        super().__init__(requirement, reward, comment, achieved)

    def check(self, game: 'Game'):
        return self.species in game.bestiary.known_bees

class AchievementManager:
    def __init__(self, game: 'Game', achievements: List[Achievement], notify: Callable[[Achievement], None]):
        self.game = game
        self.achievements = achievements
        self.notify = notify
        self.changed_recently = False

    def check_achievements(self):
        for achievement in self.achievements:
            if not achievement.achieved:
                if achievement.check(self.game):
                    achievement.achieved = True
                    achievement.reward(self.game)
                    self.notify(achievement)
                    self.changed_recently = True

@dataclass
class MatingEntry:
    parent1_dom : BeeSpecies
    parent1_rec : Union[BeeSpecies, None]
    parent2_dom : BeeSpecies
    parent2_rec : Union[BeeSpecies, None]
    child_dom : BeeSpecies
    child_rec : Union[BeeSpecies, None]
    parent1_inspected : bool = False
    parent2_inspected : bool = False
    child_inspected : bool = False

    @staticmethod
    def from_bees(parent1: Bee, parent2: Bee, child: Bee, force_inspect=False):
        if force_inspect:
            parent1.inspect()
            parent2.inspect()
            child.inspect()
        return MatingEntry(
            *parent1.genes.species,
            *parent2.genes.species,
            *child.genes.species,
            parent1.inspected,
            parent2.inspected,
            child.inspected
        )

    def set_parent1_inspected(self):
        self.parent1_inspected = True
        self.set_history_something_changed()

    def set_parent2_inspected(self):
        self.parent2_inspected = True
        self.set_history_something_changed()

    def set_child_inspected(self):
        self.child_inspected = True
        self.set_history_something_changed()


class MatingHistory:
    def __init__(self):
        self.history = []
        self.counts = []
        self.something_changed = False

    def append(self, entry: MatingEntry):
        if entry not in self.history:
            entry.set_history_something_changed = self.set_something_changed # dirty!
            self.history.append(entry)
            self.counts.append(1)
            res = entry
        else:
            index = self.history.index(entry)
            self.counts[index] += 1
            res = self.history[index]
        self.something_changed = True
        return res

    def get_history_counts(self, debug=False):
        if debug:
            return self.history, self.counts
        front_history = []
        front_counts = []
        for entry, count in zip(self.history, self.counts):
            front_entry = MatingEntry(
                entry.parent1_dom,
                entry.parent1_rec if entry.parent1_inspected else None,
                entry.parent2_dom,
                entry.parent2_rec if entry.parent2_inspected else None,
                entry.child_dom,
                entry.child_rec if entry.child_inspected else None,
                entry.parent1_inspected,
                entry.parent2_inspected,
                entry.child_inspected,
            )
            if front_entry not in front_history:
                front_history.append(front_entry)
                front_counts.append(count)
            else:
                index = front_history.index(front_entry)
                front_counts[index] += count
        return front_history, front_counts

    def set_something_changed(self):
        self.something_changed = True

    def acknowledge_changes(self, debug=False):
        if not debug:
            self.something_changed = False

class Slot:
    empty_str = 'Slot empty'
    def __init__(self, slot=None, amount=0):
        self.slot = slot
        self.amount = amount
        super().__init__()

    def __str__(self):
        if self.slot is not None:
            return str(self.slot) + self.str_amount()
        else:
            return Slot.empty_str

    def small_str(self):
        if self.slot is not None:
            return self.slot.small_str() + self.str_amount()
        else:
            return Slot.empty_str

    def str_amount(self):
        return f'({self.amount})' if self.amount > 1 else ''

    def put(self, bee, amount=1):
        if amount > 0:
            if self.slot == bee:
                self.slot.mating_entries.extend(bee.mating_entries) # with this change Slots are now capable of only holding bees :(
                self.amount += amount
                return
            if self.slot is None:
                self.slot = bee
                self.amount = amount
            else:
                raise SlotOccupiedError('The slot is not empty')

    def take(self):
        bee = self.slot
        self.amount -= 1
        if self.amount <= 0:
            self.slot = None
            self.amount = 0
        return bee

    def take_all(self):
        bee = self.slot
        self.slot = None
        amt = self.amount
        self.amount = 0
        return bee, amt

    def swap(self, other: 'Slot'):
        bee1 = self.take_all()
        bee2 = other.take_all()
        self.put(*bee2)
        other.put(*bee1)

    def is_empty(self):
        return self.slot is None


class Inventory:
    cost = {ResourceTypes.WOOD: 50, ResourceTypes.FLOWERS: 50}
    def __init__(self, capacity=None, name=''):
        self.capacity = capacity or 100
        self.storage = [Slot() for i in range(self.capacity)]
        self.name = name

    def __setitem__(self, key, value):
        self.storage[key].put(value)

    def __getitem__(self, key):
        return self.storage[key]

    def __len__(self):
        return self.capacity

    def __str__(self):
        res = ['------ INV ------']

        empty = True
        for index, slot in enumerate(self.storage):
            if not slot.is_empty():
                empty = False
                res.append(str(index) + ' ' + slot.small_str())
        if empty:
            res.append('  Empty...')

        return '\n'.join(res)

    def take(self, index):
        bee = self.storage[index].take()
        return bee

    def take_all(self, index):
        return self.storage[index].take_all()

    def empty_slots(self):
        return sum(el.is_empty() for el in self.storage)

    def swap(self, i1, i2):
        self.storage[i1], self.storage[i2] = self.storage[i2], self.storage[i1]

    def mate(self, i1, i2):
        if i1 == i2:
            raise ValueError("Can't mate a bee with itself")
        princess = self.storage[i1].take()
        drone = self.storage[i2].take()
        self.storage[i1].put(princess.mate(drone))

    def check_enough_space(self, list_things: Union[List[Bee], List[Slot]]):
        not_in_storage = 0
        for thing_index, thing in enumerate(list_things):
            index = 0
            if isinstance(thing, Slot):
                bee = thing.slot
            else:
                bee = thing
            if bee is None:
                continue
            while index < self.capacity:
                if self.storage[index].is_empty(): # this slot is empty, we are handling empty slots later
                    index += 1
                    continue
                if self.storage[index].slot == bee: # this thing is already in storage
                    break
                else:
                    index += 1
            else:
                if thing not in list_things[:thing_index]: # if thing was already seen
                    not_in_storage += 1
        return not_in_storage <= self.empty_slots() # return True if amt of things not found in storage less than amt of empty slots


    def place_bees(self, list_things: Union[List[Bee], List[Slot]]):
        if not self.check_enough_space(list_things):
            raise SlotOccupiedError('Tried to insert too many bees')
        for thing in list_things: # try to put into occupied slots first
            index = 0
            if isinstance(thing, Slot):
                bee, amt = thing.take_all()
            elif isinstance(thing, Bee):
                bee = thing
                amt = 1
            if bee is None:
                continue
            while index < self.capacity:
                if self.storage[index].is_empty():
                    index += 1
                    continue
                try:
                    self.storage[index].put(bee, amt)
                    index += 1
                    break
                except SlotOccupiedError:
                    index += 1
                    continue
            else:
                index = 0
                while index < self.capacity:
                    try:
                        self.storage[index].put(bee, amt)
                        index += 1
                        break
                    except SlotOccupiedError:
                        index += 1
                        continue

    def sort(self):
        r = []
        for slot in self:
            if not slot.is_empty():
                r.append(slot)
        self.place_bees(r)


def except_print(*exceptions):
    def try_clause_decorator(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except exceptions as e:
                try:
                    self.print(e, out=self.command_out, flush=True)
                except AttributeError:
                    print(e)

        return wrapper

    return try_clause_decorator


class ApiaryProblems(Enum):
    ALL_OK = 'all_ok'
    NO_QUEEN = 'no_queen'
    NO_SPACE = 'no_space'

class Apiary:
    cost = {ResourceTypes.HONEY: 100, ResourceTypes.WOOD: 50, ResourceTypes.FLOWERS: 50}
    production_modifier = 1/3
    def __init__(self, name, add_resources, add_mating_entry, bestiary: Bestiary):
        self.inv = Inventory(7)
        self.princess = Slot()
        self.drone = Slot()
        self.name = name
        self.problem = ApiaryProblems.NO_QUEEN
        self.add_resources = add_resources
        self.add_mating_entry = add_mating_entry
        self.bestiary = bestiary
        super().__init__()

    def __getitem__(self, key):
        return self.inv.__getitem__(key)

    def __str__(self):
        res = [f'------ APIARY {self.name} ------']
        res.append('Princess: ' + self.princess.small_str())
        res.append('Drone: ' + self.drone.small_str())
        inv_str = textwrap.indent(str(self.inv), '  ')
        res.append(inv_str)
        return '\n'.join(res)

    def get_problem(self):
        return self.problem

    def put_princess(self, bee, amount=1):
        if not isinstance(bee, Princess) and not isinstance(bee, Queen):
            raise TypeError('Bee should be a Princess or a Queen')
        self.princess.put(bee, amount)
        self.try_breed()

    def take_princess(self):
        return self.princess.take_all()

    def put_drone(self, bee, amount=1):
        if not isinstance(bee, Drone):
            raise TypeError('Bee should be a Drone')
        self.drone.put(bee, amount)
        self.try_breed()

    def take_drone(self):
        return self.drone.take_all()

    def put(self, bee, amount=1):
        if isinstance(bee, Princess) or isinstance(bee, Queen):
            self.put_princess(bee, amount)
        elif isinstance(bee, Drone):
            self.put_drone(bee, amount)

    def take(self, index):
        bee, amount = self.inv.take_all(index)
        if isinstance(self.princess.slot, Queen):
            if self.princess.slot.remaining_lifespan == 0:
                self.try_queen_die()
        return bee, amount

    def take_several(self, indices):
        res = []
        for i in indices:
            if not self.inv[i].is_empty():
                res.append(self.inv[i].take_all())
        self.try_queen_die()
        return res

    def try_breed(self):
        if isinstance(self.princess.slot, Princess) and isinstance(self.drone.slot, Drone):
            if self.princess.amount == 1:
                princess = self.princess.take()
                drone = self.drone.take()
                self.princess.put(princess.mate(drone))
            else:
                raise ValueError('Can mate only when 1 Princess in slot')

    def try_queen_die(self):
        if isinstance(self.princess.slot, Queen) and self.princess.slot.remaining_lifespan == 0:
            try:
                self.inv.place_bees(self.princess.slot.die())
            except SlotOccupiedError:
                self.problem = ApiaryProblems.NO_SPACE
                return False
            queen : Queen = self.princess.take()

            for child in queen.children:
                entry = MatingEntry(
                    *queen.parent1.genes.species,
                    *queen.parent2.genes.species,
                    *child.genes.species,
                    queen.parent1.inspected,
                    queen.parent2.inspected,
                    child.inspected,
                )
                entry = self.add_mating_entry(entry)
                queen.parent1.mating_entries.append(entry.set_parent1_inspected)
                queen.parent2.mating_entries.append(entry.set_parent2_inspected)
                child.mating_entries.append(entry.set_child_inspected)

                self.bestiary.add_offspring(child.genes.species[0])
            return True
        return False

    @except_print(Exception)
    def update(self):
        if isinstance(self.princess.slot, Queen):
            queen_died = self.try_queen_die()
            if not queen_died and self.princess.slot.remaining_lifespan > 0:
                self.problem = ApiaryProblems.ALL_OK
                self.princess.slot.remaining_lifespan -= 1
                res = products.get(self.princess.slot.genes.species[0])
                if res is not None:
                    resources_to_add = defaultdict(int)
                    for res_name in res:
                        amt, prob = res[res_name]
                        probability = (self.princess.slot.genes.speed[0].value) * (self.production_modifier) * config_production_modifier * (prob)
                        # print(self.princess.slot.genes.speed[0], prob, probability)
                        if probability > 1:
                            resources_to_add[res_name] = int(probability)
                            probability -= int(probability)
                        if random.random() < probability:
                            resources_to_add[res_name] += 1
                    self.add_resources(resources_to_add)
                    self.bestiary.add_produced_resources(self.princess.slot.genes.species[0], resources_to_add)
                else:
                    assert False, 'Should be unreachable'
        else:
            self.problem = ApiaryProblems.NO_QUEEN

class Alveary(Apiary):
    cost = {ResourceTypes.HONEY: 1000, ResourceTypes.ROYAL_JELLY: 250, ResourceTypes.POLLEN_CLUSTER: 250}

class Game:
    inspect_cost = 3
    def __init__(self):
        self.exit_event = threading.Event()
        self.inner_state_thread = None
        self.restart_game()

    def restart_game(self):
        self.resources = Resources()
        # self.resources = Resources({ResourceTypes.WOOD: 50, ResourceTypes.FLOWERS: 50})
        self.bestiary = Bestiary()
        self.mating_history = MatingHistory()
        self.inventories : dict[str, Inventory] = {}
        self.build('inventory', free=True)
        self.inv = self.inventories[local['Inventory'] + ' 1']
        self.apiaries : List[Apiary] = []
        self.build('apiary', free=True)
        self.total_inspections = 0

        product_achievements = [
            ProducedProducts({ResourceTypes.FLOWERS: 10, ResourceTypes.WOOD: 10}, {ResourceTypes.HONEY: 5}, **local['produce10flowers10wood']),
            ProducedProducts({ResourceTypes.HONEY: 1}, {ResourceTypes.HONEY: 5}, **local['produce1honey']),
            ProducedProducts({ResourceTypes.HONEY: 50}, {ResourceTypes.POLLEN_CLUSTER: 1, ResourceTypes.ROYAL_JELLY: 1}, **local['produce50honey']),
            ProducedProducts({ResourceTypes.POLLEN_CLUSTER: 1}, {ResourceTypes.POLLEN_CLUSTER: 5}, **local['produce1pollencluster']),
            ProducedProducts({ResourceTypes.ROYAL_JELLY: 1}, {ResourceTypes.ROYAL_JELLY: 5}, **local['produce1royaljelly']),
        ]
        achievement_species = [
            (BeeSpecies.COMMON, 'breedCOMMON'),
            (BeeSpecies.CULTIVATED, 'breedCULTIVATED'),
            (BeeSpecies.NOBLE, 'breedNOBLE'),
            (BeeSpecies.MAJESTIC, 'breedMAJESTIC'),
            (BeeSpecies.IMPERIAL, 'breedIMPERIAL'),
            (BeeSpecies.DILIGENT, 'breedDILIGENT'),
            (BeeSpecies.UNWEARY, 'breedUNWEARY'),
            (BeeSpecies.INDUSTRIOUS, 'breedINDUSTRIOUS'),
        ]
        species_achievements = [BredSpecies(species, **local[text]) for species, text in achievement_species]
        self.achievement_manager = AchievementManager(
            self,
            product_achievements + species_achievements,
            self.notify_achievement
        )

        if self.inner_state_thread is not None:
            self.exit_event.set()
            self.inner_state_thread.join()
            self.inner_state_thread = None
        self.exit_event.clear()
        self.inner_state_thread = threading.Thread(target=self.update_state)
        self.inner_state_thread.start()

    def notify_achievement(self, achievement: Achievement):
        self.print(local['unlocked'] + ':\n' +
                   local['requirement'] + achievement.requirement_str + '\n' +
                   local['reward'] + achievement.reward_str + '\n' +
                   local['comment'] + achievement.comment_str)

    def exit(self):  # tested
        self.exit_event.set()
        self.print('Exiting...')

    @staticmethod
    def parse_ranges_numbers(*params):
        res = []
        for w in params:
            if '..' in w:
                try:
                    left, right = w.split('..')
                except ValueError:
                    raise ValueError(f'Range must have exactly 1 `..`')
                left, right = int(left), int(right)
                res.extend(list(range(left, right+1)))
            else:
                res.append(int(w))
        return res

    @staticmethod
    def where_what(*params):
        where, *what = params
        where = int(where)
        return where, Game.parse_ranges_numbers(*what)

    @except_print(IndexError, ValueError, SlotOccupiedError)
    def put(self, *params):
        where, what = Game.where_what(*params)
        if len(what) > 2:
            raise ValueError("Can't put more than two bees")
        for w in what:
            self.apiaries[where].put(self.inv[w].slot)
            self.inv.take(w)

    @except_print(IndexError, ValueError, SlotOccupiedError)
    def reput(self, *params):
        where, what = Game.where_what(*params)
        if len(what) > 2:
            raise ValueError("Can't reput more than two bees")
        for w in what:
            self.apiaries[where].put(self.apiaries[where][w].slot)
            self.apiaries[where].take(w)

    @except_print(IndexError, ValueError, SlotOccupiedError)
    def take(self, *params):
        where, what = Game.where_what(*params)
        bees = self.apiaries[where].take_several(what)
        self.inv.place_bees(bees)

    @except_print(ValueError)
    def throw(self, *params):
        what = Game.parse_ranges_numbers(*params)
        for idx in what:
            self.inv.take(idx)

    @except_print(ValueError)
    def swap(self, *params):
        self.inv.swap(*map(int, params))

    @staticmethod
    def forage(inventory: Inventory):
        genes = Genes.sample()
        inventory.place_bees([Princess(genes), Drone(genes)])

    @except_print(IndexError, ValueError)
    def inspect(self, *params):  # tested
        slot = self.inv[int(params[0])]
        if not slot.is_empty():
            self.inspect_bee(slot.slot)

    def inspect_bee(self, bee):
        if bee is not None and not bee.inspected:
            self.resources.remove_resources({ResourceTypes.HONEY: self.inspect_cost})
            bee.inspect()
            self.total_inspections += 1

    @except_print(IndexError)
    def build(self, *params, free=False):
        if params[0] in ['apiary', 'api', 'a']:  # tested
            if not free:
                self.resources.remove_resources(Apiary.cost)
            self.apiaries.append(Apiary(str(len(self.apiaries)), self.resources.add_resources, self.mating_history.append, self.bestiary))
            return self.apiaries[-1]
        elif params[0] in ['inventory', 'inv', 'i']:
            if not free:
                self.resources.remove_resources(Inventory.cost)
            name = local['Inventory'] +' ' + str(len(self.inventories)+1)
            self.inventories[name] = (Inventory(49, name))
            return self.inventories[name]
        elif params[0] == 'alveary':
            if not free:
                self.resources.remove_resources(Alveary.cost)
            self.print('You won the demo!', out=self.command_out, flush=True)

    def rename_inventory(self, from_str, to_str):
        if to_str == '':
            raise ValueError('Cannot save empty inventory name')
        if from_str == to_str:
            return
        if to_str in self.inventories:
            raise ValueError('This name is already in use')
        inv = self.inventories.pop(from_str)
        self.inventories[to_str] = inv
        inv.name = to_str

    def get_available_build_options(self):
        options = []
        if self.resources.check_enough(Apiary.cost):
            options.append(('Apiary', Apiary.cost))
        if self.resources.check_enough(Inventory.cost):
            options.append(('Inventory', Inventory.cost))
        if self.resources.check_enough(Alveary.cost):
            options.append(('Alveary', Alveary.cost))
        return options

    def update_state(self):
        while True:
            time.sleep(1)
            if self.exit_event.is_set():
                break

            for apiary in self.apiaries:
                apiary.update()

            self.achievement_manager.check_achievements()

            self.state_updated()

    def state_updated(self):
        pass

    def get_state(self) -> dict:
        from migration import \
            CURRENT_BACK_VERSION  # import here to avoid circular imports
        return {
            'back_version': CURRENT_BACK_VERSION,
            'resources': self.resources,
            'inventories': self.inventories,
            'apiaries': self.apiaries,
            'total_inspections': self.total_inspections,
            'mating_history': self.mating_history,
            'bestiary': self.bestiary,
            'achievements': self.achievement_manager.achievements,
        }

    def save(self, name):
        if not os.path.exists('saves'):
            os.mkdir('saves')
        with open('saves/' + name + '.forestry', 'wb') as f:
            pickle.dump(self.get_state(), f)

    def get_save_names_list(self):
        if not os.path.exists('saves'):
            return []
        return [x.replace('.forestry', '') for x in os.listdir('saves') if x.endswith('.forestry')]

    def load_last(self):
        d = {name: os.path.getmtime('saves/' + name + '.forestry') for name in self.get_save_names_list()}
        if len(d) == 0:
            return
        latest = max(d, key=d.get)
        print(latest)
        self.load(latest)

    def load(self, name) -> dict:
        with open('saves/' + name + '.forestry', 'rb') as f:
            state : dict = pickle.load(f)

        from migration import (  # import here to avoid circular imports
            CURRENT_BACK_VERSION, update_back_versions)

        try:
            if state.get('back_version', 0) < CURRENT_BACK_VERSION:
                for update_back_func in update_back_versions[state.get('back_version', 0):]:
                    state = update_back_func(state)
        except Exception as e:
            self.exit()
            print_exc()

        self.resources = state['resources']
        self.inventories = state['inventories']
        self.apiaries = state['apiaries']
        self.total_inspections = state['total_inspections']
        self.mating_history = state['mating_history']
        self.bestiary = state['bestiary']
        if 'achievements' in state:
            self.achievement_manager.achievements = state['achievements']
        return state