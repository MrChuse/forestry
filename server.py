import pickle
import threading
import time

from aiohttp import web

from forestry import *

PORT = 8081


class WebInterface(Game):
    def __init__(self):
        self.out = {'text': ''}
        self.command_out = {'text': ''}
        self.text_memory = []
        self.text_counter = -1

        self.print_buffer = []
        self.print_buffer_size = 0

        super().__init__()

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

            if len(self.to_render) == 0:
                self.print(flush=True)
                continue

            if self.render_event.is_set():
                if self.render_help.is_set():
                    self.print(self.help_text, flush=True)
                else:
                    for thing in self.to_render[:-1]:
                        self.print(thing)
                    self.print(self.to_render[-1], flush=True)
                    self.render_event.clear()


async def game(request):
    return web.FileResponse('my-app/build/index.html')


async def out(request):
    return web.json_response(web_interface.out)


async def command_out(request):
    return web.json_response(web_interface.command_out)


async def command(request):
    if web_interface.exit_event.is_set():
        return
    value = await request.text()
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
        web.get('/game', game),
        web.static('/game', 'my-app/build'),
        web.get('/out', out),
        web.get('/command_out', command_out),
        web.post('/command', command)
    ])
    web.run_app(app, port=PORT)
finally:
    web_interface.execute_command('q')