
from typing import Callable, List, Tuple, Union, Dict

import pygame
from pygame_gui.core import ObjectID, UIElement
from pygame_gui.core.interfaces import IUIManagerInterface, IContainerLikeInterface
from pygame_gui.elements import UIVerticalScrollBar, UIWindow, UIPanel

class UIGridPanel(UIPanel):
    def __init__(self, relative_rect: pygame.Rect, starting_layer_height: int, manager: IUIManagerInterface, *, element_id: str = 'panel', margins: Dict[str, int] = None, container: Union[IContainerLikeInterface, None] = None, parent_element: UIElement = None, object_id: Union[ObjectID, str, None] = None, anchors: Dict[str, str] = None, visible: int = 1, min_marginx: int = 0, min_marginy: int = 0, subelements_function: Callable[['UIGridWindow'], List[UIElement]] = None):
        self.subelements_function = subelements_function
        self.subelements = None
        self.subelement_size = None
        self.total_rows = None
        self.total_columns = None
        self.min_marginx = min_marginx
        self.min_marginy = min_marginy

        self.scroll_bar = None
        self.scroll_bar_width = 20
        super().__init__(relative_rect, starting_layer_height, manager, element_id=element_id, margins=margins, container=container, parent_element=parent_element, object_id=object_id, anchors=anchors, visible=visible)
        self.set_positions_of_subelements()

    def subelements_method(self):
        return []

    def set_subelements(self):
        if self.subelements is None:
            if self.subelements_function is not None:
                self.subelements = self.subelements_function(self)
            else:
                self.subelements = self.subelements_method()
            if len(self.subelements) > 0:
                self.subelement_size = self.subelements[0].get_abs_rect().size
                for subelement in self.subelements:
                    if subelement.get_abs_rect().size != self.subelement_size:
                        raise RuntimeError(f'UIGridWindow was called with different-sized elements: {self.subelement_size}, {subelement.get_abs_rect().size}')

    def set_positions_of_subelements(self):
        if self.subelements is None:
            self.set_subelements()
        if len(self.subelements) == 0:
            return
        available_space = self.get_container().get_abs_rect().width
        total_columns = max(1, available_space // self.subelement_size[0])
        marginx = self.min_marginx
        # print(f'top one {available_space=},{total_columns=},{horizontal_space_left=},{marginx=}')
        total_rows = len(self.subelements) // total_columns
        total_rows += 1 if len(self.subelements) % total_columns else 0
        total_height = self.min_marginy * (total_rows + 1) + self.subelement_size[1] * total_rows
        # print(f'{available_space=},{total_columns=},{horizontal_space_left=},{marginx=},{total_rows=},{total_rows=},{total_height=}')
        if total_height <= self.get_container().get_abs_rect().height:
            # no need for scrollbar
            if self.scroll_bar is not None:
                self.scroll_bar.kill()
                self.scroll_bar = None
            marginy = self.min_marginy
            height_adjustment = 0
        else:
            # need a scrollbar, recalculate the margins
            available_space = self.get_container().get_abs_rect().width - self.scroll_bar_width
            total_columns = max(1, available_space // self.subelement_size[0])
            marginx = self.min_marginx
            # print(f'bot one {available_space=},{total_columns=},{horizontal_space_left=},{marginx=}')
            total_rows = len(self.subelements) // total_columns
            total_rows += 1 if len(self.subelements) % total_columns else 0
            total_height = self.min_marginy * (total_rows + 1) + self.subelement_size[1] * total_rows
            # print(f'{available_space=},{total_columns=},{horizontal_space_left=},{marginx=},{total_rows=},{total_rows=},{total_height=}')
            if self.scroll_bar is None:
                scroll_bar_rect = pygame.Rect(
                    self.get_container().get_abs_rect().width - self.scroll_bar_width,
                    0,
                    self.scroll_bar_width,
                    self.get_container().get_abs_rect().height
                )
                percentage_visible = self.get_container().get_abs_rect().height / total_height
                self.scroll_bar = UIVerticalScrollBar(scroll_bar_rect,
                                                      percentage_visible,
                                                      self.ui_manager,
                                                      self,
                                                      visible=self.visible)
            else:
                self.scroll_bar.visible_percentage = self.get_container().get_abs_rect().height / total_height
                self.scroll_bar.set_relative_position((self.get_container().get_abs_rect().width - self.scroll_bar_width, 0))
                self.scroll_bar.set_dimensions((self.scroll_bar_width, self.get_container().get_abs_rect().height))
            marginy = self.min_marginy
            height_adjustment = -self.scroll_bar.start_percentage * total_height
        for index, element in enumerate(self.subelements):
            j, i = index // total_columns, index % total_columns
            pos = (marginx * (i+1) + self.subelement_size[0] * i,
                    marginy * (j+1) + self.subelement_size[1] * j + height_adjustment)
            element.set_relative_position(pos)
        self.total_columns = total_columns
        self.total_rows = total_rows

    def set_dimensions(self, dimensions: Union[pygame.math.Vector2, Tuple[int, int], Tuple[float, float]]):
        super().set_dimensions(dimensions)
        self.set_positions_of_subelements()

    def update(self, time_delta: float):
        super().update(time_delta)
        if self.scroll_bar is not None and self.scroll_bar.check_has_moved_recently():
            self.set_positions_of_subelements()

    # def kill(self):
    #     print('killed panel')
    #     self.kill_subelements()
    #     return super().kill()

    # def kill_subelements(self):
    #     if self.subelements is not None:
    #         for subelement in self.subelements:
    #             print('killed', subelement)
    #             subelement.kill()

class UIGridWindow(UIWindow):
    def __init__(self, rect: pygame.Rect, manager: IUIManagerInterface, window_display_title: str = "", element_id: Union[str, None] = None, object_id: Union[ObjectID, str, None] = None, resizable: bool = False, visible: int = 1, min_marginx: int = 0, min_marginy: int = 0, subelements_function: Callable[['UIGridWindow'], List[UIElement]] = None):
        self.subelements_function = subelements_function
        self.min_marginx = min_marginx
        self.min_marginy = min_marginy
        self.grid_panel = None
        super().__init__(rect, manager, window_display_title, element_id, object_id, resizable, visible)

    def create_grid_panel(self):
        if self.grid_panel is None:
            self.grid_panel = UIGridPanel(pygame.Rect((0, 0), self.get_container().get_size()), 0, self.ui_manager, container=self.get_container(), min_marginx=self.min_marginx, min_marginy=self.min_marginy, subelements_function=self.subelements_function)
            size = self.grid_panel.subelement_size
            if size is not None:
                self.set_minimum_dimensions((size[0] + self.grid_panel.scroll_bar_width + 2 * self.border_width + 2 * self.grid_panel.border_width, size[1] + 2 * self.border_width + 2 * self.grid_panel.border_width))

    def set_dimensions(self, dimensions: Union[pygame.math.Vector2, Tuple[int, int], Tuple[float, float]]):
        super().set_dimensions(dimensions)
        self.create_grid_panel()
        self.grid_panel.set_dimensions(self.get_container().get_size())

    def set_subelements(self):
        self.create_grid_panel()
        self.grid_panel.set_subelements()

    def rebuild(self):
        super().rebuild()
        self.grid_panel.rebuild()

    def process_event(self, event: pygame.event.Event) -> bool:
        if (self is not None and event.type == pygame.MOUSEBUTTONUP and
                event.button == pygame.BUTTON_LEFT and self.resizing_mode_active and
                self.grid_panel.subelements is not None):

            xdim = self.grid_panel.subelement_size[0] * self.grid_panel.total_columns +\
                   self.grid_panel.min_marginx * (self.grid_panel.total_columns + 1) +\
                   2 * self.shadow_width + 2 * self.grid_panel.shadow_width + 2 * self.grid_panel.subelements[0].shadow_width
            if self.grid_panel.scroll_bar is not None:
                xdim += self.grid_panel.scroll_bar_width

            # ydim = self.grid_panel.subelement_size[1] * self.grid_panel.total_rows +\
            #        self.grid_panel.min_marginy * (self.grid_panel.total_rows + 1) +\
            #        2 * self.shadow_width

            self.set_dimensions((xdim, self.rect.height))
        return super().process_event(event)
