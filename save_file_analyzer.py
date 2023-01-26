import pickle
from pprint import pprint

with open('save.forestry', 'rb') as f:
    save = pickle.load(f)
    pprint(save)
