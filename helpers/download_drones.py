import string
from multiprocessing import Pool
from forestry import BeeSpecies
import requests

def try_download(species):
    l = []
    s = string.digits + string.ascii_lowercase
    for i in s:
        for j in s:
            new_s = f'{i}/{i}{j}'
            l.append(new_s)
    for thing in l:
        link = f'https://ftbwiki.org/images/{thing}/Item_{species.name.capitalize()}_Bee.png'
        response = requests.get(link)
        if response.ok:
            print(response.url)
            return response.content, species
    return None


if __name__ == '__main__':
    print(len(BeeSpecies))
    with Pool(processes=10) as pool:
        for content, species in pool.imap_unordered(try_download, list(BeeSpecies)):
            for gender in ['Princess', 'Queen', 'Drone']:
                with open(f'assets/{species.name}_{gender}.png', 'wb') as f:
                    f.write(content)