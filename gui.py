import pygame
import pygame_gui
from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_button import UIButton
from pygame_gui.elements.ui_panel import UIPanel 
from forestry import Inventory, Game, Slot
import time

def check_slot_empty(s):
    return '' if s == 'Slot empty' else s

class InventoryWindow(UIWindow):
    def __init__(self, inv, button_hor, button_vert, rect, manager, *args, margin=5, **kwargs):
        self.button_hor = button_hor
        self.button_vert = button_vert
        self.margin = margin
        self.cursor = None
        self.inv = inv
        self.manager = manager
        
        super().__init__(rect, manager, *args, **kwargs)
        if len(inv) != button_hor * button_vert:
            raise ValueError(
                'Inventory should have button_hor*button_vert number of slots')
    
    def set_cursor(self, c):
        self.cursor = c
    
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
                        if self.cursor is not None:
                            index = i * self.button_hor + j
                            inv_bee = self.inv[index].take()
                            cur_bee = self.cursor.slot.take()
                            self.cursor.slot.put(inv_bee)
                            self.inv[index].put(cur_bee)
                            b.set_text(check_slot_empty(self.inv[index].small_str()))
                            self.cursor.set_text_slot()
                            print(inv_bee, i, j)
                            return True
                        else:
                            raise RuntimeError('You must set cursor first')
        elif event.type == pygame.MOUSEMOTION:
            pass
        if not should_consume:
            return super().process_event(event)

class Cursor(UIButton):
    def __init__(self, *args, **kwargs):
        self.slot = Slot()
        super().__init__(*args, **kwargs)
        #self.disable()
        
    def enable(self):
        pass
    
    def process_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.rect.topleft = event.pos
        return super().process_event(event)
        
    def set_text_slot(self):
        self.set_text(check_slot_empty(self.slot.small_str()))
        self.rect.topleft = pygame.mouse.get_pos()

class TransparentUIPanel(UIPanel):
    def process_event(self, event):
        return False
        
class GUI(Game):
    def render(self):
        pass

    def print(self, *args, **kwargs):
        print(*args, **kwargs)
        
def main():
    try:
        pygame.init()

        pygame.display.set_caption('Bee Breeding Game')
        window_surface = pygame.display.set_mode((800, 600))

        background = pygame.Surface((800, 600))
        background.fill(pygame.Color('#000000'))

        manager = pygame_gui.UIManager((800, 600))
        cursor_manager = pygame_gui.UIManager((800, 600))

        game = GUI()
        for i in range(9):
            game.forage()
        inv_window = InventoryWindow(game.inv, 10, 10,
            pygame.Rect(0, 0, 800, 600), manager, 'Inventory', resizable=True)
        cursor = Cursor(pygame.Rect(0, 0, -1, -1), '', cursor_manager)
        inv_window.set_cursor(cursor)
        
        clock = pygame.time.Clock()
        is_running = True
        visual_debug = False
        while is_running:
            time_delta = clock.tick(60)/1000.0
            # state = game.get_state()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    is_running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        visual_debug = not visual_debug
                        manager.set_visual_debug_mode(visual_debug)
                manager.process_events(event)
                cursor_manager.process_events(event)

            manager.update(time_delta)
            cursor_manager.update(time_delta)

            window_surface.blit(background, (0, 0))
            manager.draw_ui(window_surface)
            cursor_manager.draw_ui(window_surface)

            pygame.display.update()
    finally:
        game.exit()


if __name__ == '__main__':
    main()