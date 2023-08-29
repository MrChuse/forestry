from typing import Optional, Union

import pygame
from pygame_gui.core import ObjectID
from pygame_gui.core.interfaces import IUIManagerInterface
from pygame_gui.elements import UILabel, UIWindow

from config import BeeSpecies, local
from forestry import Bestiary, Drone, Genes, Slot
from ui.game_components import UIButtonSlot

from ..elements import UITable
from .resources_panel import create_resources_row


class BestiaryWindow(UIWindow):
    def __init__(self, bestiary: Bestiary, rect: pygame.Rect, manager: Optional[IUIManagerInterface]  = None, window_display_title: str = "", element_id: Optional[str]  = None, object_id: Union[ObjectID, str, None]  = None, resizable: bool = False, visible: int = 1, draggable: bool = True):
        self.bestiary = bestiary
        self.table : Optional[UITable]  = None
        self.shown_bestiary : Optional[Bestiary]  = None
        self.first_frame = True # just to make killing on the second frame
        super().__init__(rect, manager, window_display_title, element_id, object_id, resizable, visible, draggable)

    def rebuild(self):
        super().rebuild()
        if self.table is not None:
            self.table.kill()

        self.table = UITable(pygame.Rect(0, 0, 0, 0), resizable=True, container=self, kill_on_repopulation=False)
        row_length = max(map(len, self.bestiary.produced_resources.values()))
        self.table.table_contents.append([
            UILabel(pygame.Rect(0, 0, 132, 30), local['species'], container=self.table, object_id='@Centered'),
            UILabel(pygame.Rect(0, 0, 132, 30), local['born'], container=self.table, object_id='@Centered')
            ]
        )
        for _ in range(row_length):
            self.table.table_contents[0].append(UILabel(pygame.Rect(0, 0, 132, 30), local['resource'], container=self.table, object_id='@Centered'))
            self.table.table_contents[0].append(UILabel(pygame.Rect(0, 0, 132, 30), local['produced'], container=self.table, object_id='@Centered'))

        for known_bee_species in self.bestiary.known_bees:
            product_labels = create_resources_row(self.bestiary.produced_resources[known_bee_species], self.table) # these are added in the tail of the row
            needed = max(2 - len(product_labels), 2 * row_length - 2 * len(self.bestiary.produced_resources[known_bee_species])) # should be at least 4 to match first row (and 2 is already present, so max 2-len)
            for _ in range(needed):
                product_labels.append(UILabel(pygame.Rect(0, 0, 132, 30), '', container=self.table))
            self.table.table_contents.append([
                UIButtonSlot(Slot(Drone(Genes((known_bee_species, known_bee_species))), 1), pygame.Rect(0, 0, 64, 64), '', is_inspectable=False, container=self.table),
                UILabel(pygame.Rect(0, 0, 132, 30), str(self.bestiary.known_bees[known_bee_species]), container=self.table, object_id='@Centered')
            ] + product_labels)
        self.table.rebuild()

    def update(self, time_delta: float):
        if self.shown_bestiary != self.bestiary and not self.first_frame:
            self.rebuild()
            self.shown_bestiary = self.bestiary.copy()
        self.first_frame = False
        super().update(time_delta)
