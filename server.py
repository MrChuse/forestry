from aiohttp import web

import pickle
import threading
import time

from forestry import *

PORT = 8081

class WebInterface:
    def __init__(self):
        self.exit_event = threading.Event()
        self.render_event = threading.Event()
        self.render_event.set()
        
        self.out = {'text': ''}
        self.command_out = {'text': ''}
        self.text_memory = []
        self.text_counter = -1
        # self.button_left = widgets.Button(
        #     icon='arrow-left'
        # )
        # self.button_right = widgets.Button(
        #     icon='arrow-right'
        # )
        # self.button_left.on_click(self.text_previous)
        # self.button_right.on_click(self.text_next)
        # self.console = widgets.HBox([self.text, self.button_left, self.button_right])
        # display(widgets.VBox([self.out, self.command_out, self.console]))
        
        self.resources = Resources(honey=0)
        self.inv = Inventory(100)
        self.apiaries = [Apiary(self.resources.add_resources)]
        
        self.to_render = [self.resources, self.inv, self.apiaries[0]]
        
        self.print_buffer = []
        self.print_buffer_size = 0
        
        # self.print(type(self.inv[0]), out=self.command_out, flush=True)
        
        self.inner_state_thread = threading.Thread(target=self.update_state)
        self.inner_state_thread.start()
        self.render_thread = threading.Thread(target=self.render)
        self.render_thread.start()
        
    def print(self, *strings, sep=' ', end='\n', flush=False, out=None):
        if out is None:
            out = self.out
        thing = sep.join(map(str, strings)) + end
        
        self.print_buffer.append(thing)
        self.print_buffer_size += len(thing)
        if flush:
            out['text'] = ''.join(self.print_buffer)
            self.print_buffer = []
            self.print_buffer_size = 0
        
    def render(self):
        while True:
            if self.exit_event.is_set():
                self.print(flush=True)
                break
                
            # self.print(self.to_render, out=self.command_out, flush=True)
            
            if len(self.to_render) == 0:
                self.print(flush=True)
                continue
                
            if self.render_event.is_set():
                for thing in self.to_render[:-1]:
                    self.print(thing)
                self.print(self.to_render[-1], flush=True)
                self.render_event.clear()
        
    def execute_command(self, value):
        command, *params = value.split()
        if command in ['exit', 'q']: # tested
            self.exit_event.set()
            self.print('Exiting...')
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

    def text_next(self, b):
        self.text_counter = min(self.text_counter + 1, len(self.text_memory))
        if self.text_counter == len(self.text_memory):
            self.text.value = ''
        else:
            self.text.value = self.text_memory[self.text_counter]
    
    def text_previous(self, b):
        self.text_counter = max(self.text_counter - 1, 0)
        if self.text_counter != 0 or len(self.text_memory) != 0:
            self.text.value = self.text_memory[self.text_counter]
        
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
                'out.outputs' : self.out.outputs,
                'command_out.outputs' : self.command_out.outputs,
                'text_memory' : self.text_memory,
                'text_counter' : self.text_counter,
                'resources' : self.resources,
                'inv' : self.inv,
                'apiaries' : self.apiaries,
                'to_render' : self.to_render
            }
            pickle.dump(state, f)
            
    def load(self, filename):
        with open(filename+'.forestry', 'rb') as f:
            saved = pickle.load(f)
        self.out.outputs = saved['out.outputs']
        self.command_out.outputs = saved['command_out.outputs']
        self.text_memory = saved['text_memory']
        self.text_counter = saved['text_counter']
        self.resources = saved['resources']
        self.inv = saved['inv']
        self.apiaries = saved['apiaries']
        self.to_render = saved['to_render']        
                

async def out(request):
    return web.json_response(web_interface.out)

async def command_out(request):
    return web.json_response(web_interface.command_out)

async def command(request):
    if web_interface.exit_event.is_set():
        return
    value = await request.text()
    print('value:', value)
    web_interface.print(value, out=web_interface.command_out, flush=True)
    web_interface.execute_command(value)
    return web.Response(text='Success')


@web.middleware
async def cors_middleware(request, handler):
    response = await handler(request)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


try:
    web_interface = WebInterface()
    app = web.Application(middlewares=[cors_middleware])
    app.add_routes([
        web.get('/out', out),
        web.get('/command_out', command_out),
        web.post('/command', command)
    ])
    web.run_app(app, port=PORT)
finally:
    web_interface.execute_command('q')