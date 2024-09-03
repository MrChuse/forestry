from typing import Dict, List, Optional, Union, Tuple
import logging

import pygame
import pygame_gui
from pygame_gui.core import ObjectID, UIElement
from pygame_gui.core.interfaces import (IContainerLikeInterface,
                                        IUIManagerInterface)
from pygame_gui.elements import UIButton, UILabel, UIWindow, UIDropDownMenu

from config import ResourceTypes, local
from forestry import Resources

from ..elements import UITable, UICheckbox

def create_resource_button(resource, container):
    return UIButton(pygame.Rect(0, 0, 32, 32), '', container=container, tool_tip_text=local.get(resource, resource.name), object_id='#'+str(resource))

def create_resources_row(resources: dict, container):
    row = []
    for resource, amount in resources.items():
        row.append(create_resource_button(resource, container))
        row.append(UILabel(pygame.Rect(0, 0, 64, 28), str(amount), container=container))
    return row

def create_custom_resources_row(resources_list: list, resources: dict, container):
    row = []
    for resource, should_add in resources_list:
        if not should_add: continue
        row.append(create_resource_button(resource, container))
        row.append(UILabel(pygame.Rect(0, 0, 64, 28), str(resources[resource]), container=container))
    return row

class ResourcesPanelOptions(UIWindow):
    def __init__(self, resources: Resources, config: List[List[Tuple]]):
        self.resources = resources
        self.config = config
        self.config_recently_changed = False
        super().__init__(pygame.Rect(200, 200, 400, 400), window_display_title='Resources options')
        self.table = UITable(pygame.Rect(0, 0, 400, 400), container=self, fill_jagged=True, resizable=True, kill_on_repopulation=False, object_id='#panel_no_borders')
        self.plus_buttons = []
        self.minus_buttons = []
        self.checkboxes = []
        self.add_row_button = UIButton(pygame.Rect(0, 0, 96, 32), 'Add row', container=self, anchors={'top_target': self.table})
        self.change_resource_drop_down_menu = None
        self.non_local_res_list = None
        self.local_res_list = None
        self.rebuild_table()

    def rebuild_table(self):
        self.table.clear()
        self.plus_buttons = []
        self.minus_buttons = []
        self.checkboxes = []
        for row in self.config:
            table_row = []
            checkboxes_row = []
            for resource, selected in row:
                table_row.append(create_resource_button(resource, self.table))
                checkboxes_row.append(UICheckbox(pygame.Rect(0, 0, 24, 24), selected, container=self.table))
                table_row.append(checkboxes_row[-1])
            self.plus_buttons.append(UIButton(pygame.Rect(0, 0, 36, 32), '+', container=self.table))
            self.minus_buttons.append(UIButton(pygame.Rect(0, 0, 36, 32), '-', container=self.table))
            table_row.append(self.plus_buttons[-1])
            table_row.append(self.minus_buttons[-1])
            self.table.add_row(table_row)
            self.checkboxes.append(checkboxes_row)
        self.table.rebuild()
        s = self.table.get_relative_rect().size
        self.set_dimensions((s[0]+32, s[1]+200))

    def process_event(self, event: pygame.Event) -> bool:
        tmp = super().process_event(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.add_row_button:
                self.config.append([])
                self.config_recently_changed = True
                self.rebuild_table()
            else:
                for row_num, button in enumerate(self.plus_buttons):
                    if event.ui_element == button:
                        # add new resource to the row
                        self.config[row_num].append((ResourceTypes.HONEY, True))
                        self.config_recently_changed = True
                        self.rebuild_table()
                        break
                for row_num, button in enumerate(self.minus_buttons):
                    if event.ui_element == button:
                        try:
                            self.config[row_num].pop()
                        except IndexError:
                            self.config.pop(row_num)
                        self.config_recently_changed = True
                        self.rebuild_table()
                        break
                for row_num, row in enumerate(self.checkboxes):
                    for element_num, checkbox in enumerate(row):
                        if event.ui_element == checkbox:
                            self.config[row_num][element_num] = (self.config[row_num][element_num][0], checkbox.checked)
                            self.config_recently_changed = True
                            self.rebuild_table()
                            break
                for row_num, row in enumerate(self.table.table_contents):
                    for element_num, button in enumerate(row[::2]):
                        if event.ui_element == button:
                            if self.change_resource_drop_down_menu is not None:
                                self.change_resource_drop_down_menu.kill()
                            rect = pygame.Rect(0, 0, 150, 24)
                            rect.centerx = button.relative_rect.centerx
                            if rect.left < 0: rect.left = 0
                            rect.top = button.relative_rect.bottom
                            self.non_local_res_list = [res for res in self.resources.res]
                            self.local_res_list = [local[res] for res in self.resources.res]
                            self.change_resource_drop_down_menu = UIDropDownMenu(self.local_res_list, local[self.config[row_num][element_num][0]], rect, container=self)
                            self.change_resource_drop_down_menu.current_state.finish()
                            self.change_resource_drop_down_menu.current_state = self.change_resource_drop_down_menu.menu_states['expanded']
                            self.change_resource_drop_down_menu.current_state.start()
                            self.change_resource_drop_down_menu.resource_row_el_num = (row_num, element_num)
                            break
        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.change_resource_drop_down_menu:
                row_num, element_num = self.change_resource_drop_down_menu.resource_row_el_num
                self.config[row_num][element_num] = (self.non_local_res_list[self.local_res_list.index(event.text)], self.config[row_num][element_num][1])
                self.config_recently_changed = True
                self.rebuild_table()
                self.change_resource_drop_down_menu.kill()
                self.change_resource_drop_down_menu = None
                self.non_local_res_list = None
                self.local_res_list = None
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == pygame.BUTTON_LEFT:
                if self.change_resource_drop_down_menu is not None:
                    if not self.change_resource_drop_down_menu.hover_point(*self.ui_manager.get_mouse_position()):
                        self.change_resource_drop_down_menu.kill()
                        self.change_resource_drop_down_menu = None
                        self.non_local_res_list = None
                        self.local_res_list = None
        return tmp
class ResourcesPanel(UITable):
    def __init__(self, resources: Resources, relative_rect: pygame.Rect, starting_layer_height: int = 1, manager: Optional[IUIManagerInterface]  = None, *, element_id: str = 'panel', margins: Optional[Dict[str, int]]  = None, container: Optional[IContainerLikeInterface]  = None, parent_element: Optional[UIElement]  = None, object_id: Union[ObjectID, str, None]  = None, anchors: Optional[Dict[str, Union[str, UIElement]]]  = None, visible: int = 1):
        self.resources = resources
        self.shown_resources = None
        self.settings_button = None
        self.settings_window = None
        self.config = None
        super().__init__(relative_rect, starting_layer_height, manager, element_id=element_id, margins=margins, container=container, parent_element=parent_element, object_id=object_id, anchors=anchors, visible=visible, resizable=True, fill_jagged=True)

    def populate_table_contents(self):
        super().populate_table_contents()
        if self.settings_button is not None:
            self.settings_button.kill()
        self.settings_button = UIButton(pygame.Rect(0, 0, 32, 32), '', container=self, tool_tip_text='Options', object_id='@TooltipDelay')
        if len(self.resources) > 0 and self.config is not None:
            for row in self.config:
                custom_resources_row = create_custom_resources_row(row, self.resources, self)
                self.table_contents.append(custom_resources_row)
            self.table_contents[0].append(self.settings_button)

    def update_config(self):
        if self.config is None:
            self.config = [[(res, True) for res in self.resources.res]]
        if self.shown_resources is not None:
            for res in self.resources.res:
                if res not in self.shown_resources:
                    self.config[0].append((res, True))

    def update(self, time_delta: float):
        super().update(time_delta)
        if self.shown_resources != self.resources:
            self.update_config()
            self.shown_resources = self.resources.copy()
            self.rebuild()
        if self.settings_window is not None and self.settings_window.config_recently_changed:
            self.rebuild()
            self.settings_window.config_recently_changed = False

    def process_event(self, event: pygame.Event) -> bool:
        tmp = super().process_event(event)
        if event.type == pygame.MOUSEWHEEL:
            for button, resource_name in zip(self.table_contents[0][::2], self.resources.res):
                if button.hovered:
                    self.resources.add_resources({resource_name:event.y})
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.settings_button:
                self.settings_window = ResourcesPanelOptions(self.resources, self.config)
        return tmp
