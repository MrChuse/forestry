import pygame
import pygame_gui
from pygame_gui.elements.ui_drop_down_menu import UIExpandedDropDownState
from pygame_gui.elements import UIDropDownMenu

class UINonChangingExpandedDropDownState(UIExpandedDropDownState):
    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element in self.active_buttons:
            self.should_transition = True

        if (event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION and
                event.ui_element == self.options_selection_list):
            self.should_transition = True

            event_data = {'text': self.options_selection_list.get_single_selection(),
                          'ui_element': self.drop_down_menu_ui,
                          'ui_object_id': self.drop_down_menu_ui.most_specific_combined_id}
            pygame.event.post(pygame.event.Event(pygame_gui.UI_DROP_DOWN_MENU_CHANGED, event_data))

        return False  # don't consume any events

class UINonChangingDropDownMenu(UIDropDownMenu):
    def __init__(self, options_list, starting_option: str, relative_rect: pygame.Rect, manager, container=None, parent_element=None, object_id=None, expansion_height_limit=None, anchors=None, visible: int = 1):
        super().__init__(options_list, starting_option, relative_rect, manager, container, parent_element, object_id, expansion_height_limit, anchors, visible)
        self.menu_states['expanded'] = UINonChangingExpandedDropDownState(
            self,
            self.options_list,
            self.selected_option,
            self.background_rect,
            self.open_button_width,
            self.expand_direction,
            self.ui_manager,
            self,
            self.element_ids,
            self.object_ids
        )