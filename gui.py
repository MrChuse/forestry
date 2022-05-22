import math
import time

import pygame
import pygame_gui
from pygame_gui.elements import (UIButton, UIPanel, UIProgressBar, UIStatusBar,
                                 UITextBox, UIWindow, UIDropDownMenu)
from pygame_gui.elements.ui_drop_down_menu import UIExpandedDropDownState

from forestry import Apiary, Game, Inventory, Queen, Resources, Slot


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
    
    def set_text_slot(self):
        self.set_text(self.slot.small_str())
        self.rect.topleft = pygame.mouse.get_pos()

    def update(self, time_delta: float):
        self.set_text_slot()
        return super().update(time_delta)

class InventoryWindow(UIWindowNoX):
    def __init__(self, inv, button_hor, button_vert,  cursor: Cursor, rect, manager, *args, margin=5, **kwargs):
        self.button_hor = button_hor
        self.button_vert = button_vert
        self.margin = margin
        self.cursor = cursor
        self.inv = inv
        if len(inv) != button_hor * button_vert:
            raise ValueError(
                'Inventory should have button_hor*button_vert number of slots')
        
        self.title_bar_sort_button_width = 100
        super().__init__(rect, manager, *args, **kwargs)
        self.title_bar.set_dimensions((self._window_root_container.relative_rect.width -
                                        self.title_bar_sort_button_width,
                                        self.title_bar_height))
    
    def rebuild(self):
        sort_rect = pygame.Rect((-self.title_bar_sort_button_width, 0),
                                (self.title_bar_sort_button_width,
                                self.title_bar_height))
        self.sort_window_button = UIButton(relative_rect=sort_rect,
                                            text='Sort',
                                            manager=self.ui_manager,
                                            container=self._window_root_container,
                                            parent_element=self,
                                            object_id='#close_button',
                                            anchors={'top': 'top',
                                                     'bottom': 'top',
                                                     'left': 'right',
                                                     'right': 'right'}
                                            )
        super().rebuild()
        
    def create_buttons_if_needed(self):
        try:
            self.buttons
        except AttributeError:
            self.buttons = []
            for j in range(self.button_hor):
                self.buttons.append([])
                for i in range(self.button_vert):
                    rect = pygame.Rect(0, 0, 100, 100)
                    self.buttons[j].append(UIButton(rect, self.inv[i * self.button_hor + j].small_str(), self.ui_manager, self,))
    
    def place_buttons(self, size):
        self.create_buttons_if_needed()
        hor_margin_size = (self.button_hor + 1) * self.margin
        vert_margin_size = (self.button_vert + 1) * self.margin
        remaining_width = size[0] - hor_margin_size - 32  # why 32 & 64!?
        remaining_height = size[1] - vert_margin_size - 64
        hor_size = remaining_width / self.button_hor
        vert_size = remaining_height / self.button_vert
        bsize = (hor_size, vert_size)
        for i, row in enumerate(self.buttons):
            for j, b in enumerate(row):
                pos = (self.margin + i * (hor_size + self.margin), self.margin + j * (vert_size + self.margin))
                b.relative_rect.topleft = pos
                b.rect.size = bsize
                b.rebuild()
    
    def set_dimensions(self, size):
        self.place_buttons(size)
        super().set_dimensions(size)
    
    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.sort_window_button:
                self.inv.sort()
            for j, row in enumerate(self.buttons):
                for i, b in enumerate(row):
                    if event.ui_element == b:
                        index = i * self.button_hor + j
                        self.cursor.slot.swap(self.inv[index])
                        return True
        return super().process_event(event)
    
    def update(self, time_delta: float):
        for j, row in enumerate(self.buttons):
            for i, b in enumerate(row):
                index = i * self.button_hor + j
                b.set_text(self.inv[index].small_str())
        return super().update(time_delta)

class UIRelativeStatusBar(UIStatusBar):
    def rebuild(self):
        """
        Rebuild the status bar entirely because the theming data has changed.

        """
        # self.rect.x, self.rect.y = self.position

        self.border_rect = pygame.Rect((self.shadow_width, self.shadow_width),
                                       (self.rect.width - (self.shadow_width * 2),
                                        self.rect.height - (self.shadow_width * 2)))

        self.capacity_width = self.rect.width - (self.shadow_width * 2) - (self.border_width * 2)
        self.capacity_height = self.rect.height - (self.shadow_width * 2) - (self.border_width * 2)
        self.capacity_rect = pygame.Rect((self.border_width + self.shadow_width,
                                          self.border_width + self.shadow_width),
                                         (self.capacity_width, self.capacity_height))

        self.redraw()
    
    def update(self, time_delta: float):
        """
        Updates the status bar sprite's image and rectangle with the latest status and position
        data from the sprite we are monitoring

        :param time_delta: time passed in seconds between one call to this method and the next.

        """
        super(UIStatusBar, self).update(time_delta)
        if self.alive():
            # self.rect.x, self.rect.y = self.position
            # self.relative_rect.topleft = self.rect.topleft

            # If they've provided a method to call, we'll track previous value in percent_full.
            if self.percent_method:
                # This triggers status_changed if necessary.
                self.percent_full = self.percent_method()

            if self.status_changed:
                self.status_changed = False
                self.redraw()

