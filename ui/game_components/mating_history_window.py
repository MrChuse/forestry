from typing import Union

import pygame
from pygame_gui.core import ObjectID

from forestry import MatingHistory

from ..elements import UIGridWindow
from . import MatingEntryPanel


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
            if self.grid_panel is not None:
                self.grid_panel.hide() # this should hide the buttons too
                self.grid_panel.kill() # investigate the killing with grid_panel.kill doesn't kill the buttons inside
                self.grid_panel = None
            self.set_subelements()
            self.mating_history.acknowledge_changes()
        return super().update(time_delta)
