#!/usr/bin/env python
# coding: utf-8


import asyncio
import pickle
import random
import sys
import textwrap
import threading
import time
import typing
from collections import defaultdict
from dataclasses import dataclass, fields
from enum import Enum, IntEnum, auto
from pprint import pprint
from typing import Any, Callable, List, Tuple, Union
from config import BeeSpecies, BeeFertility, BeeLifespan, BeeSpeed, dominant, mutations, products, local


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


Allele = Union[BeeSpecies, BeeFertility]
Gene = Tuple[Allele, Allele]


@dataclass(eq=True, frozen=True)
class Genes:
    species: Gene
    fertility: Gene
    lifespan: Gene
    speed: Gene

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

    def crossingover(self, genes2):
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
        genes1_dict = vars(self)
        genes2_dict = vars(genes2)
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
    def __init__(self, genes: Genes, inspected: bool = False):
        self.genes = genes
        self.inspected = inspected
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

    def __eq__(self, other):
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


class Queen(Bee):
    type_str = 'Queen'
    def __init__(self, g1, g2, inspected: bool = False):
        self.g1 = g1
        self.g2 = g2
        super().__init__(g1, inspected)
        self.lifespan = g1.lifespan[0].value
        self.remaining_lifespan = self.lifespan

    def small_str(self):
        return super().small_str() + ', rem: ' + str(self.remaining_lifespan)

    def die(self):
        return [Princess(self.g1.crossingover(self.g2))] + [
            Drone(self.g1.crossingover(self.g2)) for i in range(self.genes.fertility[0].value)
        ]


class Princess(Bee):
    type_str = 'Princess'
    def __init__(self, genes, inspected: bool = False):
        super().__init__(genes, inspected)

    def mate(self, other: 'Drone') -> Queen:
        if not isinstance(other, Drone):
            raise TypeError('Princesses can only mate drones')
        return Queen(self.genes, other.genes)


class Drone(Bee):
    type_str = 'Drone'
    def __init__(self, genes, inspected: bool = False):
        super().__init__(genes, inspected)


class Resources:
    def __init__(self, **kwargs):
        self.res = defaultdict(int)
        self.res.update(kwargs)
        super().__init__()

    def __str__(self):
        res = ['------ RESOURCES ------']
        for k in self.res:
            res.append(k + ': ' + str(self.res[k]))
        if len(res) == 1:
            res.append('  Empty...')
        return '\n'.join(res)

    def __getitem__(self, key):
        return self.res[key]

    def add_resources(self, resources):
        for k in resources:
            self.res[k] += resources[k]

    def remove_resources(self, resources):
        s = ''
        for k in resources:
            if self.res[k] - resources[k] < 0:
                s += f'Not enough {k}: you have {self.res[k]} but you need {resources[k]}\n'
        if s != '':
            raise ValueError(s)
        for k in resources:
            self.res[k] -= resources[k]


class Slot:
    empty_str = 'Slot empty'
    def __init__(self):
        self.slot = None
        self.amount = 0
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
        return sum([el.is_empty() for el in self.storage])

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
        for thing in list_things:
            index = 0
            if isinstance(thing, Slot):
                bee = thing.slot
            else:
                bee = thing
            while index < self.capacity:
                if self.storage[index].is_empty():
                    index += 1
                    continue
                if self.storage[index].slot == bee:
                    break
                else:
                    index += 1
            else:
                not_in_storage += 1
        return not_in_storage <= self.empty_slots()
                

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


class Apiary:
    production_modifier = 1/3
    def __init__(self, name, add_resources):
        self.inv = Inventory(7)
        self.princess = Slot()
        self.drone = Slot()
        self.name = name
        self.add_resources = add_resources
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
            queen = self.princess.slot
            bees = queen.die()
            self.inv.place_bees(bees)
            self.princess.take()
            return True
        return False

    @except_print(Exception)
    def update(self):
        if isinstance(self.princess.slot, Queen):
            queen_died = self.try_queen_die()
            if not queen_died and self.princess.slot.remaining_lifespan > 0:
                self.princess.slot.remaining_lifespan -= 1
                res = products.get(self.princess.slot.genes.species[0])
                if res is not None:
                    resources_to_add = dict()
                    for res_name in res:
                        amt, prob = res[res_name]
                        probability = (self.princess.slot.genes.speed[0].value) * (self.production_modifier) * (prob)
                        # print(self.princess.slot.genes.speed[0], prob, probability)
                        if random.random() < probability:
                            resources_to_add[res_name] = amt
                    self.add_resources(resources_to_add)
                else:
                    assert False, 'Should be unreachable'


class Game:
    def __init__(self):
        self.resources = Resources(honey=0)
        self.inventories = []
        self.inv = Inventory(49, '0')
        self.inventories.append(self.inv)
        self.apiaries = [Apiary('0', self.resources.add_resources)]
            
        self.exit_event = threading.Event()

        self.inner_state_thread = threading.Thread(target=self.update_state)
        self.inner_state_thread.start()

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
    def forage(inventory):
        genes = Genes.sample()
        inventory.place_bees([Princess(genes), Drone(genes)])

    @except_print(IndexError, ValueError)
    def inspect(self, *params):  # tested
        slot = self.inv[int(params[0])]
        if not slot.is_empty():
            self.inspect_bee(slot.slot)

    def inspect_bee(self, bee):
        if bee is not None and not bee.inspected:
            self.resources.remove_resources({'honey': 1})
            bee.inspected = True

    @except_print(IndexError)
    def build(self, *params):
        if params[0] in ['apiary', 'api', 'a']:  # tested
            self.resources.remove_resources(
                {'honey': 10, 'wood': 5, 'flowers': 5})
            self.apiaries.append(Apiary(str(len(self.apiaries)), self.resources.add_resources))
            return self.apiaries[-1]
        elif params[0] in ['inventory', 'inv', 'i']:
            self.resources.remove_resources(
                {'wood': 5, 'flowers': 5})
            self.inventories.append(Inventory(49, str(len(self.inventories))))
            return self.inventories[-1]
        elif params[0] == 'alveary':
            self.resources.remove_resources(
                {'honey': 100, 'royal jelly': 25, 'pollen cluster': 25}
            )
            self.print('You won the demo!', out=self.command_out, flush=True)

    def update_state(self):
        while True:
            time.sleep(1)
            if self.exit_event.is_set():
                break

            for apiary in self.apiaries:
                apiary.update()
            
            self.state_updated()

    def state_updated(self):
        pass

    def get_state(self):
        return {
            'resources': self.resources,
            'inventories': self.inventories,
            'apiaries': self.apiaries
        }
            
    def save(self, name):
        with open(name + '.forestry', 'wb') as f:
            pickle.dump(self.get_state(), f)

    def load(self, name):
        with open(name + '.forestry', 'rb') as f:
            saved = pickle.load(f)
        self.resources = saved['resources']
        self.inventories = saved['inventories']
        self.apiaries = saved['apiaries']
        return saved