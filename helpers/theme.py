import json

from config import BeeSpecies
from forestry import ApiaryProblems

tool_tip_delay = '0.4'
theme = {
    '#TooltipDelay': {
        'misc':{
            'tool_tip_delay': tool_tip_delay
        }
    },
    '#BeeButton':{
        'prototype': f'#TooltipDelay'
    },
    '@Centered':{
        'misc': {
            'text_horiz_alignment': 'center'
        }
    },
    'label': {
        'misc': {
            'text_horiz_alignment': 'left'
        }
    },
    '#restart_label': {
        'colours': {
            'normal_text': '#ec3661'
        }
    },
    '#checkbox': {
        'misc': {
            "text_horiz_alignment_padding": "0"
        }
    },
    '#unpinned':{
        'images':{
            'normal_image':{
                'path': 'assets/pin.png'
            }
        }
    },
    '#pinned':{
        'prototype': '#unpinned',
        'colours':{
            'normal_bg': '#686c9c',
            'hovered_bg': '#686c9c'
        }
    },
    '#InspectedStatus':{
        'colours':{
            'filled_bar': '#73D444',
            'unfilled_bar': '#777777'
        }
    },
    '#MendelianTutorialProgressBar':{
        'colours':{
            'filled_bar': '#73A444',
            'unfilled_bar': '#777777'
        }
    },
    '#PrincessEmpty':{
        'images':{
            'normal_image':{
                'path': 'assets/black_princess.png'
            }
        }
    },
    '#DroneEmpty':{
        'images':{
            'normal_image':{
                'path': 'assets/black_drone.png'
            }
        }
    },
    '#WinWindow.text_box':{
        'misc':{
            'text_horiz_alignment': 'center',
            'text_vert_alignment': 'center'
        }
    },
    '#mating_history_right_arrow_button':{
        'images':{
            'normal_image':{
                'path': 'assets/mating_history_right_arrow.png'
            }
        }
    },
    '#mating_history_plus_button':{
        'images':{
            'normal_image':{
                'path': 'assets/mating_history_plus.png'
            }
        }
    }
}

for problem in ApiaryProblems:
    theme.update({
        f'#Apiary_problem_'+problem.name: {
            'prototype': '#TooltipDelay',
            'images': {
                'normal_image': {
                    'path': f'assets/Apiary_problem_{problem.name}.png'
                }
            }
        }
    })

for species in BeeSpecies:
    for gender in ['Princess', 'Drone', 'Queen']:
        theme.update(
            {f'#{species.name}_{gender}': {
                'prototype': f'#BeeButton',
                'images':{
                    'normal_image': {
                        'path': f'assets/{species.name}_{gender}.png'
                    }
                }
            }})
        theme.update(
            {f'#{species.name}_{gender}_highlighted': {
                'prototype': f'#BeeButton',
                'colours': {
                    'normal_bg': '#686c6c',
                    'hovered_bg': '#686c6c',
                },
                'images':{
                    'normal_image': {
                        'path': f'assets/{species.name}_{gender}.png'
                    }
                }
            }})
print(json.dumps(theme, indent=2))
with open('theme.json', 'w') as f:
    json.dump(theme, f, indent=2)