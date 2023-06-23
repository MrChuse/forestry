from typing import Optional, Union
import pygame
from pygame_gui.core import ObjectID
from pygame_gui.core.interfaces import IUIManagerInterface

from forestry import Bestiary, Drone, Genes, Slot
from ui.game_components import UIButtonSlot
from ..elements import UITable
from pygame_gui.elements import UIWindow, UILabel
from config import BeeSpecies, local

class BestiaryWindow(UIWindow):
    def __init__(self, bestiary: Bestiary, rect: pygame.Rect, manager: IUIManagerInterface | None = None, window_display_title: str = "", element_id: str | None = None, object_id: ObjectID | str | None = None, resizable: bool = False, visible: int = 1, draggable: bool = True):
        self.bestiary = bestiary
        self.table : UITable | None = None
        self.shown_bestiary : Bestiary | None = None
        self.first_frame = True # just to make killing on the second frame
        super().__init__(rect, manager, window_display_title, element_id, object_id, resizable, visible, draggable)

    def rebuild(self):
        super().rebuild()
        if self.table is not None:
            self.table.kill()

        self.table = UITable((0, 0, 0, 0), resizable=True, container=self)
        self.table.table_contents.append([
            UILabel(pygame.Rect(0, 0, 132, 30), local['species'], container=self.table, object_id='@Centered'),
            UILabel(pygame.Rect(0, 0, 132, 30), local['produced'], container=self.table, object_id='@Centered'),
            UILabel(pygame.Rect(0, 0, 132, 30), local['resource'], container=self.table, object_id='@Centered'),
            UILabel(pygame.Rect(0, 0, 132, 30), local['produced'], container=self.table, object_id='@Centered')
        ])
        row_length = 2 * max(map(len, self.bestiary.produced_resources.values()))
        for known_bee_species in self.bestiary.known_bees:
            product_labels = [] # these are added in the tail of the row
            for product, amount in self.bestiary.produced_resources[known_bee_species].items():
                product_labels.append(UILabel(pygame.Rect(0, 0, 132, 30), local[product], container=self.table, object_id='@Centered'))
                product_labels.append(UILabel(pygame.Rect(0, 0, 132, 30), str(amount), container=self.table, object_id='@Centered'))
            needed = max(2 - len(product_labels), row_length - 2 * len(self.bestiary.produced_resources[known_bee_species])) # should be at least 4 to match first row (and 2 is already present, so max 2-len)
            for _ in range(needed):
                product_labels.append(UILabel(pygame.Rect(0, 0, 132, 30), '', container=self.table))
            self.table.table_contents.append([
                UIButtonSlot(Slot(Drone(Genes((known_bee_species, known_bee_species))), 1), pygame.Rect(0, 0, 64, 64), '', is_inspectable=False, container=self.table),
                UILabel(pygame.Rect(0, 0, 132, 30), str(self.bestiary.known_bees[known_bee_species]), container=self.table, object_id='@Centered')
            ] + product_labels)
        def f():
            return
        self.table.populate_table_contents = f # hack to disable clearing UITable
        self.table.rebuild()

    def update(self, time_delta: float):
        if self.shown_bestiary != self.bestiary and not self.first_frame:
            self.rebuild()
            self.shown_bestiary = self.bestiary.copy()
        self.first_frame = False
        super().update(time_delta)
