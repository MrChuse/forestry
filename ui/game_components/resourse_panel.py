from typing import Tuple, Union

import pygame
import pygame_gui
from pygame_gui.elements import UIPanel, UITextBox
from pygame_gui.windows import UIMessageWindow

from config import local
from forestry import Apiary, Inventory

from ..custom_events import TUTORIAL_STAGE_CHANGED
from ..elements import UINonChangingDropDownMenu
from . import ApiaryWindow, Cursor, InventoryWindow
from .tutorial_stage import CurrentTutorialStage, TutorialStage


class ResourcePanel(UIPanel):
    def __init__(self, game, cursor: Cursor, rect: pygame.Rect, starting_layer_height, manager, *args, **kwargs):
        self.game = game
        self.resources = game.resources
        self.cursor = cursor

        self.shown_resources = None

        super().__init__(rect, starting_layer_height, manager, *args, **kwargs)
        bottom_buttons_height = 40

        r = pygame.Rect((0, 0), (rect.size[0]-6, rect.size[1] - 440))
        self.text_box = UITextBox(str(self.resources),
            r,
            manager,
            container=self)

        self.original_build_options = ['Inventory', 'Apiary', 'Alveary']
        self.known_build_options = []
        self.local_build_options = []
        self.build_dropdown = UINonChangingDropDownMenu([], local['Build'], pygame.Rect(0, 0, rect.size[0]-6, bottom_buttons_height), manager, container=self,
            anchors={
                'top':'top',
                'bottom':'top',
                'left':'left',
                'right':'right',
                'top_target': self.text_box
            }, visible=False)

    def update_text_box(self):
        if CurrentTutorialStage.current_tutorial_stage == TutorialStage.NO_RESOURCES and len(self.resources) > 0:
            CurrentTutorialStage.current_tutorial_stage = TutorialStage.RESOURCES_AVAILABLE
            pygame.event.post(pygame.event.Event(TUTORIAL_STAGE_CHANGED, {}))
        elif CurrentTutorialStage.current_tutorial_stage == TutorialStage.RESOURCES_AVAILABLE and 'honey' in self.resources:
            CurrentTutorialStage.current_tutorial_stage = TutorialStage.INSPECT_AVAILABLE
            pygame.event.post(pygame.event.Event(TUTORIAL_STAGE_CHANGED, {}))

        if self.shown_resources != self.resources:
            self.shown_resources = self.resources.copy()
            text = str(self.resources)
            for r in local['resources'].items():
                text = text.replace(*r)
            self.text_box.set_text(text)

            available_build_options = self.game.get_available_build_options()
            if len(available_build_options) > 0:
                self.build_dropdown.show()
            for option in available_build_options:
                if option not in self.known_build_options:
                    self.known_build_options.append(option)
                    self.local_build_options.append(local[option])
                    self.build_dropdown.add_options([local[option]])

    def update(self, time_delta):
        self.update_text_box()
        super().update(time_delta)

    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.build_dropdown:
                if event.text != 'Build':
                    text = event.text
                    index = self.local_build_options.index(text)
                    building_name = self.known_build_options[index]
                    building = self.game.build(building_name.lower())
                    if isinstance(building, Apiary):
                        window = ApiaryWindow(self.game, building, self.cursor, pygame.Rect(pygame.mouse.get_pos(), (300, 420)), self.ui_manager)
                        self.game.apiary_windows.append(window)
                        self.game.update_windows_list()
                    elif isinstance(building, Inventory):
                        if self.game.apiary_selection_list is not None:
                            width = self.game.apiary_selection_list.rect.left
                        else:
                            width = self.game.window_size[0]
                        window = InventoryWindow(building, self.cursor,
                        pygame.Rect(0, 0, width, self.game.window_size[1]),
                        self.ui_manager, resizable=True)
                        self.game.inventory_windows.append(window)
                        self.game.update_windows_list()
                    else: #if isinstance(building, Alveary):
                        win_window = UIMessageWindow(pygame.Rect((0,0), self.game.window_size), '<effect id=bounce><font size=7.0>You won the demo!</font></effect>', self.ui_manager, window_title='You won the demo!', object_id='#WinWindow')
                        win_window.text_block.set_active_effect(pygame_gui.TEXT_EFFECT_BOUNCE, effect_tag='bounce')
        return super().process_event(event)

    def show(self):
        super().show()
        if len(self.game.get_available_build_options()) == 0:
            self.build_dropdown.hide()
