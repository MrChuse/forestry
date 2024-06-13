import pygame
import pygame_gui
from pygame_gui.elements import UIButton

from forestry import Alveary, AlvearyUpgrades
from ..elements import UITable
from ..custom_events import ALVEARY_RENAMED
from ..game_components.cursor import Cursor
from .apiary_window import ApiaryWindow

from config import ALVEARY_WINDOW_SIZE, ALVEARY_AUTOREPLACE_UPGRADED_WINDOW_SIZE, APIARY_WINDOW_SIZE

class AlvearyWindow(ApiaryWindow):
    rename_event = ALVEARY_RENAMED
    def __init__(self, game, alveary: Alveary, cursor: Cursor, relative_rect: pygame.Rect, manager, *args, **kwargs):
        if relative_rect.size == (-1, -1):
            relative_rect.size = ALVEARY_WINDOW_SIZE
        self.alveary = alveary
        super().__init__(game, alveary, cursor, relative_rect, manager, *args, **kwargs)
        self.upgrade_buttons = []
        m = 16
        self.upgrade_table = UITable(pygame.Rect(0, 0, relative_rect.width, 64), container=self, anchors={'top_target': self.take_all_button, 'centerx': 'centerx'}, kill_on_repopulation=False, object_id='#panel_no_borders', resizable=True)
        for i, upgrade in enumerate(AlvearyUpgrades):
            self.upgrade_buttons.append(UIButton(pygame.Rect(0, 0, 60, 60), upgrade.name, container=self.upgrade_table, tool_tip_text=upgrade.name))
        self.upgrade_table.add_row(self.upgrade_buttons)
        self.upgrade_table.rebuild()
        if self.alveary.upgrade is not None:
            self.set_upgrage(self.alveary.upgrade)

    def set_upgrage(self, upgrade: AlvearyUpgrades):
        if upgrade == AlvearyUpgrades.AUTOREPLACE:
            if self.alveary.inv.empty_slots() != 7: raise RuntimeError('Empty the inventory first')
            self.alveary.set_upgrage(upgrade)
            self.set_dimensions(ALVEARY_AUTOREPLACE_UPGRADED_WINDOW_SIZE)
            self.upgrade_table.kill()
            for b in self.buttons:
                b.kill()
            self.take_all_button.kill()
        elif upgrade == AlvearyUpgrades.BETTERMUTATION or upgrade == AlvearyUpgrades.MAKEPRISTINE:
            self.alveary.set_upgrage(upgrade)
            self.set_dimensions(APIARY_WINDOW_SIZE)
            self.upgrade_table.kill()

    def process_event(self, event: pygame.Event) -> bool:
        tmp = super().process_event(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            for button, upgrade in zip(self.upgrade_buttons, AlvearyUpgrades):
                if event.ui_element == button:
                    self.set_upgrage(upgrade)
        elif event.type == ALVEARY_RENAMED:
            if event.ui_element != self and event.building == self.alveary:
                self.entry_line.set_text(event.new_name)
        return tmp