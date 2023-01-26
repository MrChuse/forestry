from typing import Union

import pygame
import pygame_gui
from pygame_gui.core import ObjectID
from pygame_gui.elements import UIButton, UIWindow

from config import local
from forestry import Game, Slot

from ..custom_events import INSPECT_BEE
from . import BeeStats, Cursor, UIButtonSlot


class InspectWindow(UIWindow):
    def __init__(self, game: Game, cursor: Cursor, rect: pygame.Rect, manager, element_id: Union[str, None] = None, object_id: Union[ObjectID, str, None] = None):
        self.game = game
        self.cursor = cursor
        rect = pygame.Rect(rect.left, rect.top, 350, 300)
        self.bee_stats = None
        super().__init__(rect, manager, local['Inspect Window'], element_id, object_id, resizable=False, visible=1)
        self.inspect_button_height = 64
        bee_button_rect = pygame.Rect(-self.inspect_button_height, 0, self.inspect_button_height, self.inspect_button_height)
        self.bee_button = UIButtonSlot(Slot(), bee_button_rect, '', manager, self,
            anchors={
                'left': 'right',
                'right': 'right',
                'bottom': 'top',
                'top': 'top',
            }
        )
        self.inspect_button = UIButton(pygame.Rect(0, 0, self.get_container().get_size()[0] - self.inspect_button_height, self.inspect_button_height), local['Inspect'], manager, self,
            anchors={
                'left':'left',
                'right': 'right',
                'right_target': self.bee_button
            }
        )
        self.bee_button.empty_object_id = '#DroneEmpty'
        self.bee_stats = BeeStats(None, pygame.Rect(0, self.inspect_button_height, self.get_container().get_rect().width, self.get_container().get_rect().height-self.inspect_button_height), manager, container=self, resizable=True)

    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.bee_button:
                self.cursor.slot.swap(self.bee_button.slot)
                self.bee_stats.bee = self.bee_button.slot.slot
                self.bee_stats.rebuild()
            elif event.ui_element == self.inspect_button:
                event_data = {'ui_element': self}
                pygame.event.post(pygame.event.Event(INSPECT_BEE, event_data))
        return super().process_event(event)

    def rebuild(self):
        super().rebuild()
        if self.bee_stats is not None:
            self.bee_stats.rebuild()
            self.reshape_according_to_bee_stats()

    def reshape_according_to_bee_stats(self):
        self.set_dimensions(self.ui_container.get_size())
        self.bee_stats.rebuild()
        bee_stats_size_x, bee_stats_size_y = self.bee_stats.get_abs_rect().size
        new_dimensions = (bee_stats_size_x + (2 * self.shadow_width) + self.bee_stats.shadow_width,
                          bee_stats_size_y + self.title_bar_height + self.inspect_button_height + (2 * self.shadow_width) + self.bee_stats.shadow_width)
        self.set_dimensions(new_dimensions)
