
from typing import Optional, Union
import pygame
import pygame_gui
from pygame_gui.core import ObjectID
from pygame_gui.elements import UIButton, UIStatusBar, UITextBox
from pygame_gui.core.interfaces import IUIManagerInterface

from config import ANALYZER_WINDOW_SIZE, local
from forestry import Analyzer, Slot
from ..elements import UICustomTitleBarWindow
from . import UIButtonSlot, Cursor



class AnalyzerWindow(UICustomTitleBarWindow):
    def __init__(self, analyzer: Analyzer, cursor: Cursor, rect: pygame.Rect, manager: Optional[IUIManagerInterface] = None, window_display_title: str = "", element_id: Optional[str] = None, object_id: Union[ObjectID, str, None] = None, resizable: bool = False, visible: int = 1, draggable: bool = True):
        self.analyzer = analyzer
        self.cursor = cursor

        rect.size = ANALYZER_WINDOW_SIZE
        super().__init__(rect, manager, local['Analyzer']+' '+analyzer.name, element_id, object_id, True, visible, draggable)

        bee_button_rect = pygame.Rect(0,14,64,64)
        bee_button_rect.centerx = self.get_container().get_rect().width//2
        self.bee_button = UIButtonSlot(analyzer.slot, bee_button_rect, '', manager, self,
            # anchors={
            #     'centerx': 'centerx'
            # }
        )
        self.bee_button.empty_object_id = '#DroneEmpty'

        tick_status_bar_rect = pygame.Rect(0, 14, rect.size[0]//2, 10)
        tick_status_bar_rect.centerx = rect.size[0] / 2 - 16
        self.tick_status_bar = UIStatusBar(tick_status_bar_rect, manager, container=self, anchors={'top_target': self.bee_button})
        self.tick_status_bar.percent_full = 0

        text_box_rect = pygame.Rect(0, 14, self.get_container().get_size()[0], 175)
        # text_box_rect.height = self.get_container().get_rect().bottom - self.tick_status_bar.get_relative_rect().bottom - 2
        # text_box_rect.bottom = self.get_container().get_rect().height - 100

        self.text_box = UITextBox('', text_box_rect,
            anchors={
                'top': 'top',
                'bottom': 'bottom',
                'left': 'left',
                'right': 'right',
                'top_target': self.tick_status_bar,
            }, container=self, object_id='@SmallFont')

    def process_event(self, event: pygame.Event) -> bool:
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.bee_button:
                # self.cursor.process_cursor_slot_interaction(event, self.bee_button.slot)
                if event.mouse_button == pygame.BUTTON_LEFT:
                    if self.cursor.slot.slot == self.bee_button.slot.slot:
                        self.bee_button.slot.put(*self.cursor.slot.take_all()) # stack
                    else:
                        try:
                            # swap
                            bee_from_cursor, amount_from_cursor = self.cursor.slot.take_all()
                            bee_from_analyzer, amount_from_analyzer = self.bee_button.slot.take_all()
                            self.analyzer.put(bee_from_cursor, amount_from_cursor)
                            self.cursor.slot.put(bee_from_analyzer, amount_from_analyzer)
                        except ValueError as e:
                            self.cursor.slot.put(bee_from_cursor, amount_from_cursor)
                            self.analyzer.put(bee_from_analyzer, amount_from_analyzer)
                            raise e
                elif event.mouse_button == pygame.BUTTON_RIGHT:
                    if self.cursor.slot.is_empty():
                        bee, amt = self.bee_button.slot.take_all() # take half
                        amt2 = amt//2
                        self.cursor.slot.put(bee, amt-amt2)
                        self.analyzer.put(bee, amt2)
                    else:
                        self.analyzer.put(self.cursor.slot.slot) # put one
                        self.cursor.slot.take()

        return super().process_event(event)

    def update(self, time_delta: float):
        super().update(time_delta)
        if self.analyzer.time_left is not None:
            self.tick_status_bar.percent_full = self.analyzer.time_left / self.analyzer.time_to_analyze
        else:
            self.tick_status_bar.percent_full = 0
        text = []
        if self.analyzer.species is not None:
            text.append(local[self.analyzer.species][0])
            text.append(f'{local["analyzed"]} {self.analyzer.consumed_amount}/{self.analyzer.amount_needed_to_consume}')
            if self.analyzer.consumed_enough():
                text.append(f'{local["hints"]}')
                if len(self.analyzer.hints) > 0:
                    for mutation in self.analyzer.hints:
                        text.append(f'{local[mutation[0]][0]} + {local[mutation[1]][0]}')
                else:
                    text.append(f'{local["no_mutations"]}')
        self.text_box.set_text('\n'.join(text))

    # def rebuild_title_bar(self):
    #     """
    #     Rebuilds the window when the theme has changed.

    #     """
    #     if self.entry_line is None:
    #         self.entry_line = UITextEntryLine(
    #             pygame.Rect(1, 1, self.title_bar_entry_line_width, self.title_bar_height+1),
    #             manager=self.ui_manager,
    #             container=self._window_root_container,
    #             parent_element=self,
    #             object_id='#rename_entry_line',
    #             anchors={'top': 'top', 'bottom': 'top',
    #                     'left': 'left', 'right': 'left'},
    #             initial_text=self.window_display_title,
    #         )
    #     if self.title_bar is not None:
    #         self.title_bar.set_dimensions((self._window_root_container.relative_rect.width -
    #                                         self.title_bar_sort_button_width -
    #                                         self.title_bar_close_button_width -
    #                                         self.title_bar_entry_line_width,
    #                                         self.title_bar_height))
    #     else:
    #         title_bar_width = (self._window_root_container.relative_rect.width -
    #                             self.title_bar_sort_button_width - self.title_bar_close_button_width -
    #                             self.title_bar_entry_line_width)
    #         self.title_bar = UIButton(relative_rect=pygame.Rect(0, 0,
    #                                                             title_bar_width,
    #                                                             self.title_bar_height),
    #                                     text='',
    #                                     manager=self.ui_manager,
    #                                     container=self._window_root_container,
    #                                     parent_element=self,
    #                                     object_id='#title_bar',
    #                                     anchors={'top': 'top', 'bottom': 'top',
    #                                             'left': 'left', 'right': 'right',
    #                                             'left_target': self.entry_line}
    #                                     )
    #         self.title_bar.set_hold_range((100, 100))

    #     if self.close_window_button is not None:
    #         close_button_pos = (-self.title_bar_close_button_width, 0)
    #         self.close_window_button.set_dimensions((self.title_bar_close_button_width,
    #                                                     self.title_bar_height))
    #         self.close_window_button.set_relative_position(close_button_pos)
    #     else:
    #         close_rect = pygame.Rect((-self.title_bar_close_button_width, 0),
    #                                 (self.title_bar_close_button_width,
    #                                 self.title_bar_height))
    #         self.close_window_button = UIButton(relative_rect=close_rect,
    #                                             text='╳',
    #                                             manager=self.ui_manager,
    #                                             container=self._window_root_container,
    #                                             parent_element=self,
    #                                             object_id='#close_button',
    #                                             anchors={'top': 'top',
    #                                                     'bottom': 'top',
    #                                                     'left': 'right',
    #                                                     'right': 'right'}
    #                                             )

# from typing import List, Union

# import pygame
# import pygame_gui
# from pygame_gui.elements import UIButton, UIWindow, UITextEntryLine

# from config import local
# from forestry import Inventory

# from ..elements import UIGridWindow, UICustomTitleBarWindow
# from . import Cursor, UIButtonSlot
# from ..custom_events import INVENTORY_RENAMED, SET_MOST_RECENT_INVENTORY


# class InventoryWindow(UICustomTitleBarWindow, UIGridWindow):
#     def __init__(self, inv: Inventory,  cursor: Cursor, rect, manager, *args, **kwargs):
#         self.inv = inv
#         self.cursor = cursor

#         self.title_bar_entry_line_width = 150
#         self.entry_line = None
#         self.title_bar_sort_button_width = 100
#         self.sort_window_button = None
#         self.buttons : Union[List[List[UIButtonSlot]], None] = None

#         kwargs['window_display_title'] = inv.name
#         kwargs['resizable'] = True
#         super().__init__(rect, manager, *args, **kwargs, subelements_function=self.subelements_method)

#
#         if self.sort_window_button is not None:
#             sort_button_pos = (-self.title_bar_sort_button_width, 0)
#             self.sort_window_button.set_dimensions((self.title_bar_sort_button_width,
#                                                         self.title_bar_height))
#             self.sort_window_button.set_relative_position(sort_button_pos)
#         else:
#             sort_rect = pygame.Rect((-self.title_bar_sort_button_width, 0),
#                                     (self.title_bar_sort_button_width,
#                                     self.title_bar_height))
#             self.sort_window_button = UIButton(relative_rect=sort_rect,
#                                                 text=local['Sort'],
#                                                 manager=self.ui_manager,
#                                                 container=self._window_root_container,
#                                                 parent_element=self,
#                                                 object_id='#close_button',
#                                                 anchors={'top': 'top',
#                                                         'bottom': 'top',
#                                                         'left': 'right',
#                                                         'right': 'right',
#                                                         'right_target':self.close_window_button}
#                                                 )

#     def subelements_method(self, container):
#         bsize = (64, 64)
#         self.buttons = []
#         for slot in self.inv:
#             rect = pygame.Rect((0, 0), bsize)
#             self.buttons.append(UIButtonSlot(slot, rect, '', self.ui_manager, container))
#         return self.buttons

#     def process_event(self, event):
#         should_set_as_most_recent = False
#         if event.type == pygame_gui.UI_BUTTON_START_PRESS:
#             if event.ui_element == self.sort_window_button:
#                 self.inv.sort()
#                 should_set_as_most_recent = True
#             for index, button in enumerate(self.buttons):
#                     if event.ui_element == button:
#                         should_set_as_most_recent = True
#                         mods = pygame.key.get_mods()
#                         if mods & pygame.KMOD_LSHIFT:
#                             self.inv.take_all(index)
#                         else:
#                             self.cursor.process_cursor_slot_interaction(event, self.inv[index])
#                         return True
#         elif event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
#             if event.ui_element == self.entry_line:
#                 should_set_as_most_recent = True
#                 if self.title_bar is not None:
#                     self.title_bar.set_text(local['entertosave'])
#         elif event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
#             if event.ui_element == self.entry_line:
#                 should_set_as_most_recent = True
#                 if self.title_bar is not None:
#                     self.title_bar.set_text('')
#                 event_data = {'ui_element': self,
#                               'ui_object_id': self.most_specific_combined_id,
#                               'inventory': self.inv,
#                               'old_name': self.inv.name,
#                               'new_name': event.text}
#                 pygame.event.post(pygame.event.Event(INVENTORY_RENAMED, event_data))
#         elif event.type == INVENTORY_RENAMED:
#             if event.ui_element != self and event.inventory == self.inv:
#                 self.entry_line.set_text(event.new_name)
#         if should_set_as_most_recent:
#             event_data = {'ui_element': self,
#                           'inventory': self.inv}
#             pygame.event.post(pygame.event.Event(SET_MOST_RECENT_INVENTORY, event_data))

#         return super().process_event(event)
