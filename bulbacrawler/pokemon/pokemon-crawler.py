from bs4 import BeautifulSoup
import argparse
import json
import requests
import re

###############################
genMap = {
  'i'   : 1,
  'ii'  : 2,
  'iii' : 3,
  'iv'  : 4,
  'v'   : 5,
  'vi'  : 6,
  'vii' : 7,
  'viii': 8,
  'ix'  : 9,
}
###############################
# PARAMETERS

parser = argparse.ArgumentParser()
parser.add_argument('--pokemon', '-p', help = "The name of the Pokémon", type = str)
parser.add_argument('--gen', '-g', help = "The number of the generation", type = str, default = 'i')
parser.add_argument('--regForm', '-r', help = "The name of the region for the regional form", type = str)
parser.add_argument('--altForm', '-a', help = "The name of the alternate form", type = str)

args = parser.parse_args()

pokemon = args.pokemon
gen = args.gen
regionalForm = args.regForm
alternateForm = args.altForm

###############################
# BULBAPEDIA PAGE

res = requests.get('https://bulbapedia.bulbagarden.net/wiki/' + pokemon.replace(' ', '_').title() + '_(Pok%C3%A9mon)')

soup = BeautifulSoup(res.text, 'html.parser')
firstP = soup.find('div', id = 'mw-content-text').div.p
pText = ''.join(map(lambda p: p.string, firstP.contents)).replace('\n', '')
pList = pText.split(' ')

###############################
# GENERATION CHECK

if 'introduced in Generation' in pText:
  introducedGen = pList[pList.index('introduced') + 3].lower().replace('.', '')
  if genMap[introducedGen] > genMap[gen]:
    # print('Param \'generation\' before Pokémon\'s introduction.')
    exit()

###############################
# BASIC DATA

output = {}

# NUMBER
output['number'] = int(soup.find('a', title = 'Pokémon category').parent.parent.parent.parent.parent.parent.find('th').big.big.a.span.string[1:])

# NAME
output['name'] = soup.find('a', title = 'Pokémon category').parent.big.big.b.string.lower()

###############################
# TYPES

pokemonTypes = []

# OLD TYPES
typeChange = 'Prior to Generation' in pText
if typeChange:
  oldTypes = []
  pChange = pList[pList.index('Prior'):]
  genChange = pChange[pChange.index('Generation') + 1].replace(',', '').lower()

  if 'Pokémon.' in pChange:
    typeIndex = pChange.index('Pokémon.') - 1
    if '/' in pChange[typeIndex]:
      oldTypes = pChange[typeIndex].lower().split('/')
    if '-' in pChange[typeIndex]:
      oldTypes = [pChange[typeIndex].lower().replace('-type', '')]

  elif 'pure' in pChange:
    typeIndex = pChange.index('pure') + 1
    oldTypes = [pChange[typeIndex].lower().replace('-type.', '')]

  elif 'dual-type' in typeChange:
    typeIndex = pChange.index('pure') + 1
    oldTypes = pChange[typeIndex].lower().replace('.', '').split('/')

if typeChange and genMap[genChange] > genMap[gen]:
  pokemonTypes = oldTypes

# CURRENT TYPES
else:
  typeTable = soup.find('span', string = re.compile('Type')).parent.parent.parent.table.tbody
  if regionalForm == None and alternateForm == None:
    for pokemonType in typeTable.find('td').table.tbody.tr.find_all('b'):
      if (pokemonType.string != 'Unknown'):
        pokemonTypes.append(pokemonType.string.lower())

  elif regionalForm != None and alternateForm == None:
    tag = typeTable.find(string = re.compile(regionalForm.title()))
    if tag.name != 'small':
      tag = tag.parent
    for pokemonType in tag.parent.table.tbody.tr.find_all('b'):
      if (pokemonType.string != 'Unknown'):
        pokemonTypes.append(pokemonType.string.lower())

  elif regionalForm == None and alternateForm != None:
    tag = typeTable.find(string = re.compile(alternateForm.title()))
    if tag.name != 'small':
      tag = tag.parent
    for pokemonType in tag.parent.table.tbody.tr.find_all('b'):
      if (pokemonType.string != 'Unknown'):
        pokemonTypes.append(pokemonType.string.lower())

  else:
    tag = typeTable.find(lambda tag: tag.name == 'small' and alternateForm.title() in tag.text and regionalForm.title() in tag.text)
    if tag.name != 'small':
      tag = tag.parent
    for pokemonType in tag.parent.table.tbody.tr.find_all('b'):
      if (pokemonType.string != 'Unknown'):
        pokemonTypes.append(pokemonType.string.lower())
  
  if len(pokemonTypes) == 0:
    for pokemonType in typeTable.find('td').table.tbody.tr.find_all('b'):
      if (pokemonType.string != 'Unknown'):
        pokemonTypes.append(pokemonType.string.lower())

