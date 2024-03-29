import codecs
import os
from enum import Enum
from typing import Dict

import yaml


class LocalEnum(Enum):
    def __str__(self):
        return local[self].upper() if dominant[self] else local[self].lower()
class NameEnum(Enum):
    def __str__(self):
        return self.name

with open('config.yaml') as f:
    config = yaml.safe_load(f)

# some ui stuff
UI_MESSAGE_SIZE = (500, 300)
INVENTORY_WINDOW_SIZE = (486, 513)
APIARY_WINDOW_SIZE = (300, 420)
ANALYZER_WINDOW_SIZE = (300, 350)

# load all the genes and their alleles
genes_conf = config['genes_alleles']
genes_enums : Dict[str, LocalEnum] = {}
dominant : Dict[LocalEnum, bool] = {}
for gene_name, list_of_alleles in genes_conf.items():
    enum_dict = []
    for allele_name, allele_value, _ in list_of_alleles:
        enum_dict.append((allele_name, allele_value))
    gene_enum = LocalEnum(gene_name, enum_dict)
    genes_enums[gene_name] = gene_enum
    for allele_name, _, dominance in list_of_alleles:
        dominant[gene_enum[allele_name]] = dominance
BeeSpecies, BeeFertility, BeeLifespan, BeeSpeed = genes_enums.values()

tiers_conf = config['tier']
tiers: Dict[LocalEnum, int] = {}
for gene_name, dict_of_tiers in tiers_conf.items():
    for allele_name, tier in dict_of_tiers.items():
        allele = genes_enums[gene_name][allele_name]
        tiers[allele] = tier

# load mutations
mutations_conf = config['mutations']
mutations = {}
for gene_name, list_of_mutations in mutations_conf.items():
    for parent1, parent2, offspring, probability in list_of_mutations:
        parent1 = genes_enums[gene_name][parent1]
        parent2 = genes_enums[gene_name][parent2]
        offspring = genes_enums[gene_name][offspring]
        if (parent1, parent2) in mutations and offspring in mutations[(parent1, parent2)][0]:
            raise RuntimeError('Encountered repeating mutations in config file')
        if (parent1, parent2) not in mutations:
            mutations[(parent1, parent2)] = ([], [])
            mutations[(parent2, parent1)] = ([], [])
        mutations[(parent1, parent2)][0].append(offspring)
        mutations[(parent2, parent1)][0].append(offspring)
        mutations[(parent1, parent2)][1].append(probability)
        mutations[(parent2, parent1)][1].append(probability)
# appends None with weight that sums up to 1 in order to use random.choices later
for k in mutations:
    mutations[k][0].append(None)
    mutations[k][1].append(1 - sum(mutations[k][1]))

# resources and products
ResourceTypes = NameEnum('ResourceTypes', zip(config['resources'], range(len(config['resources']))))

config_production_modifier = config['production_modifier']

products_config = config['products']
products = {}
for allele_name, prod_dict in products_config.items():
    if BeeSpecies[allele_name] not in products:
        products[BeeSpecies[allele_name]] = {}
    else:
        raise RuntimeError('Encountered repeating alleles in products in config file')
    for prod_name, (amt, prob) in prod_dict.items():
        try:
            prod_name = ResourceTypes[prod_name]
        except KeyError as e:
            print('prod_name was not listed in the `resources` section')
            raise e
        products[BeeSpecies[allele_name]][prod_name] = (amt, prob)

amount_needed_to_analyze_config = config['amount_needed_to_analyze']
amount_needed_to_analyze = {}
for allele_name, amt in amount_needed_to_analyze_config.items():
    if BeeSpecies[allele_name] not in amount_needed_to_analyze:
        amount_needed_to_analyze[BeeSpecies[allele_name]] = amt
    else:
        raise RuntimeError('Encountered repeating alleles in `amount_needed_to_analyze` in config file')

# local
existing_locals = [i[:-5] for i in os.listdir('locals')] # drop .yaml

def load_settings(filename='settings.yaml'):
    settings = {
        'fullscreen': True,
        'master_volume': 1,
        'click_volume': 1,
        'language': 'en'
    }

    if os.path.exists(filename):
        with open(filename, 'r') as f:
            settings.update(yaml.safe_load(f))

    return settings

language = load_settings()['language']
filename = f'./locals/{language}.yaml'
with codecs.open(filename, "r", "utf_8_sig" ) as f:
    local_conf = yaml.safe_load(f)

local = {}
straight = ['genes', 'bee_genders', 'buildings', 'esc_menu', 'achievements', 'achievements_misc', 'mendel_text_additionals']
for thing in straight:
    local.update(local_conf[thing])
for res, translation in local_conf['resources'].items():
    try:
        res = ResourceTypes[res]
    except KeyError:
        pass
    local[res] = translation
local['notenough'] = local_conf['resources']['notenough']
for gene_name, dict_of_alleles in local_conf['genes_alleles'].items():
    for allele_name, allele_local in dict_of_alleles.items():
        local[genes_enums[gene_name][allele_name]] = allele_local

helper_text = local_conf['texts']['helper_text']
mendel_text = local_conf['texts']['mendel_text']

logging_default = {
  'version': 1,
  'formatters': {
    'default': {
      'format': "%(asctime)-15s %(levelname)-8s %(filename)s:%(lineno)s \t%(message)s"
    } # %(name)-8s
  },
  'handlers': {
    'console': {
      'class': 'logging.StreamHandler',
      'formatter': 'default'
    }
  },
  'loggers':{
    "":{
      'handlers': ["console"],
      'level': 'INFO'
    }
  }
}

import logging
import logging.config
logging.config.dictConfig(logging_default)
