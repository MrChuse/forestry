import math
import time
import os.path
from typing import List, Tuple, Union

import pygame
from pygame import mixer
import pygame_gui
from pygame_gui.elements import (UIButton, UIPanel, UIProgressBar, UIStatusBar,
                                 UITextBox, UIWindow, UIDropDownMenu, UISelectionList)
from pygame_gui.elements.ui_drop_down_menu import UIExpandedDropDownState
from pygame_gui.core import ObjectID
from pygame_gui.windows import UIMessageWindow, UIConfirmationDialog

from forestry import Apiary, Bee, Drone, Game, Inventory, Princess, Queen, Resources, Slot, local, dominant, helper_text, mendel_text, dom_local

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



class UIWindowNoX(UIWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enable_close_button = False
        self.title_bar_close_button_width = 0
        self.rebuild()

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
        self.text_box = UITextBox('1', r, self.ui_manager, container=self.ui_container, layer_starting_height=2, object_id=ObjectID(class_id='@Centered'))
        self.text_box.hide()
        self.saved_amount = 0
        r = pygame.Rect(0,0,0,0)
        r.size = 20, 20
        r.topright = self.relative_rect.topright
        self.inspected_status = None
        if not self.slot.is_empty():
            self.inspected_status = UIRelativeStatusBar(r, self.ui_manager, container=self.ui_container, object_id='#InspectedStatus')
            self.inspected_status.percent_full = int(self.slot.slot.inspected)
        self.highlighted = highlighted

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
            text = self.slot.small_str()
            text = text if text != '' else None
            self.args = (pygame.Rect(pos, size),) + self.args[1:]
            self.kwargs['object_id'] = obj_id
            self.kwargs['tool_tip_text'] = text
            self.__init__(self.slot, *self.args, highlighted=self.highlighted, **self.kwargs)
        if self.inspected_status is not None and self.inspected_status.percent_full != int(self.slot.slot.inspected):
            self.inspected_status.percent_full = int(self.slot.slot.inspected)
        if self.slot.amount != self.saved_amount:
            if self.slot.amount < 2:
                self.text_box.hide()
                self.saved_amount = 0
            else:
                self.text_box.set_text(str(self.slot.amount))
                self.saved_amount = self.slot.amount
                self.text_box.show()
        return super().update(time_delta)

    def set_dimensions(self, dimensions: Union[pygame.math.Vector2, Tuple[int, int], Tuple[float, float]]):
        tmp = super().set_dimensions(dimensions)
        text_box_size = self.text_box.rect.size
        bottomright = self.relative_rect.bottomright
        pos = (bottomright[0] - text_box_size[0], bottomright[1] - text_box_size[1])
        self.text_box.set_relative_position(pos)
        if self.inspected_status is not None:
            inspected_width = self.inspected_status.rect.width
            topright = self.relative_rect.topright
            pos = (topright[0] - inspected_width, topright[1])
            self.inspected_status.set_relative_position(pos)
        return tmp

    def kill(self):
        self.text_box.kill()
        if self.inspected_status is not None:
            self.inspected_status.kill()
        return super().kill()
    
    def process_event(self, event: pygame.event.Event) -> bool:
        ret = super().process_event(event)
        if event.type == pygame_gui.UI_BUTTON_ON_HOVERED: # TODO: come up with better solution
            if isinstance(event.ui_element, UIButtonSlot):
                if event.ui_element.slot.slot is not None and event.ui_element.slot.slot == self.slot.slot:
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

class InventoryWindow(UIWindow):
    def __init__(self, inv, button_hor, button_vert,  cursor: Cursor, rect, manager, *args, margin=5, **kwargs):
        self.inv = inv
        self.button_hor = button_hor
        self.button_vert = button_vert
        self.margin = margin
        self.cursor = cursor
        if len(self.inv) != button_hor * button_vert:
            raise ValueError(
                'Inventory should have button_hor*button_vert number of slots')

        self.title_bar_sort_button_width = 100
        self.sort_window_button = None
        self.buttons : Union[List[List[UIButtonSlot]], None] = None

        kwargs['window_display_title'] = local['Inventory'] + ' ' + inv.name
        kwargs['resizable'] = True
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
                    b.set_relative_position(pos)
                    b.set_dimensions(bsize)
                    
    
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
                        mods = pygame.key.get_mods()
                        if mods & pygame.KMOD_LSHIFT:
                            self.inv.take_all(index)
                        else:
                            process_cursor_slot_interaction(event, self.cursor, self.inv[index])
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
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
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
                        self.cursor.slot.put(*bee1)
                        self.apiary.put_princess(*bee2)
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
                            self.game.print('Cursor not empty', out=1)
        return super().process_event(event)
    
    def update(self, time_delta):
        self.update_health_bar()
        self.princess_button.tool_tip_text = self.princess_button.slot.small_str()
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
        self.inspect_button = UIButton(pygame.Rect(0, 0, rect.width - inspect_button_height - 6, inspect_button_height), local['Inspect'], manager, self)
        bee_button_rect = pygame.Rect(0, 0, inspect_button_height, inspect_button_height)
        bee_button_rect.right = rect.right - 6
        self.bee_button = UIButtonSlot(Slot(), bee_button_rect, '', manager, self,)
        self.bee_button.empty_object_id = '#DroneEmpty'
        self.text_box = UITextBox('', pygame.Rect(0, inspect_button_height, rect.width-6, rect.height-inspect_button_height-6), manager, container=self)
        self.inspect_confirm = None
    
    def process_inspect(self):
        bee = self.bee_button.slot.slot
        if bee is None:
            self.text_box.set_text('')
            return
        res = []
        if not bee.inspected:
            res.append(bee.small_str())
        else:
            name, bee_species_index = local[bee.type_str]
            res.append(name)
            genes = vars(bee.genes)
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
                res.append(f'  {local[key]} : <font color={"#ec3661" if dominant[genes[key][0]] else "#3687ec"}>{dom_local(allele0, dom0)}</font>, <font color={"#ec3661" if dominant[genes[key][1]] else "#3687ec"}>{dom_local(allele1, dom1)}</font>')
        self.text_box.set_text('<br>'.join(res))

    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.bee_button:
                self.cursor.slot.swap(self.bee_button.slot)
                self.process_inspect()
            elif event.ui_element == self.inspect_button:
                if self.game.total_inspections == 0:
                    r = pygame.Rect((pygame.mouse.get_pos()), (200, 100))
                    self.inspect_confirm = UIConfirmationDialog(r, self.ui_manager, local['Inspection popup'])
                else:
                    self.game.inspect_bee(self.bee_button.slot.slot)
                    self.process_inspect()
                    self.bee_button.most_specific_combined_id = 'some nonsense' # dirty hack to make the button refresh inspect status
        if event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
            if event.ui_element == self.inspect_confirm:
                self.game.inspect_bee(self.bee_button.slot.slot)
                self.process_inspect()
                self.bee_button.most_specific_combined_id = 'some nonsense' # dirty hack to make the button refresh inspect status
        return super().process_event(event)



class ResourcePanel(UIPanel):
    def __init__(self, game: 'GUI', cursor: Cursor, rect: pygame.Rect, starting_layer_height, manager, *args, **kwargs):
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
        self.forage_button = UIButton(pygame.Rect(0, 0, rect.size[0]-6, bottom_buttons_height), local['Forage'], manager, container=self,
            anchors={
                'top':'top',
                'bottom':'bottom',
                'left':'left',
                'right':'right',
                'top_target': self.text_box
            }
        )
        self.original_build_options = ['Inventory', 'Apiary', 'Alveary']
        self.local_build_options = [local[option] for option in self.original_build_options]
        self.build_dropdown = UINonChangingDropDownMenu(self.local_build_options, local['Build'], pygame.Rect(0, 0, rect.size[0]-6, bottom_buttons_height), manager, container=self,
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
        text = str(self.resources)
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
                        InventoryWindow(building, 7, 7, self.cursor, 
                        pygame.Rect(0, 0, self.game.apiary_selection_list.rect.left, self.game.window_size[1]),
                        self.ui_manager, resizable=True)
                        self.game.update_windows_list()
                    else: #if isinstance(building, Alveary):
                        win_window = UIMessageWindow(pygame.Rect((0,0), self.game.window_size), '<effect id=bounce><font size=7.0>You won the demo!</font></effect>', self.ui_manager, window_title='You won the demo!', object_id='#WinWindow')
                        win_window.text_block.set_active_effect(pygame_gui.TEXT_EFFECT_BOUNCE, effect_tag='bounce')
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.forage_button:
                self.game.forage(self.game.most_recent_inventory)
        return super().process_event(event)

class GUI(Game):
    def __init__(self, window_size, manager, cursor_manager):
        self.command_out = 1
        super().__init__()
        Slot.empty_str = ''
        Slot.str_amount = lambda x: ''

        self.cursor = Cursor(Slot(), pygame.Rect(0, 0, 64, 64), '', cursor_manager)
        self.window_size = window_size
        self.ui_manager = manager
        resource_panel_width = 330
        self.resource_panel = ResourcePanel(self, self.cursor, pygame.Rect(0, 0, resource_panel_width, window_size[1]), 0, manager)
        self.apiary_windows = []
        self.inventory_windows = []
        api_window = ApiaryWindow(self, self.apiaries[0], self.cursor, pygame.Rect((resource_panel_width, 0), (300, 420)), manager)
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
        self.apiary_selection_list = UISelectionList(apiary_selection_list_rect, [], manager,
            anchors={
                'top':'top',
                'bottom':'bottom',
                'left':'right',
                'right':'right',
                'right_target': self.right_text_box
            })
        self.update_windows_list()
        self.inv_window = InventoryWindow(self.inv, 7, 7, self.cursor,
            pygame.Rect(api_window.rect.right, 0, self.apiary_selection_list.rect.left-api_window.rect.right, window_size[1]),
            manager, resizable=True)
        self.inventory_windows.append(self.inv_window)
        self.most_recent_inventory = self.inv
        esc_menu_rect = pygame.Rect(0, 0, 200, 500)
        esc_menu_rect.center = (self.window_size[0]/2, self.window_size[1]/2)
        self.esc_menu = UISelectionList(esc_menu_rect, [local['Greetings Window'], local['Mendelian Inheritance'], local['Load'], local['Save'], local['Exit']], cursor_manager, visible=False, starting_height=30)
        
        if not os.path.exists('save.forestry'):
            self.help_window()

    def help_window(self):
        r = pygame.Rect(0, 0, self.window_size[0] - 100, self.window_size[1] - 100)
        r.center = (self.window_size[0]/2, self.window_size[1]/2)
        return UIMessageWindow(r, helper_text, self.ui_manager)

    def mendel_window(self):
        r = pygame.Rect(0, 0, 3/4*self.window_size[0], 3/4*self.window_size[1])
        r.center = (self.window_size[0]/2, self.window_size[1]/2)
        return UIMessageWindow(r, mendel_text, self.ui_manager)

    def render(self):
        pass

    def print(self, *strings, sep=' ', end='\n', flush=False, out=None):
        print(*strings, sep=sep, end=end, flush=flush)

        thing = sep.join(map(str, strings)) + end
        if out is not None:
            thing = "<font color='#ED9FA6'>" + thing + "</font>"
        self.right_text_box.append_html_text(thing.replace('\n', '<br>'))
    
    def update_windows_list(self):
        self.apiary_selection_list.set_item_list(
            [local['Inventory'] + ' ' + i.name for i in self.inventories] +\
            [local['Apiary'] + ' ' + a.name for a in self.apiaries]
        )

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
                        InventoryWindow(self.inventories[index], 7, 7, self.cursor,
                            pygame.Rect(0, 0, self.apiary_selection_list.rect.left, self.window_size[1]),
                            self.ui_manager, resizable=True)
                        )
            elif event.ui_element == self.esc_menu:
                if event.text == local['Exit']:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                elif event.text == local['Load']:
                    self.load('save')
                    self.print('Loaded save from disk')
                elif event.text == local['Save']:
                    self.save('save')
                    self.print('Saved the game to the disk')
                elif event.text == local['Mendelian Inheritance']:
                    self.mendel_window()
                elif local['Greetings Window']:
                    self.help_window()
                self.esc_menu.hide()
        elif event.type == pygame_gui.UI_WINDOW_MOVED_TO_FRONT:
            if isinstance(event.ui_element, InventoryWindow):
                self.most_recent_inventory = event.ui_element.inv
        elif event.type == pygame_gui.UI_WINDOW_CLOSE:
            try:
                if isinstance(event.ui_element, InventoryWindow):
                    self.inventory_windows.remove(event.ui_element)
                if isinstance(event.ui_element, ApiaryWindow):
                    self.apiary_windows.remove(event.ui_element)
            except ValueError:
                pass
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.esc_menu.visible:
                    self.esc_menu.hide()
                else:
                    self.esc_menu.show()
    
    def get_state(self):
        state = super().get_state()
        state['cursor_slot'] = self.cursor.slot
        state['inspect_slot'] = self.resource_panel.inspect_panel.bee_button.slot
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
        for window in self.apiary_windows:
            window.kill()
        for window in self.inventory_windows:
            window.kill()
        for i, row in enumerate(self.inv_window.buttons):
            for j, b in enumerate(row):
                slot = self.inv[j * len(row) + i]
                b.slot = slot
        self.resource_panel.resources = self.resources
        self.update_windows_list()
        self.cursor.slot = saved['cursor_slot']
        self.resource_panel.inspect_panel.bee_button.slot = saved['inspect_slot']
        self.inventory_windows = [InventoryWindow(inv, 7, 7, self.cursor, rect, self.ui_manager) for inv, rect in saved['inventory_windows']]
        self.apiary_windows = [ApiaryWindow(self, api, self.cursor, rect, self.ui_manager) for api, rect in saved['apiary_windows']]
        return saved

def main():
    try:
        mixer.init()
        sounds = {
            'click-start': mixer.Sound('assets/ui-click-start.wav'),
            'click-end': mixer.Sound('assets/ui-click-end.wav')
        }
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
                elif event.type == pygame_gui.UI_BUTTON_START_PRESS:
                    sounds['click-start'].play()
                elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                    sounds['click-end'].play()
                try:
                    if game is not None:
                        game.process_event(event)
                    consumed = cursor_manager.process_events(event)
                    if not consumed:
                        manager.process_events(event)
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
