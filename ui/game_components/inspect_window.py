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
