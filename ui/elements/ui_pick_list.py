from typing import Dict, List, Optional, Tuple, Union

import pygame
from pygame_gui._constants import (UI_BUTTON_DOUBLE_CLICKED, UI_BUTTON_PRESSED,
                                   UI_SELECTION_LIST_DOUBLE_CLICKED_SELECTION,
                                   UI_SELECTION_LIST_DROPPED_SELECTION,
                                   UI_SELECTION_LIST_NEW_SELECTION, OldType)
from pygame_gui.core import ObjectID, UIElement
from pygame_gui.core.interfaces import (IContainerLikeInterface,
                                        IUIManagerInterface)
from pygame_gui.elements import UISelectionList


class UIPickList(UISelectionList):
    def __init__(self, relative_rect: pygame.Rect, item_list: Union[List[str], List[Tuple[str, str]]], manager: Optional[IUIManagerInterface] = None, *, allow_multi_select: bool = False, allow_double_clicks: bool = True, container: Optional[IContainerLikeInterface] = None, starting_height: int = 1, parent_element: Optional[UIElement] = None, object_id: Optional[Union[ObjectID, str]] = None, anchors: Optional[Dict[str, Union[str, UIElement]]] = None, visible: int = 1, default_selection: Optional[Union[str, Tuple[str, str], List[str], List[Tuple[str, str]]]] = None, not_select=True):
        self.not_select = not_select
        super().__init__(relative_rect, item_list, manager, allow_multi_select=allow_multi_select, allow_double_clicks=allow_double_clicks, container=container, starting_height=starting_height, parent_element=parent_element, object_id=object_id, anchors=anchors, visible=visible, default_selection=default_selection)

    def process_event(self, event: pygame.event.Event) -> bool:
        """
        Can be overridden, also handle resizing windows. Gives UI Windows access to pygame events.
        Currently just blocks mouse click down events from passing through the panel.

        :param event: The event to process.

        :return: Should return True if this element makes use of this event.

        """
        if self.is_enabled and (
                event.type in [UI_BUTTON_PRESSED, UI_BUTTON_DOUBLE_CLICKED]
                and event.ui_element in self.item_list_container.elements):
            for item in self.item_list:
                if item['button_element'] == event.ui_element:
                    if event.type == UI_BUTTON_DOUBLE_CLICKED:

                        # old event - to be removed in 0.8.0
                        event_data = {
                            'user_type': OldType(UI_SELECTION_LIST_DOUBLE_CLICKED_SELECTION),
                            'text': event.ui_element.text,
                            'ui_element': self,
                            'ui_object_id': self.most_specific_combined_id}
                        pygame.event.post(pygame.event.Event(pygame.USEREVENT, event_data))

                        # new event
                        event_data = {
                            'text': event.ui_element.text,
                            'ui_element': self,
                            'ui_object_id': self.most_specific_combined_id}
                        pygame.event.post(
                            pygame.event.Event(UI_SELECTION_LIST_DOUBLE_CLICKED_SELECTION,
                                                event_data))
                    else:
                        if item['selected']:
                            item['selected'] = False
                            event.ui_element.unselect()

                            # old event - to be removed in 0.8.0
                            event_data = {'user_type': OldType(UI_SELECTION_LIST_DROPPED_SELECTION),
                                            'text': event.ui_element.text,
                                            'ui_element': self,
                                            'ui_object_id': self.most_specific_combined_id}
                            pygame.event.post(pygame.event.Event(pygame.USEREVENT, event_data))

                            # new event
                            event_data = {'text': event.ui_element.text,
                                            'ui_element': self,
                                            'ui_object_id': self.most_specific_combined_id}
                            pygame.event.post(
                                pygame.event.Event(UI_SELECTION_LIST_DROPPED_SELECTION, event_data))

                        else:
                            if not self.not_select:
                                item['selected'] = True
                                event.ui_element.select()

                            # old event - to be removed in 0.8.0
                            event_data = {'user_type': OldType(UI_SELECTION_LIST_NEW_SELECTION),
                                            'text': event.ui_element.text,
                                            'ui_element': self,
                                            'ui_object_id': self.most_specific_combined_id}
                            pygame.event.post(pygame.event.Event(pygame.USEREVENT, event_data))

                            # new event
                            event_data = {'text': event.ui_element.text,
                                            'ui_element': self,
                                            'ui_object_id': self.most_specific_combined_id}
                            pygame.event.post(pygame.event.Event(UI_SELECTION_LIST_NEW_SELECTION,
                                                                    event_data))

                elif not self.allow_multi_select:
                    if item['selected']:
                        item['selected'] = False
                        if item['button_element'] is not None:
                            item['button_element'].unselect()

                            # old event - to be removed in 0.8.0
                            event_data = {'user_type': OldType(UI_SELECTION_LIST_DROPPED_SELECTION),
                                            'text': item['text'],
                                            'ui_element': self,
                                            'ui_object_id': self.most_specific_combined_id}
                            drop_down_changed_event = pygame.event.Event(pygame.USEREVENT,
                                                                            event_data)
                            pygame.event.post(drop_down_changed_event)

                            # new event
                            event_data = {'text': item['text'],
                                            'ui_element': self,
                                            'ui_object_id': self.most_specific_combined_id}
                            drop_down_changed_event = pygame.event.Event(
                                UI_SELECTION_LIST_DROPPED_SELECTION, event_data)
                            pygame.event.post(drop_down_changed_event)

        return False  # Don't consume any events
