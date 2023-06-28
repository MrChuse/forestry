import os
from enum import IntEnum
from traceback import print_exc
from typing import Union

import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UITextBox, UITextEntryLine
from pygame_gui.windows import UIMessageWindow

from config import (INVENTORY_WINDOW_SIZE, UI_MESSAGE_SIZE, ResourceTypes,
                    config_production_modifier, helper_text, local)
from forestry import Achievement, Apiary, Game, Inventory, Slot
from migration import CURRENT_FRONT_VERSION, update_front_versions

from ..custom_events import (INSPECT_BEE, INVENTORY_RENAMED,
                             TUTORIAL_STAGE_CHANGED)
from ..elements import (UIFloatingTextBox, UILocationFindingConfirmationDialog,
                        UILocationFindingMessageWindow,
                        UINonChangingDropDownMenu, UIPickList)
from . import (BestiaryWindow, Cursor, InspectWindow, InventoryWindow,
               MatingHistoryWindow, MendelTutorialWindow, ResourcesPanel,
               SettingsWindow, TutorialStage)
from .apiary_window import ApiaryWindow
from .tutorial_stage import CurrentTutorialStage


class GUI(Game):
    def restart_game(self):
        super().restart_game()

        CurrentTutorialStage.current_tutorial_stage = TutorialStage.BEFORE_FORAGE
        if self.new_game or not os.path.exists('saves') or len(list(filter(lambda x: x.endswith('.forestry'), os.listdir('saves')))) == 0:
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
        bottom_buttons_height = 40
        self.build_dropdown = UINonChangingDropDownMenu([], local['Build'], pygame.Rect(0, 0, resources_panel_rect.size[0]-6, bottom_buttons_height),
            anchors={
                'top':'top',
                'bottom':'top',
                'left':'left',
                'right':'left',
                'top_target': self.resources_panel
            }, visible=False)

        if self.forage_button is not None:
            self.forage_button.kill()
            self.forage_button = None
        self.forage_button = UIButton(pygame.Rect(0, 0, resources_panel_rect.size[0]-6, 40), local['Forage'], container=None,
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
        self.open_inspect_window_button = UIButton(pygame.Rect(0, 0, resources_panel_rect.size[0]-6, 40), local['Open Inspect Window'], container=None,
            anchors={
                'top':'top',
                'bottom':'top',
                'left':'left',
                'right':'left',
                'top_target': self.forage_button
            },
            visible=False)

        if self.menu_button is not None:
            self.menu_button.kill()
            self.menu_button = None
        self.menu_button = UIButton(pygame.Rect(0, -40, resources_panel_rect.size[0]-6, 40), local['Menu'], container=None,
            anchors={
                'top':'bottom',
                'bottom':'bottom',
                'left':'left',
                'right':'left',
            },
            visible=True)

        for w in self.apiary_windows:
            w.kill()
        for w in self.inventory_windows:
            w.kill()
        for w in self.inspect_windows:
            w.kill()
        self.apiary_windows = []
        self.inventory_windows = []
        self.inspect_windows = []

        if self.apiary_selection_list is not None:
            self.apiary_selection_list.kill()

        if self.bestiary_window is not None:
            self.bestiary_window.kill()
            self.bestiary_window = None
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

    def __init__(self, window_size, manager: pygame_gui.UIManager, cursor_manager: pygame_gui.UIManager, new_game: bool = False):
        self.command_out = 1
        Slot.empty_str = ''
        Slot.str_amount = lambda x: '' # type: ignore

        self.window_size = window_size
        self.ui_manager = manager
        self.cursor_manager = cursor_manager
        self.new_game = new_game

        self.resources_panel_width = 330

        self.shown_resources = None
        self.resources_panel = None

        self.original_build_options = ['Inventory', 'Apiary', 'Alveary']
        self.known_build_options = []
        self.local_build_options = []
        self.build_dropdown = None

        self.forage_button = None
        self.open_inspect_window_button = None
        self.menu_button = None

        self.apiary_windows = []
        self.inventory_windows = []
        self.inspect_windows = []

        self.apiary_selection_list_width = 100
        self.apiary_selection_list = None

        self.bestiary_window = None
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
        r = pygame.Rect(0, 0, 3/4*self.window_size[0], 3/4*self.window_size[1])
        r.center = (self.window_size[0]/2, self.window_size[1]/2)
        return BestiaryWindow(self.bestiary, r, self.ui_manager, local['Bestiary'])

    def open_mendel_window(self):
        r = pygame.Rect(0, 0, 1036, 584)
        print(r)
        r.center = (self.window_size[0]/2, self.window_size[1]/2)
        return MendelTutorialWindow(r, self.ui_manager)

    def open_mating_history_window(self):
        r = pygame.Rect(0, 0, 3/4*self.window_size[0], 3/4*self.window_size[1])
        r.center = (self.window_size[0]/2, self.window_size[1]/2)
        return MatingHistoryWindow(self.mating_history, r, self.ui_manager, 'Mating History')

    def open_inspect_window(self, rect: Union[pygame.Rect, None] = None):
        if rect is None:
            rect = pygame.Rect(pygame.mouse.get_pos(), (0, 0))
        self.inspect_windows.append(InspectWindow(self, self.cursor, rect, self.ui_manager))

    def open_apiary_selection_list(self):
        print('opened apiary selection')
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

    def open_bestiary_notification(self):
        mouse_pos = self.ui_manager.get_mouse_position()
        r = pygame.Rect(mouse_pos, UI_MESSAGE_SIZE)
        return UILocationFindingMessageWindow(r, local['bestiary_notification'], self.ui_manager)

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
                [local['Apiary'] + ' ' + a.name for a in self.apiaries]
            )

    def update(self, time_delta):
        if CurrentTutorialStage.current_tutorial_stage == TutorialStage.NO_RESOURCES and len(self.resources) > 0:
            CurrentTutorialStage.current_tutorial_stage = TutorialStage.RESOURCES_AVAILABLE
            pygame.event.post(pygame.event.Event(TUTORIAL_STAGE_CHANGED, {}))
        elif CurrentTutorialStage.current_tutorial_stage == TutorialStage.RESOURCES_AVAILABLE and ResourceTypes.HONEY in self.resources:
            CurrentTutorialStage.current_tutorial_stage = TutorialStage.INSPECT_AVAILABLE
            pygame.event.post(pygame.event.Event(TUTORIAL_STAGE_CHANGED, {}))

        if self.shown_resources != self.resources:
            self.shown_resources = self.resources.copy()
            available_build_options = self.get_available_build_options()
            if len(available_build_options) > 0:
                self.build_dropdown.show()
            for option in available_build_options:
                if option not in self.known_build_options:
                    self.known_build_options.append(option)
                    self.local_build_options.append(local[option])
                    self.build_dropdown.add_options([local[option]])

    def add_bestiary_to_esc_menu(self):
        if local['Bestiary'] not in self.esc_menu._raw_item_list:
            self.esc_menu._raw_item_list.insert(1, local['Bestiary'])
            self.esc_menu.set_item_list(self.esc_menu._raw_item_list)

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
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.apiary_selection_list:
                if event.text.startswith(local['Apiary']):
                    index = int(event.text.split()[-1])
                    mouse_pos_x, mouse_pos_y = self.ui_manager.get_mouse_position()
                    self.apiary_windows.append(
                        ApiaryWindow(self, self.apiaries[index], self.cursor, pygame.Rect((mouse_pos_x - 300, mouse_pos_y), (300, 420)), self.ui_manager)
                    )
                elif event.text in self.inventories:
                    index = event.text
                    mouse_pos_x, mouse_pos_y = self.ui_manager.get_mouse_position()
                    self.inventory_windows.append(
                        InventoryWindow(self.inventories[index], self.cursor,
                            pygame.Rect((mouse_pos_x - 486, mouse_pos_y), INVENTORY_WINDOW_SIZE), #type: ignore
                            self.ui_manager, resizable=True)
                        )
            elif event.ui_element == self.esc_menu:
                if event.text == local['Exit']:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                elif event.text == local['Load']:
                    self.open_load_file_selection_list()
                    if self.save_file_selection_list is not None:
                        self.save_file_selection_list.kill()
                        self.save_file_selection_list = None
                        self.filename_entry.kill()
                        self.filename_entry = None
                elif event.text == local['Save']:
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
                elif event.text == local['Bestiary']:
                    self.bestiary_window = self.open_bestiary_window()
                    self.toggle_esc_menu()
                elif event.text == local['Mendelian Inheritance']:
                    self.mendel_window = self.open_mendel_window()
                    self.toggle_esc_menu()
                elif event.text == local['Greetings Window']:
                    self.help_window()
                    self.toggle_esc_menu()
                elif event.text == local['Mating History']:
                    if self.mating_history_window is None:
                        self.mating_history_window = self.open_mating_history_window()
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
        elif event.type == pygame_gui.UI_WINDOW_CLOSE:
            try:
                if isinstance(event.ui_element, InventoryWindow):
                    self.inventory_windows.remove(event.ui_element)
                elif isinstance(event.ui_element, ApiaryWindow):
                    self.apiary_windows.remove(event.ui_element)
                elif isinstance(event.ui_element, MatingHistoryWindow):
                    self.mating_history_window = None
                elif isinstance(event.ui_element, BestiaryWindow):
                    self.bestiary_window = None
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
        elif event.type == INSPECT_BEE:
            if self.total_inspections == 0:
                r = pygame.Rect((pygame.mouse.get_pos()), UI_MESSAGE_SIZE)
                self.inspect_confirm = UILocationFindingConfirmationDialog(r, local['Inspection popup'].format(config_production_modifier), self.ui_manager)
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

                    self.apiary_windows.append(ApiaryWindow(self, self.apiaries[0], self.cursor, pygame.Rect((self.resources_panel_width, 0), (300, 420)), self.ui_manager))

                    self.inv_window = InventoryWindow(self.inv, self.cursor,
                        pygame.Rect((self.apiary_windows[0].rect.right, 0), INVENTORY_WINDOW_SIZE),
                        self.ui_manager, resizable=True)
                    self.inventory_windows.append(self.inv_window)
                    self.most_recent_inventory = self.inv

                self.forage(self.most_recent_inventory)
            elif event.ui_element == self.open_inspect_window_button:
                self.open_inspect_window()
            elif event.ui_element == self.menu_button:
                self.toggle_esc_menu()
        elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.build_dropdown:
                if event.text != 'Build':
                    text = event.text
                    index = self.local_build_options.index(text)
                    building_name = self.known_build_options[index]
                    building = self.build(building_name.lower())
                    if isinstance(building, Apiary):
                        window = ApiaryWindow(self, building, self.cursor, pygame.Rect(pygame.mouse.get_pos(), (300, 420)), self.ui_manager)
                        self.apiary_windows.append(window)
                        self.update_windows_list()
                    elif isinstance(building, Inventory):
                        window = InventoryWindow(building, self.cursor,
                        pygame.Rect(self.ui_manager.get_mouse_position(), INVENTORY_WINDOW_SIZE),
                        self.ui_manager, resizable=True)
                        self.inventory_windows.append(window)
                        self.update_windows_list()
                    else: #if isinstance(building, Alveary):
                        win_window = UIMessageWindow(pygame.Rect((0,0), self.window_size), '<effect id=bounce><font size=7.0>You won the demo!</font></effect>', self.ui_manager, window_title='You won the demo!', object_id='#WinWindow')
                        win_window.text_block.set_active_effect(pygame_gui.TEXT_EFFECT_BOUNCE, effect_tag='bounce')
        elif event.type == TUTORIAL_STAGE_CHANGED:
            if CurrentTutorialStage.current_tutorial_stage == TutorialStage.RESOURCES_AVAILABLE:
                self.open_bestiary_notification()
                self.add_bestiary_to_esc_menu()
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
        state['apiary_list_opened'] = self.apiary_selection_list is not None
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
        if self.apiary_selection_list is not None:
            self.apiary_selection_list.kill()

        self.cursor.slot = state['cursor_slot']

        CurrentTutorialStage.current_tutorial_stage = state['current_tutorial_stage']
        if state['current_tutorial_stage'] >= TutorialStage.RESOURCES_AVAILABLE:
            self.add_bestiary_to_esc_menu()
            self.resources_panel.resources = state['resources']
            self.resources_panel.show()
        if state['current_tutorial_stage'] >= TutorialStage.INSPECT_AVAILABLE:
            self.open_inspect_window_button.show()
        if state['current_tutorial_stage'] >= TutorialStage.GENE_HELPER_TEXT_CLICKED:
            self.add_mendelian_inheritance_to_esc_menu()
        if state['apiary_list_opened']:
            print(' in load apiary_list_opened')
            self.open_apiary_selection_list()
        self.inspect_windows = [InspectWindow(self, self.cursor, rect, self.ui_manager) for rect in state['inspect_windows']]
        for window, slot in zip(self.inspect_windows, state['inspect_slots']):
            window.bee_button.slot = slot
            window.bee_stats.bee = slot.slot # TODO: some stupid initialization here, rework?
            window.reshape_according_to_bee_stats()
        self.inventory_windows = [InventoryWindow(state['inventories'][inv_name], self.cursor, rect, self.ui_manager) for inv_name, rect in state['inventory_windows']]
        self.apiary_windows = [ApiaryWindow(self, api, self.cursor, rect, self.ui_manager) for api, rect in state['apiary_windows']]
        if self.mating_history_window is not None:
            self.mating_history_window.mating_history = self.mating_history
            self.mating_history.something_changed = True
        return state
