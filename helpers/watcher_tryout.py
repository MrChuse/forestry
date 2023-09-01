import logging
logging.basicConfig(level=logging.DEBUG)

class CostWatcher(type):
    def __init__(cls, name, bases, clsdict):
        mro = cls.mro()
        if len(mro) > 2:
            if not hasattr(cls, 'cost'):
                raise SyntaxError(f'All buildings must have costs: {cls}')
            mro[-2].__dict__['all_buildings_costs'][name] = cls.cost
            logging.debug("Building registered: " + name)
        super(CostWatcher, cls).__init__(name, bases, clsdict)

class Building(metaclass=CostWatcher):
    all_buildings_costs = {}

class Inventory(Building):
    cost = {'money': 10}

class BetterInventory(Inventory):
    cost = {'money': 100}

print(Building.all_buildings_costs)