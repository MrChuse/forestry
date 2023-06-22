from typing import List, Union

import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UIWindow, UITextEntryLine

from config import local
from forestry import Inventory

from ..elements import UIGridWindow, UICustomTitleBarWindow
from . import Cursor, UIButtonSlot
from ..custom_events import INVENTORY_RENAMED


class InventoryWindow(UICustomTitleBarWindow, UIGridWindow):
    def __init__(self, inv: Inventory,  cursor: Cursor, rect, manager, *args, **kwargs):
        self.inv = inv
        self.cursor = cursor

        self.title_bar_entry_line_width = 150
        self.entry_line = None
        self.title_bar_sort_button_width = 100
        self.sort_window_button = None
        self.buttons : Union[List[List[UIButtonSlot]], None] = None

        kwargs['window_display_title'] = inv.name
        kwargs['resizable'] = True
        super().__init__(rect, manager, *args, **kwargs, subelements_function=self.subelements_method)

    def rebuild_title_bar(self):
        """
        Rebuilds the window when the theme has changed.

        """
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
                                            self.title_bar_sort_button_width -
                                            self.title_bar_close_button_width -
                                            self.title_bar_entry_line_width,
                                            self.title_bar_height))
        else:
            title_bar_width = (self._window_root_container.relative_rect.width -
                                self.title_bar_sort_button_width - self.title_bar_close_button_width -
                                self.title_bar_entry_line_width)
            self.title_bar = UIButton(relative_rect=pygame.Rect(0, 0,
                                                                title_bar_width,
                                                                self.title_bar_height),
                                        text='',
                                        manager=self.ui_manager,
                                        container=self._window_root_container,
                                        parent_element=self,
                                        object_id='#title_bar',
                                        anchors={'top': 'top', 'bottom': 'top',
                                                'left': 'left', 'right': 'right',
                                                'left_target': self.entry_line}
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
        elif event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            if event.ui_element == self.entry_line:
                if self.title_bar is not None:
                    self.title_bar.set_text(local['entertosave'])
        elif event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
            if event.ui_element == self.entry_line:
                if self.title_bar is not None:
                    self.title_bar.set_text('')
                event_data = {'ui_element': self,
                            'ui_object_id': self.most_specific_combined_id,
                            'inventory': self.inv,
                            'old_name': self.inv.name,
                            'new_name': event.text}
                pygame.event.post(pygame.event.Event(INVENTORY_RENAMED, event_data))
        elif event.type == INVENTORY_RENAMED:
            if event.ui_element != self and event.inventory == self.inv:
                self.entry_line.set_text(event.new_name)
        return super().process_event(event)
