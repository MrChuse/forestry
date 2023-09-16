import logging
import os
from enum import IntEnum
from traceback import print_exc
from typing import Union

import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UITextBox, UITextEntryLine
from pygame_gui.windows import UIMessageWindow

from config import (ANALYZER_WINDOW_SIZE, INVENTORY_WINDOW_SIZE, APIARY_WINDOW_SIZE,
                    UI_MESSAGE_SIZE, ResourceTypes,
                    config_production_modifier, helper_text, local)
from forestry import Achievement, Alveary, Analyzer, Apiary, Game, Inventory, Slot
from migration import CURRENT_FRONT_VERSION, update_front_versions

from ..custom_events import (INSPECT_BEE, INVENTORY_RENAMED,
                             TUTORIAL_STAGE_CHANGED, SET_MOST_RECENT_INVENTORY)
from ..elements import (UIFloatingTextBox, UILocationFindingConfirmationDialog,
                        UILocationFindingMessageWindow,
                        UIPickList)
from . import (AchievementsWindow, ApiaryWindow, BestiaryWindow, Cursor, InspectWindow, InventoryWindow,
               AnalyzerWindow, MatingHistoryWindow, MendelTutorialWindow, ResourcesPanel,
               SettingsWindow, CurrentTutorialStage, TutorialStage, BuildButtonPanel)


