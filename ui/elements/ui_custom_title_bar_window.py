from typing import Optional, Union
from pygame_gui.core.interfaces import IUIManagerInterface
from pygame_gui.elements import UIWindow, UIButton, UITextEntryLine
from pygame_gui.core import ObjectID, UIContainer
from pygame_gui.core.drawable_shapes import RectDrawableShape, RoundedRectangleShape
import pygame
import pygame_gui

from config import local

class UICustomTitleBarWindow(UIWindow):
    def __init__(self, rect: pygame.Rect, manager: Optional[IUIManagerInterface] = None, window_display_title: str = "", element_id: Optional[str] = None, object_id: Union[ObjectID, str, None] = None, resizable: bool = False, visible: int = 1, draggable: bool = True, **kwargs):
        self.title_bar_entry_line_width = 150
        self.entry_line = None
        super().__init__(rect, manager, window_display_title, element_id, object_id, resizable, visible, draggable, **kwargs)

    def rebuild(self):
        if self._window_root_container is None:
            self._window_root_container = UIContainer(pygame.Rect(self.relative_rect.x +
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
            self.window_element_container = UIContainer(window_container_rect,
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
            self.drawable_shape = RectDrawableShape(self.rect, theming_parameters,
                                                    ['normal'], self.ui_manager)
        elif self.shape == 'rounded_rectangle':
            self.drawable_shape = RoundedRectangleShape(self.rect, theming_parameters,
                                                        ['normal'], self.ui_manager)

        self._set_image(self.drawable_shape.get_fresh_surface())

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

            self.rebuild_title_bar()

    def rebuild_title_bar(self):
        if self.enable_title_bar:
            if self.entry_line is None:
                self.entry_line = UITextEntryLine(
                    pygame.Rect(1, 1, self.title_bar_entry_line_width, self.title_bar_height+1),
                    manager=self.ui_manager,
                    container=self._window_root_container,
                    parent_element=self,
                    object_id='#rename_entry_line',
                    anchors={'top': 'top', 'bottom': 'top',
                            'left': 'left', 'right': 'left'},
                    initial_text=self.window_display_title,
                )
            if self.title_bar is not None:
                self.title_bar.set_dimensions((self._window_root_container.relative_rect.width -
                                                self.title_bar_close_button_width -
                                                self.title_bar_entry_line_width,
                                                self.title_bar_height))
            else:
                title_bar_width = (self._window_root_container.relative_rect.width -
                                   self.title_bar_close_button_width -
                                   self.title_bar_entry_line_width)
                self.title_bar = UIButton(relative_rect=pygame.Rect(0, 0,
                                                                    title_bar_width,
                                                                    self.title_bar_height),
                                            text='', # self.window_display_title,
                                            manager=self.ui_manager,
                                            container=self._window_root_container,
                                            parent_element=self,
                                            object_id='#title_bar',
                                            anchors={'top': 'top', 'bottom': 'top',
                                                    'left': 'left', 'right': 'right',
                                                    'left_target': self.entry_line}
                                            )
                self.title_bar.set_hold_range((100, 100))

            if self.enable_close_button:
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

            else:
                if self.close_window_button is not None:
                    self.close_window_button.kill()
                    self.close_window_button = None
        else:
            if self.title_bar is not None:
                self.title_bar.kill()
                self.title_bar = None
            if self.close_window_button is not None:
                self.close_window_button.kill()
                self.close_window_button = None

    def process_event(self, event: pygame.Event) -> bool:
        tmp = super().process_event(event)
        if event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            if event.ui_element == self.entry_line:
                self.title_bar.set_text(local['entertosave'])
        elif event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
            if event.ui_element == self.entry_line:
                self.title_bar.set_text('')
        return tmp