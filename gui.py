from enum import IntEnum
import json
import math
import time
import os.path
from traceback import print_exc
from typing import List, Tuple, Union, Dict
import warnings

import pygame
from pygame import mixer
import pygame_gui
from pygame_gui.elements import (UIButton, UIPanel, UITooltip, UILabel, UIHorizontalSlider,
                                 UITextBox, UIWindow, UISelectionList)
from pygame_gui.core import ObjectID, UIContainer
from pygame_gui.windows import UIMessageWindow, UIConfirmationDialog

from forestry import Apiary, Bee, Drone, Game, Genes, Inventory, MatingEntry, MatingHistory, Princess, Queen, Resources, Slot, SlotOccupiedError, local, dominant, helper_text, mendel_text, dom_local
from ui import UIGridWindow, UIGridPanel, UIRelativeStatusBar, UIFloatingTextBox, UINonChangingDropDownMenu
from migration import CURRENT_FRONT_VERSION, update_front_versions

def process_cursor_slot_interaction(event, cursor, slot):
    if event.mouse_button == pygame.BUTTON_LEFT:
        if cursor.slot.slot == slot.slot:
            slot.put(*cursor.slot.take_all()) # stack
        else:
            cursor.slot.swap(slot) # swap
    elif event.mouse_button == pygame.BUTTON_RIGHT:
        if cursor.slot.is_empty():
            bee, amt = slot.take_all() # take half
            amt2 = amt//2
            cursor.slot.put(bee, amt-amt2)
            slot.put(bee, amt2)
        else:
            slot.put(cursor.slot.slot) # put one
            cursor.slot.take()

INSPECT_BEE = pygame.event.custom_type()
class InspectPopup(UITooltip):
    def __init__(self, bee_button: 'UIButtonSlot', hover_distance: Tuple[int, int], manager, parent_element = None, object_id: Union[ObjectID, str, None] = None, anchors: Dict[str, str] = None):
        super().__init__('', hover_distance, manager, parent_element, object_id, anchors)
        self.container = UIContainer(pygame.Rect(0, 0, -1, -1), manager, starting_height=self.ui_manager.get_sprite_group().get_top_layer()+1, parent_element=self)
        self.bee_button = bee_button
        if not self.bee_button.slot.is_empty() and not self.bee_button.slot.slot.inspected:
            width = 170
        else:
            width = 320
        self.top_margin = 4
        self.inspect_button_height = 32

        bee_stats_rect = pygame.Rect(0, self.top_margin, width, -1)
        self.inspect_button = None
        if not self.bee_button.slot.is_empty() and GUI.current_tutorial_stage >= TutorialStage.INSPECT_AVAILABLE and not self.bee_button.slot.slot.inspected:
            self.inspect_button = UIButton(pygame.Rect(0, self.top_margin, width - self.inspect_button_height, self.inspect_button_height), local['Inspect'], manager, self.container)
            self.inspect_button.set_hold_range((2, 2))
            bee_stats_rect.top += self.inspect_button_height

        self.bee_stats = BeeStats(self.bee_button.slot.slot, bee_stats_rect, manager, True, container=self.container)

        self.pin_button_unpinned = UIButton(pygame.Rect(width - self.inspect_button_height,
                                                        self.top_margin,
                                                        self.inspect_button_height,
                                                        self.inspect_button_height),
                                            '', manager, self.container, object_id='#unpinned', starting_height=2)
        self.pin_button_pinned = UIButton(pygame.Rect(width - self.inspect_button_height,
                                                      self.top_margin,
                                                      self.inspect_button_height,
                                                      self.inspect_button_height),
                                          '', manager, self.container, object_id='#pinned', starting_height=2)
        self.pin_button_pinned.hide()
        self.pinned = False

        xdim = self.bee_stats.rect.size[0]
        ydim = self.bee_stats.rect.size[1] + self.top_margin
        if self.inspect_button is not None:
            ydim += self.inspect_button.rect.size[1]
        self.container.set_dimensions((xdim, ydim))
        super().set_dimensions((xdim, ydim))
        self.text_block.kill()

    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.inspect_button:
                event_data = {'bee_button': self.bee_button,
                              'bee_stats': self.bee_stats}
                pygame.event.post(pygame.event.Event(INSPECT_BEE, event_data))
            elif event.ui_element == self.pin_button_unpinned:
                self.pinned = True
                self.pin_button_unpinned.hide()
                self.pin_button_pinned.show()
            elif event.ui_element == self.pin_button_pinned:
                self.pinned = False
                self.pin_button_pinned.hide()
                self.pin_button_unpinned.show()
        return super().process_event(event)

    def kill(self):
        self.container.kill()
        return super().kill()

    def find_valid_position(self, position: pygame.math.Vector2) -> bool:
        window_rect = self.ui_manager.get_root_container().get_rect()

        if not window_rect.contains(pygame.Rect(int(position[0]), int(position[1]), 1, 1)):
            self.relative_rect = self.rect.copy()
            warnings.warn("initial position for tool tip is off screen,"
                          " unable to find valid position")
            return False

        self.rect.left = int(position.x - self.rect.width/2)
        self.rect.top = int(position.y + self.hover_distance_from_target[1] - self.top_margin)

        if window_rect.contains(self.rect):
            self.relative_rect = self.rect.copy()
            self.container.set_position(self.rect.topleft)
            return True
        else:
            if self.rect.bottom > window_rect.bottom:
                self.rect.bottom = int(position.y - self.hover_distance_from_target[1])
            if self.rect.right > window_rect.right:
                self.rect.right = window_rect.right - self.hover_distance_from_target[0]
            if self.rect.left < window_rect.left:
                self.rect.left = window_rect.left + self.hover_distance_from_target[0]

        if window_rect.contains(self.rect):
            self.relative_rect = self.rect.copy()
            self.container.set_position(self.rect.topleft)
            return True
        else:
            self.relative_rect = self.rect.copy()
            warnings.warn("Unable to fit tool tip on screen")
            return False


