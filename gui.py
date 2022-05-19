import pygame
import pygame_gui
from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_button import UIButton
from forestry import Inventory, Game, Slot
import time

def check_slot_empty(s):
    return '' if s == 'Slot empty' else s
    
class InventoryWindow(UIWindow):
    def __init__(self, inv, button_hor, button_vert, rect, manager, *args, margin=5, **kwargs):
        self.button_hor = button_hor
        self.button_vert = button_vert
        self.margin = margin
        self.inv = inv
        self.manager = manager
        
        super().__init__(rect, manager, *args, **kwargs)
        if len(inv) != button_hor * button_vert:
            raise ValueError(
                'Inventory should have button_hor*button_vert number of slots')

    def on_close_window_button_pressed(self):
        pass

    def create_buttons_if_needed(self):
        try:
            self.buttons
        except AttributeError:
            self.buttons = []
            for j in range(self.button_hor):
                self.buttons.append([])
                for i in range(self.button_vert):
                    rect = pygame.Rect(0, 0, 100, 100)
                    self.buttons[j].append(UIButton(rect, check_slot_empty(self.inv[i * self.button_hor + j].small_str()), self.manager, self,))
    
    def place_buttons(self, size):
        self.create_buttons_if_needed()
        hor_margin_size = (self.button_hor + 1) * self.margin
        vert_margin_size = (self.button_vert + 1) * self.margin
        remaining_width = size[0] - hor_margin_size - 30  # why 30 & 60!?
        remaining_height = size[1] - vert_margin_size - 60
        hor_size = remaining_width / self.button_hor
        vert_size = remaining_height / self.button_vert
        size = (hor_size, vert_size)
        for i, row in enumerate(self.buttons):
            for j, b in enumerate(row):
                pos = (self.margin + i * (hor_size + self.margin), self.margin + j * (vert_size + self.margin))
                b.relative_rect.topleft = pos
                b.rect.size = size
                b.rebuild()
    
    def set_dimensions(self, size):
        super().set_dimensions(size)
        self.place_buttons(size)
    
    def process_event(self, event):
        # print(event, time.time())
        should_consume = False
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            for j, row in enumerate(self.buttons):
                for i, b in enumerate(row):
                    if event.ui_element == b:
                        index = i * self.button_hor + j
                        bee = self.inv.take(index)
                        b.set_text(check_slot_empty(self.inv[index].small_str()))
                        print(bee, i, j)
                        return True
        elif event.type == pygame.MOUSEMOTION:
            pass
        if not should_consume:
            return super().process_event(event)


class GUI(Game):
    def render(self):
        pass

    def print(self, *args, **kwargs):
        print(*args, **kwargs)

class MyWindow(UIWindow):
    def __init__(self, *args, **kwargs):
        self.manager = args[1]
        super().__init__(*args, **kwargs)
        
    def place_buttons(self, size):
        print(time.time())
        try:
            self.b
        except AttributeError:
            self.b = pygame_gui.elements.UIButton(pygame.Rect((350, 275), (100, 50)),
                                             text='Say Hello',
                                             manager=self.manager,
                                             container=self)
        else:
            rect = pygame.Rect((0, 0), (50, 100))
            print(self.b.relative_rect)
            self.b.relative_rect = rect
            self.b.rebuild()
    def set_dimensions(self, size):
        super().set_dimensions(size)
        self.place_buttons(size)
        
def main():
    try:
        pygame.init()

        pygame.display.set_caption('Bee Breeding Game')
        window_surface = pygame.display.set_mode((800, 600))

        background = pygame.Surface((800, 600))
        background.fill(pygame.Color('#000000'))

        manager = pygame_gui.UIManager((800, 600))

        game = GUI()
        for i in range(9):
            game.forage()
        inv_window = InventoryWindow(game.inv, 10, 10, pygame.Rect(
            0, 0, 800, 600), manager, 'Inventory', resizable=True)
        # w = MyWindow(pygame.Rect((0, 0), (800, 600)), manager, resizable=True)
        
        clock = pygame.time.Clock()
        is_running = True
        while is_running:
            time_delta = clock.tick(60)/1000.0
            # state = game.get_state()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    is_running = False

                manager.process_events(event)

            manager.update(time_delta)

            window_surface.blit(background, (0, 0))
            manager.draw_ui(window_surface)

            pygame.display.update()
    finally:
        game.exit()


if __name__ == '__main__':
    main()