if pokemon == 'rotom' and genMap[gen] < genMap['v']:
  pokemonTypes = ['electric', 'ghost']

output['types'] = pokemonTypes

###############################
# STATS

stats = {}
baseStats = soup.find('span', id = 'Base_stats').parent
statTable = baseStats.next_sibling.next_sibling

if statTable.name != 'table':
  if statTable.name == 'h5' and pokemon.title() in statTable.span.string:
    if alternateForm:
      statTable = statTable.find_next('h5', string = re.compile(alternateForm.title())).next_sibling.next_sibling

    if regionalForm:
      statTable = statTable.find_next('h5', string = re.compile(regionalForm.title())).next_sibling.next_sibling
    
    if statTable.next_sibling.next_sibling.name == 'h6':
      statTable = statTable.next_sibling.next_sibling
        
  if statTable.name == 'h6':
    if 'Generation' in statTable.span.string:
      genChange = statTable.span.string.split(' ')[-1].lower()
      if '-' in genChange:
        genChange = genChange.split('-')[-1]
      if genMap[genChange] < genMap[gen]:
        statTable = statTable.find_next('h6').find_next('table')
      else:
        statTable = statTable.find_next('table')
  
  elif statTable.name != 'table':
    statTable = statTable.find_next('table')

if genMap[gen] == 1:
  stats['hp'] = statTable.find('span', string = 'HP').parent.parent.next_sibling.string
  stats['atk'] = statTable.find('span', string = 'Attack').parent.parent.next_sibling.string
  stats['def'] = statTable.find('span', string = 'Defense').parent.parent.next_sibling.string
  stats['spc'] = statTable.find('a', title = 'Generation I').find_next('b').string
  stats['spe'] = statTable.find('span', string = 'Speed').parent.parent.next_sibling.string
else:
  stats['hp'] = statTable.find('span', string = 'HP').parent.parent.next_sibling.string
  stats['atk'] = statTable.find('span', string = 'Attack').parent.parent.next_sibling.string
  stats['def'] = statTable.find('span', string = 'Defense').parent.parent.next_sibling.string
  stats['spa'] = statTable.find('span', string = 'Sp. Atk').parent.parent.next_sibling.string
  stats['spd'] = statTable.find('span', string = 'Sp. Def').parent.parent.next_sibling.string
  stats['spe'] = statTable.find('span', string = 'Speed').parent.parent.next_sibling.string

output['stats'] = stats

###############################
# ABILITIES

if genMap[gen] >= 3:
  abilityTable = soup.find('a', title = 'Ability').parent.parent.find_next('table')
  abilities = []
  for i, ability in enumerate(abilityTable.tbody.tr.td.find_all('a', limit = 2)):
    abilities.append({
      'name': ability.string.lower(),
      'slot': i + 1,
      'hidden': False,
    })

  sup = abilityTable.find('sup')
  if sup:
    abilityGen = sup.a.string.split(' ')[-1].replace('+', '').lower()
    if genMap[abilityGen] > genMap[gen]:
      abilities.pop()

  if genMap[gen] >= 5:
    hiddenAbility = abilityTable.find_all(string = re.compile('Hidden Ability'))
    # if len(hiddenAbility) > 1:
      
    hiddenAbility = hiddenAbility[0]
    if hiddenAbility:
      if 'Gen' in hiddenAbility:
        abilityGen = hiddenAbility.split(' ')[hiddenAbility.split(' ').index('Gen') + 1].replace('+', '').lower()
        if genMap[abilityGen] <= genMap[gen]:
          abilities.append({
            'name': hiddenAbility.parent.parent.a.string.lower(),
            'slot': 3,
            'hidden': True,
          })
      else:
        abilities.append({
          'name': hiddenAbility.parent.parent.a.string.lower(),
          'slot': 3,
          'hidden': True,
        })

  output['abilities'] = abilities


###############################
print(output)