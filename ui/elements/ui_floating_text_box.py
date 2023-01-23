from typing import Dict, Tuple, Union

import pygame
from pygame_gui.core import ObjectID
from pygame_gui.elements import UITextBox


class UIFloatingTextBox(UITextBox):
    def __init__(self, time_before_killing: float, speed: Tuple[float, float], html_text: str, relative_rect: pygame.Rect, manager, wrap_to_height: bool = False, layer_starting_height: int = 1, container=None, parent_element=None, object_id: Union[ObjectID, str, None] = None, anchors: Dict[str, str] = None, visible: int = 1):
        self.remaining_time = time_before_killing
        self.speed = speed
        self.overall_movement_x = 0
        self.overall_movement_y = 0

        super().__init__(html_text, relative_rect, manager, wrap_to_height, layer_starting_height, container, parent_element, object_id, anchors, visible)

    def update(self, time_delta: float):
        super().update(time_delta)
        if self.remaining_time <= 0:
            self.kill()
            return
        self.remaining_time -= time_delta
        tl = self.relative_rect.topleft
        dx = self.speed[0] * time_delta
        dy = self.speed[1] * time_delta
        self.overall_movement_x += dx
        self.overall_movement_y += dy
        actual_dx = 0
        actual_dy = 0
        if self.overall_movement_x < -1 or self.overall_movement_x > 1:
            actual_dx = int(self.overall_movement_x)
            self.overall_movement_x -= actual_dx
        if self.overall_movement_y < -1 or self.overall_movement_y > 1:
            actual_dy = int(self.overall_movement_y)
            self.overall_movement_y -= actual_dy

        pos = (tl[0] + actual_dx, tl[1] + actual_dy)
        self.set_relative_position(pos)
