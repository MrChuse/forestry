from typing import Optional, Union

import pygame
from pygame_gui.core import ObjectID
from pygame_gui.core.interfaces import IUIManagerInterface
from pygame_gui.elements import UIWindow, UILabel, UIButton

from config import local
from forestry import AchievementManager
from ..elements import UITable

class AchievementsWindow(UIWindow):
    def __init__(self, achievement_manager: AchievementManager, rect: pygame.Rect, manager: Optional[IUIManagerInterface] = None, window_display_title: str = "", element_id: Optional[str] = None, object_id: Union[ObjectID, str, None] = None, resizable: bool = False, visible: int = 1, draggable: bool = True):
        self.achievement_manager = achievement_manager
        self.achieved_label : Optional[UILabel]  = None
        self.achieved_table : Optional[UITable]  = None
        self.future_achievements_label : Optional[UILabel]  = None
        self.future_achievements_achievement_label : Optional[UILabel]  = None
        self.shown_achievements : Optional[AchievementManager]  = None
        super().__init__(rect, manager, window_display_title, element_id, object_id, resizable, visible, draggable)

    def rebuild(self):
        super().rebuild()
        if self.achieved_table is None:
            self.achieved_label = UILabel(pygame.Rect(0,0, self.get_container().get_rect().w, 28),
                                        local['achieved'], container=self)
            self.achieved_table = UITable(pygame.Rect(0, 0, 0, 0), resizable=True, container=self, kill_on_repopulation=False, fill_jagged=True,
                                 anchors={'top_target': self.achieved_label})
            self.future_achievements_label = UILabel(pygame.Rect(0,0, self.get_container().get_rect().w, 28),
                                             local['next_achievements'], container=self,
                                             anchors={'top_target': self.achieved_table})

        self.achieved_table.clear()
        self.achieved_table.add_row([UILabel(pygame.Rect(0, 0, self.rect.w//3, 28), local['requirement'], container=self.achieved_table),
                            UILabel(pygame.Rect(0, 0, self.rect.w//3, 28), local['reward'], container=self.achieved_table),
                            UILabel(pygame.Rect(0, 0, self.rect.w//3, 28), local['comment'], container=self.achieved_table)])
        for achievement in self.achievement_manager.achievements:
            if achievement.achieved:
                row = [
                    UILabel(pygame.Rect(0, 0, self.rect.w//3, 28), achievement.requirement_str, container=self.achieved_table, object_id='@SmallFont'),
                    UILabel(pygame.Rect(0, 0, self.rect.w//3, 28), achievement.reward_str, container=self.achieved_table, object_id='@SmallFont'),
                    ]
                if achievement.comment_str:
                    row.append(UIButton(pygame.Rect(0, 0, self.rect.w//3-100, 28), local['hover'], container=self.achieved_table, object_id='@TooltipDelay', tool_tip_text=achievement.comment_str, tool_tip_object_id='@SmallFont'))
                self.achieved_table.add_row(row)
        self.achieved_table.rebuild()

        for achievement in self.achievement_manager.achievements:
            if not achievement.achieved:
                if self.future_achievements_achievement_label is not None:
                    self.future_achievements_achievement_label.kill()
                    self.future_achievements_achievement_label = None
                self.future_achievements_achievement_label = UILabel(pygame.Rect(0,0, self.get_container().get_rect().w, 28),
                                             achievement.requirement_str, container=self,
                                             anchors={'top_target': self.future_achievements_label})
                break


    def update(self, time_delta: float):
        if self.achievement_manager.changed_recently: # and not self.first_frame:
            self.rebuild()
            self.achievement_manager.changed_recently = False
        super().update(time_delta)