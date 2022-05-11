#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# %pip install -r requirements.txt
from IPython.display import clear_output
#clear_output()
from enum import Enum, IntEnum, auto
from dataclasses import dataclass, fields
import typing
from typing import Any, Tuple, Union
from collections import defaultdict
import random
from pprint import pprint
import asyncio
import threading
import sys
import time
import textwrap


# In[ ]:


def weighted_if(weight, out1, out2):
    return out1 if random.random() < weight else out2


# In[ ]:


class BeeSpecies(Enum):
    def __str__(self):
        return local[self].upper() if dominant[self] else local[self].lower()
    FOREST       = auto()
    MEADOWS      = auto()
    COMMON       = auto()
    CULTIVATED   = auto()
    NOBLE        = auto()
    MAJESTIC     = auto()
    IMPERIAL     = auto()
    DILIGENT     = auto()
    UNWEARY      = auto()
    INDUSTRIOUS  = auto()
    # COMMON     = auto()
    # COMMON     = auto()
    # COMMON     = auto()
    # COMMON     = auto()

class BeeFertility(IntEnum):
    def __str__(self):
        return local[self]+'D' if dominant[self] else local[self]+'p'
    TWO = 2
    THREE = 3
    FOUR = 4

class BeeLifespan(Enum):
    def __str__(self):
        return local[self].upper() if dominant[self] else local[self].lower()
    LONGEST    = 14
    LONGER     = 12
    LONG       = 10
    ELONGATED  = 9
    NORMAL     = 8
    SHORTENED  = 7
    SHORT      = 6
    SHORTER    = 4
    SHORTEST   = 2

class BeeSpeed(Enum):
    def __str__(self):
        return local[self].upper() if dominant[self] else local[self].lower()
    FASTEST  = 1.7
    FASTER   = 1.4
    FAST     = 1.2
    NORMAL   = 1
    SLOW     = 0.8
    SLOWER   = 0.6
    SLOWEST  = 0.3
    
bs = BeeSpecies
bf = BeeFertility
bl = BeeLifespan
bS = BeeSpeed
    
dominant = {
    bs.FOREST      : True,  # known
    bs.MEADOWS     : True,  # known
    bs.COMMON      : True,  # known
    bs.CULTIVATED  : True,  # known
    bs.NOBLE       : False, # known
    bs.MAJESTIC    : True,  # known
    bs.IMPERIAL    : False, # known
    bs.DILIGENT    : False, # known
    bs.UNWEARY     : True,  # known
    bs.INDUSTRIOUS : False, # known
    bf(2)          : True,  # known
    bf(3)          : False, # known
    bf(4)          : False, # known
    bl.LONGEST     : False,
    bl.LONGER      : False,
    bl.LONG        : False,
    bl.ELONGATED   : False,
    bl.NORMAL      : False,
    bl.SHORTENED   : False,
    bl.SHORT       : True,  # known
    bl.SHORTER     : True,  # known
    bl.SHORTEST    : False,
    bS.FASTEST     : False,
    bS.FASTER      : False,
    bS.FAST        : False,
    bS.NORMAL      : False,
    bS.SLOW        : False,
    bS.SLOWER      : True,  # known
    bS.SLOWEST     : True   # known
}

