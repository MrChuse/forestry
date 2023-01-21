from typing import List, Union

import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UIWindow

from config import local
from forestry import Inventory

from ..elements import UIGridWindow
from . import Cursor, UIButtonSlot


class InventoryWindow(UIGridWindow):
    def __init__(self, inv: Inventory,  cursor: Cursor, rect, manager, *args, **kwargs):
        self.inv = inv
        self.cursor = cursor

        self.title_bar_sort_button_width = 100
        self.sort_window_button = None
        self.buttons : Union[List[List[UIButtonSlot]], None] = None

        kwargs['window_display_title'] = local['Inventory'] + ' ' + inv.name
        kwargs['resizable'] = True
        super().__init__(rect, manager, *args, **kwargs, subelements_function=self.subelements_method)

    def rebuild(self):
        """
        Rebuilds the window when the theme has changed.

        """
        if self._window_root_container is None:
            self._window_root_container = pygame_gui.core.UIContainer(pygame.Rect(self.relative_rect.x +
                                                                  self.shadow_width,
                                                                  self.relative_rect.y +
                                                                  self.shadow_width,
                                                                  self.relative_rect.width -
                                                                  (2 * self.shadow_width),
                                                                  self.relative_rect.height -
                                                                  (2 * self.shadow_width)),
                                                      manager=self.ui_manager,
                                                      starting_height=1,
                                                      is_window_root_container=True,
                                                      container=None,
                                                      parent_element=self,
                                                      object_id="#window_root_container",
                                                      visible=self.visible)
        if self.window_element_container is None:
            window_container_rect = pygame.Rect(self.border_width,
                                                self.title_bar_height,
                                                (self._window_root_container.relative_rect.width -
                                                 (2 * self.border_width)),
                                                (self._window_root_container.relative_rect.height -
                                                 (self.title_bar_height + self.border_width)))
            self.window_element_container = pygame_gui.core.UIContainer(window_container_rect,
                                                        self.ui_manager,
                                                        starting_height=0,
                                                        container=self._window_root_container,
                                                        parent_element=self,
                                                        object_id="#window_element_container",
                                                        anchors={'top': 'top', 'bottom': 'bottom',
                                                                 'left': 'left', 'right': 'right'})

        theming_parameters = {'normal_bg': self.background_colour,
                              'normal_border': self.border_colour,
                              'border_width': self.border_width,
                              'shadow_width': self.shadow_width,
                              'shape_corner_radius': self.shape_corner_radius}

        if self.shape == 'rectangle':
            self.drawable_shape = pygame_gui.core.drawable_shapes.RectDrawableShape(self.rect, theming_parameters,
                                                    ['normal'], self.ui_manager)
        elif self.shape == 'rounded_rectangle':
            self.drawable_shape = pygame_gui.core.drawable_shapes.RoundedRectangleShape(self.rect, theming_parameters,
                                                        ['normal'], self.ui_manager)

        self.set_image(self.drawable_shape.get_fresh_surface())

        self.set_dimensions(self.relative_rect.size)

        if self.window_element_container is not None:
            element_container_width = (self._window_root_container.relative_rect.width -
                                       (2 * self.border_width))
            element_container_height = (self._window_root_container.relative_rect.height -
                                        (self.title_bar_height + self.border_width))
            self.window_element_container.set_dimensions((element_container_width,
                                                          element_container_height))
            self.window_element_container.set_relative_position((self.border_width,
                                                                 self.title_bar_height))

            if self.title_bar is not None:
                self.title_bar.set_dimensions((self._window_root_container.relative_rect.width -
                                                self.title_bar_sort_button_width - self.title_bar_close_button_width,
                                                self.title_bar_height))
            else:
                title_bar_width = (self._window_root_container.relative_rect.width -
                                    self.title_bar_sort_button_width - self.title_bar_close_button_width)
                self.title_bar = UIButton(relative_rect=pygame.Rect(0, 0,
                                                                    title_bar_width,
                                                                    self.title_bar_height),
                                            text=self.window_display_title,
                                            manager=self.ui_manager,
                                            container=self._window_root_container,
                                            parent_element=self,
                                            object_id='#title_bar',
                                            anchors={'top': 'top', 'bottom': 'top',
                                                    'left': 'left', 'right': 'right'}
                                            )
                self.title_bar.set_hold_range((100, 100))

            if self.close_window_button is not None:
                close_button_pos = (-self.title_bar_close_button_width, 0)
                self.close_window_button.set_dimensions((self.title_bar_close_button_width,
                                                            self.title_bar_height))
                self.close_window_button.set_relative_position(close_button_pos)
            else:
                close_rect = pygame.Rect((-self.title_bar_close_button_width, 0),
                                        (self.title_bar_close_button_width,
                                        self.title_bar_height))
                self.close_window_button = UIButton(relative_rect=close_rect,
                                                    text='╳',
                                                    manager=self.ui_manager,
                                                    container=self._window_root_container,
                                                    parent_element=self,
                                                    object_id='#close_button',
                                                    anchors={'top': 'top',
                                                            'bottom': 'top',
                                                            'left': 'right',
                                                            'right': 'right'}
                                                    )
            if self.sort_window_button is not None:
                sort_button_pos = (-self.title_bar_sort_button_width, 0)
                self.sort_window_button.set_dimensions((self.title_bar_sort_button_width,
                                                            self.title_bar_height))
                self.sort_window_button.set_relative_position(sort_button_pos)
            else:
                sort_rect = pygame.Rect((-self.title_bar_sort_button_width, 0),
                                        (self.title_bar_sort_button_width,
                                        self.title_bar_height))
                self.sort_window_button = UIButton(relative_rect=sort_rect,
                                                    text=local['Sort'],
                                                    manager=self.ui_manager,
                                                    container=self._window_root_container,
                                                    parent_element=self,
                                                    object_id='#close_button',
                                                    anchors={'top': 'top',
                                                            'bottom': 'top',
                                                            'left': 'right',
                                                            'right': 'right',
                                                            'right_target':self.close_window_button}
                                                    )
        super(UIWindow, self).rebuild()

    def subelements_method(self, container):
        bsize = (64, 64)
        self.buttons = []
        for slot in self.inv:
            rect = pygame.Rect((0, 0), bsize)
            self.buttons.append(UIButtonSlot(slot, rect, '', self.ui_manager, container))
        return self.buttons

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.sort_window_button:
                self.inv.sort()
            for index, button in enumerate(self.buttons):
                    if event.ui_element == button:
                        mods = pygame.key.get_mods()
                        if mods & pygame.KMOD_LSHIFT:
                            self.inv.take_all(index)
                        else:
                            self.cursor.process_cursor_slot_interaction(event, self.inv[index])
                        return True
        return super().process_event(event)
