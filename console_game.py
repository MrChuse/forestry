from dataclasses import dataclass
import threading
from typing import List, Callable

from forestry import Game, except_print


@dataclass
class Command:
    names: List[str]
    action: Callable
    desc: str
    short_desc: str = ''

class ConsoleGame(Game):
    def __init__(self) -> None:
        super().__init__()
        self.to_render = [self.resources, self.inv, self.apiaries[0]]

        self.manual = self.parse_manual()
        self.current_manual_page = 0

        desc = self.parse_command_description()
        self.commands = [
            Command(['exit', 'q'], self.exit, *desc['exit']),
            Command(['help', 'h'], self.help, *desc['help']),
            Command(['manual'], lambda : self.execute_command('help manual'), *desc['manual']),
            Command(['save'], self.save, *desc['save']),
            Command(['load'], self.load, *desc['load']),
            Command(['show', 's'], self.show, *desc['show']),
            Command(
                ['unshow', 'uns', 'us', 'u'],
                lambda : self.to_render.pop(),
                *desc['unshow'],
            ),
            Command(['put'], self.put, *desc['put']),
            Command(['take'], self.take, *desc['take']),
            Command(['reput'], self.reput, *desc['reput']),
            Command(['throw'], self.throw, *desc['throw']),
            Command(['swap'], self.swap, *desc['swap']),
            Command(['sort'], self.inv.sort, *desc['sort']),
            Command(['forage'], self.forage, *desc['forage']),
            Command(['inspect'], self.inspect, *desc['inspect']),
            Command(['build', 'b'], self.build, *desc['build']),
        ]

        self.commands_actions = {
            name: command.action for command in self.commands for name in command.names
        }

        self.show_manual()

        self.render_help = threading.Event()
        self.render_help.set()
        self.render_event = threading.Event()
        self.render_event.set()

        
        self.render_thread = threading.Thread(target=self.render)
        self.render_thread.start()

    def render_frame(self):
        if self.render_event.is_set():
            if self.render_help.is_set():
                self.print(self.help_text, flush=True)
            else:
                if len(self.to_render) == 0:
                    self.print(flush=True)
                    self.render_event.clear()
                    return
                for thing in self.to_render[:-1]:
                    self.print(thing)
                    self.print()
                self.print(self.to_render[-1], flush=True)
            self.render_event.clear()

    def state_updated(self):
        self.render_event.set()

    @staticmethod
    def parse_manual():
        with open('manual.txt') as f:
            manual = f.read().split('===\n')
        return manual

    @staticmethod
    def parse_command_description():
        with open('command_description.txt') as f:
            raw_desc = f.read().split('===\n')
            desc_list = [desc.split(';;;\n') for desc in raw_desc]
            desc = {desc[0][:-1]: desc[1:] for desc in desc_list}
        return desc
    
    @except_print(KeyError)
    def get_command(self, command):
        return self.commands_actions[command]

    def execute_command(self, value):
        command, *params = value.split()
        f = self.get_command(command)
        f(*params)
        self.render_event.set()
    
    def show_manual(self):
        self.help_text = self.manual[self.current_manual_page]
        self.help_text += f'\n{self.current_manual_page}/{len(self.manual)}'
    
    def help(self, *params):
        if len(params) == 0:
            l = []
            for command in self.commands:
                if command.short_desc == '':
                    desc = command.desc
                else:
                    desc = command.short_desc
                l.append(command.names[0] + ': ' + desc)
            self.help_text = ''.join(l)
            self.render_help.set()

        elif params[0] == 'prev':
            self.current_manual_page = max(self.current_manual_page - 1, 0)
            self.show_manual()
        elif params[0] == 'next':
            self.current_manual_page = min(
                self.current_manual_page + 1, len(self.manual)
            )
            self.show_manual()
        elif params[0] == 'go':
            page = int(params[1])
            self.current_manual_page = min(len(self.manual), max(page, 0))
            self.show_manual()
        elif params[0] == 'close':
            self.render_help.clear()
        elif params[0] == 'manual':
            self.show_manual()
            self.render_help.set()
        else:
            # try to find the command in list of commands
            for command in self.commands:
                if params[0] in command.names:
                    self.help_text = command.desc
                    self.render_help.set()

    def show(self, *params):  # probably tested
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
    
    def get_state(self):
        state = super().get_state()
        state['to_render'] =  self.to_render
        return state
    
    def load(self, name):
        saved = super().load(name)
        self.to_render = saved['to_render']
        return saved