default_genes = {
    bs.FOREST      : {'species': bs.FOREST      , 'fertility': bf(3), 'lifespan': bl.SHORTER,   'speed': bS.SLOWEST},
    bs.MEADOWS     : {'species': bs.MEADOWS     , 'fertility': bf(2), 'lifespan': bl.SHORTER,   'speed': bS.SLOWEST},
    bs.COMMON      : {'species': bs.COMMON      , 'fertility': bf(2), 'lifespan': bl.SHORTER,   'speed': bS.SLOWER},
    bs.CULTIVATED  : {'species': bs.CULTIVATED  , 'fertility': bf(2), 'lifespan': bl.SHORTEST,  'speed': bS.FAST},
    bs.NOBLE       : {'species': bs.NOBLE       , 'fertility': bf(2), 'lifespan': bl.SHORT,     'speed': bS.SLOWER},
    bs.MAJESTIC    : {'species': bs.MAJESTIC    , 'fertility': bf(4), 'lifespan': bl.SHORTENED, 'speed': bS.NORMAL},
    bs.IMPERIAL    : {'species': bs.IMPERIAL    , 'fertility': bf(2), 'lifespan': bl.NORMAL,    'speed': bS.SLOWER},
    bs.DILIGENT    : {'species': bs.DILIGENT    , 'fertility': bf(2), 'lifespan': bl.SHORT,     'speed': bS.SLOWER},
    bs.UNWEARY     : {'species': bs.UNWEARY     , 'fertility': bf(2), 'lifespan': bl.SHORTENED, 'speed': bS.NORMAL},
    bs.INDUSTRIOUS : {'species': bs.INDUSTRIOUS , 'fertility': bf(2), 'lifespan': bl.NORMAL,    'speed': bS.SLOWER},
}
    

assert len(BeeSpecies) == 10, 'Dont forget to update basic species'
basic_species = [
    bs.FOREST,
    bs.MEADOWS
]

mutations = {
    (bs.FOREST,     bs.MEADOWS): ([bs.COMMON],              [0.15]),
    (bs.FOREST,     bs.COMMON ): ([bs.CULTIVATED],          [0.12]),
    (bs.COMMON,     bs.MEADOWS): ([bs.CULTIVATED],          [0.12]),
    (bs.CULTIVATED, bs.COMMON ): ([bs.NOBLE, bs.DILIGENT],  [0.1, 0.1]),
    (bs.CULTIVATED, bs.NOBLE  ): ([bs.MAJESTIC],            [0.08]),
    (bs.MAJESTIC,   bs.NOBLE  ): ([bs.IMPERIAL],            [0.08]),
    
}
for k in mutations:
    mutations[k][0].append(None)
    mutations[k][1].append(1-sum(mutations[k][1]))
mutations.update({ (key[1], key[0]) : mutations[key] for key in mutations})

products = {
    bs.FOREST      : {'honey': (1, 0.5), 'wood': (1, 0.5)},
    bs.MEADOWS     : {'honey': (1, 0.5), 'flowers': (1, 0.5)},
    bs.COMMON      : {'honey': (1, 0.75)},
    bs.CULTIVATED  : {'honey': (1, 1)},
    bs.NOBLE       : {'honey': (1, 0.25), 'gold': (1, 0.1)},
    bs.MAJESTIC    : {'honey': (1, 0.25), 'gold': (1, 0.15)},
    bs.IMPERIAL    : {'honey': (1, 0.25), 'gold': (1, 0.1), 'royal gelly': (1, 0.1)},
    bs.DILIGENT    : {'honey': (1, 0.25), 'string': (1, 0.1)},
    bs.UNWEARY     : {'honey': (1, 0.25), 'string': (1, 0.15)},
    bs.INDUSTRIOUS : {'honey': (1, 0.25), 'string': (1, 0.1), 'pollen cluster': (1, 0.1)},
}

del bs, bf

class SlotOccupiedError(RuntimeError):
    pass


# In[ ]:


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
        if mut is not None: # mutation found in mutation map
            allele = random.choices(mut[0], weights=mut[1])[0] # sample with weights from mutation map
            if allele is not None:
                return weighted_if(0.5, (allele, allele2), (allele1, allele)) # gene from mutation
        return (allele1, allele2) # same genes if not mutated
    
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
            return Genes(
                **{k: (g, g) for k, g in genes.items()}
            )


# In[ ]:


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
        res.append(local[type(self)])
        genes = vars(self.genes)
        for key in genes:
            res.append(f'  {key} : {genes[key][0]}, {genes[key][1]}')
        return '\n'.join(res)
    
    def __hash__(self):
        return hash(self.genes)
    
    def __eq__(self, other):
        return self.genes == other.genes
    
    
    def small_str(self):
        return local[self.genes.species[0]] + ' ' + local[type(self)]
    
    def inspect(self):
        self.inspected = True

