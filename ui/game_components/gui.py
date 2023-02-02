import os
from enum import IntEnum
from typing import Union

import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UITextBox
from pygame_gui.windows import UIMessageWindow

from config import (INVENTORY_WINDOW_SIZE, UI_MESSAGE_SIZE,
                    config_production_modifier, helper_text, local)
from forestry import Apiary, Game, Inventory, Slot
from migration import CURRENT_FRONT_VERSION, update_front_versions

from ..custom_events import INSPECT_BEE, TUTORIAL_STAGE_CHANGED
from ..elements import (UIFloatingTextBox, UILocationFindingConfirmationDialog,
                        UILocationFindingMessageWindow,
                        UINonChangingDropDownMenu, UIPickList)
from . import (Cursor, InspectWindow, InventoryWindow, MatingHistoryWindow,
               MendelTutorialWindow, ResourcePanel, SettingsWindow,
               TutorialStage)
from .apiary_window import ApiaryWindow
from .tutorial_stage import CurrentTutorialStage


class GUI(Game):
    def __init__(self, window_size, manager: pygame_gui.UIManager, cursor_manager):
        self.command_out = 1
        super().__init__()
        Slot.empty_str = ''
        Slot.str_amount = lambda x: '' # type: ignore

        self.window_size = window_size
        self.ui_manager = manager
        if not os.path.exists('save.forestry'):
            self.help_window()

        self.cursor_manager = cursor_manager
        self.cursor = Cursor(Slot(), pygame.Rect(0, 0, 64, 64), '', cursor_manager)
        self.inspect_windows = []
        self.resource_panel_width = 330

        bottom_buttons_height = 40

        self.shown_resources = None

        resource_panel_rect = pygame.Rect(0, 0, self.resource_panel_width, window_size[1])
        r = pygame.Rect((0, 0), (resource_panel_rect.size[0]-6, resource_panel_rect.size[1] - 440))
        self.resources_text_box = UITextBox(str(self.resources), r)

        self.original_build_options = ['Inventory', 'Apiary', 'Alveary']
        self.known_build_options = []
        self.local_build_options = []
        self.build_dropdown = UINonChangingDropDownMenu([], local['Build'], pygame.Rect(0, 0, resource_panel_rect.size[0]-6, bottom_buttons_height),
            anchors={
                'top':'top',
                'bottom':'top',
                'left':'left',
                'right':'left',
                'top_target': self.resources_text_box
            }, visible=False)

        #self.resource_panel = ResourcePanel(self, self.cursor, resource_panel_rect, 0, manager, visible=False)

        self.forage_button = UIButton(pygame.Rect(0, 0, resource_panel_rect.size[0]-6, 40), local['Forage'], container=None,
            anchors={
                'top':'top',
                'bottom':'top',
                'left':'left',
                'right':'left',
                'top_target': self.build_dropdown
            }
        )
        self.open_inspect_window_button = UIButton(pygame.Rect(0, 0, resource_panel_rect.size[0]-6, 40), local['Open Inspect Window'], container=None,
            anchors={
                'top':'top',
                'bottom':'top',
                'left':'left',
                'right':'left',
                'top_target': self.forage_button
            },
            visible=False)
        self.menu_button = UIButton(pygame.Rect(0, -40, resource_panel_rect.size[0]-6, 40), local['Menu'], container=None,
            anchors={
                'top':'bottom',
                'bottom':'bottom',
                'left':'left',
                'right':'left',
            },
            visible=True)
        self.apiary_windows = []
        self.inventory_windows = []

        self.apiary_selection_list_width = 100
        self.apiary_selection_list = None

        self.mating_history_window = None
        self.load_confirm = None
        self.save_confirm = None

        esc_menu_rect = pygame.Rect(0, 0, 200, 500)
        esc_menu_rect.center = (self.window_size[0]/2, self.window_size[1]/2)
        self.esc_menu = UIPickList(esc_menu_rect, [local['Greetings Window'], local['Settings'], local['Load'], local['Save'], local['Exit']], cursor_manager, visible=False, starting_height=30)

        self.load('save')

    def settings_window(self):
        return SettingsWindow(pygame.Rect((0,0), self.window_size), self.ui_manager, local['Settings'])

    def help_window(self):
        r = pygame.Rect(0, 0, self.window_size[0] - 100, self.window_size[1] - 100)
        r.center = (self.window_size[0]/2, self.window_size[1]/2)
        return UILocationFindingMessageWindow(r, helper_text[0], self.ui_manager)

    def mendel_window(self):
        r = pygame.Rect(0, 0, 3/4*self.window_size[0], 3/4*self.window_size[1])
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

    def toggle_esc_menu(self):
        if self.esc_menu.visible:
            self.esc_menu.hide()
        else:
            self.esc_menu.show()

    def render(self):
        pass

    def print(self, *strings, sep=' ', end='\n', flush=False, out=None, floating_text_box_time=1.3):
        print(*strings, sep=sep, end=end, flush=flush)

        thing = sep.join(map(str, strings)) + end
        if out is not None:
            thing = "<font color='#ED9FA6'>" + thing + "</font>"
        UIFloatingTextBox(floating_text_box_time, (0, -65 // floating_text_box_time), thing.replace('\n', '<br>'), pygame.Rect(pygame.mouse.get_pos(), (250, -1)), self.cursor_manager)

    def update_windows_list(self):
        if self.apiary_selection_list is not None:
            self.apiary_selection_list.set_item_list(
                [local['Inventory'] + ' ' + i.name for i in self.inventories] +\
                [local['Apiary'] + ' ' + a.name for a in self.apiaries]
            )

    def update_resources_text_box(self):
        if CurrentTutorialStage.current_tutorial_stage == TutorialStage.NO_RESOURCES and len(self.resources) > 0:
            CurrentTutorialStage.current_tutorial_stage = TutorialStage.RESOURCES_AVAILABLE
            pygame.event.post(pygame.event.Event(TUTORIAL_STAGE_CHANGED, {}))
        elif CurrentTutorialStage.current_tutorial_stage == TutorialStage.RESOURCES_AVAILABLE and 'honey' in self.resources:
            CurrentTutorialStage.current_tutorial_stage = TutorialStage.INSPECT_AVAILABLE
            pygame.event.post(pygame.event.Event(TUTORIAL_STAGE_CHANGED, {}))

        if self.shown_resources != self.resources:
            self.shown_resources = self.resources.copy()
            text = str(self.resources)
            for r in local['resources'].items():
                text = text.replace(*r)
            self.resources_text_box.set_text(text)

            available_build_options = self.get_available_build_options()
            if len(available_build_options) > 0:
                self.build_dropdown.show()
            for option in available_build_options:
                if option not in self.known_build_options:
                    self.known_build_options.append(option)
                    self.local_build_options.append(local[option])
                    self.build_dropdown.add_options([local[option]])

    def add_mendelian_inheritance_to_esc_menu(self):
        self.esc_menu.set_item_list([local['Greetings Window'], local['Mendelian Inheritance'], local['Mating History'], local['Settings'], local['Load'], local['Save'], local['Exit']])

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
                else:
                    index = int(event.text.split()[-1])
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
                    r = pygame.Rect((pygame.mouse.get_pos()), UI_MESSAGE_SIZE)
                    self.load_confirm = UILocationFindingConfirmationDialog(r, local['load_confirm'], self.cursor_manager)
                elif event.text == local['Save']:
                    if os.path.exists('save.forestry'):
                        r = pygame.Rect((pygame.mouse.get_pos()), UI_MESSAGE_SIZE)
                        self.save_confirm = UILocationFindingConfirmationDialog(r, local['save_confirm'], self.cursor_manager)
                    else:
                        self.save('save')
                        self.print('Saved the game to the disk')
                elif event.text == local['Settings']:
                    self.settings_window()
                elif event.text == local['Mendelian Inheritance']:
                    self.mendel_window()
                elif event.text == local['Greetings Window']:
                    self.help_window()
                elif event.text == local['Mating History']:
                    if self.mating_history_window is None:
                        self.mating_history_window = self.open_mating_history_window()
                self.esc_menu.hide()
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
        elif event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
            if event.ui_element == self.load_confirm:
                self.load('save')
                self.print('Loaded save from disk')
            elif event.ui_element == self.save_confirm:
                self.save('save')
                self.print('Saved the game to the disk')
            elif event.ui_element == self.inspect_confirm:
                self.inspect_bee(self.inspect_confirm.bee_button.slot.slot)
                if isinstance(self.inspect_confirm.ui_element, InspectWindow):
                    self.inspect_confirm.ui_element.reshape_according_to_bee_stats()
                self.inspect_confirm.bee_button.most_specific_combined_id = 'some nonsense' ## dirty hack to make the button refresh inspect status
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.forage_button:
                if CurrentTutorialStage.current_tutorial_stage == TutorialStage.BEFORE_FORAGE:
                    CurrentTutorialStage.current_tutorial_stage = TutorialStage.NO_RESOURCES # progress the tutorial

                    self.apiary_windows.append(ApiaryWindow(self, self.apiaries[0], self.cursor, pygame.Rect((self.resource_panel_width, 0), (300, 420)), self.ui_manager))

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
                self.resource_panel.show()
            elif CurrentTutorialStage.current_tutorial_stage == TutorialStage.INSPECT_AVAILABLE:
                self.open_inspect_window_button.show()
                self.open_inspect_window(rect=pygame.Rect(-10, self.open_inspect_window_button.rect.bottom-13, 0, 0)) #type: ignore
            elif CurrentTutorialStage.current_tutorial_stage == TutorialStage.GENE_HELPER_TEXT_CLICKED:
                self.open_mendel_notification()
                self.add_mendelian_inheritance_to_esc_menu()

    def update(self, time_delta):
        self.update_resources_text_box()

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
        api_win = []
        for window in self.apiary_windows:
            api_win.append((window.apiary, window.relative_rect))
        state['apiary_windows'] = api_win
        inv_win = []
        for window in self.inventory_windows:
            inv_win.append((window.inv, window.relative_rect))
        state['inventory_windows'] = inv_win
        return state

    def load(self, name):
        try:
            saved = super().load(name)
        except FileNotFoundError:
            return

        if saved.get('front_version', 0) < CURRENT_FRONT_VERSION:
            for update_front_func in update_front_versions[saved.get('front_version', 0):]:
                saved = update_front_func(saved)

        for window in self.apiary_windows:
            window.kill()
        for window in self.inventory_windows:
            window.kill()
        for window in self.inspect_windows:
            window.kill()
        if self.apiary_selection_list is not None:
            self.apiary_selection_list.kill()

        self.cursor.slot = saved['cursor_slot']

        CurrentTutorialStage.current_tutorial_stage = saved['current_tutorial_stage']
        if saved['current_tutorial_stage'] >= TutorialStage.RESOURCES_AVAILABLE:
            self.resources_text_box.show()
        if saved['current_tutorial_stage'] >= TutorialStage.INSPECT_AVAILABLE:
            self.open_inspect_window_button.show()
        if saved['current_tutorial_stage'] >= TutorialStage.GENE_HELPER_TEXT_CLICKED:
            self.add_mendelian_inheritance_to_esc_menu()
        if saved['apiary_list_opened']:
            self.open_apiary_selection_list()
        self.inspect_windows = [InspectWindow(self, self.cursor, rect, self.ui_manager) for rect in saved['inspect_windows']]
        for window, slot in zip(self.inspect_windows, saved['inspect_slots']):
            window.bee_button.slot = slot
            window.bee_stats.bee = slot.slot # TODO: some stupid initialization here, rework?
            window.reshape_according_to_bee_stats()
        self.inventory_windows = [InventoryWindow(inv, self.cursor, rect, self.ui_manager) for inv, rect in saved['inventory_windows']]
        self.apiary_windows = [ApiaryWindow(self, api, self.cursor, rect, self.ui_manager) for api, rect in saved['apiary_windows']]
        if self.mating_history_window is not None:
            self.mating_history_window.mating_history = self.mating_history
            self.mating_history.something_changed = True
        return saved
