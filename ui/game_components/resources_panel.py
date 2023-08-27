from typing import Dict, List, Optional, Union

import pygame
from pygame_gui.core import ObjectID, UIElement
from pygame_gui.core.interfaces import (IContainerLikeInterface,
                                        IUIManagerInterface)
from pygame_gui.elements import UIButton, UILabel

from config import local
from forestry import Resources

from ..elements import UITable

def create_resources_row(resources: dict, container):
    row = []
    for resource, amount in resources.items():
        row.append(UIButton(pygame.Rect(0, 0, 32, 32), '', container=container, tool_tip_text=local[resource], object_id='#'+str(resource)))
        row.append(UILabel(pygame.Rect(0, 0, 64, 30), str(amount), container=container))
    return row

class ResourcesPanel(UITable):
    def __init__(self, resources: Resources, relative_rect: pygame.Rect, starting_layer_height: int = 1, manager: Optional[IUIManagerInterface]  = None, *, element_id: str = 'panel', margins: Optional[Dict[str, int]]  = None, container: Optional[IContainerLikeInterface]  = None, parent_element: Optional[UIElement]  = None, object_id: Union[ObjectID, str, None]  = None, anchors: Optional[Dict[str, Union[str, UIElement]]]  = None, visible: int = 1):
        self.resources = resources
        self.shown_resources = None
        super().__init__(relative_rect, starting_layer_height, manager, element_id=element_id, margins=margins, container=container, parent_element=parent_element, object_id=object_id, anchors=anchors, visible=visible, resizable=True)

    def populate_table_contents(self):
        super().populate_table_contents()
        if len(self.resources) > 0:
            self.table_contents.append(create_resources_row(self.resources, self))


    def update(self, time_delta: float):
        super().update(time_delta)
        if self.shown_resources != self.resources:
            self.shown_resources = self.resources.copy()
            self.rebuild()