class Queen(Bee):
    def __init__(self, g1, g2, inspected: bool = False):
        self.g1 = g1
        self.g2 = g2
        super().__init__(g1, inspected)
        self.lifespan = g1.lifespan[0].value
        self.remaining_lifespan = self.lifespan
    
    def small_str(self):
        return super().small_str() + ', rem: ' + str(self.remaining_lifespan)
    
    def die(self):
        return [Princess(self.g1.crossingover(self.g2))] + [Drone(self.g1.crossingover(self.g2)) for i in range(self.genes.fertility[0])]
    
class Princess(Bee):
    def __init__(self, genes, inspected: bool = False):
        super().__init__(genes, inspected)
    
    def mate(self, other: 'Drone') -> Queen:
        if not isinstance(other, Drone):
            raise TypeError('Princesses can only mate drones')
        return Queen(self.genes, other.genes, 3)

class Drone(Bee):
    def __init__(self, genes, inspected: bool = False):
        super().__init__(genes, inspected)


# In[ ]:


local = {
    Drone                   : 'Drone',
    Princess                : 'Princess',
    Queen                   : 'Queen',
    BeeSpecies.FOREST       : 'FOREST',
    BeeSpecies.MEADOWS      : 'MEADOWS',    
    BeeSpecies.COMMON       : 'COMMON',     
    BeeSpecies.CULTIVATED   : 'CULTIVATED', 
    BeeSpecies.MAJESTIC     : 'MAJESTIC',   
    BeeSpecies.NOBLE        : 'NOBLE',      
    BeeSpecies.IMPERIAL     : 'IMPERIAL',   
    BeeSpecies.DILIGENT     : 'DILIGENT',   
    BeeSpecies.UNWEARY      : 'UNWEARY',    
    BeeSpecies.INDUSTRIOUS  : 'INDUSTRIOUS',
    BeeFertility(2)         : '2',
    BeeFertility(3)         : '3',
    BeeFertility(4)         : '4',
    BeeLifespan.LONGEST     : 'Longest',    
    BeeLifespan.LONGER      : 'Longer',     
    BeeLifespan.LONG        : 'Long',       
    BeeLifespan.ELONGATED   : 'Elongated', 
    BeeLifespan.NORMAL      : 'Normal',     
    BeeLifespan.SHORTENED   : 'Shortened',  
    BeeLifespan.SHORT       : 'Short',      
    BeeLifespan.SHORTER     : 'Shorter',    
    BeeLifespan.SHORTEST    : 'Shortest',
    BeeSpeed.FASTEST        : 'FASTEST',
    BeeSpeed.FASTER         : 'FASTER',
    BeeSpeed.FAST           : 'FAST',
    BeeSpeed.NORMAL         : 'NORMAL',
    BeeSpeed.SLOW           : 'SLOW',
    BeeSpeed.SLOWER         : 'SLOWER',
    BeeSpeed.SLOWEST        : 'SLOWEST',
}


# In[ ]:


class Resources:
    def __init__(self, **kwargs):
        self.res = defaultdict(int)
        self.res.update(kwargs)
        super().__init__()
    
    def __str__(self):
        res = ['------ RESOURCES ------']
        for k in self.res:
            res.append(k + ': ' + str(self.res[k]))
        return '\n'.join(res)
    
    def __getitem__(self, key):
        return self.res[key]
    
    def add_resources(self, resources):
        for k in resources:
            self.res[k] += resources[k]
    
    def remove_resources(self, resources):
        for k in resources:
            if self.res[k] - resources[k] < 0:
                raise ValueError(f'Not enough {k}: you have {self.res[k]} but you need {resources[k]}')
        for k in resources:
            self.res[k] -= resources[k]


# In[ ]:


class Slot:
    def __init__(self):
        self.slot = None
        super().__init__()
    
    def __str__(self):
        if self.slot is not None:
            return str(self.slot)
        else:
            return 'Slot empty'
        
    def small_str(self):
        if self.slot is not None:
            return self.slot.small_str()
        else:
            return 'Slot empty'
    
    def put(self, bee):
        if self.slot is None:
            self.slot = bee
        else:
            raise SlotOccupiedError('The slot is not empty')
            
    def take(self):
        bee = self.slot
        self.slot = None
        return bee
    
    def is_empty(self):
        return self.slot is None


