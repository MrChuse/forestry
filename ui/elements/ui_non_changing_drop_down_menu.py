import pygame
import pygame_gui
from pygame_gui.elements.ui_drop_down_menu import UIExpandedDropDownState
from pygame_gui.elements import UIDropDownMenu, UIButton, UISelectionList
from pygame_gui.core import ObjectID

class UINonChangingExpandedDropDownState(UIExpandedDropDownState):
    def start(self, should_rebuild: bool = True):
        """
        Called each time we enter the expanded state. It creates the necessary elements, the
        selected option, all the other available options and the close button.

        """
        self.should_transition = False

        border_and_shadow = (self.drop_down_menu_ui.shadow_width +
                             self.drop_down_menu_ui.border_width)
        self.active_buttons = []
        self.selected_option_button = UIButton(pygame.Rect((border_and_shadow, border_and_shadow),
                                                           (self.base_position_rect.width -
                                                            self.close_button_width,
                                                            self.base_position_rect.height)),
                                               self.selected_option,
                                               self.ui_manager,
                                               self.ui_container,
                                               starting_height=2,
                                               parent_element=self.drop_down_menu_ui,
                                               object_id=ObjectID('#selected_option', None))
        self.drop_down_menu_ui.join_focus_sets(self.selected_option_button)
        self.active_buttons.append(self.selected_option_button)

        expand_button_symbol = '▼'

        list_object_id = '#drop_down_options_list'
        list_object_ids = self.drop_down_menu_ui.object_ids[:]
        list_object_ids.append(list_object_id)
        list_class_ids = self.drop_down_menu_ui.class_ids[:]
        list_class_ids.append(None)
        list_element_ids = self.drop_down_menu_ui.element_ids[:]
        list_element_ids.append('selection_list')

        final_ids = self.ui_manager.get_theme().build_all_combined_ids(list_element_ids,
                                                                       list_class_ids,
                                                                       list_object_ids)

        self._calculate_options_list_sizes(final_ids)
        if self.expand_direction is not None:
            if self.expand_direction == 'up':
                expand_button_symbol = '▲'

                if self.drop_down_menu_ui.expansion_height_limit is None:
                    self.drop_down_menu_ui.expansion_height_limit = self.base_position_rect.top

                self.options_list_height = min(self.options_list_height,
                                               self.drop_down_menu_ui.expansion_height_limit)

                self.option_list_y_pos = self.base_position_rect.top - self.options_list_height

            elif self.expand_direction == 'down':
                expand_button_symbol = '▼'

                if self.drop_down_menu_ui.expansion_height_limit is None:
                    height_limit = (self.drop_down_menu_ui.ui_container.relative_rect.height -
                                    self.base_position_rect.bottom)
                    self.drop_down_menu_ui.expansion_height_limit = height_limit

                self.options_list_height = min(self.options_list_height,
                                               self.drop_down_menu_ui.expansion_height_limit)

                self.option_list_y_pos = self.base_position_rect.bottom

        if self.close_button_width > 0:
            close_button_x = (border_and_shadow +
                              self.base_position_rect.width -
                              self.close_button_width)

            self.close_button = UIButton(pygame.Rect((close_button_x,
                                                      border_and_shadow),
                                                     (self.close_button_width,
                                                      self.base_position_rect.height)),
                                         expand_button_symbol,
                                         self.ui_manager,
                                         self.ui_container,
                                         starting_height=2,
                                         parent_element=self.drop_down_menu_ui,
                                         object_id='#expand_button')
            self.drop_down_menu_ui.join_focus_sets(self.close_button)
            self.active_buttons.append(self.close_button)
        list_rect = pygame.Rect(self.drop_down_menu_ui.relative_rect.left,
                                self.option_list_y_pos,
                                (self.drop_down_menu_ui.relative_rect.width -
                                 self.close_button_width),
                                self.options_list_height)
        self.options_selection_list = UISelectionList(list_rect,
                                                      starting_height=3,
                                                      item_list=self.options_list,
                                                      allow_double_clicks=False,
                                                      manager=self.ui_manager,
                                                      parent_element=self.drop_down_menu_ui,
                                                      container=self.drop_down_menu_ui.ui_container,
                                                      anchors=self.drop_down_menu_ui.anchors,
                                                      object_id='#drop_down_options_list')
        self.drop_down_menu_ui.join_focus_sets(self.options_selection_list)
        if self.options_selection_list.scroll_bar is not None:
            # our options list is long enough to have a scroll bar.
            # we want to scroll it enough that the currently selected option is on screen.
            start_percentage = self.options_selection_list.get_single_selection_start_percentage()
            self.options_selection_list.scroll_bar.set_scroll_from_start_percentage(start_percentage)
            self.options_selection_list.update(0.0)

        if should_rebuild:
            self.rebuild()

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
            self.object_ids,
            None
        )