class ApiaryWindow(UIWindow):
    initial_position = (0, 0)
    def __init__(self, apiary: Apiary, cursor: Cursor, manager, *args, **kwargs):
        self.apiary = apiary
        self.cursor = cursor
        self.size = (300, 400)
        super().__init__(pygame.Rect(self.initial_position, self.size), manager, "Apiary " + apiary.name, *args, **kwargs)

        self.button_size = (60, 60)
        self.top_margin2 = 15
        self.side_margin2 = 63
        self.princess_button = UIButton(pygame.Rect((self.side_margin2, self.top_margin2), self.button_size),
            self.apiary.princess.small_str(), manager, self)
        drone_rect = pygame.Rect((0, 0), self.button_size)
        drone_rect.topright = (-self.side_margin2, self.top_margin2)
        self.drone_button = UIButton(drone_rect,
                                     text='', manager=manager,
                                     container=self,
                                     anchors={'left': 'right',
                                              'right': 'right',
                                              'top': 'top',
                                              'bottom': 'top'})

        queen_health_rect = pygame.Rect(0, self.princess_button.relative_rect.bottom + 14, self.size[0] - self.side_margin2 * 2, 10)
        queen_health_rect.centerx = self.size[0] / 2 - 16
        self.queen_health = UIRelativeStatusBar(queen_health_rect, manager, container=self)
        self.queen_health.percent_full = 0

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
    
    def update_health_bar(self):
        bee = self.apiary.princess.slot
        if isinstance(bee, Queen):
            self.queen_health.percent_full = bee.remaining_lifespan / bee.lifespan
        else:
            self.queen_health.percent_full = 0
    
    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.princess_button:
                if self.cursor.slot.is_empty():
                    self.cursor.slot.put(self.apiary.take_princess())
                else:
                    bee1 = self.apiary.take_princess()
                    try:
                        self.apiary.put_princess(self.cursor.slot.slot)
                    except TypeError as e:
                        self.apiary.put_princess(bee1)
                        raise e
                    else:
                        self.cursor.slot.take()
                        self.cursor.slot.put(bee1)
            elif event.ui_element == self.drone_button:
                if self.cursor.slot.is_empty():
                    self.cursor.slot.put(self.apiary.take_drone())
                else:
                    bee1 = self.apiary.take_drone()
                    try:
                        self.apiary.put_drone(self.cursor.slot.slot)
                    except TypeError:
                        self.apiary.put_drone(bee1)
                    else:
                        self.cursor.slot.take()
                        self.cursor.slot.put(bee1)
            for index, b in enumerate(self.buttons):
                if event.ui_element == b:
                    if self.cursor.slot.is_empty():
                        self.cursor.slot.put(self.apiary.take(index))
                    else:
                        print('Cursor not empty')
        return super().process_event(event)
    
    def update(self, time_delta):
        self.set_button_texts()
        self.update_health_bar()
        super().update(time_delta)

class UINonChangingExpandedDropDownState(UIExpandedDropDownState):
    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element in self.active_buttons:
            self.should_transition = True

        if (event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION and
                event.ui_element == self.options_selection_list):
            self.should_transition = True

            event_data = {'text': self.options_selection_list.get_single_selection(),
                          'ui_element': self.drop_down_menu_ui,
                          'ui_object_id': self.drop_down_menu_ui.most_specific_combined_id}
            pygame.event.post(pygame.event.Event(pygame_gui.UI_DROP_DOWN_MENU_CHANGED, event_data))

        return False  # don't consume any events

class UINonChangingDropDownMenu(UIDropDownMenu):
    def __init__(self, options_list, starting_option: str, relative_rect: pygame.Rect, manager, container=None, parent_element=None, object_id=None, expansion_height_limit=None, anchors=None, visible: int = 1):
        super().__init__(options_list, starting_option, relative_rect, manager, container, parent_element, object_id, expansion_height_limit, anchors, visible)
        self.menu_states['expanded'] = UINonChangingExpandedDropDownState(
            self,
            self.options_list,
            self.selected_option,
            self.background_rect,
            self.open_button_width,
            self.expand_direction,
            self.ui_manager,
            self,
            self.element_ids,
            self.object_ids
        )