# In[ ]:


class Inventory:
    def __init__(self, capacity=None, /):
        self.capacity = capacity or 100
        self.storage = [Slot() for i in range(self.capacity)]
        super().__init__()
        
    def __setitem__(self, key, value):
        self.storage[key].put(value)
    
    def __getitem__(self, key):
        return self.storage[key]
    
    def __str__(self):
        res = ['------ INV ------']
        
        empty = True
        for index, slot in enumerate(self.storage):
            if not slot.is_empty():
                empty = False
                res.append(str(index) + ' ' + slot.small_str())
        if empty:
            res.append('Empty...')
        
        return '\n'.join(res)
    
    def take(self, index):
        bee = self.storage[index].take()
        return bee
    
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

    def place_bees(self, offspring, parent_index=None):
        if parent_index is not None:
            self.storage[parent_index].take()
        index = 0
        for bee in offspring:
            while index < self.capacity:
                try:
                    self.storage[index].put(bee)
                    index += 1
                    break
                except SlotOccupiedError:
                    index += 1
                    continue
            else:
                self.print('Beware that', bee, 'was thrown out...')
    


# In[ ]:


class Apiary:
    def __init__(self, add_resources):
        self.inv = Inventory(7)
        self.princess = Slot()
        self.drone = Slot()
        self.add_resources = add_resources
        super().__init__()
        
    def __str__(self):
        res = ['------ APIARY ------']
        res.append('Princess: ' + self.princess.small_str())
        res.append('Drone: ' + self.drone.small_str())
        inv_str = textwrap.indent(str(self.inv), '  ')
        res.append(inv_str)
        return '\n'.join(res)
    
    def __getitem__(self, key):
        res = self.inv.take(key)
        return res
        
    def put_princess(self, bee):
        if not isinstance(bee, Princess) and not isinstance(bee, Queen):
            raise TypeError('Bee should be a Princess or a Queen')
        self.princess.put(bee)
        self.try_breed()
    
    def put_drone(self, bee):
        if not isinstance(bee, Drone):
            raise TypeError('Bee should be a Drone')
        self.drone.put(bee)
        self.try_breed()
    
    def put(self, bee):
        if isinstance(bee, Princess) or isinstance(bee, Queen):
            self.put_princess(bee)
        elif isinstance(bee, Drone):
            self.put_drone(bee)
    
    def try_breed(self):
        if not self.princess.is_empty() and not self.drone.is_empty():
            princess = self.princess.take()
            drone = self.drone.take()
            self.princess.put(princess.mate(drone))
    
    def update(self):
        if isinstance(self.princess.slot, Queen):
            if self.princess.slot.remaining_lifespan == 0:
                queen = self.princess.take()
                bees = queen.die()
                if len(bees) <= self.inv.empty_slots():
                    self.inv.place_bees(bees)
                else:
                    self.princess.put(queen)
            else:
                self.princess.slot.remaining_lifespan -= 1
                res = products.get(self.princess.slot.genes.species[0])
                if res is not None:
                    resources_to_add = dict()
                    for res_name in res:
                        amt, prob = res[res_name]
                        if random.random() < prob:
                            resources_to_add[res_name] = amt
                    self.add_resources(resources_to_add)
                else:
                    assert False, 'Should be unreachable'

