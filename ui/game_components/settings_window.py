import json
import os
from typing import Union

import pygame
import pygame_gui
from pygame_gui.core import ObjectID
from pygame_gui.elements import UIButton, UIHorizontalSlider, UILabel, UIWindow

from config import local

from ..custom_events import APPLY_VOLUME_CHANGE
from ..elements import UICheckbox


class SettingsWindow(UIWindow):
    settings = None
    def __init__(self, rect: pygame.Rect, manager, window_display_title: str = "", element_id: Union[str, None] = None, object_id: Union[ObjectID, str, None] = None, resizable: bool = False, visible: int = 1):
        super().__init__(rect, manager, window_display_title, element_id, object_id, resizable, visible)
        self.settings = self.load_settings()
        self.full_screen_checkbox = UICheckbox(pygame.Rect(20, 20, 20, 20), self.settings['fullscreen'], manager, self)
        self.full_screen_label = UILabel(pygame.Rect(0,-20,100,20), local['Fullscreen'], manager, container=self,
            anchors={
                'left': 'left',
                'right': 'left',
                'bottom': 'top',
                'top': 'top',
                'left_target': self.full_screen_checkbox,
                'top_target': self.full_screen_checkbox
            })
        self.master_volume_slider = UIHorizontalSlider(pygame.Rect((20, 0), (100, 20)), int(self.settings['master_volume'] * 100), (0, 100), manager, self,
            anchors={
                'left': 'left',
                'right': 'left',
                'bottom': 'top',
                'top': 'top',
                'top_target': self.full_screen_checkbox
            })
        self.master_volume_value_label = UILabel(pygame.Rect(0,-20,25,20), str(self.master_volume_slider.current_value), manager, self,
            anchors={
                'left': 'left',
                'right': 'left',
                'bottom': 'top',
                'top': 'top',
                'left_target': self.master_volume_slider,
                'top_target': self.master_volume_slider
            })
        self.master_volume_label = UILabel(pygame.Rect(0,-20,120,20), local['Master volume'], manager, self,
            anchors={
                'left': 'left',
                'right': 'left',
                'bottom': 'top',
                'top': 'top',
                'left_target': self.master_volume_value_label,
                'top_target': self.master_volume_value_label
            })
        self.click_volume_slider = UIHorizontalSlider(pygame.Rect((20, 0), (100, 20)), int(self.settings['click_volume'] * 100), (0, 100), manager, self,
            anchors={
                'left': 'left',
                'right': 'left',
                'bottom': 'top',
                'top': 'top',
                'top_target': self.master_volume_slider
            })
        self.click_volume_value_label = UILabel(pygame.Rect(0,-20,25,20), str(self.click_volume_slider.current_value), manager, self,
            anchors={
                'left': 'left',
                'right': 'left',
                'bottom': 'top',
                'top': 'top',
                'left_target': self.click_volume_slider,
                'top_target': self.click_volume_slider
            })
        self.click_volume_label = UILabel(pygame.Rect(0,-20,120,20), local['Click volume'], manager, self,
            anchors={
                'left': 'left',
                'right': 'left',
                'bottom': 'top',
                'top': 'top',
                'left_target': self.click_volume_value_label,
                'top_target': self.click_volume_value_label
            })


        # bottom buttons stuff
        save_button_rect = pygame.Rect((0, 0), (100, 40))
        save_button_rect.left = 20
        save_button_rect.bottom = -20
        self.save_button = UIButton(save_button_rect, local['Save'], manager, self,
            anchors={
                'left': 'left',
                'right': 'left',
                'bottom': 'bottom',
                'top': 'bottom'
            })
        self.cancel_button = UIButton(save_button_rect, local['Cancel'], manager, self,
            anchors={
                'left': 'left',
                'right': 'left',
                'bottom': 'bottom',
                'top': 'bottom',
                'left_target': self.save_button
            })

    def process_event(self, event: pygame.event.Event) -> bool:
        consume = super().process_event(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.save_button:
                self.persist_settings()
            elif event.ui_element == self.cancel_button:
                self.kill()
        elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            if event.ui_element == self.master_volume_slider:
                self.master_volume_value_label.set_text(str(int(self.master_volume_slider.current_value)))
            elif event.ui_element == self.click_volume_slider:
                self.click_volume_value_label.set_text(str(int(self.click_volume_slider.current_value)))
        return consume

    def persist_settings(self, filename='settings'):
        settings = {}
        settings['fullscreen'] = self.full_screen_checkbox.is_selected
        settings['click_volume'] = self.click_volume_slider.current_value / 100
        settings['master_volume'] = self.master_volume_slider.current_value / 100
        with open(filename, 'w') as f:
            json.dump(settings, f, indent=2)
        if self.settings['master_volume'] != settings['master_volume'] or\
           self.settings['click_volume'] != settings['click_volume']:
            event_data = {'settings': settings}
            pygame.event.post(pygame.event.Event(APPLY_VOLUME_CHANGE, event_data))
        self.settings = settings

    @staticmethod
    def load_settings(filename='settings'):
        settings = {
            'fullscreen': True,
            'master_volume': 1,
            'click_volume': 1,
        }

        if os.path.exists(filename):
            with open(filename, 'r') as f:
                settings.update(json.load(f))
        return settings