class InspectPanel(UIPanel):
    def __init__(self, cursor, rect, starting_layer_height, manager, *args, **kwargs):
        self.cursor = cursor
        super().__init__(rect, starting_layer_height, manager, *args, **kwargs)
        inspect_button_height = 60
        self.inspect_button = UIButton(pygame.Rect(0, 0, rect.width - inspect_button_height, inspect_button_height), 'Inspect', manager, self)
        bee_button_rect = pygame.Rect(0, 0, inspect_button_height, inspect_button_height)
        bee_button_rect.right = 0
        self.bee_button = UIButton(bee_button_rect, '', manager, self,
            anchors={
                'top':'top',
                'bottom':'bottom',
                'left':'right',
                'right':'right',
            })
        self.slot = Slot()
        self.text_box = UITextBox('', pygame.Rect(0, inspect_button_height, rect.width-6, rect.height-inspect_button_height-6), manager, container=self)
    
    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.bee_button:
                print('swap')
                self.cursor.slot.swap(self.slot)
                self.bee_button.set_text(self.slot.small_str())
                self.cursor.set_text_slot()
                self.text_box.set_text(str(self.slot).replace('\n', '<br>'))
            elif event.ui_element == self.inspect_button:
                self.slot.slot.inspect()
                self.text_box.set_text(str(self.slot.slot).replace('\n', '<br>'))
        return super().process_event(event)



class ResourcePanel(UIPanel):
    def __init__(self, game: Game, cursor: Cursor, rect: pygame.Rect, starting_layer_height, manager, *args, **kwargs):
        self.game = game
        self.resources = game.resources
        self.cursor = cursor
        self.manager = manager
        super().__init__(rect, starting_layer_height, manager, *args, **kwargs)
        bottom_buttons_height = 40

        r = pygame.Rect((0, 0), (rect.size[0]-6, rect.size[1]/2))
        self.text_box = UITextBox(str(self.resources), 
            r,
            manager,
            container=self)
        self.build_dropdown = UINonChangingDropDownMenu(['Apiary', 'Alveary'], 'Build', pygame.Rect(0, 0, rect.size[0]-6, bottom_buttons_height), manager, container=self,
            anchors={
                'top':'top',
                'bottom':'bottom',
                'left':'left',
                'right':'right',
                'top_target': self.text_box
            })
        inspect_panel = InspectPanel(cursor, pygame.Rect(0, 0, rect.size[0]-6, rect.bottom - self.build_dropdown.rect.bottom), starting_layer_height, manager, container=self,
            anchors={
                'top':'top',
                'bottom':'bottom',
                'left':'left',
                'right':'right',
                'top_target': self.build_dropdown
            })

    def update_text_box(self):
        self.text_box.set_text(str(self.resources).replace('\n', '<br>'))

    def update(self, time_delta):
        self.update_text_box()
        super().update(time_delta)
    
    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.build_dropdown:
                if event.text != 'Build':
                    apiary = self.game.build(event.text.lower())
                    if apiary is not None:
                        ApiaryWindow(apiary, self.cursor, self.manager)
        return super().process_event(event)

class GUI(Game):
    def __init__(self, window_size, manager, cursor_manager):
        self.command_out = 1
        super().__init__()
        Slot.empty_str = ''
        for i in range(9):
            self.forage()

        cursor = Cursor(pygame.Rect(0, 0, -1, -1), '', cursor_manager)
        resource_panel_width = 330
        resource_panel = ResourcePanel(self, cursor, pygame.Rect(0, 0, resource_panel_width, window_size[1]), 0, manager)
        ApiaryWindow.initial_position = (resource_panel_width, 0)
        api_window = ApiaryWindow(self.apiaries[0], cursor, manager)
        right_text_box_rect = pygame.Rect(0, 0, resource_panel_width, window_size[1])
        right_text_box_rect.right = 0
        self.right_text_box = UITextBox(' ------- Errors ------- <br>', right_text_box_rect, manager,
            anchors={
                'top':'top',
                'bottom':'bottom',
                'left':'right',
                'right':'right',
            })
        inv_window = InventoryWindow(self.inv, 10, 10, cursor,
            pygame.Rect(api_window.rect.right, 0, self.right_text_box.rect.left-api_window.rect.right, window_size[1]),
            manager, 'Inventory', resizable=True)

    def render(self):
        pass

    def print(self, *strings, sep=' ', end='\n', flush=False, out=None):
        print(*strings, sep=sep, end=end, flush=flush)

        thing = sep.join(map(str, strings)) + end
        if out is not None:
            thing = "<font color='#ED9FA6'>" + thing + "</font>"
        self.right_text_box.append_html_text(thing.replace('\n', '<br>'))
        
def main():
    try:
        pygame.init()

        pygame.display.set_caption('Bee Breeding Game')
        
        window_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        # window_surface = pygame.display.set_mode((800, 600))
        window_size = window_surface.get_rect().size

        background = pygame.Surface(window_size)
        background.fill(pygame.Color('#000000'))

        manager = pygame_gui.UIManager(window_size)
        cursor_manager = pygame_gui.UIManager(window_size)

        game = None
        game = GUI(window_size, manager, cursor_manager)
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
                try:
                    manager.process_events(event)
                    cursor_manager.process_events(event)
                except Exception as e:
                    game.print(e, out=1)

            manager.update(time_delta)
            cursor_manager.update(time_delta)

            window_surface.blit(background, (0, 0))
            manager.draw_ui(window_surface)
            cursor_manager.draw_ui(window_surface)

            pygame.display.update()
    finally:
        if game is not None:
            game.exit()


if __name__ == '__main__':
    main()
