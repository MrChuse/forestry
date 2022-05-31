from enum import Enum
import yaml

# from forestry import local, dominant

class LocalEnum(Enum):
    def __str__(self):
        return local[self].upper() if dominant[self] else local[self].lower()

with open('config.yaml') as f:
    config = yaml.safe_load(f)

# load all the genes and their alleles
genes_conf = config['genes_alleles']
genes_enums = {}
dominant = {}
for gene_name, list_of_alleles in genes_conf.items():
    enum_dict = []
    for allele_name, allele_value, _ in list_of_alleles:
        enum_dict.append((allele_name, allele_value))
    gene_enum = LocalEnum(gene_name, enum_dict)
    genes_enums[gene_name] = gene_enum
    for allele_name, _, dominance in list_of_alleles:
        dominant[gene_enum[allele_name]] = dominance
BeeSpecies, BeeFertility, BeeLifespan, BeeSpeed = genes_enums.values()

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

# products
products_config = config['products']
products = {}
for allele_name, prod_dict in products_config.items():
    if BeeSpecies[allele_name] not in products:
        products[BeeSpecies[allele_name]] = {}
    else:
        raise RuntimeError('Encountered repeating alleles in products in config file')
    for prod_name, (amt, prob) in prod_dict.items():
        products[BeeSpecies[allele_name]][prod_name] = (amt, prob)

# local
filename = f'./locals/{config["local"]}.yaml'
import codecs
with codecs.open(filename, "r", "utf_8_sig" ) as f:
    local_conf = yaml.safe_load(f)

local = {}
straight = ['genes', 'bee_genders', 'buildings']
for thing in straight:
    local = {**local, **local_conf[thing]}
for gene_name, gene_local in local_conf['genes'].items():
    local[gene_name] = gene_local
for bee_gender, (gender_local, species_local_index) in local_conf['bee_genders'].items():
    local[bee_gender] = (gender_local, species_local_index)
for gene_name, dict_of_alleles in local_conf['genes_alleles'].items():
    for allele_name, allele_local in dict_of_alleles.items():
        local[genes_enums[gene_name][allele_name]] = allele_local
print(local)