class GUI(Game):
    def restart_game(self):
        super().restart_game()

        CurrentTutorialStage.current_tutorial_stage = TutorialStage.BEFORE_FORAGE
        if not os.path.exists('saves') or len(list(filter(lambda x: x.endswith('.forestry'), os.listdir('saves')))) == 0:
            self.help_window()

        self.cursor = Cursor(Slot(), pygame.Rect(0, 0, 64, 64), '', self.cursor_manager)

        if self.resources_panel is not None:
            self.resources_panel.kill()
            self.resources_panel = None
        resources_panel_rect = pygame.Rect(0, 0, self.resources_panel_width, self.window_size[1])
        r = pygame.Rect(0, 0, resources_panel_rect.size[0]-6, 44)
        self.resources_panel = ResourcesPanel(self.resources, r, visible=False)

        if self.build_dropdown is not None:
            self.build_dropdown.kill()
            self.build_dropdown = None

        self.build_dropdown = BuildButtonPanel(self.resources, self.get_available_build_options(), self.left_menu_buttons_height, pygame.Rect(0, 0, resources_panel_rect.size[0]-6, (self.left_menu_buttons_height + 4) * 3),
            anchors={
                'top':'top',
                'bottom':'top',
                'left':'left',
                'right':'left',
                'top_target': self.resources_panel
            }, visible=False, fill_jagged=True, kill_on_repopulation=False, resizable=True)

        if self.forage_button is not None:
            self.forage_button.kill()
            self.forage_button = None
        self.forage_button = UIButton(pygame.Rect(0, 0, resources_panel_rect.size[0]-6, 40), local['Forage'],
            anchors={
                'top':'top',
                'bottom':'top',
                'left':'left',
                'right':'left',
                'top_target': self.build_dropdown
            }
        )

        if self.open_inspect_window_button is not None:
            self.open_inspect_window_button.kill()
            self.open_inspect_window_button = None
        self.open_inspect_window_button = UIButton(pygame.Rect(0, 45, resources_panel_rect.size[0]-6, 40), local['Open Inspect Window'],
            anchors={
                'top':'top',
                'bottom':'top',
                'left':'left',
                'right':'left',
                'top_target': self.build_dropdown
            },
            visible=False)

        if self.menu_button is not None:
            self.menu_button.kill()
            self.menu_button = None
        self.menu_button = UIButton(pygame.Rect(0, -40, resources_panel_rect.size[0]-6, 40), local['Menu'],
            anchors={
                'top':'bottom',
                'bottom':'bottom',
                'left':'left',
                'right':'left',
            },
            visible=True)

        if self.bestiary_button is not None:
            self.bestiary_button.kill()
            self.bestiary_button = None
        self.bestiary_button = UIButton(pygame.Rect(0, -40, resources_panel_rect.size[0]-6, 40), local['Bestiary'],
            anchors={
                'top':'bottom',
                'bottom':'bottom',
                'left':'left',
                'right':'left',
                'bottom_target': self.menu_button
            },
            visible=False)

        if self.achievements_button is not None:
            self.achievements_button.kill()
            self.achievements_button = None
        self.achievements_button = UIButton(pygame.Rect(0, -40, resources_panel_rect.size[0]-6, 40), local['Achievements'],
            anchors={
                'top':'bottom',
                'bottom':'bottom',
                'left':'left',
                'right':'left',
                'bottom_target': self.bestiary_button
            },
            visible=False)

        for w in self.apiary_windows:
            w.kill()
        for w in self.inventory_windows:
            w.kill()
        for w in self.inspect_windows:
            w.kill()
        for w in self.analyzer_windows:
            w.kill()
        self.apiary_windows = []
        self.inventory_windows = []
        self.inspect_windows = []
        self.analyzer_windows = []

        if self.apiary_selection_list is not None:
            self.apiary_selection_list.kill()
            self.apiary_selection_list = None
        if self.bestiary_window is not None:
            self.bestiary_window.kill()
            self.bestiary_window = None
        if self.achievements_window is not None:
            self.achievements_window.kill()
            self.achievements_window = None
        if self.mendel_window is not None:
            self.mendel_window.kill()
            self.mendel_window = None
        if self.mating_history_window is not None:
            self.mating_history_window.kill()
            self.mating_history_window = None
        if self.load_confirm is not None:
            self.load_confirm.kill()
            self.load_confirm = None
        if self.save_confirm is not None:
            self.save_confirm.kill()
            self.save_confirm = None
        if self.new_game_confirm is not None:
            self.new_game_confirm.kill()
            self.new_game_confirm = None

        if self.esc_menu is not None:
            self.esc_menu.kill()
            self.esc_menu = None
        esc_menu_rect = pygame.Rect(0, 0, self.esc_menu_width, 500)
        esc_menu_rect.center = (self.window_size[0]/2, self.window_size[1]/2)
        self.esc_menu = UIPickList(esc_menu_rect, [local['Greetings Window'], local['Settings'], local['Load'], local['Save'], local['New game'], local['Exit']], self.cursor_manager, visible=False, starting_height=30)

        if self.load_file_selection_list is not None:
            self.load_file_selection_list.kill()
            self.load_file_selection_list = None
        if self.filename_entry is not None:
            self.filename_entry.kill()
            self.filename_entry = None
        if self.save_file_selection_list is not None:
            self.save_file_selection_list.kill()
            self.save_file_selection_list = None

    def __init__(self, window_size, manager: pygame_gui.UIManager, cursor_manager: pygame_gui.UIManager):
        self.command_out = 1
        Slot.empty_str = ''
        Slot.str_amount = lambda x: '' # type: ignore

        self.window_size = window_size
        self.ui_manager = manager
        self.cursor_manager = cursor_manager

        self.resources_panel_width = 330
        self.left_menu_buttons_height = 40

        self.shown_resources = None
        self.resources_panel = None

        self.build_dropdown = None

        self.forage_button = None
        self.open_inspect_window_button = None
        self.achievements_button = None
        self.bestiary_button = None
        self.menu_button = None

        self.apiary_windows = []
        self.inventory_windows = []
        self.inspect_windows = []
        self.analyzer_windows = []

        self.apiary_selection_list_width = 100
        self.apiary_selection_list = None

        self.bestiary_window = None
        self.achievements_window = None
        self.mendel_window = None
        self.mating_history_window = None
        self.load_confirm = None
        self.save_confirm = None
        self.new_game_confirm = None

        self.esc_menu_width = 200
        self.esc_menu = None
        self.load_file_selection_list = None
        self.filename_entry = None
        self.save_file_selection_list = None

        super().__init__()

        if not new_game:
            self.load_last()

    def settings_window(self):
        return SettingsWindow(pygame.Rect((0,0), self.window_size), self.ui_manager, local['Settings'])

    def help_window(self):
        r = pygame.Rect(0, 0, self.window_size[0] - 100, self.window_size[1] - 100)
        r.center = (self.window_size[0]/2, self.window_size[1]/2)
        return UILocationFindingMessageWindow(r, helper_text[0], self.ui_manager)

    def open_bestiary_window(self):
        if self.bestiary_window is not None:
            self.bestiary_window.kill()
            self.bestiary_window = None
        r = pygame.Rect(0, 0, 3/4*self.window_size[0], 3/4*self.window_size[1])
        r.center = (self.window_size[0]/2, self.window_size[1]/2)
        self.bestiary_window = BestiaryWindow(self.bestiary, r, self.ui_manager, local['Bestiary'])

    def open_achievements_window(self):
        if self.achievements_window is not None:
            self.achievements_window.kill()
            self.achievements_window = None
        r = pygame.Rect(0, 0, 3/4*self.window_size[0], 3/4*self.window_size[1])
        r.center = (self.window_size[0]/2, self.window_size[1]/2)
        self.achievements_window = AchievementsWindow(self.achievement_manager, r, self.ui_manager, local['Achievements'])

    def open_mendel_window(self):
        if self.mendel_window is not None:
            self.mendel_window.kill()
            self.mendel_window = None
        r = pygame.Rect(0, 0, 1036, 584)
        r.center = (self.window_size[0]/2, self.window_size[1]/2)
        self.mendel_window = MendelTutorialWindow(r, self.ui_manager)

    def open_mating_history_window(self):
        if self.mating_history_window is not None:
            self.mating_history_window.kill()
            self.mating_history_window = None
        r = pygame.Rect(0, 0, 3/4*self.window_size[0], 3/4*self.window_size[1])
        r.center = (self.window_size[0]/2, self.window_size[1]/2)
        self.mating_history_window = MatingHistoryWindow(self.mating_history, r, self.ui_manager, 'Mating History')

    def open_inspect_window(self, rect: Union[pygame.Rect, None] = None):
        if rect is None:
            rect = pygame.Rect(pygame.mouse.get_pos(), (0, 0))
        self.inspect_windows.append(InspectWindow(self, self.cursor, rect, self.ui_manager))

    def open_apiary_selection_list(self):
        apiary_selection_list_rect = pygame.Rect(0, 0, self.apiary_selection_list_width, self.window_size[1])
        apiary_selection_list_rect.right = 0
        self.apiary_selection_list = UIPickList(apiary_selection_list_rect, [], self.ui_manager,
            anchors={
                'top':'top',
                'bottom':'bottom',
                'left':'right',
                'right':'right',
            })
        self.update_windows_list()

    def open_mendel_notification(self):
        mouse_pos = self.ui_manager.get_mouse_position()
        r = pygame.Rect((mouse_pos[0] + UI_MESSAGE_SIZE[0], mouse_pos[1]), UI_MESSAGE_SIZE)
        return UILocationFindingMessageWindow(r, local['mendel_notification'], self.ui_manager)

    def open_load_file_selection_list(self):
        self.load_file_selection_list = UIPickList(pygame.Rect(0, self.esc_menu.get_abs_rect().top, self.esc_menu_width, 500),
                                                   self.get_save_names_list(),
                                                   manager=self.cursor_manager,
                                                   anchors={'left_target': self.esc_menu})

    def open_save_file_selection_list(self):
        self.filename_entry = UITextEntryLine(pygame.Rect(0, self.esc_menu.get_abs_rect().top, self.esc_menu_width, 44),
                                              manager=self.cursor_manager,
                                              anchors={'left_target': self.esc_menu})
        self.save_file_selection_list = UIPickList(pygame.Rect(0, 0, self.esc_menu_width, 500),
                                                   self.get_save_names_list(),
                                                   manager=self.cursor_manager,
                                                   anchors={'left_target': self.esc_menu,
                                                            'top_target': self.filename_entry})
        diff = self.save_file_selection_list.rect.bottom - self.esc_menu.rect.bottom
        self.save_file_selection_list.set_dimensions((self.esc_menu_width, 500 - diff))


    def toggle_esc_menu(self):
        if self.esc_menu.visible:
            self.esc_menu.hide()
            if self.load_file_selection_list is not None:
                self.load_file_selection_list.kill()
                self.load_file_selection_list = None
            if self.save_file_selection_list is not None:
                self.save_file_selection_list.kill()
                self.save_file_selection_list = None
            if self.filename_entry is not None:
                self.filename_entry.kill()
                self.filename_entry = None
        else:
            self.esc_menu.show()

    def render(self):
        pass

    def notify_achievement(self, achievement: Achievement):
        self.print(local['unlocked'] + ':<br>' + achievement.text, floating_text_box_time=7)

    def print(self, *strings, sep=' ', end='\n', flush=False, out=None, floating_text_box_time=1.3):
        print(*strings, sep=sep, end=end, flush=flush)

        thing = sep.join(map(str, strings)) + end
        if out is not None:
            thing = "<font color='#ED9FA6'>" + thing + "</font>"
        UIFloatingTextBox(floating_text_box_time, (0, -65 // floating_text_box_time), thing.replace('\n', '<br>'), pygame.Rect(pygame.mouse.get_pos(), (250, -1)), self.cursor_manager)

    def update_windows_list(self):
        if self.apiary_selection_list is not None:
            self.apiary_selection_list.set_item_list(
                [i.name for i in self.inventories.values()] +\
                [local['Apiary'] + ' ' + a.name for a in self.apiaries] +\
                [local['Analyzer'] + ' ' + a.name for a in self.analyzers]
            )

    def update(self, time_delta):
        if CurrentTutorialStage.current_tutorial_stage == TutorialStage.NO_RESOURCES and len(self.resources) > 0:
            CurrentTutorialStage.current_tutorial_stage = TutorialStage.RESOURCES_AVAILABLE
            pygame.event.post(pygame.event.Event(TUTORIAL_STAGE_CHANGED, {}))
        elif CurrentTutorialStage.current_tutorial_stage == TutorialStage.RESOURCES_AVAILABLE and ResourceTypes.HONEY in self.resources:
            CurrentTutorialStage.current_tutorial_stage = TutorialStage.INSPECT_AVAILABLE
            pygame.event.post(pygame.event.Event(TUTORIAL_STAGE_CHANGED, {}))

        self.build_dropdown.set_available_build_options(self.get_available_build_options())

    def add_mendelian_inheritance_to_esc_menu(self):
        if local['Mendelian Inheritance'] not in self.esc_menu._raw_item_list:
            self.esc_menu._raw_item_list.insert(2, local['Mendelian Inheritance'])
            self.esc_menu.set_item_list(self.esc_menu._raw_item_list)

    def set_dimensions(self, size):
        self.window_size = size
        esc_menu_rect = pygame.Rect(0, 0, 200, 500)
        esc_menu_rect.center = (self.window_size[0]/2, self.window_size[1]/2)
        self.esc_menu.set_relative_position(esc_menu_rect.topleft)
        if self.apiary_selection_list is not None:
            self.apiary_selection_list.set_dimensions((self.apiary_selection_list_width, size[1]))

    def process_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.esc_menu.visible:
                mouse_hovers_esc_menu = self.esc_menu.hover_point(*self.ui_manager.get_mouse_position())
                mouse_hovers_save_file_selection_list = self.save_file_selection_list is not None and self.save_file_selection_list.hover_point(*self.ui_manager.get_mouse_position())
                mouse_hovers_load_file_selection_list = self.load_file_selection_list is not None and self.load_file_selection_list.hover_point(*self.ui_manager.get_mouse_position())
                mouse_hovers_filename_entry = self.filename_entry is not None and self.filename_entry.hover_point(*self.ui_manager.get_mouse_position())
                mouse_hovers_save_confirm = self.save_confirm is not None and self.save_confirm.hover_point(*self.ui_manager.get_mouse_position())
                mouse_hovers_load_confirm = self.load_confirm is not None and self.load_confirm.hover_point(*self.ui_manager.get_mouse_position())
                mouse_hovers_new_game_confirm = self.new_game_confirm is not None and self.new_game_confirm.hover_point(*self.ui_manager.get_mouse_position())
                if (not mouse_hovers_esc_menu and
                    not mouse_hovers_save_file_selection_list and
                    not mouse_hovers_load_file_selection_list and
                    not mouse_hovers_filename_entry and
                    not mouse_hovers_save_confirm and
                    not mouse_hovers_load_confirm and
                    not mouse_hovers_new_game_confirm):
                        self.toggle_esc_menu()
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.apiary_selection_list:
                if event.text.startswith(local['Apiary']):
                    index = int(event.text.split()[-1])
                    mouse_pos_x, mouse_pos_y = self.ui_manager.get_mouse_position()
                    self.apiary_windows.append(
                        ApiaryWindow(self, self.apiaries[index], self.cursor, pygame.Rect((mouse_pos_x - 300, mouse_pos_y), APIARY_WINDOW_SIZE), self.ui_manager)
                    )
                elif event.text in self.inventories:
                    index = event.text
                    mouse_pos_x, mouse_pos_y = self.ui_manager.get_mouse_position()
                    self.inventory_windows.append(
                        InventoryWindow(self.inventories[index], self.cursor,
                            pygame.Rect((mouse_pos_x - 486, mouse_pos_y), INVENTORY_WINDOW_SIZE), #type: ignore
                            self.ui_manager, resizable=True)
                        )
                elif event.text.startswith(local['Analyzer']):
                    index = int(event.text.split()[-1])
                    analyzer = self.analyzers[index]
                    mouse_pos_x, mouse_pos_y = self.ui_manager.get_mouse_position()
                    pos_x = mouse_pos_x - ANALYZER_WINDOW_SIZE[0]
                    self.analyzer_windows.append(
                        AnalyzerWindow(analyzer, self.cursor,
                        pygame.Rect((pos_x, mouse_pos_y), (0,0)))
                    )
            elif event.ui_element == self.esc_menu:
                if event.text == local['Exit']:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                elif event.text == local['Load']:
                    if self.load_file_selection_list is None:
                        self.open_load_file_selection_list()
                    if self.save_file_selection_list is not None:
                        self.save_file_selection_list.kill()
                        self.save_file_selection_list = None
                        self.filename_entry.kill()
                        self.filename_entry = None
                elif event.text == local['Save']:
                    if self.save_file_selection_list is None:
                        self.open_save_file_selection_list()
                    if self.load_file_selection_list is not None:
                        self.load_file_selection_list.kill()
                        self.load_file_selection_list = None
                elif event.text == local['New game']:
                    r = pygame.Rect((pygame.mouse.get_pos()), UI_MESSAGE_SIZE)
                    self.new_game_confirm = UILocationFindingConfirmationDialog(r, local['new_game_confirm'], self.cursor_manager)
                elif event.text == local['Settings']:
                    self.settings_window()
                    self.toggle_esc_menu()
                elif event.text == local['Mendelian Inheritance']:
                    self.open_mendel_window()
                    self.toggle_esc_menu()
                elif event.text == local['Greetings Window']:
                    self.help_window()
                    self.toggle_esc_menu()
                elif event.text == local['Mating History']:
                    if self.mating_history_window is None:
                        self.open_mating_history_window()
                    self.toggle_esc_menu()
            elif event.ui_element == self.load_file_selection_list:
                r = pygame.Rect((pygame.mouse.get_pos()), UI_MESSAGE_SIZE)
                self.load_confirm = UILocationFindingConfirmationDialog(r, local['load_confirm'], self.cursor_manager)
                self.load_confirm.filename = event.text
            elif event.ui_element == self.save_file_selection_list:
                r = pygame.Rect((pygame.mouse.get_pos()), UI_MESSAGE_SIZE)
                self.save_confirm = UILocationFindingConfirmationDialog(r, local['save_confirm'], self.cursor_manager)
                self.save_confirm.filename = event.text
        elif event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
            if event.ui_element == self.filename_entry:
                if event.text in self.get_save_names_list():
                    r = pygame.Rect((pygame.mouse.get_pos()), UI_MESSAGE_SIZE)
                    self.save_confirm = UILocationFindingConfirmationDialog(r, local['save_confirm'], self.cursor_manager)
                    self.save_confirm.filename = event.text
                else:
                    self.save(event.text)
                    self.print('Saved the game to the disk')
                    self.toggle_esc_menu()
        elif event.type == pygame_gui.UI_WINDOW_MOVED_TO_FRONT:
            if isinstance(event.ui_element, InventoryWindow):
                self.most_recent_inventory = event.ui_element.inv
        elif event.type == SET_MOST_RECENT_INVENTORY:
            self.most_recent_inventory = event.inventory
        elif event.type == pygame_gui.UI_WINDOW_CLOSE:
            try:
                if isinstance(event.ui_element, InventoryWindow):
                    self.inventory_windows.remove(event.ui_element)
                    for window in reversed(self.ui_manager.get_window_stack().get_stack()):
                        if isinstance(window, InventoryWindow):
                            self.most_recent_inventory = window.inv
                            break
                elif isinstance(event.ui_element, ApiaryWindow):
                    self.apiary_windows.remove(event.ui_element)
                elif isinstance(event.ui_element, AnalyzerWindow):
                    self.analyzer_windows.remove(event.ui_element)
                elif isinstance(event.ui_element, MatingHistoryWindow):
                    self.mating_history_window = None
                elif isinstance(event.ui_element, BestiaryWindow):
                    self.bestiary_window = None
                elif isinstance(event.ui_element, Achievement):
                    self.achievements_window = None
                elif isinstance(event.ui_element, InspectWindow):
                    self.inspect_windows.remove(event.ui_element)
            except ValueError:
                print('Somehow window was closed that wasnt in any list:', event.ui_element)
            else:
                if self.apiary_selection_list is None and isinstance(event.ui_element, (InventoryWindow, ApiaryWindow)):
                    self.open_apiary_selection_list()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.toggle_esc_menu()
            elif event.key == pygame.K_F5:
                self.resources.add_resources({ResourceTypes.HONEY: 1000, ResourceTypes.ROYAL_JELLY: 250, ResourceTypes.POLLEN_CLUSTER: 250})
        elif event.type == INSPECT_BEE:
            if self.total_inspections == 0:
                r = pygame.Rect((pygame.mouse.get_pos()), UI_MESSAGE_SIZE)
                self.inspect_confirm = UILocationFindingConfirmationDialog(r, local['Inspection popup'].format(self.inspect_cost * config_production_modifier), self.ui_manager)
                self.inspect_confirm.bee_button = event.ui_element.bee_button
                self.inspect_confirm.bee_stats = event.ui_element.bee_stats
                self.inspect_confirm.ui_element = event.ui_element
            else:
                self.inspect_bee(event.ui_element.bee_button.slot.slot)
                event.ui_element.rebuild()
                event.ui_element.bee_button.most_specific_combined_id = 'some nonsense' # dirty hack to make the button refresh inspect status
        elif event.type == INVENTORY_RENAMED:
            self.rename_inventory(event.old_name, event.new_name)
            self.update_windows_list()
        elif event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
            if event.ui_element == self.load_confirm:
                self.load(self.load_confirm.filename)
                self.print('Loaded save from disk')
                self.toggle_esc_menu()
            elif event.ui_element == self.save_confirm:
                self.save(self.save_confirm.filename)
                self.print('Saved the game to the disk')
                self.toggle_esc_menu()
            elif event.ui_element == self.new_game_confirm:
                self.restart_game()
            elif event.ui_element == self.inspect_confirm:
                self.inspect_bee(self.inspect_confirm.bee_button.slot.slot)
                if isinstance(self.inspect_confirm.ui_element, InspectWindow):
                    self.inspect_confirm.ui_element.reshape_according_to_bee_stats()
                self.inspect_confirm.bee_button.most_specific_combined_id = 'some nonsense' ## dirty hack to make the button refresh inspect status
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.forage_button:
                if CurrentTutorialStage.current_tutorial_stage == TutorialStage.BEFORE_FORAGE:
                    CurrentTutorialStage.current_tutorial_stage = TutorialStage.NO_RESOURCES # progress the tutorial

                    self.apiary_windows.append(ApiaryWindow(self, self.apiaries[0], self.cursor, pygame.Rect((self.resources_panel_width, 0), APIARY_WINDOW_SIZE), self.ui_manager))

                    self.inv_window = InventoryWindow(self.inv, self.cursor,
                        pygame.Rect((self.apiary_windows[0].rect.right, 0), INVENTORY_WINDOW_SIZE),
                        self.ui_manager, resizable=True)
                    self.inventory_windows.append(self.inv_window)
                    self.most_recent_inventory = self.inv

                self.forage(self.most_recent_inventory)
            elif event.ui_element == self.open_inspect_window_button:
                self.open_inspect_window()
            elif event.ui_element == self.bestiary_button:
                self.open_bestiary_window()
            elif event.ui_element == self.achievements_button:
                self.open_achievements_window()
            elif event.ui_element == self.menu_button:
                self.toggle_esc_menu()
            if event.ui_element in self.build_dropdown.buttons:
                text = event.ui_element.text
                index = self.build_dropdown.local_build_options.index(text)
                building_name = self.build_dropdown.known_build_options[index]
                building = self.build(building_name.lower())
                if isinstance(building, Alveary):
                    win_window = UIMessageWindow(pygame.Rect((0,0), self.window_size), f'<effect id=bounce><font size=7.0>{local["won_the_demo"]}</font></effect>', self.ui_manager, window_title='You won the demo!', object_id='#WinWindow')
                    win_window.text_block.set_active_effect(pygame_gui.TEXT_EFFECT_BOUNCE, effect_tag='bounce')
                elif isinstance(building, Apiary):
                    window = ApiaryWindow(self, building, self.cursor, pygame.Rect(pygame.mouse.get_pos(), APIARY_WINDOW_SIZE), self.ui_manager)
                    self.apiary_windows.append(window)
                    self.update_windows_list()
                elif isinstance(building, Inventory):
                    window = InventoryWindow(building, self.cursor,
                        pygame.Rect(self.ui_manager.get_mouse_position(), INVENTORY_WINDOW_SIZE),
                        self.ui_manager, resizable=True)
                    self.inventory_windows.append(window)
                    self.update_windows_list()
                elif isinstance(building, Analyzer):
                    window = AnalyzerWindow(building, self.cursor,
                        pygame.Rect(self.ui_manager.get_mouse_position(), (0,0)))
                    self.analyzer_windows.append(window)
                    self.update_windows_list()
                else:
                    self.print('Building is not provided or not implemented')

        elif event.type == TUTORIAL_STAGE_CHANGED:
            if CurrentTutorialStage.current_tutorial_stage == TutorialStage.RESOURCES_AVAILABLE:
                self.bestiary_button.show()
                self.achievements_button.show()
                self.resources_panel.show()
            elif CurrentTutorialStage.current_tutorial_stage == TutorialStage.INSPECT_AVAILABLE:
                self.open_inspect_window_button.show()
                self.open_inspect_window(rect=pygame.Rect(-13, self.open_inspect_window_button.rect.bottom-13, 0, 0)) #type: ignore
            elif CurrentTutorialStage.current_tutorial_stage == TutorialStage.GENE_HELPER_TEXT_CLICKED:
                self.open_mendel_notification()
                self.add_mendelian_inheritance_to_esc_menu()

    def get_state(self):
        state = super().get_state()
        state['front_version'] = CURRENT_FRONT_VERSION
        state['current_tutorial_stage'] = CurrentTutorialStage.current_tutorial_stage
        state['apiary_list_opened'] = self.apiary_selection_list is not None and self.apiary_selection_list.visible
        state['cursor_slot'] = self.cursor.slot
        insp_win = []
        insp_slots = []
        for window in self.inspect_windows:
            insp_win.append(window.relative_rect)
            insp_slots.append(window.bee_button.slot)
        state['inspect_windows'] = insp_win
        state['inspect_slots'] = insp_slots
        state['apiary_windows'] = [(window.apiary, window.relative_rect) for window in self.apiary_windows]
        state['inventory_windows'] = [(window.inv.name, window.relative_rect) for window in self.inventory_windows]
        state['analyzer_windows'] = [window.relative_rect for window in self.analyzer_windows]
        return state

    def load(self, name):
        try:
            state = super().load(name)
        except FileNotFoundError:
            return

        try:
            if state.get('front_version', 0) < CURRENT_FRONT_VERSION:
                for update_front_func in update_front_versions[state.get('front_version', 0):]:
                    state = update_front_func(state)
        except Exception:
            print_exc()
            self.exit()
        for window in self.apiary_windows:
            window.kill()
        for window in self.inventory_windows:
            window.kill()
        for window in self.inspect_windows:
            window.kill()
        for window in self.analyzer_windows:
            window.kill()
        if self.apiary_selection_list is not None:
            logging.debug('killed apiary_selection in load')
            self.apiary_selection_list.kill()

        self.cursor.slot = state['cursor_slot']

        CurrentTutorialStage.current_tutorial_stage = state['current_tutorial_stage']
        if state['current_tutorial_stage'] >= TutorialStage.RESOURCES_AVAILABLE:
            self.bestiary_button.show()
            self.achievements_button.show()
            self.resources_panel.resources = state['resources']
            self.resources_panel.show()
            self.build_dropdown.resources = state['resources']
            self.build_dropdown.set_available_build_options(self.get_available_build_options())
        if state['current_tutorial_stage'] >= TutorialStage.INSPECT_AVAILABLE:
            self.open_inspect_window_button.show()
        if state['current_tutorial_stage'] >= TutorialStage.GENE_HELPER_TEXT_CLICKED:
            self.add_mendelian_inheritance_to_esc_menu()
        if state['apiary_list_opened']:
            logging.debug('open apiary_selection in load')
            self.open_apiary_selection_list()
        self.inspect_windows = [InspectWindow(self, self.cursor, rect, self.ui_manager) for rect in state['inspect_windows']]
        for window, slot in zip(self.inspect_windows, state['inspect_slots']):
            window.bee_button.slot = slot
            window.bee_stats.bee = slot.slot # TODO: some stupid initialization here, rework?
            window.reshape_according_to_bee_stats()
        self.inventory_windows = [InventoryWindow(state['inventories'][inv_name], self.cursor, rect, self.ui_manager) for inv_name, rect in state['inventory_windows']]
        self.apiary_windows = [ApiaryWindow(self, api, self.cursor, rect, self.ui_manager) for api, rect in state['apiary_windows']]
        self.analyzer_windows = [AnalyzerWindow(self.analyzers[index], self.cursor, rect, self.ui_manager) for index, rect in enumerate(state.get('analyzer_windows', []))]
        if self.mating_history_window is not None:
            self.mating_history_window.mating_history = self.mating_history
            self.mating_history.something_changed = True
        return state