class UIButtonSlot(UIButton):
    empty_object_id = '#EMPTY'
    def __init__(self, slot: Slot, *args, highlighted=False, **kwargs):
        self.slot = slot
        self.args = args
        self.kwargs = kwargs
        self.kwargs['generate_click_events_from'] = [pygame.BUTTON_LEFT, pygame.BUTTON_RIGHT]
        super().__init__(*args, **kwargs)

        r = pygame.Rect(0,0,0,0)
        r.size = 34, 30
        r.bottomright = self.relative_rect.bottomright
        self.text_box = UITextBox('1', r, self.ui_manager, container=self.ui_container, layer_starting_height=2, object_id=ObjectID(class_id='@Centered'), anchors=self.kwargs.get('anchors'))
        self.text_box.hide()
        self.saved_amount = 0

        self.inspected_status = None
        if not self.slot.is_empty():
            r = pygame.Rect(0,0,0,0)
            r.size = 20, 20
            r.topright = self.relative_rect.topright
            self.inspected_status = UIRelativeStatusBar(r, self.ui_manager, container=self.ui_container, object_id='#InspectedStatus', anchors=self.kwargs.get('anchors'))
            self.inspected_status.percent_full = int(self.slot.slot.inspected)

        self.highlighted = highlighted

        self.inspect_popup = None

    def get_object_id_from_bee(self, bee: Bee):
        typ = {
            Princess: 'Princess',
            Drone: 'Drone',
            Queen: 'Queen'
        }
        return f'#{bee.genes.species[0].name.upper()}_{typ[type(bee)]}{"_highlighted" if self.highlighted else ""}' if bee is not None else self.empty_object_id

    def highlight(self):
        self.highlighted = True

    def unhighlight(self):
        self.highlighted = False

    def update(self, time_delta: float):
        bee = self.slot.slot
        obj_id = self.get_object_id_from_bee(bee)
        prev_obj_id = self.most_specific_combined_id.split('.')[-1]
        if obj_id != prev_obj_id:
            pos = self.relative_rect.topleft
            size = self.rect.size
            self.kill()
            self.args = (pygame.Rect(pos, size),) + self.args[1:]
            self.kwargs['object_id'] = obj_id
            self.__init__(self.slot, *self.args,    highlighted=self.highlighted, **self.kwargs)
        if self.inspected_status is not None and self.inspected_status.percent_full != int(self.slot.slot.inspected):
            self.inspected_status.percent_full = int(self.slot.slot.inspected)
        if self.slot.amount != self.saved_amount:
            if self.slot.amount < 2:
                self.text_box.hide()
            else:
                if self.visible:
                    self.text_box.set_text(str(self.slot.amount))
                    self.text_box.show()
            self.saved_amount = self.slot.amount

        if (self.inspect_popup is not None and
                not self.inspect_popup.pinned and
                not self.hover_point(*self.ui_manager.get_mouse_position()) and
                not self.inspect_popup.container.hover_point(*self.ui_manager.get_mouse_position())):
            self.inspect_popup.kill()
            self.inspect_popup = None
        return super().update(time_delta)

    def _set_relative_position_subelements(self):
        text_box_size = self.text_box.rect.size
        bottomright = self.relative_rect.bottomright
        pos = (bottomright[0] - text_box_size[0], bottomright[1] - text_box_size[1])
        self.text_box.set_relative_position(pos)
        if self.inspected_status is not None:
            inspected_width = self.inspected_status.rect.width
            topright = self.relative_rect.topright
            pos = (topright[0] - inspected_width, topright[1])
            self.inspected_status.set_relative_position(pos)

    def set_relative_position(self, position: Union[pygame.math.Vector2, Tuple[int, int], Tuple[float, float]]):
        tmp = super().set_relative_position(position)
        self._set_relative_position_subelements()
        return tmp

    def set_dimensions(self, dimensions: Union[pygame.math.Vector2, Tuple[int, int], Tuple[float, float]]):
        tmp = super().set_dimensions(dimensions)
        self._set_relative_position_subelements()
        return tmp

    def kill(self):
        self.text_box.hide()
        self.text_box.kill()
        if self.inspected_status is not None:
            self.inspected_status.kill()
        if self.inspect_popup is not None:
            self.inspect_popup.kill()
        return super().kill()

    def while_hovering(self, time_delta: float, mouse_pos: Union[pygame.math.Vector2, Tuple[int, int], Tuple[float, float]]):
        if self.inspect_popup is None and self.hover_time > self.tool_tip_delay and not self.slot.is_empty():
            hover_height = int(self.rect.height / 2)
            self.inspect_popup = InspectPopup(self, (-150, hover_height), self.ui_manager)
            self.inspect_popup.find_valid_position(pygame.math.Vector2(self.rect.centerx, self.rect.centery))
        super().while_hovering(time_delta, mouse_pos)


    def hide(self):
        if self.visible:
            super().hide()
            self.text_box.hide()
            if self.inspected_status is not None:
                self.inspected_status.hide()

    def show(self):
        if not self.visible:
            super().show()
            if self.slot.amount >= 2:
                self.text_box.set_text(str(self.slot.amount))
                self.saved_amount = self.slot.amount
                self.text_box.show()
            if self.inspected_status is not None:
                self.inspected_status.show()


    def process_event(self, event: pygame.event.Event) -> bool:
        ret = super().process_event(event)
        if event.type == pygame_gui.UI_BUTTON_ON_HOVERED: # TODO: come up with better solution
            if isinstance(event.ui_element, UIButtonSlot):
                if event.ui_element.slot.slot is not None and event.ui_element != self and event.ui_element.slot.slot == self.slot.slot:
                    self.highlight()
        elif event.type == pygame_gui.UI_BUTTON_ON_UNHOVERED:
            if isinstance(event.ui_element, UIButtonSlot):
                if event.ui_element.slot.slot is not None and event.ui_element.slot.slot == self.slot.slot:
                    self.unhighlight()
        return ret

class Cursor(UIButtonSlot):
    def __init__(self, slot, *args, **kwargs):
        super().__init__(slot, *args, **kwargs)

    def process_event(self, event: pygame.event.Event) -> bool:
        return False

    def update(self, time_delta: float):
        pos = pygame.mouse.get_pos()
        self.relative_rect.topleft = pos
        self.rect.topleft = pos

        self.text_box.rect.size = 30, 30
        self.text_box.rect.bottomright = self.rect.bottomright
        if self.inspected_status is not None:
            self.inspected_status.rect.topright = self.rect.topright

        if self.slot.is_empty():
            self.hide()
        else:
            self.show()
        return super().update(time_delta)

