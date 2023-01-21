from typing import List

import pygame
import pygame_gui
from pygame_gui.elements import (UIButton, UIPanel, UIStatusBar, UITextBox,
                                 UIWindow)

from config import local, mendel_text


class MendelTutorialWindow(UIWindow):
    def __init__(self, rect: pygame.Rect, manager):
        super().__init__(rect, manager, local['Mendelian Inheritance'])
        self.set_minimum_dimensions((700, 500))
        self.interactive_panel_height = self.get_container().get_rect().height//2
        self.arrow_buttons_height = 40
        size = self.get_container().get_size()
        self.text_boxes : List[UITextBox] = []
        for text in mendel_text:
            text_box = UITextBox(text, pygame.Rect((0,0), (size[0], size[1] - self.interactive_panel_height - self.arrow_buttons_height)), self.ui_manager, container=self)
            self.text_boxes.append(text_box)

        self.panels = [UIPanel(pygame.Rect((0,0), (size[0], self.interactive_panel_height)), manager=self.ui_manager, container=self,
            anchors={
                'left': 'left',
                'right': 'right',
                'top': 'top',
                'bottom': 'bottom',
                'top_target': text_box
            }) for text_box in self.text_boxes]
        self.left_arrow_button = UIButton(pygame.Rect(0, -self.arrow_buttons_height, self.arrow_buttons_height, self.arrow_buttons_height), '<', self.ui_manager, self,
            anchors={
                'left': 'left',
                'right': 'left',
                'top': 'bottom',
                'bottom': 'bottom'
            })
        self.right_arrow_button = UIButton(pygame.Rect(-self.arrow_buttons_height, -self.arrow_buttons_height, self.arrow_buttons_height, self.arrow_buttons_height), '>', self.ui_manager, self,
            anchors={
                'left': 'right',
                'right': 'right',
                'top': 'bottom',
                'bottom': 'bottom'
            })
        progress_bar_rect = pygame.Rect(0, -self.arrow_buttons_height, 300, self.arrow_buttons_height)
        progress_bar_rect.centerx = self.get_container().get_rect().width//2
        self.progress_bar = UIStatusBar(progress_bar_rect, self.ui_manager, container=self, object_id='#MendelianTutorialProgressBar',
            anchors={
                'left': 'left',
                'right': 'left',
                'top': 'bottom',
                'bottom': 'bottom'
            })
        self.current_page = 0
        self.progress_bar.status_text = lambda : f'{self.current_page+1} / {len(self.text_boxes)}'
        self.progress_bar.redraw()
        self.show_current_page()

    def add_page(self, amount: int):
        self.current_page += amount
        self.current_page = min(self.current_page, len(mendel_text)-1)
        self.current_page = max(self.current_page, 0) # clamp
        self.show_current_page()

    def set_page(self, page: int):
        self.current_page = page
        self.show_current_page()

    def show_current_page(self):
        for text_box in self.text_boxes:
            text_box.hide()
        for panel in self.panels:
            panel.hide()
        self.text_boxes[self.current_page].show()
        self.panels[self.current_page].show()

    def process_event(self, event: pygame.event.Event) -> bool:
        consumed = super().process_event(event)
        if event.type == pygame_gui. UI_BUTTON_PRESSED:
            if event.ui_element == self.left_arrow_button:
                self.add_page(-1)
                self.progress_bar.percent_full = self.current_page / (len(self.text_boxes)-1)
            elif event.ui_element == self.right_arrow_button:
                self.add_page(1)
                self.progress_bar.percent_full = self.current_page / (len(self.text_boxes)-1)
        return consumed
