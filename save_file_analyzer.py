import pickle
from pprint import pprint

with open('saves/1.forestry', 'rb') as f:
    save = pickle.load(f)
    pprint(save)
    pprint(save['resources'].res)