class Game:
    def __init__(self):
        self.exit_event = threading.Event()
        self.render_event = threading.Event()
        self.render_event.set()
        
        self.resources = Resources(honey=0)
        self.inv = Inventory(100)
        self.apiaries = [Apiary(self.resources.add_resources)]
    
        self.to_render = [self.resources, self.inv, self.apiaries[0]]
        
        self.inner_state_thread = threading.Thread(target=self.update_state)
        self.inner_state_thread.start()
        self.render_thread = threading.Thread(target=self.render)
        self.render_thread.start()
        
    def execute_command(self, value):
        command, *params = value.split()
        if command in ['exit', 'q']: # tested
            self.exit_event.set()
            self.print('Exiting...')
            self.console.layout.display = 'none'
        elif command == 'save':
            self.save(params[0])
        elif command == 'load':
            self.load(params[0])
        elif command in ['inv', 'i']: # tested both
            if len(params) == 0:
                self.to_render = [self.resources, self.inv]
            else:
                slot = int(params[0])
                # self.print(self.inv[slot], out=self.command_out, flush=True)
                self.to_render = [self.resources, self.inv[slot]]
        elif command in ['apiary', 'api', 'a']: # tested
            try:
                apiary = self.apiaries[int(params[0])]
            except (ValueError, IndexError) as e:
                self.print(e, out=self.command_out, flush=True)
                print(e)
            else:
                self.to_render = [self.resources, apiary]
        elif command in ['show', 's']: # probably tested
            if params[0] in ['inv', 'i']:
                if len(params) == 1:
                    self.to_render.append(self.inv)
                else:
                    slot = int(params[1])
                    self.to_render.append(self.inv[slot])
            elif params[0] in ['apiary', 'api', 'a']:
                apiary = self.apiaries[int(params[1])]
                self.to_render.append(apiary)
            elif params[0] in ['resources', 'r']:
                self.to_render.append(self.resources)
        elif command in ['unshow', 'uns', 'us', 'u']: # tested
            self.to_render.pop()
        elif command == 'put':
            try:
                where, *what = map(int, params)
                for w in what:
                    self.apiaries[where].put(self.inv.take(w))
            except (IndexError, ValueError) as e:
                self.print(e, out=self.command_out, flush=True)
        elif command == 'reput':
            try:
                where, *what = map(int, params)
                for w in what:
                    self.apiaries[where].put(self.apiaries[where][w])
            except (IndexError, ValueError) as e:
                self.print(e, out=self.command_out, flush=True)
        elif command == 'take':
            try:
                where, *what = map(int, params)
                for w in what:
                    self.inv.place_bees([self.apiaries[where][w]])
            except (IndexError, ValueError) as e:
                self.print(e, out=self.command_out, flush=True)
        elif command == 'throw':
            try:
                for idx in map(int, params):
                    self.inv.take(idx)
            except ValueError as e:
                self.print(e, out=self.command_out, flush=True)
        elif command == 'swap':
            self.inv.swap(*map(int, params))
        elif command == 'forage': # tested
            genes = Genes.sample()
            self.inv.place_bees([Princess(genes), Drone(genes)])
        elif command == 'inspect': # tested
            try:
                slot = self.inv[int(params[0])]
                if not slot.is_empty() and not slot.slot.inspected:
                    self.resources.remove_resources({'honey': 5})
                    slot.slot.inspected = True
            except (IndexError, ValueError) as e:
                self.print(e, out=self.command_out, flush=True)
        elif command == 'build':
            try:
                if params[0] in ['apiary', 'api', 'a']: # tested
                    self.resources.remove_resources({'wood': 5, 'flowers': 5, 'honey': 10})
                    self.apiaries.append(Apiary(self.resources.add_resources))
                elif params[0] == 'alveary':
                    self.resources.remove_resources({'royal gelly': 25, 'pollen cluster': 25, 'honey': 100})
                    self.print('You won the demo!', out=self.command_out, flush=True)
                    self.exit_event.set()
            except (IndexError, ValueError) as e:
                self.print(e, out=self.command_out, flush=True)
        self.render_event.set()
                
    def update_state(self):
        while True:
            time.sleep(1)
            if self.exit_event.is_set():
                break
            
            for apiary in self.apiaries:
                apiary.update()
            self.render_event.set()
    
    def save(self, filename):
        with open(filename+'.forestry', 'wb') as f:
            
            state = {
                'resources' : self.resources,
                'inv' : self.inv,
                'apiaries' : self.apiaries,
                'to_render' : self.to_render
            }
            pickle.dump(state, f)
            
    def load(self, filename):
        with open(filename+'.forestry', 'rb') as f:
            saved = pickle.load(f)
        self.resources = saved['resources']
        self.inv = saved['inv']
        self.apiaries = saved['apiaries']
        self.to_render = saved['to_render']
