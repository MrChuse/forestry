import time
import math

import pygame
import pygame_gui
from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_button import UIButton
from pygame_gui.elements.ui_panel import UIPanel

from forestry import Slot, Inventory, Apiary, Game


class UIWindowNoX(UIWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enable_close_button = False
        self.title_bar_close_button_width = 0
        self.rebuild()

class Cursor(UIButton):
    def __init__(self, *args, **kwargs):
        self.slot = Slot()
        super().__init__(*args, **kwargs)
        
    def enable(self):
        pass
    
    def process_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.rect.topleft = event.pos
        return super().process_event(event)
        
    def set_text_slot(self):
        self.set_text(self.slot.small_str())
        self.rect.topleft = pygame.mouse.get_pos()

class InventoryWindow(UIWindowNoX):
    def __init__(self, inv, button_hor, button_vert,  cursor: Cursor, rect, manager, *args, margin=5, **kwargs):
        self.button_hor = button_hor
        self.button_vert = button_vert
        self.margin = margin
        self.cursor = cursor
        self.inv = inv
        self.manager = manager
        
        super().__init__(rect, manager, *args, **kwargs)
        if len(inv) != button_hor * button_vert:
            raise ValueError(
                'Inventory should have button_hor*button_vert number of slots')
        
    def create_buttons_if_needed(self):
        try:
            self.buttons
        except AttributeError:
            self.buttons = []
            for j in range(self.button_hor):
                self.buttons.append([])
                for i in range(self.button_vert):
                    rect = pygame.Rect(0, 0, 100, 100)
                    self.buttons[j].append(UIButton(rect, self.inv[i * self.button_hor + j].small_str(), self.manager, self,))
    
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
                        self.cursor.slot.swap(self.inv[index])
                        b.set_text(self.inv[index].small_str())
                        self.cursor.set_text_slot()
                        print(self.cursor.slot, i, j)
                        return True
        elif event.type == pygame.MOUSEMOTION:
            pass
        if not should_consume:
            return super().process_event(event)

class ApiaryWindow(UIWindow):
    def __init__(self, apiary: Apiary, cursor: Cursor, manager, *args, **kwargs):
        self.apiary = apiary
        self.cursor = cursor
        self.initial_position = (0, 0)
        self.size = (300, 400)
        super().__init__(pygame.Rect(self.initial_position, self.size), manager, *args, **kwargs)

        self.button_size = (60, 60)
        self.top_margin2 = 15
        self.side_margin2 = 63
        self.princess_button = UIButton(pygame.Rect((self.side_margin2, self.top_margin2), self.button_size), self.apiary.princess.small_str(), manager, self)
        drone_rect = pygame.Rect((0, 0), self.button_size)
        drone_rect.topright = (-self.side_margin2, self.top_margin2)
        self.drone_button = UIButton(drone_rect,
                                     text='', manager=manager,
                                     container=self,
                                     anchors={'left': 'right',
                                              'right': 'right',
                                              'top': 'top',
                                              'bottom': 'top'})
        self.margin3 = (self.size[0] - 32 - 3 * self.button_size[0]) / 4
        radius = self.margin3 + self.button_size[0]
        center_rect = pygame.Rect((0, 0), self.button_size)
        center_rect.center = (self.size[0]/2 - 32/2, self.size[1]/2 + 15) # 30
        self.buttons = [UIButton(center_rect, '', manager, self)]
        for i in range(6):
            angle = 2 * math.pi / 6 * i
            dx = radius * math.cos(angle)
            dy = radius * math.sin(angle)

            rect = center_rect.copy()
            rect.x += dx
            rect.y += dy
            self.buttons.append(UIButton(rect, '', manager, self))
    
    def set_button_texts(self):
        self.princess_button.set_text(self.apiary.princess.small_str())
        self.drone_button.set_text(self.apiary.drone.small_str())
        for b, slot in zip(self.buttons, self.apiary.inv):
            b.set_text(slot.small_str())
    
    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            try:
                if event.ui_element == self.princess_button:
                    print('put princess')
                    self.apiary.put_princess(self.cursor.slot.slot)
                    self.cursor.slot.take()
                    # self.cursor.slot.swap(self.apiary.princess)
                elif event.ui_element == self.drone_button:
                    print('put drone')
                    self.apiary.put_drone(self.cursor.slot.slot)
                    self.cursor.slot.take()
                    # self.cursor.slot.swap(self.apiary.drone)
            except TypeError as e:
                print(e)
            for b, slot in zip(self.buttons, self.apiary.inv):
                if event.ui_element == b:
                    if self.cursor.slot.is_empty():
                        self.cursor.slot.swap(slot)
                    else:
                        print('Cursor not empty')
            self.set_button_texts()
            self.cursor.set_text_slot()
        return super().process_event(event)
    
    def update_apiary(self, apiary):
        self.apiary = apiary
        self.set_button_texts()

        
class GUI(Game):
    def render(self):
        pass

    def print(self, *args, **kwargs):
        print(*args, **kwargs)
        
def main():
    try:
        pygame.init()

        pygame.display.set_caption('Bee Breeding Game')
        
        window_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        window_size = window_surface.get_rect().size

        background = pygame.Surface(window_size)
        background.fill(pygame.Color('#000000'))

        manager = pygame_gui.UIManager(window_size)
        cursor_manager = pygame_gui.UIManager(window_size)

        Slot.empty_str = ''
        game = GUI()
        for i in range(9):
            game.forage()
        cursor = Cursor(pygame.Rect(0, 0, -1, -1), '', cursor_manager)
        inv_window = InventoryWindow(game.inv, 10, 10, cursor,
            pygame.Rect((0, 0), window_size), manager, 'Inventory', resizable=True)
        api_window = ApiaryWindow(game.apiaries[0], cursor,
            manager, "Apiary " + game.apiaries[0].name)
        clock = pygame.time.Clock()
        is_running = True
        visual_debug = False
        while is_running:
            time_delta = clock.tick(60)/1000.0
            state = game.get_state()
            api_window.update_apiary(state['apiaries'][0])

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
    # except Exception as e:
    #     print(type(e), e)
    finally:
        game.exit()


if __name__ == '__main__':
    main()