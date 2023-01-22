from typing import Dict, Union

import pygame
import pygame_gui
from pygame_gui.core import ObjectID
from pygame_gui.elements import UIButton


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