class InventoryWindow(UIGridWindow):
    def __init__(self, inv: Inventory,  cursor: Cursor, rect, manager, *args, **kwargs):
        self.inv = inv
        self.cursor = cursor

        self.title_bar_sort_button_width = 100
        self.sort_window_button = None
        self.buttons : Union[List[List[UIButtonSlot]], None] = None

        kwargs['window_display_title'] = local['Inventory'] + ' ' + inv.name
        kwargs['resizable'] = True
        super().__init__(rect, manager, *args, **kwargs, subelements_function=self.subelements_method)

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
                                                self.title_bar_sort_button_width - self.title_bar_close_button_width,
                                                self.title_bar_height))
            else:
                title_bar_width = (self._window_root_container.relative_rect.width -
                                    self.title_bar_sort_button_width - self.title_bar_close_button_width)
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

            if self.close_window_button is not None:
                close_button_pos = (-self.title_bar_close_button_width, 0)
                self.close_window_button.set_dimensions((self.title_bar_close_button_width,
                                                            self.title_bar_height))
                self.close_window_button.set_relative_position(close_button_pos)
            else:
                close_rect = pygame.Rect((-self.title_bar_close_button_width, 0),
                                        (self.title_bar_close_button_width,
                                        self.title_bar_height))
                self.close_window_button = UIButton(relative_rect=close_rect,
                                                    text='╳',
                                                    manager=self.ui_manager,
                                                    container=self._window_root_container,
                                                    parent_element=self,
                                                    object_id='#close_button',
                                                    anchors={'top': 'top',
                                                            'bottom': 'top',
                                                            'left': 'right',
                                                            'right': 'right'}
                                                    )
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
                                                    text=local['Sort'],
                                                    manager=self.ui_manager,
                                                    container=self._window_root_container,
                                                    parent_element=self,
                                                    object_id='#close_button',
                                                    anchors={'top': 'top',
                                                            'bottom': 'top',
                                                            'left': 'right',
                                                            'right': 'right',
                                                            'right_target':self.close_window_button}
                                                    )
        super(UIWindow, self).rebuild()

    def subelements_method(self, container):
        bsize = (64, 64)
        self.buttons = []
        for slot in self.inv:
            rect = pygame.Rect((0, 0), bsize)
            self.buttons.append(UIButtonSlot(slot, rect, '', self.ui_manager, container))
        return self.buttons

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.sort_window_button:
                self.inv.sort()
            for index, button in enumerate(self.buttons):
                    if event.ui_element == button:
                        mods = pygame.key.get_mods()
                        if mods & pygame.KMOD_LSHIFT:
                            self.inv.take_all(index)
                        else:
                            process_cursor_slot_interaction(event, self.cursor, self.inv[index])
                        return True
        return super().process_event(event)


