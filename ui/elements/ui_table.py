from typing import Dict, List, Optional, Union

import pygame
from pygame_gui.core import ObjectID, UIElement
from pygame_gui.core.interfaces import (IContainerLikeInterface,
                                        IUIManagerInterface)
from pygame_gui.elements import UIPanel, UIWindow, UILabel


class UITable(UIPanel):
    def __init__(self, relative_rect: pygame.Rect, starting_layer_height: int = 1, manager: Optional[IUIManagerInterface]  = None, *, element_id: str = 'panel', margins: Optional[Dict[str, int]]  = None, container: Optional[IContainerLikeInterface]  = None, parent_element: Optional[UIElement]  = None, object_id: Union[ObjectID, str, None] = None, anchors: Optional[Dict[str, Union[str, UIElement]]]  = None, visible: int = 1, resizable: bool = False, table_contents: Optional[List[List[UIElement]]]  = None, kill_on_repopulation: bool = True, fill_jagged=False):
        self.resizable = resizable
        self.kill_on_repopulation = kill_on_repopulation
        self.table_contents = table_contents if table_contents is not None else []
        self.original_rect = pygame.Rect(relative_rect)
        self.buttons = []
        self.fill_jagged = fill_jagged
        super().__init__(relative_rect, starting_layer_height, manager, element_id=element_id, margins=margins, container=container, parent_element=parent_element, object_id=object_id, anchors=anchors, visible=visible)
        self.rebuild()

    def populate_table_contents(self):
        if self.kill_on_repopulation:
            if self.table_contents is not None:
                for row in self.table_contents:
                    for element in row:
                        element.kill()
            self.table_contents = []

    def rebuild(self):
        if self.panel_container is not None:
            self.populate_table_contents()

        super().rebuild()
        if self.table_contents == []:
            return

        sizes2 = list(map(len, self.table_contents))
        if any(map(lambda x: x != sizes2[0], sizes2)):
            if not self.fill_jagged:
                raise ValueError(f'UITable was rebuilt with jagged table_contents: {sizes2}')
            max_size = max(sizes2)
            for row, row_size in zip(self.table_contents, sizes2):
                need_to_fill = max_size - row_size
                for _ in range(need_to_fill):
                    row.append(UILabel(pygame.Rect(0, 0, 0, 0), '', container=self))

        heights = [max(map(lambda x: x.get_abs_rect().height, row)) for row in self.table_contents]
        transposed = zip(*self.table_contents)
        widths = [max(map(lambda x: x.get_abs_rect().width, row)) for row in transposed]

        for row_n in range(len(self.table_contents)):
            for el_n in range(len(self.table_contents[row_n])):
                center_x = sum(widths[:el_n]) + widths[el_n]/2 - 2 * el_n
                center_y = sum(heights[:row_n]) + heights[row_n]/2 - 2 * row_n
                element = self.table_contents[row_n][el_n]
                rel_rect = element.get_relative_rect()
                rel_rect.center = center_x, center_y
                element.set_relative_position(rel_rect.topleft)

        if self.resizable:
            new_dimensions = (sum(widths) + self.container_margins['left'] + self.container_margins['right'] - 2 * len(widths) + 2,
                              sum(heights) + self.container_margins['top'] + self.container_margins['bottom'] - 2 * len(heights) + 2)
            self.set_dimensions(new_dimensions)

    def add_row(self, row):
        if len(self.table_contents) and not self.fill_jagged:
            if len(self.table_contents[0]) != len(row):
                raise ValueError(f'Length of a row must be equal to length of a table row ({len(row)} != {len(self.table_contents[0])})')
        self.table_contents.append(row)
