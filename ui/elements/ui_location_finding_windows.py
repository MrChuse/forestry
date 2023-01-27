import warnings
from typing import Optional, Union

import pygame
from pygame_gui.core import ObjectID
from pygame_gui.core.interfaces import IUIManagerInterface
from pygame_gui.elements import UIWindow
from pygame_gui.windows import UIConfirmationDialog, UIMessageWindow


class UILocationFindingWindow(UIWindow):
    def __init__(self, rect: pygame.Rect, manager: Optional[IUIManagerInterface] = None, window_display_title: str = "", element_id: Optional[str] = None, object_id: Optional[Union[ObjectID, str]] = None, resizable: bool = False, visible: int = 1):
        super().__init__(rect, manager, window_display_title, element_id, object_id, resizable, visible)
        self.find_valid_position(pygame.math.Vector2(self.get_abs_rect().center))

    def find_valid_position(self, position: pygame.math.Vector2) -> bool:
        window_rect = self.ui_manager.get_root_container().get_rect()

        self.rect.center = position
        if window_rect.contains(self.rect):
            self.relative_rect = self.rect.copy()
            self.set_position(self.rect.topleft)
            return True
        else:
            if self.rect.bottom > window_rect.bottom:
                self.rect.bottom = window_rect.bottom
            if self.rect.right > window_rect.right:
                self.rect.right = window_rect.right
            if self.rect.left < window_rect.left:
                self.rect.left = window_rect.left

        if window_rect.contains(self.rect):
            self.relative_rect = self.rect.copy()
            self.set_position(self.rect.topleft)
            return True
        else:
            self.relative_rect = self.rect.copy()
            warnings.warn("Unable to fit message window on screen")
            return False

class UILocationFindingConfirmationDialog(UIConfirmationDialog, UILocationFindingWindow):
    pass

class UILocationFindingMessageWindow(UIMessageWindow, UILocationFindingWindow):
    pass