class ApiaryWindow(UIWindow):
    def __init__(self, game: 'GUI', apiary: Apiary, cursor: Cursor, relative_rect: pygame.Rect, manager, *args, **kwargs):
        self.game = game
        self.apiary = apiary
        self.cursor = cursor
        self.size = relative_rect.size
        super().__init__(relative_rect, manager, local['Apiary'] + ' ' + apiary.name, *args, **kwargs)

        self.button_size = (64, 64)
        self.top_margin2 = 15
        self.side_margin2 = 63
        self.princess_button = UIButtonSlot(self.apiary.princess, pygame.Rect((self.side_margin2, self.top_margin2), self.button_size),
            '', manager, self)
        self.princess_button.empty_object_id = '#PrincessEmpty'
        drone_rect = pygame.Rect((self.size[0] - self.button_size[0] - self.side_margin2 - 32, self.top_margin2), self.button_size)
        self.drone_button = UIButtonSlot(self.apiary.drone, drone_rect,
                                     text='', manager=manager,
                                     container=self)
        self.drone_button.empty_object_id = '#DroneEmpty'

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
        self.take_all_button = UIButton(take_all_button_rect, local['Take'], manager, self,
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
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_h:
                for b in self.buttons:
                    b.hide()
            if event.key == pygame.K_g:
                for b in self.buttons:
                    b.show()
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.take_all_button:
                r = []
                for b in self.buttons:
                    if not b.slot.is_empty():
                        r.append(b.slot)
                self.game.most_recent_inventory.place_bees(r)
            elif event.ui_element == self.princess_button:
                if self.cursor.slot.is_empty():
                    self.cursor.slot.put(*self.apiary.take_princess()) # just take it from apiary
                else:
                    # cursor not empty
                    if self.apiary.princess.is_empty():
                        bee = self.cursor.slot.take()
                        try:
                            self.apiary.put_princess(bee)
                        except TypeError as e:
                            self.cursor.slot.put(bee)
                            raise e
                    else:
                        if self.cursor.slot.amount > 1:
                            raise ValueError("Can't put more than 1 princess into apiary")
                        bee1 = self.apiary.take_princess()
                        bee2 = self.cursor.slot.take_all()
                        try:
                            self.apiary.put_princess(*bee2)
                        except TypeError as e:
                            self.cursor.slot.put(*bee2)
                            self.apiary.put_princess(*bee1)
                            raise e
                        self.cursor.slot.put(*bee1)
            elif event.ui_element == self.drone_button:
                if isinstance(self.cursor.slot.slot, (Drone, type(None))):
                    process_cursor_slot_interaction(event, self.cursor, self.drone_button.slot)
                    self.apiary.try_breed()
                else:
                    raise ValueError('Bee should be a Drone')
            for index, b in enumerate(self.buttons):
                if event.ui_element == b:
                    mods = pygame.key.get_mods()
                    if mods & pygame.KMOD_LSHIFT:
                        bee, amt = self.apiary.take(index)
                        self.game.most_recent_inventory.place_bees([bee]*amt)
                    else:
                        if self.cursor.slot.is_empty():
                            self.cursor.slot.put(*self.apiary.take(index))
                        else:
                            self.game.print("Can't take from slot", out=1)
        return super().process_event(event)

    def update(self, time_delta):
        self.update_health_bar()
        super().update(time_delta)


class BeeStats(UITextBox):
    def __init__(self, bee: Bee, relative_rect: pygame.Rect, manager, wrap_to_height: bool = False, layer_starting_height: int = 1, container = None, parent_element = None, object_id: Union[ObjectID, str, None] = None, anchors: Dict[str, str] = None, visible: int = 1):
        self.bee = bee
        super().__init__('', relative_rect, manager, wrap_to_height, layer_starting_height, container, parent_element, object_id, anchors, visible)
        self.process_inspect()

    def process_inspect(self):
        if self.bee is None:
            self.set_text('')
            return
        res = []
        if not self.bee.inspected:
            res.append(self.bee.small_str())
        else:
            name, bee_species_index = local[self.bee.type_str]
            res.append(name)
            genes = self.bee.genes.asdict()
            res.append(local['trait'])
            for key in genes:
                try:
                    allele0 = local[genes[key][0]][bee_species_index]
                    allele1 = local[genes[key][1]][bee_species_index]
                except IndexError:
                    allele0 = local[genes[key][0]][0] # TODO: remove [0]
                    allele1 = local[genes[key][1]][0]
                dom0 = dominant[genes[key][0]]
                dom1 = dominant[genes[key][1]]
                res.append(f'  {local[key]} <a href=\'{key}\'>(?)</a>: <font color={"#ec3661" if dominant[genes[key][0]] else "#3687ec"}>{dom_local(allele0, dom0)}</font>, <font color={"#ec3661" if dominant[genes[key][1]] else "#3687ec"}>{dom_local(allele1, dom1)}</font>')
        self.set_text('<br>'.join(res))

    def open_gene_helper(self, gene):
        if GUI.current_tutorial_stage == TutorialStage.INSPECT_AVAILABLE:
            GUI.current_tutorial_stage = TutorialStage.GENE_HELPER_TEXT_CLICKED
            pygame.event.post(pygame.event.Event(TUTORIAL_STAGE_CHANGED, {}))
        return UIMessageWindow(pygame.Rect(self.ui_manager.get_mouse_position(), (260, 200)),
                               local[gene+'_helper_text'], self.ui_manager)

    def process_event(self, event: pygame.event.Event) -> bool:
        consumed = super().process_event(event)
        if event.type == pygame_gui.UI_TEXT_BOX_LINK_CLICKED:
            if event.ui_element == self:
                try:
                    self.open_gene_helper(event.link_target)
                    consumed = True
                except KeyError:
                    pass
        return consumed


class InspectWindow(UIWindow):
    def __init__(self, game: Game, cursor: Cursor, rect: pygame.Rect, manager, element_id: Union[str, None] = None, object_id: Union[ObjectID, str, None] = None):
        self.game = game
        self.cursor = cursor
        rect = pygame.Rect(rect.left, rect.top, 350, 300)
        super().__init__(rect, manager, local['Inspect Window'], element_id, object_id, resizable=False, visible=1)
        inspect_button_height = 64
        self.inspect_button = UIButton(pygame.Rect(0, 0, self.get_container().get_size()[0] - inspect_button_height, inspect_button_height), local['Inspect'], manager, self)
        bee_button_rect = pygame.Rect(0, 0, inspect_button_height, inspect_button_height)
        self.bee_button = UIButtonSlot(Slot(), bee_button_rect, '', manager, self,
            anchors={
                'left': 'left',
                'right': 'right',
                'bottom': 'bottom',
                'top': 'top',
                'left_target': self.inspect_button
            }
        )
        self.bee_button.empty_object_id = '#DroneEmpty'
        self.bee_stats = BeeStats(None, pygame.Rect(0, inspect_button_height, self.get_container().get_rect().width, self.get_container().get_rect().height-inspect_button_height), manager, container=self)

    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.bee_button:
                self.cursor.slot.swap(self.bee_button.slot)
                self.bee_stats.bee = self.bee_button.slot.slot
                self.bee_stats.process_inspect()
            elif event.ui_element == self.inspect_button:
                event_data = {'bee_button': self.bee_button,
                              'bee_stats': self.bee_stats}
                pygame.event.post(pygame.event.Event(INSPECT_BEE, event_data))
        return super().process_event(event)


TUTORIAL_STAGE_CHANGED = pygame.event.custom_type()
class ResourcePanel(UIPanel):
    def __init__(self, game: 'GUI', cursor: Cursor, rect: pygame.Rect, starting_layer_height, manager, *args, **kwargs):
        self.game = game
        self.resources = game.resources
        self.cursor = cursor
        super().__init__(rect, starting_layer_height, manager, *args, **kwargs)
        bottom_buttons_height = 40

        r = pygame.Rect((0, 0), (rect.size[0]-6, rect.size[1] - 400))
        self.text_box = UITextBox(str(self.resources),
            r,
            manager,
            container=self)

        self.original_build_options = ['Inventory', 'Apiary', 'Alveary']
        self.known_build_options = []
        self.local_build_options = []
        self.build_dropdown = UINonChangingDropDownMenu(self.local_build_options, local['Build'], pygame.Rect(0, 0, rect.size[0]-6, bottom_buttons_height), manager, container=self,
            anchors={
                'top':'top',
                'bottom':'top',
                'left':'left',
                'right':'right',
                'top_target': self.text_box
            }, visible=False)

    def update_text_box(self):
        text = str(self.resources)
        if GUI.current_tutorial_stage == TutorialStage.NO_RESOURCES and len(self.resources) > 0:
            GUI.current_tutorial_stage = TutorialStage.RESOURCES_AVAILABLE
            pygame.event.post(pygame.event.Event(TUTORIAL_STAGE_CHANGED, {}))
        elif GUI.current_tutorial_stage == TutorialStage.RESOURCES_AVAILABLE and 'honey' in self.resources:
            GUI.current_tutorial_stage = TutorialStage.INSPECT_AVAILABLE
            pygame.event.post(pygame.event.Event(TUTORIAL_STAGE_CHANGED, {}))
        available_build_options = self.game.get_available_build_options()
        if len(available_build_options) > 0:
            self.build_dropdown.show()
        for option in available_build_options:
            if option not in self.known_build_options:
                self.known_build_options.append(option)
                self.local_build_options.append(local[option])
                self.build_dropdown.options_list = self.local_build_options
        for r in local['resources'].items():
            text = text.replace(*r)
        self.text_box.set_text(text.replace('\n', '<br>'))

    def update(self, time_delta):
        self.update_text_box()
        super().update(time_delta)

    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.build_dropdown:
                if event.text != 'Build':
                    text = event.text
                    index = self.local_build_options.index(text)
                    building_name = self.original_build_options[index]
                    building = self.game.build(building_name.lower())
                    if isinstance(building, Apiary):
                        ApiaryWindow(self.game, building, self.cursor, pygame.Rect(pygame.mouse.get_pos(), (300, 420)), self.ui_manager)
                        self.game.update_windows_list()
                    elif isinstance(building, Inventory):
                        InventoryWindow(building, self.cursor,
                        pygame.Rect(0, 0, self.game.apiary_selection_list.rect.left, self.game.window_size[1]),
                        self.ui_manager, resizable=True)
                        self.game.update_windows_list()
                    else: #if isinstance(building, Alveary):
                        win_window = UIMessageWindow(pygame.Rect((0,0), self.game.window_size), '<effect id=bounce><font size=7.0>You won the demo!</font></effect>', self.ui_manager, window_title='You won the demo!', object_id='#WinWindow')
                        win_window.text_block.set_active_effect(pygame_gui.TEXT_EFFECT_BOUNCE, effect_tag='bounce')
        return super().process_event(event)

class MatingEntryPanel(UIGridPanel):
    def __init__(self, count: int, entry: MatingEntry, relative_rect: pygame.Rect, starting_layer_height: int, manager, *, element_id: str = 'panel', margins: Dict[str, int] = None, container = None, parent_element = None, object_id: Union[ObjectID, str, None] = None, anchors: Dict[str, str] = None, visible: int = 1):
        self.count = count
        self.entry = entry
        relative_rect.size = (518, 70)
        super().__init__(relative_rect, starting_layer_height, manager, element_id=element_id, margins=margins, container=container, parent_element=parent_element, object_id=object_id, anchors=anchors, visible=visible, subelements_function=self.subelements_method)

    def subelements_method(self, container):
        buttons = []
        for index, (cls, allele, inspected) in enumerate(zip(
                [Princess, Princess, Drone, Drone, Drone, Drone],
                [self.entry.parent1_dom, self.entry.parent1_rec, self.entry.parent2_dom, self.entry.parent2_rec, self.entry.child_dom, self.entry.child_rec],
                [self.entry.parent1_inspected, self.entry.parent1_inspected, self.entry.parent2_inspected, self.entry.parent2_inspected, self.entry.child_inspected, self.entry.child_inspected])):
            if index % 2 == 1 and not inspected:
                slot = Slot()
            else:
                bee = cls(Genes((allele, allele), None, None, None), inspected=inspected)
                slot = Slot(bee, self.count)
            buttons.append(UIButtonSlot(slot, pygame.Rect(0, 0, 64, 64), '', self.ui_manager, container=container))
        buttons.insert(2, UIButton(pygame.Rect(0, 0, 64, 64), '', self.ui_manager, container=container, object_id='#mating_history_plus_button'))
        buttons.insert(5, UIButton(pygame.Rect(0, 0, 64, 64), '', self.ui_manager, container=container, object_id='#mating_history_right_arrow_button'))
        return buttons


class MatingHistoryWindow(UIGridWindow):
    def __init__(self, mating_history: MatingHistory, rect: pygame.Rect, manager, window_display_title: str = "", element_id: Union[str, None] = None, object_id: Union[ObjectID, str, None] = None, visible: int = 1):
        self.mating_history = mating_history
        super().__init__(rect, manager, window_display_title, element_id, object_id, True, visible, 0, 0, self.subelements_method)

    def subelements_method(self, container):
        entry_panels = []
        for index, (entry, count) in enumerate(zip(*self.mating_history.get_history_counts())):
            entry_panels.append(MatingEntryPanel(count, entry, pygame.Rect(0,70*index,0,0), 0, self.ui_manager, container=container))
        return entry_panels

    def update(self, time_delta: float):
        if self.mating_history.something_changed:
            # print(f'something changed, so kill, {time.time() - self.timer}')
            self.grid_panel.hide() # this should hide the buttons too
            self.grid_panel.kill() # investigate the killing with grid_panel.kill doesn't kill the buttons inside
            self.grid_panel = None
            self.set_subelements()
            self.mating_history.acknowledge_changes()
        return super().update(time_delta)

class UICheckbox(UIButton):
    def __init__(self, relative_rect: pygame.Rect, checked: bool, manager, container = None, tool_tip_text: Union[str, None] = None, starting_height: int = 1, parent_element = None, object_id: Union[ObjectID, str, None] = None, anchors: Dict[str, str] = None, allow_double_clicks: bool = False, generate_click_events_from = frozenset([pygame.BUTTON_LEFT]), visible: int = 1):
        self.checked = checked
        if object_id is None:
            object_id = '#checkbox'
        super().__init__(relative_rect, '✓' if self.checked else '', manager, container, tool_tip_text, starting_height, parent_element, object_id, anchors, allow_double_clicks, generate_click_events_from, visible)
        if self.checked:
            self.select()

    def process_event(self, event: pygame.event.Event) -> bool:
        tmp = super().process_event(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self:
                self.checked = not self.checked
                if self.checked:
                    self.select()
                    self.set_text('✓')
                else:
                    self.unselect()
                    self.set_text('')
        return tmp


APPLY_VOLUME_CHANGE = pygame.event.custom_type()
class SettingsWindow(UIWindow):
    settings = None
    def __init__(self, rect: pygame.Rect, manager, window_display_title: str = "", element_id: Union[str, None] = None, object_id: Union[ObjectID, str, None] = None, resizable: bool = False, visible: int = 1):
        super().__init__(rect, manager, window_display_title, element_id, object_id, resizable, visible)
        self.settings = self.load_settings()
        self.full_screen_checkbox = UICheckbox(pygame.Rect(20, 20, 20, 20), self.settings['fullscreen'], manager, self)
        self.full_screen_label = UILabel(pygame.Rect(0,-20,100,20), local['Fullscreen'], manager, container=self,
            anchors={
                'left': 'left',
                'right': 'left',
                'bottom': 'top',
                'top': 'top',
                'left_target': self.full_screen_checkbox,
                'top_target': self.full_screen_checkbox
            })
        self.master_volume_slider = UIHorizontalSlider(pygame.Rect((20, 0), (100, 20)), int(self.settings['master_volume'] * 100), (0, 100), manager, self,
            anchors={
                'left': 'left',
                'right': 'left',
                'bottom': 'top',
                'top': 'top',
                'top_target': self.full_screen_checkbox
            })
        self.master_volume_value_label = UILabel(pygame.Rect(0,-20,25,20), str(self.master_volume_slider.current_value), manager, self,
            anchors={
                'left': 'left',
                'right': 'left',
                'bottom': 'top',
                'top': 'top',
                'left_target': self.master_volume_slider,
                'top_target': self.master_volume_slider
            })
        self.master_volume_label = UILabel(pygame.Rect(0,-20,120,20), local['Master volume'], manager, self,
            anchors={
                'left': 'left',
                'right': 'left',
                'bottom': 'top',
                'top': 'top',
                'left_target': self.master_volume_value_label,
                'top_target': self.master_volume_value_label
            })
        self.click_volume_slider = UIHorizontalSlider(pygame.Rect((20, 0), (100, 20)), int(self.settings['click_volume'] * 100), (0, 100), manager, self,
            anchors={
                'left': 'left',
                'right': 'left',
                'bottom': 'top',
                'top': 'top',
                'top_target': self.master_volume_slider
            })
        self.click_volume_value_label = UILabel(pygame.Rect(0,-20,25,20), str(self.click_volume_slider.current_value), manager, self,
            anchors={
                'left': 'left',
                'right': 'left',
                'bottom': 'top',
                'top': 'top',
                'left_target': self.click_volume_slider,
                'top_target': self.click_volume_slider
            })
        self.click_volume_label = UILabel(pygame.Rect(0,-20,120,20), local['Click volume'], manager, self,
            anchors={
                'left': 'left',
                'right': 'left',
                'bottom': 'top',
                'top': 'top',
                'left_target': self.click_volume_value_label,
                'top_target': self.click_volume_value_label
            })


        # bottom buttons stuff
        save_button_rect = pygame.Rect((0, 0), (100, 40))
        save_button_rect.left = 20
        save_button_rect.bottom = -20
        self.save_button = UIButton(save_button_rect, local['Save'], manager, self,
            anchors={
                'left': 'left',
                'right': 'left',
                'bottom': 'bottom',
                'top': 'bottom'
            })
        self.cancel_button = UIButton(save_button_rect, local['Cancel'], manager, self,
            anchors={
                'left': 'left',
                'right': 'left',
                'bottom': 'bottom',
                'top': 'bottom',
                'left_target': self.save_button
            })

    def process_event(self, event: pygame.event.Event) -> bool:
        consume = super().process_event(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.save_button:
                self.persist_settings()
            elif event.ui_element == self.cancel_button:
                self.kill()
        elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            if event.ui_element == self.master_volume_slider:
                self.master_volume_value_label.set_text(str(int(self.master_volume_slider.current_value)))
            elif event.ui_element == self.click_volume_slider:
                self.click_volume_value_label.set_text(str(int(self.click_volume_slider.current_value)))
        return consume

    def persist_settings(self, filename='settings'):
        settings = {}
        settings['fullscreen'] = self.full_screen_checkbox.is_selected
        settings['click_volume'] = self.click_volume_slider.current_value / 100
        settings['master_volume'] = self.master_volume_slider.current_value / 100
        with open(filename, 'w') as f:
            json.dump(settings, f, indent=2)
        if self.settings['master_volume'] != settings['master_volume'] or\
           self.settings['click_volume'] != settings['click_volume']:
            event_data = {'settings': settings}
            pygame.event.post(pygame.event.Event(APPLY_VOLUME_CHANGE, event_data))
        self.settings = settings

    @staticmethod
    def load_settings(filename='settings'):
        settings = {
            'fullscreen': True,
            'master_volume': 1,
            'click_volume': 1,
        }

        if os.path.exists(filename):
            with open(filename, 'r') as f:
                settings.update(json.load(f))
        return settings


class TutorialStage(IntEnum):
    BEFORE_FORAGE = 1
    NO_RESOURCES = 2
    RESOURCES_AVAILABLE = 3
    INSPECT_AVAILABLE = 4
    GENE_HELPER_TEXT_CLICKED = 5


class MendelTutorialWindow(UIWindow):
    def __init__(self, rect: pygame.Rect, manager):
        super().__init__(rect, manager, local['Mendelian Inheritance'])
        self.minimum_dimensions = (500, 700)
        self.interactive_panel_height = 400
        size = self.get_container().get_size()
        self.text_box = UITextBox(mendel_text, pygame.Rect((0,0), (size[0], size[1] - self.interactive_panel_height)), self.ui_manager, container=self)
        self.interactive_panel = None


class GUI(Game):
    current_tutorial_stage = TutorialStage.BEFORE_FORAGE # bad design TODO: rethink and refactor
    def __init__(self, window_size, manager, cursor_manager):
        self.command_out = 1
        super().__init__()
        Slot.empty_str = ''
        Slot.str_amount = lambda x: ''

        if not os.path.exists('save.forestry'):
            self.help_window()

        self.cursor_manager = cursor_manager
        self.cursor = Cursor(Slot(), pygame.Rect(0, 0, 64, 64), '', cursor_manager)
        self.window_size = window_size
        self.ui_manager = manager
        self.inspect_windows = []
        self.resource_panel_width = 330
        resource_panel_rect = pygame.Rect(0, 0, self.resource_panel_width, window_size[1])
        self.resource_panel = ResourcePanel(self, self.cursor, resource_panel_rect, 0, manager, visible=False)

        self.forage_button = UIButton(pygame.Rect(self.resource_panel.panel_container.rect.left, 0, resource_panel_rect.size[0]-6, 40), local['Forage'], manager, container=None,
            anchors={
                'top':'top',
                'bottom':'top',
                'left':'left',
                'right':'left',
                'top_target': self.resource_panel.build_dropdown
            }
        )
        self.open_inspect_window_button = UIButton(pygame.Rect(self.resource_panel.panel_container.rect.left, 0, resource_panel_rect.size[0]-6, 40), local['Open Inspect Window'], manager, container=None,
            anchors={
                'top':'top',
                'bottom':'top',
                'left':'left',
                'right':'left',
                'top_target': self.forage_button
            },
            visible=False)
        self.apiary_windows = []
        self.inventory_windows = []

        self.apiary_selection_list_width = 100
        self.apiary_selection_list = None

        self.mating_history_window = None
        self.load_confirm = None
        self.save_confirm = None

        esc_menu_rect = pygame.Rect(0, 0, 200, 500)
        esc_menu_rect.center = (self.window_size[0]/2, self.window_size[1]/2)
        self.esc_menu = UISelectionList(esc_menu_rect, [local['Greetings Window'], local['Settings'], local['Load'], local['Save'], local['Exit']], cursor_manager, visible=False, starting_height=30)

    def settings_window(self):
        return SettingsWindow(pygame.Rect((0,0), self.window_size), self.ui_manager, local['Settings'])

    def help_window(self):
        r = pygame.Rect(0, 0, self.window_size[0] - 100, self.window_size[1] - 100)
        r.center = (self.window_size[0]/2, self.window_size[1]/2)
        return UIMessageWindow(r, helper_text, self.ui_manager)

    def mendel_window(self):
        r = pygame.Rect(0, 0, 3/4*self.window_size[0], 3/4*self.window_size[1])
        r.center = (self.window_size[0]/2, self.window_size[1]/2)
        return MendelTutorialWindow(r, self.ui_manager)

    def open_mating_history_window(self):
        r = pygame.Rect(0, 0, 3/4*self.window_size[0], 3/4*self.window_size[1])
        r.center = (self.window_size[0]/2, self.window_size[1]/2)
        return MatingHistoryWindow(self.mating_history, r, self.ui_manager, 'Mating History')

    def open_inspect_window(self, rect: pygame.Rect = None):
        if rect is None:
            rect = pygame.Rect(pygame.mouse.get_pos(), (0, 0))
        self.inspect_windows.append(InspectWindow(self, self.cursor, rect, self.ui_manager))

    def open_apiary_selection_list(self):
        apiary_selection_list_rect = pygame.Rect(0, 0, self.apiary_selection_list_width, self.window_size[1])
        apiary_selection_list_rect.right = 0
        self.apiary_selection_list = UISelectionList(apiary_selection_list_rect, [], self.ui_manager,
            anchors={
                'top':'top',
                'bottom':'bottom',
                'left':'right',
                'right':'right',
            })
        self.update_windows_list()

    def open_mendel_notification(self):
        mouse_pos = self.ui_manager.get_mouse_position()
        r = pygame.Rect((mouse_pos[0]+260, mouse_pos[1]), (260, 200))
        return UIMessageWindow(r, local['mendel_notification'], self.ui_manager)

    def render(self):
        pass

    def print(self, *strings, sep=' ', end='\n', flush=False, out=None):
        print(*strings, sep=sep, end=end, flush=flush)

        thing = sep.join(map(str, strings)) + end
        if out is not None:
            thing = "<font color='#ED9FA6'>" + thing + "</font>"
        UIFloatingTextBox(1.3, (0, -50), thing.replace('\n', '<br>'), pygame.Rect(pygame.mouse.get_pos(), (250, -1)), self.cursor_manager)

    def update_windows_list(self):
        if self.apiary_selection_list is not None:
            self.apiary_selection_list.set_item_list(
                [local['Inventory'] + ' ' + i.name for i in self.inventories] +\
                [local['Apiary'] + ' ' + a.name for a in self.apiaries]
            )

    def set_dimensions(self, size):
        self.window_size = size
        if self.resource_panel is not None:
            self.resource_panel.set_dimensions((self.resource_panel_width, size[1]))
        if self.apiary_selection_list is not None:
            self.apiary_selection_list.set_dimensions((self.apiary_selection_list_width, size[1]))

    def process_event(self, event):
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.apiary_selection_list:
                if event.text.startswith(local['Apiary']):
                    index = int(event.text.split()[-1])
                    self.apiary_windows.append(
                        ApiaryWindow(self, self.apiaries[index], self.cursor, pygame.Rect(pygame.mouse.get_pos(), (300, 420)), self.ui_manager)
                    )
                else:
                    index = int(event.text.split()[-1])
                    self.inventory_windows.append(
                        InventoryWindow(self.inventories[index], self.cursor,
                            pygame.Rect(0, 0, self.apiary_selection_list.rect.left, self.window_size[1]),
                            self.ui_manager, resizable=True)
                        )
            elif event.ui_element == self.esc_menu:
                if event.text == local['Exit']:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                elif event.text == local['Load']:
                    r = pygame.Rect((pygame.mouse.get_pos()), (260, 200))
                    self.load_confirm = UIConfirmationDialog(r, self.cursor_manager, local['load_confirm'])
                elif event.text == local['Save']:
                    if os.path.exists('save.forestry'):
                        r = pygame.Rect((pygame.mouse.get_pos()), (260, 200))
                        self.save_confirm = UIConfirmationDialog(r, self.cursor_manager, local['save_confirm'])
                elif event.text == local['Settings']:
                    self.settings_window()
                elif event.text == local['Mendelian Inheritance']:
                    self.mendel_window()
                elif event.text == local['Greetings Window']:
                    self.help_window()
                elif event.text == local['Mating History']:
                    if self.mating_history_window is None:
                        self.mating_history_window = self.open_mating_history_window()
                self.esc_menu.hide()
        elif event.type == pygame_gui.UI_WINDOW_MOVED_TO_FRONT:
            if isinstance(event.ui_element, InventoryWindow):
                self.most_recent_inventory = event.ui_element.inv
        elif event.type == pygame_gui.UI_WINDOW_CLOSE:
            try:
                if isinstance(event.ui_element, InventoryWindow):
                    self.inventory_windows.remove(event.ui_element)
                elif isinstance(event.ui_element, ApiaryWindow):
                    self.apiary_windows.remove(event.ui_element)
                elif isinstance(event.ui_element, MatingHistoryWindow):
                    self.mating_history_window = None
                elif isinstance(event.ui_element, InspectWindow):
                    self.inspect_windows.remove(event.ui_element)
            except ValueError:
                print('Somehow window was closed that wasnt in any list:', event.ui_element)
            else:
                if isinstance(event.ui_element, (InventoryWindow, ApiaryWindow)):
                    self.open_apiary_selection_list()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.esc_menu.visible:
                    self.esc_menu.hide()
                else:
                    self.esc_menu.show()
        elif event.type == INSPECT_BEE:
            if self.total_inspections == 0:
                r = pygame.Rect((pygame.mouse.get_pos()), (260, 200))
                self.inspect_confirm = UIConfirmationDialog(r, self.ui_manager, local['Inspection popup'])
                self.inspect_confirm.bee_button = event.bee_button
                self.inspect_confirm.bee_stats = event.bee_stats
            else:
                self.inspect_bee(event.bee_button.slot.slot)
                event.bee_stats.process_inspect()
                event.bee_button.most_specific_combined_id = 'some nonsense' # dirty hack to make the button refresh inspect status
        elif event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
            if event.ui_element == self.load_confirm:
                self.load('save')
                self.print('Loaded save from disk')
            elif event.ui_element == self.save_confirm:
                self.save('save')
                self.print('Saved the game to the disk')
            elif event.ui_element == self.inspect_confirm:
                self.inspect_bee(self.inspect_confirm.bee_button.slot.slot)
                self.inspect_confirm.bee_stats.process_inspect() # added bee_stats and bee_button in INSPECT_BEE elif; refactor?
                self.inspect_confirm.bee_button.most_specific_combined_id = 'some nonsense' # dirty hack to make the button refresh inspect status
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.forage_button:
                if GUI.current_tutorial_stage == TutorialStage.BEFORE_FORAGE:
                    GUI.current_tutorial_stage = TutorialStage.NO_RESOURCES # progress the tutorial

                    self.apiary_windows.append(ApiaryWindow(self, self.apiaries[0], self.cursor, pygame.Rect((self.resource_panel_width, 0), (300, 420)), self.ui_manager))

                    self.inv_window = InventoryWindow(self.inv, self.cursor,
                        pygame.Rect(self.apiary_windows[0].rect.right, 0, self.window_size[0] - self.apiary_selection_list_width - self.apiary_windows[0].rect.right, self.window_size[1]),
                        self.ui_manager, resizable=True)
                    self.inventory_windows.append(self.inv_window)
                    self.most_recent_inventory = self.inv

                self.forage(self.most_recent_inventory)
            elif event.ui_element == self.open_inspect_window_button:
                self.open_inspect_window()
        elif event.type == TUTORIAL_STAGE_CHANGED:
            if self.current_tutorial_stage == TutorialStage.RESOURCES_AVAILABLE:
                self.resource_panel.show()
                self.resource_panel.build_dropdown.hide()
            elif self.current_tutorial_stage == TutorialStage.INSPECT_AVAILABLE:
                self.open_inspect_window_button.show()
                self.open_inspect_window(rect=pygame.Rect(-10, self.open_inspect_window_button.rect.bottom-13, 0, 0))
            elif self.current_tutorial_stage == TutorialStage.GENE_HELPER_TEXT_CLICKED:
                self.open_mendel_notification()
                self.esc_menu.set_item_list([local['Greetings Window'], local['Mendelian Inheritance'], local['Mating History'], local['Settings'], local['Load'], local['Save'], local['Exit']])

    def get_state(self):
        state = super().get_state()
        state['front_version'] = CURRENT_FRONT_VERSION
        state['current_tutorial_stage'] = self.current_tutorial_stage
        state['apiary_list_opened'] = self.apiary_selection_list is not None
        state['cursor_slot'] = self.cursor.slot
        insp_win = []
        insp_slots = []
        for window in self.inspect_windows:
            insp_win.append(window.relative_rect)
            insp_slots.append(window.bee_button.slot)
        state['inspect_windows'] = insp_win
        state['inspect_slots'] = insp_slots
        api_win = []
        for window in self.apiary_windows:
            api_win.append((window.apiary, window.relative_rect))
        state['apiary_windows'] = api_win
        inv_win = []
        for window in self.inventory_windows:
            inv_win.append((window.inv, window.relative_rect))
        state['inventory_windows'] = inv_win
        return state

    def load(self, name):
        saved = super().load(name)

        if saved.get('front_version', 0) < CURRENT_FRONT_VERSION:
            for update_front_func in update_front_versions[saved.get('front_version', 0):]:
                saved = update_front_func(saved)

        for window in self.apiary_windows:
            window.kill()
        for window in self.inventory_windows:
            window.kill()
        for window in self.inspect_windows:
            window.kill()
        if self.apiary_selection_list is not None:
            self.apiary_selection_list.kill()

        self.resource_panel.resources = self.resources
        self.cursor.slot = saved['cursor_slot']

        if saved['current_tutorial_stage'] >= TutorialStage.RESOURCES_AVAILABLE:
            self.resource_panel.show()
        if saved['current_tutorial_stage'] >= TutorialStage.INSPECT_AVAILABLE:
            self.open_inspect_window_button.show()
        if saved['apiary_list_opened']:
            self.open_apiary_selection_list()
        self.inspect_windows = [InspectWindow(self, self.cursor, rect, self.ui_manager) for rect in saved['inspect_windows']]
        for window, slot in zip(self.inspect_windows, saved['inspect_slots']):
            window.bee_button.slot = slot
        self.inventory_windows = [InventoryWindow(inv, self.cursor, rect, self.ui_manager) for inv, rect in saved['inventory_windows']]
        self.apiary_windows = [ApiaryWindow(self, api, self.cursor, rect, self.ui_manager) for api, rect in saved['apiary_windows']]
        if self.mating_history_window is not None:
            self.mating_history_window.mating_history = self.mating_history
            self.mating_history.something_changed = True
        return saved

def main():
    try:
        mixer.init()
        sounds = {
            'click_start': mixer.Sound('assets/ui-click-start.wav'),
            'click_end': mixer.Sound('assets/ui-click-end.wav')
        }
        pygame.init()

        pygame.display.set_caption('Bee Breeding Game')

        settings = SettingsWindow.load_settings()
        pygame.event.post(pygame.event.Event(APPLY_VOLUME_CHANGE, {'settings': settings}))


        if settings['fullscreen']:
            window_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            window_surface = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
        window_size = window_surface.get_rect().size

        background = pygame.Surface(window_size)
        background.fill(pygame.Color('#000000'))

        manager = pygame_gui.UIManager(window_size, 'theme.json', enable_live_theme_updates=False)
        cursor_manager = pygame_gui.UIManager(window_size, 'theme.json')

        game = None
        game = GUI(window_size, manager, cursor_manager)

        # settings = SettingsWindow(pygame.Rect(100, 100, 300, 300), manager, resizable=True)
        clock = pygame.time.Clock()
        is_running = True
        visual_debug = False
        while is_running:
            time_delta = clock.tick(60)/1000.0
            # state = game.get_state()

            for event in pygame.event.get():
                if event.type == pygame_gui.UI_BUTTON_START_PRESS:
                    sounds['click_start'].play()
                elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                    sounds['click_end'].play()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        visual_debug = not visual_debug
                        manager.set_visual_debug_mode(visual_debug)
                elif event.type == APPLY_VOLUME_CHANGE:
                    for key in ['click_start', 'click_end']:
                        sounds[key].set_volume(event.settings['master_volume'] * event.settings['click_volume'])
                elif event.type == pygame.QUIT:
                    is_running = False
                elif event.type == pygame.WINDOWSIZECHANGED:
                    if event.window is None:
                        manager.set_window_resolution((event.x, event.y))
                        cursor_manager.set_window_resolution((event.x, event.y))
                        background = pygame.Surface((event.x, event.y))
                        background.fill(pygame.Color('#000000'))
                        if game is not None:
                            game.set_dimensions((event.x, event.y))
                try:
                    if game is not None:
                        game.process_event(event)
                    consumed = cursor_manager.process_events(event)
                    if not consumed:
                        manager.process_events(event)
                except Exception as e:
                    if game is not None:
                        game.print(e, out=1)
                    else:
                        print(e)
                        print_exc()

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
