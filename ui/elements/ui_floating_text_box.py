from typing import Tuple, Dict, Union

import pygame
from pygame_gui.core import ObjectID
from pygame_gui.elements import UITextBox

class UIFloatingTextBox(UITextBox):
    def __init__(self, time_before_killing: float, speed: Tuple[float, float], html_text: str, relative_rect: pygame.Rect, manager, wrap_to_height: bool = False, layer_starting_height: int = 1, container=None, parent_element=None, object_id: Union[ObjectID, str, None] = None, anchors: Dict[str, str] = None, visible: int = 1):
        self.remaining_time = time_before_killing
        self.speed = speed
        super().__init__(html_text, relative_rect, manager, wrap_to_height, layer_starting_height, container, parent_element, object_id, anchors, visible)

    def update(self, time_delta: float):
        super().update(time_delta)
        if self.remaining_time <= 0:
            self.kill()
            return
        self.remaining_time -= time_delta
        tl = self.relative_rect.topleft
        self.set_relative_position((tl[0] + self.speed[0] * time_delta, tl[1] + self.speed[1] * time_delta))
