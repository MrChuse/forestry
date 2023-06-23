from pygame_gui.elements import UIWindow, UIButton
from pygame_gui.core import UIContainer
from pygame_gui.core.drawable_shapes import RectDrawableShape, RoundedRectangleShape
import pygame

class UICustomTitleBarWindow(UIWindow):
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
            if self.title_bar is not None:
                self.title_bar.set_dimensions((self._window_root_container.relative_rect.width -
                                                self.title_bar_close_button_width,
                                                self.title_bar_height))
            else:
                title_bar_width = (self._window_root_container.relative_rect.width -
                                    self.title_bar_close_button_width)
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
