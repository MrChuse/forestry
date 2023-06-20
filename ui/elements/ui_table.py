from typing import Dict, List, Optional, Union
import pygame
from pygame_gui.core import ObjectID, UIElement
from pygame_gui.core.interfaces import IContainerLikeInterface, IUIManagerInterface
from pygame_gui.elements import UIWindow, UIPanel


class UITable(UIPanel):
    def __init__(self, relative_rect: pygame.Rect, starting_layer_height: int = 1, manager: IUIManagerInterface | None = None, *, element_id: str = 'panel', margins: Dict[str, int] | None = None, container: IContainerLikeInterface | None = None, parent_element: UIElement | None = None, object_id: ObjectID | str | None = None, anchors: Dict[str, str | UIElement] | None = None, visible: int = 1, resizable: bool = False, table_contents: List[List[UIElement]] | List = None):
        self.resizable = resizable
        self.table_contents = table_contents if table_contents is not None else []
        self.original_rect = pygame.Rect(relative_rect)
        self.buttons = []
        super().__init__(relative_rect, starting_layer_height, manager, element_id=element_id, margins=margins, container=container, parent_element=parent_element, object_id=object_id, anchors=anchors, visible=visible)
        self.rebuild()

    def rebuild(self):
        super().rebuild()

        if not hasattr(self, 'panel_container'):
            # has not __init__ed yet, skipping
            return
        if self.table_contents == []:
            if hasattr(self, 'panel_container'): # revert to original size
                self.set_dimensions(self.original_rect.size)
            return

        sizes2 = list(map(len, self.table_contents))
        if any(map(lambda x: x != sizes2[0], sizes2)):
            raise ValueError(f'UITable was rebuilt with jagged table_contents: {sizes2}')

        top_margin = 2
        heights = [max(map(lambda x: x.get_abs_rect().height, row)) + top_margin for row in self.table_contents]
        left_margin = 2
        transposed = zip(*self.table_contents)
        widths = [max(map(lambda x: x.get_abs_rect().width, row)) + left_margin for row in transposed]

        for row_n in range(len(self.table_contents)):
            for el_n in range(len(self.table_contents[row_n])):
                center_x = sum(widths[:el_n]) + widths[el_n]/2 + left_margin * (el_n + 1)
                center_y = sum(heights[:row_n]) + heights[row_n]/2 + top_margin * (row_n + 1)
                element = self.table_contents[row_n][el_n]
                rel_rect = element.get_relative_rect()
                rel_rect.center = center_x, center_y
                element.set_relative_position(rel_rect.topleft)

        if self.resizable:
            new_dimensions = (sum(widths) + left_margin * (len(self.table_contents[0]) + 1) + (self.container_margins['left'] + self.container_margins['right']),
                            sum(heights) + top_margin * (len(self.table_contents) + 1) + (self.container_margins['top'] + self.container_margins['bottom']))

            self.set_dimensions(new_dimensions)