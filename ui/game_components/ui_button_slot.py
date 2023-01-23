import warnings
from typing import Dict, Tuple, Union

import pygame
import pygame_gui
from pygame_gui.core import ObjectID, UIContainer
from pygame_gui.elements import UIButton, UIStatusBar, UITextBox, UITooltip

from config import local
from forestry import Bee, Drone, Princess, Queen, Slot

from ..custom_events import INSPECT_BEE
from .bee_stats import BeeStats
from .tutorial_stage import CurrentTutorialStage, TutorialStage


class InspectPopup(UITooltip):
    def __init__(self, bee_button: 'UIButtonSlot', hover_distance: Tuple[int, int], manager, parent_element = None, object_id: Union[ObjectID, str, None] = None, anchors: Dict[str, str] = None):
        super().__init__('', hover_distance, manager, parent_element, object_id, anchors)
        self.container = UIContainer(pygame.Rect(0, 0, -1, -1), manager, starting_height=self.ui_manager.get_sprite_group().get_top_layer()+1, parent_element=self)
        self.bee_button = bee_button
        if not bee_button.bee_inspectable:
            width = 318
            height = 177
        else:
            width = 170
            height = 35
        self.top_margin = 4
        self.inspect_button_height = 32

        bee_stats_rect = pygame.Rect(0, self.top_margin, width, height)
        self.inspect_button = None
        if self.bee_button.is_inspectable and CurrentTutorialStage.current_tutorial_stage >= TutorialStage.INSPECT_AVAILABLE:
            self.inspect_button = UIButton(pygame.Rect(0, self.top_margin, width - self.inspect_button_height, self.inspect_button_height), local['Inspect'], manager, self.container)
            self.inspect_button.set_hold_range((2, 2))
            bee_stats_rect.top += self.inspect_button_height

        self.bee_stats = BeeStats(self.bee_button.slot.slot, bee_stats_rect, manager, container=self.container)

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

        # if not window_rect.contains(pygame.Rect(int(position[0]), int(position[1]), 1, 1)):
        #     self.relative_rect = self.rect.copy()
        #     warnings.warn("initial position for tool tip is off screen,"
        #                   " unable to find valid position")
        #     return False

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
        """ # must have params:
            slot,
            rect,
            text, # probably empty
            ui_manager,
            container,
            # optional:
            highlighted=False,
            is_inspectable=True
        """
        self.slot = slot
        self._is_inspectable = kwargs.pop('is_inspectable', True)
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
        self.show_was_called_recently = False

        self.inspected_status = None
        if not self.slot.is_empty():
            r = pygame.Rect(0,0,0,0)
            r.size = 20, 20
            r.topright = self.relative_rect.topright
            self.inspected_status = UIStatusBar(r, self.ui_manager, container=self.ui_container, object_id='#InspectedStatus', anchors=self.kwargs.get('anchors'))
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

    @property
    def is_inspectable(self):
        return self._is_inspectable and self.bee_inspectable

    @property
    def bee_inspectable(self):
        return not self.slot.is_empty() and not self.slot.slot.inspected

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
            self.__init__(self.slot, *self.args, highlighted=self.highlighted, is_inspectable=self._is_inspectable, **self.kwargs) # rewrite using rebuild
        if self.inspected_status is not None and self.inspected_status.percent_full != int(self.slot.slot.inspected):
            self.inspected_status.percent_full = int(self.slot.slot.inspected)
        if self.slot.amount != self.saved_amount or self.show_was_called_recently:
            self.show_was_called_recently = False
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
            self.inspect_popup = InspectPopup(self, (0, hover_height), self.ui_manager)
            self.inspect_popup.find_valid_position(pygame.math.Vector2(self.rect.centerx, self.rect.centery))
        super().while_hovering(time_delta, mouse_pos)


    def hide(self):
        if self.visible:
            super().hide()
            self.text_box.hide()
            if self.inspected_status is not None:
                self.inspected_status.hide()

    def show(self):
        self.show_was_called_recently = True
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
