from typing import Dict, Iterable, List, Optional, Tuple, Union

import pygame
import pygame_gui
from pygame_gui.core import ObjectID, UIElement, UIContainer
from pygame_gui.core.interfaces import IContainerLikeInterface, IUIManagerInterface
from pygame_gui.elements import UIButton, UITooltip
from pygame_gui.windows import UIMessageWindow

from forestry import Apiary, Inventory, Resources

from ..elements import UITable
from .resources_panel import create_resources_row
from .ui_button_slot import find_valid_position
from . import ApiaryWindow, InventoryWindow
from config import local, INVENTORY_WINDOW_SIZE

class BuildPopup(UITooltip):
    def __init__(self, cost: dict, hover_distance: Tuple[int, int], manager=None, parent_element = None, object_id: Union[ObjectID, str, None] = None, anchors: Dict[str, str] = None):
        self.cost = cost
        self.container = None
        self.top_margin = 0
        super().__init__('', hover_distance, manager, parent_element, object_id, anchors)
        self.rebuild()

    def rebuild(self):
        super().rebuild()

        if self.container is not None:
            self.container.kill()
            self.container = None

        width, height = 320, 50
        self.container = UIContainer(pygame.Rect(0, 0, width, height), self.ui_manager, starting_height=self.ui_manager.get_sprite_group().get_top_layer()+1, parent_element=self)

        self.table = UITable(pygame.Rect(0,0,0,0), container=self.container, resizable=True, kill_on_repopulation=False)
        self.table.add_row(create_resources_row(self.cost, self.table))
        self.table.rebuild()

        if self.text_block is not None:
            self.text_block.kill()

    def kill(self):
        self.container.kill()
        return super().kill()

class BuildButton(UIButton):
    def __init__(self, cost: dict, relative_rect: Union[pygame.Rect, Tuple[float, float], pygame.Vector2], text: str, manager: Optional[IUIManagerInterface] = None, container: Optional[IContainerLikeInterface] = None, tool_tip_text: Optional[str] = None, starting_height: int = 1, parent_element: UIElement = None, object_id: Union[ObjectID, str, None] = None, anchors: Optional[Dict[str, Union[str, UIElement]]] = None, allow_double_clicks: bool = False, generate_click_events_from: Iterable[int] = frozenset([pygame.BUTTON_LEFT]), visible: int = 1, *, tool_tip_object_id: Optional[ObjectID] = None, text_kwargs: Optional[Dict[str, str]] = None, tool_tip_text_kwargs: Optional[Dict[str, str]] = None):
        self.cost = cost
        self.popup = None
        super().__init__(relative_rect, text, manager, container, tool_tip_text, starting_height, parent_element, object_id, anchors, allow_double_clicks, generate_click_events_from, visible, tool_tip_object_id=tool_tip_object_id, text_kwargs=text_kwargs, tool_tip_text_kwargs=tool_tip_text_kwargs)

    def update(self, time_delta):
        if self.popup is not None:
            if (not self.hover_point(*self.ui_manager.get_mouse_position()) and
                    not self.popup.container.hover_point(*self.ui_manager.get_mouse_position())):
                self.popup.kill()
                self.popup = None
        super().update(time_delta)

    def kill(self):
        if self.popup is not None:
            self.popup.kill()
        return super().kill()

    def while_hovering(self, time_delta: float, mouse_pos: Union[pygame.Vector2, Tuple[int, int], Tuple[float, float]]):
        if self.popup is None and self.hover_time > self.tool_tip_delay:
            self.create_popup()
        super().while_hovering(time_delta, mouse_pos)

    def create_popup(self):
        hover_height = int(self.rect.height / 2)
        self.popup = BuildPopup(self.cost, (0, hover_height), self.ui_manager)
        find_valid_position(self.popup, pygame.Vector2(self.ui_manager.get_mouse_position()[0]+15, self.ui_manager.get_mouse_position()[1]+15))


class BuildButtonPanel(UITable):
    def __init__(self, resources: Resources, available_build_options: list, button_height: int, relative_rect: pygame.Rect, starting_layer_height: int = 1, manager: Optional[IUIManagerInterface] = None, *, element_id: str = 'panel', margins: Optional[Dict[str, int]] = None, container: Optional[IContainerLikeInterface] = None, parent_element: Optional[UIElement] = None, object_id: Union[ObjectID, str, None] = None, anchors: Optional[Dict[str, Union[str, UIElement]]] = None, visible: int = 1, resizable: bool = False, table_contents: Optional[List[List[UIElement]]] = None, kill_on_repopulation: bool = True, fill_jagged=False):
        self.resources = resources
        self.button_height = button_height
        self.shown_resources = None
        self.available_build_options = available_build_options # set externally because get_available_build_options is a method of `Game`
        self.known_build_options = []
        self.local_build_options = []
        self.buttons = []
        super().__init__(relative_rect, starting_layer_height, manager, element_id=element_id, margins=margins, container=container, parent_element=parent_element, object_id=object_id, anchors=anchors, visible=visible, resizable=resizable, table_contents=table_contents, kill_on_repopulation=kill_on_repopulation, fill_jagged=fill_jagged)

    def update(self, time_delta: float):
        super().update(time_delta)

        if self.shown_resources != self.resources:
            self.shown_resources = self.resources.copy()
            if len(self.available_build_options) > 0:
                self.show()
            for option, cost in self.available_build_options:
                if option not in self.known_build_options:
                    self.known_build_options.append(option)
                    self.local_build_options.append(local[option])

                    # resources_row = create_resources_row(cost, self)
                    button = BuildButton(cost, pygame.Rect(0, 0, self.get_container().get_rect().w, self.button_height), local[option], container=self)
                    self.buttons.append(button)
                    self.add_row([button])
                    self.rebuild()
