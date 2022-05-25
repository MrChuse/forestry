import math
import time
import os.path
from typing import List, Union

import pygame
import pygame_gui
from pygame_gui.elements import (UIButton, UIPanel, UIProgressBar, UIStatusBar,
                                 UITextBox, UIWindow, UIDropDownMenu, UISelectionList)
from pygame_gui.elements.ui_drop_down_menu import UIExpandedDropDownState

from forestry import Apiary, Bee, Drone, Game, Inventory, Princess, Queen, Resources, Slot


class UIWindowNoX(UIWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enable_close_button = False
        self.title_bar_close_button_width = 0
        self.rebuild()

def get_object_id_from_bee(bee: Bee):
    typ = {
        Princess: 'Princess',
        Drone: 'Drone',
        Queen: 'Queen'
    }
    return f'#{bee.genes.species[0]}_{typ[type(bee)]}' if bee is not None else '#EMPTY'

class UIButtonSlot(UIButton):
    def __init__(self, slot: Slot, *args, **kwargs):
        self.slot = slot
        self.args = args
        self.kwargs = kwargs
        super().__init__(*args, **kwargs)
    
    def update(self, time_delta: float):
        bee = self.slot.slot
        obj_id = get_object_id_from_bee(bee)
        prev_obj_id = self.most_specific_combined_id.split('.')[-1]
        if obj_id != prev_obj_id:
            pos = self.relative_rect.topleft
            size = self.rect.size
            self.kill()
            text = self.slot.small_str()
            text = text if text != '' else None
            self.args = (pygame.Rect(pos, size),) + self.args[1:]
            self.kwargs['object_id'] = obj_id
            self.kwargs['tool_tip_text'] = text
            super().__init__(*self.args, **self.kwargs)
        return super().update(time_delta)

class Cursor(UIButtonSlot):
    def __init__(self, *args, **kwargs):
        super().__init__(Slot(), *args, **kwargs)
    
    def update(self, time_delta: float):
        pos = pygame.mouse.get_pos()
        self.relative_rect.topleft = pos
        self.rect.topleft = pos
        return super().update(time_delta)

class InventoryWindow(UIWindowNoX):
    def __init__(self, game: 'GUI', button_hor, button_vert,  cursor: Cursor, rect, manager, *args, margin=5, **kwargs):
        self.game = game
        self.button_hor = button_hor
        self.button_vert = button_vert
        self.margin = margin
        self.cursor = cursor
        self.inv = game.inv
        if len(self.inv) != button_hor * button_vert:
            raise ValueError(
                'Inventory should have button_hor*button_vert number of slots')

        self.title_bar_sort_button_width = 100
        self.sort_window_button = None
        self.save_window_button = None
        self.load_window_button = None
        self.buttons : Union[List[List[UIButtonSlot]], None] = None
        super().__init__(rect, manager, *args, **kwargs)
    
    def rebuild(self):
        """
        Rebuilds the window when the theme has changed.

        """
        if self._window_root_container is None:
            self._window_root_container = pygame_gui.core.UIContainer(pygame.Rect(self.relative_rect.x +
                                                                  self.shadow_width,
                                                                  self.relative_rect.y +
                                                                  self.shadow_width,
                                                                  self.relative_rect.width -
                                                                  (2 * self.shadow_width),
                                                                  self.relative_rect.height -
                                                                  (2 * self.shadow_width)),
                                                      manager=self.ui_manager,
                                                      starting_height=1,
                                                      is_window_root_container=True,
                                                      container=None,
                                                      parent_element=self,
                                                      object_id="#window_root_container",
                                                      visible=self.visible)
        if self.window_element_container is None:
            window_container_rect = pygame.Rect(self.border_width,
                                                self.title_bar_height,
                                                (self._window_root_container.relative_rect.width -
                                                 (2 * self.border_width)),
                                                (self._window_root_container.relative_rect.height -
                                                 (self.title_bar_height + self.border_width)))
            self.window_element_container = pygame_gui.core.UIContainer(window_container_rect,
                                                        self.ui_manager,
                                                        starting_height=0,
                                                        container=self._window_root_container,
                                                        parent_element=self,
                                                        object_id="#window_element_container",
                                                        anchors={'top': 'top', 'bottom': 'bottom',
                                                                 'left': 'left', 'right': 'right'})

        theming_parameters = {'normal_bg': self.background_colour,
                              'normal_border': self.border_colour,
                              'border_width': self.border_width,
                              'shadow_width': self.shadow_width,
                              'shape_corner_radius': self.shape_corner_radius}

        if self.shape == 'rectangle':
            self.drawable_shape = pygame_gui.core.drawable_shapes.RectDrawableShape(self.rect, theming_parameters,
                                                    ['normal'], self.ui_manager)
        elif self.shape == 'rounded_rectangle':
            self.drawable_shape = pygame_gui.core.drawable_shapes.RoundedRectangleShape(self.rect, theming_parameters,
                                                        ['normal'], self.ui_manager)

        self.set_image(self.drawable_shape.get_fresh_surface())

        self.set_dimensions(self.relative_rect.size)

        if self.window_element_container is not None:
            element_container_width = (self._window_root_container.relative_rect.width -
                                       (2 * self.border_width))
            element_container_height = (self._window_root_container.relative_rect.height -
                                        (self.title_bar_height + self.border_width))
            self.window_element_container.set_dimensions((element_container_width,
                                                          element_container_height))
            self.window_element_container.set_relative_position((self.border_width,
                                                                 self.title_bar_height))

            if self.title_bar is not None:
                self.title_bar.set_dimensions((self._window_root_container.relative_rect.width -
                                                3 * self.title_bar_sort_button_width,
                                                self.title_bar_height))
            else:
                title_bar_width = (self._window_root_container.relative_rect.width -
                                    3 * self.title_bar_sort_button_width)
                self.title_bar = UIButton(relative_rect=pygame.Rect(0, 0,
                                                                    title_bar_width,
                                                                    self.title_bar_height),
                                            text=self.window_display_title,
                                            manager=self.ui_manager,
                                            container=self._window_root_container,
                                            parent_element=self,
                                            object_id='#title_bar',
                                            anchors={'top': 'top', 'bottom': 'top',
                                                    'left': 'left', 'right': 'right'}
                                            )
                self.title_bar.set_hold_range((100, 100))

            if self.sort_window_button is not None:
                sort_button_pos = (-self.title_bar_sort_button_width, 0)
                self.sort_window_button.set_dimensions((self.title_bar_sort_button_width,
                                                            self.title_bar_height))
                self.sort_window_button.set_relative_position(sort_button_pos)
            else:
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
            if self.save_window_button is not None:
                save_button_pos = (-self.title_bar_sort_button_width, 0)
                self.save_window_button.set_dimensions((self.title_bar_sort_button_width,
                                                            self.title_bar_height))
                self.save_window_button.set_relative_position(save_button_pos)
            else:
                save_rect = pygame.Rect((-self.title_bar_sort_button_width, 0),
                                        (self.title_bar_sort_button_width,
                                        self.title_bar_height))
                self.save_window_button = UIButton(relative_rect=save_rect,
                                                    text='Save',
                                                    manager=self.ui_manager,
                                                    container=self._window_root_container,
                                                    parent_element=self,
                                                    object_id='#close_button',
                                                    anchors={'top': 'top',
                                                            'bottom': 'top',
                                                            'left': 'right',
                                                            'right': 'right',
                                                            'right_target':self.sort_window_button}
                                                    )
            if self.load_window_button is not None:
                load_button_pos = (-self.title_bar_sort_button_width, 0)
                self.load_window_button.set_dimensions((self.title_bar_sort_button_width,
                                                            self.title_bar_height))
                self.load_window_button.set_relative_position(load_button_pos)
            else:
                load_rect = pygame.Rect((-self.title_bar_sort_button_width, 0),
                                        (self.title_bar_sort_button_width,
                                        self.title_bar_height))
                self.load_window_button = UIButton(relative_rect=load_rect,
                                                    text='Load',
                                                    manager=self.ui_manager,
                                                    container=self._window_root_container,
                                                    parent_element=self,
                                                    object_id='#close_button',
                                                    anchors={'top': 'top',
                                                            'bottom': 'top',
                                                            'left': 'right',
                                                            'right': 'right',
                                                            'right_target':self.save_window_button}
                                                    )
        super(UIWindow, self).rebuild()

    def place_buttons(self, size):
        hor_margin_size = (self.button_hor + 1) * self.margin
        vert_margin_size = (self.button_vert + 1) * self.margin
        remaining_width = size[0] - hor_margin_size - 32  # why 32 & 64!?
        remaining_height = size[1] - vert_margin_size - 64
        hor_size = remaining_width / self.button_hor
        vert_size = remaining_height / self.button_vert
        bsize = (hor_size, vert_size)

        if self.buttons is None:
            self.buttons = []
            for i in range(self.button_hor):
                self.buttons.append([])
                for j in range(self.button_vert):
                    pos = (self.margin + i * (hor_size + self.margin), self.margin + j * (vert_size + self.margin))
                    rect = pygame.Rect(pos, bsize)
                    slot = self.inv[j * self.button_hor + i]
                    self.buttons[i].append(UIButtonSlot(slot, rect, '', self.ui_manager, self))
        else:
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
            elif event.ui_element == self.load_window_button:
                self.game.load('save')
                self.game.print('Loaded save from disk')
            elif event.ui_element == self.save_window_button:
                self.game.save('save')
                self.game.print('Saved the game to the disk')
            for j, row in enumerate(self.buttons):
                for i, b in enumerate(row):
                    if event.ui_element == b:
                        index = i * self.button_hor + j
                        mods = pygame.key.get_mods()
                        if mods & pygame.KMOD_LSHIFT:
                            self.inv.take(index)
                        else:
                            self.cursor.slot.swap(self.inv[index])
                        return True
        return super().process_event(event)

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
    def __init__(self, game: Game, apiary: Apiary, cursor: Cursor, manager, *args, **kwargs):
        self.game = game
        self.apiary = apiary
        self.cursor = cursor
        self.size = (300, 420)
        super().__init__(pygame.Rect(self.initial_position, self.size), manager, "Apiary " + apiary.name, *args, **kwargs)

        self.button_size = (64, 64)
        self.top_margin2 = 15
        self.side_margin2 = 63
        self.princess_button = UIButtonSlot(self.apiary.princess, pygame.Rect((self.side_margin2, self.top_margin2), self.button_size),
            '', manager, self)
        drone_rect = pygame.Rect((0, 0), self.button_size)
        drone_rect.topright = (-self.side_margin2, self.top_margin2)
        self.drone_button = UIButtonSlot(self.apiary.drone, drone_rect,
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
        self.buttons = [UIButtonSlot(self.apiary.inv[0], center_rect, '', manager, self)]
        for i in range(6):
            angle = 2 * math.pi / 6 * i
            dx = radius * math.cos(angle)
            dy = radius * math.sin(angle)

            rect = center_rect.copy()
            rect.x += dx
            rect.y += dy
            self.buttons.append(UIButtonSlot(self.apiary.inv[i+1], rect, '', manager, self))
        take_all_button_rect = pygame.Rect(0, 0, self.size[0] - self.side_margin2 * 2, 30)
        take_all_button_rect.centerx = rect.centerx - 40 # no clue why 40
        self.take_all_button = UIButton(take_all_button_rect, 'Take all', manager, self,
            anchors={
                'left': 'left',
                'right': 'right',
                'top': 'top',
                'bottom': 'bottom',
                'top_target': self.buttons[3]
            })
    
    def update_health_bar(self):
        bee = self.apiary.princess.slot
        if isinstance(bee, Queen):
            self.queen_health.percent_full = bee.remaining_lifespan / bee.lifespan
        else:
            self.queen_health.percent_full = 0
    
    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.take_all_button:
                self.game.take(self.apiary.name, '0..6')
            elif event.ui_element == self.princess_button:
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
                        self.game.print('Cursor not empty', out=1)
        return super().process_event(event)
    
    def update(self, time_delta):
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
    def __init__(self, game: Game, cursor: Cursor, rect, starting_layer_height, manager, *args, **kwargs):
        self.game = game
        self.cursor = cursor
        super().__init__(rect, starting_layer_height, manager, *args, **kwargs)
        inspect_button_height = 64
        self.inspect_button = UIButton(pygame.Rect(0, 0, rect.width - inspect_button_height, inspect_button_height), 'Inspect', manager, self)
        bee_button_rect = pygame.Rect(0, 0, inspect_button_height, inspect_button_height)
        bee_button_rect.right = 0
        self.bee_button = UIButtonSlot(Slot(), bee_button_rect, '', manager, self,
            anchors={
                'top':'top',
                'bottom':'bottom',
                'left':'right',
                'right':'right',
            })
        self.text_box = UITextBox('', pygame.Rect(0, inspect_button_height, rect.width-6, rect.height-inspect_button_height-6), manager, container=self)
    
    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.bee_button:
                self.cursor.slot.swap(self.bee_button.slot)
            elif event.ui_element == self.inspect_button:
                self.game.inspect_bee(self.bee_button.slot.slot)
        return super().process_event(event)
    
    def update(self, time_delta: float):
        self.text_box.set_text(str(self.bee_button.slot).replace('\n', '<br>'))
        return super().update(time_delta)



class ResourcePanel(UIPanel):
    def __init__(self, game: Game, cursor: Cursor, rect: pygame.Rect, starting_layer_height, manager, *args, **kwargs):
        self.game = game
        self.resources = game.resources
        self.cursor = cursor
        super().__init__(rect, starting_layer_height, manager, *args, **kwargs)
        bottom_buttons_height = 40

        r = pygame.Rect((0, 0), (rect.size[0]-6, rect.size[1]/2))
        self.text_box = UITextBox(str(self.resources), 
            r,
            manager,
            container=self)
        self.forage_button = UIButton(pygame.Rect(0, 0, rect.size[0]-6, bottom_buttons_height), 'Forage', manager, container=self,
            anchors={
                'top':'top',
                'bottom':'bottom',
                'left':'left',
                'right':'right',
                'top_target': self.text_box
            }
        )
        self.build_dropdown = UINonChangingDropDownMenu(['Apiary', 'Alveary'], 'Build', pygame.Rect(0, 0, rect.size[0]-6, bottom_buttons_height), manager, container=self,
            anchors={
                'top':'top',
                'bottom':'bottom',
                'left':'left',
                'right':'right',
                'top_target': self.forage_button
            })
        self.inspect_panel = InspectPanel(game, cursor, pygame.Rect(0, 0, rect.size[0]-6, rect.bottom - self.build_dropdown.rect.bottom), starting_layer_height, manager, container=self,
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
                        ApiaryWindow(self.game, apiary, self.cursor, self.ui_manager)
                    self.game.update_apiary_list()
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.forage_button:
                self.game.forage()
        return super().process_event(event)

class GUI(Game):
    def __init__(self, window_size, manager, cursor_manager):
        self.command_out = 1
        super().__init__()
        Slot.empty_str = ''

        self.cursor = Cursor(pygame.Rect(0, 0, 64, 64), '', cursor_manager)
        self.ui_manager = manager
        resource_panel_width = 330
        self.resource_panel = ResourcePanel(self, self.cursor, pygame.Rect(0, 0, resource_panel_width, window_size[1]), 0, manager)
        self.apiary_windows = []
        ApiaryWindow.initial_position = (resource_panel_width, 0)
        api_window = ApiaryWindow(self, self.apiaries[0], self.cursor, manager)
        self.apiary_windows.append(api_window)
        right_text_box_rect = pygame.Rect(0, 0, resource_panel_width, window_size[1])
        right_text_box_rect.right = 0
        self.right_text_box = UITextBox(' ------- Logs ------- <br>', right_text_box_rect, manager,
            anchors={
                'top':'top',
                'bottom':'bottom',
                'left':'right',
                'right':'right',
            })
        apiary_selection_list_rect = pygame.Rect(0, 0, 100, window_size[1])
        apiary_selection_list_rect.right = 0
        self.apiary_selection_list = UISelectionList(apiary_selection_list_rect, ['Apiary ' + a.name for a in self.apiaries], manager,
            anchors={
                'top':'top',
                'bottom':'bottom',
                'left':'right',
                'right':'right',
                'right_target': self.right_text_box
            })
        self.inv_window = InventoryWindow(self, 10, 10, self.cursor,
            pygame.Rect(api_window.rect.right, 0, self.apiary_selection_list.rect.left-api_window.rect.right, window_size[1]),
            manager, 'Inventory', resizable=True)

        r = pygame.Rect(0,0,window_size[0]/2, window_size[1]/2)
        r.center = (window_size[0]/2, window_size[1]/2)
        if not os.path.exists('save.forestry'):
            help_window = UIWindow(r, manager)
            help_text = UITextBox(
                '''Welcome to a demo of my little game about selective breeding!
You are going to be a professional bee breeder and your goal for this demo is to build an alveary.
In order to do this you'll have to (surprisingly) breed the bees you have and try to find the pairs of species that result in a mutation after mating.

You start with 0 bees, so you need a way to collect them in the first place. `Forage` button on the left will help you.
You can put the bees into the apiary, just click the bee and click one of the two top slots in the apiary window.

Bees have genes, and you only see their phenotype at first; to discover their genotype you should place the bee into the inspection slot on the left and hit `Inspect` button
You can build new apiaries using `Build` button on the left. When you build an alveary, you win the game!

Also, you can change the size of the inventory window (if you have lower resolution, you may not see the bees' species and sex)
On the right side you can see logs which show when something went wrong and some other information

Don't forget to save your progress using `Save` button located at the top of your inventory.
You can load your saved progress. Only one save slot is available (you can manipulate save.forestry file however)'''.replace('\n', '<br>'),
                pygame.Rect(0,0, r.width-32, r.height-59), manager, container=help_window
            )

    def render(self):
        pass

    def print(self, *strings, sep=' ', end='\n', flush=False, out=None):
        print(*strings, sep=sep, end=end, flush=flush)

        thing = sep.join(map(str, strings)) + end
        if out is not None:
            thing = "<font color='#ED9FA6'>" + thing + "</font>"
        self.right_text_box.append_html_text(thing.replace('\n', '<br>'))
    
    def update_apiary_list(self):
        self.apiary_selection_list.set_item_list(['Apiary ' + a.name for a in self.apiaries])

    def process_event(self, event):
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.apiary_selection_list:
                index = int(event.text.split()[-1])
                self.apiary_windows.append(
                    ApiaryWindow(self, self.apiaries[index], self.cursor, self.ui_manager)
                )
    
    def get_state(self):
        state = super().get_state()
        state['cursor_slot'] = self.cursor.slot
        state['inspect_slot'] = self.resource_panel.inspect_panel.bee_button.slot
        return state

    def load(self, name):
        saved = super().load(name)
        for window in self.apiary_windows:
            window.kill()
        self.inv_window.inv = self.inv
        for i, row in enumerate(self.inv_window.buttons):
            for j, b in enumerate(row):
                slot = self.inv[j * len(row) + i]
                b.slot = slot
        self.resource_panel.resources = self.resources
        self.update_apiary_list()
        self.cursor.slot = saved['cursor_slot']
        self.resource_panel.inspect_panel.bee_button.slot = saved['inspect_slot']
        return saved

def main():
    try:
        pygame.init()

        pygame.display.set_caption('Bee Breeding Game')
        
        window_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        # window_surface = pygame.display.set_mode((800, 600))
        window_size = window_surface.get_rect().size

        background = pygame.Surface(window_size)
        background.fill(pygame.Color('#000000'))

        manager = pygame_gui.UIManager(window_size, 'theme.json', enable_live_theme_updates=False)
        cursor_manager = pygame_gui.UIManager(window_size, 'theme.json')

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
                    if game is not None:
                        game.process_event(event)
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
