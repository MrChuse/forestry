from typing import Dict, Union

import pygame
from pygame_gui.core import ObjectID
from pygame_gui.elements import UIButton

from forestry import Drone, Genes, MatingEntry, Princess, Slot

from ..elements import UIGridPanel
from .ui_button_slot import UIButtonSlot


class MatingEntryPanel(UIGridPanel):
    def __init__(self, count: int, entry: MatingEntry, relative_rect: pygame.Rect, starting_layer_height: int, manager, *, element_id: str = 'panel', margins: Dict[str, int] = None, container = None, parent_element = None, object_id: Union[ObjectID, str, None] = None, anchors: Dict[str, str] = None, visible: int = 1):
        self.count = count
        self.entry = entry
        relative_rect.size = (518, 70)
        super().__init__(relative_rect, starting_layer_height, manager, element_id=element_id, margins=margins, container=container, parent_element=parent_element, object_id=object_id, anchors=anchors, visible=visible, subelements_function=self.subelements_method)

    def subelements_method(self, container):
        buttons = []
        for index, (cls, allele, inspected) in enumerate(zip(
                [Princess, Princess, Drone, Drone, Drone, Drone],
                [self.entry.parent1_dom, self.entry.parent1_rec, self.entry.parent2_dom, self.entry.parent2_rec, self.entry.child_dom, self.entry.child_rec],
                [self.entry.parent1_inspected, self.entry.parent1_inspected, self.entry.parent2_inspected, self.entry.parent2_inspected, self.entry.child_inspected, self.entry.child_inspected])):
            if index % 2 == 1 and not inspected:
                slot = Slot()
            else:
                bee = cls(Genes((allele, allele), None, None, None), inspected=inspected)
                slot = Slot(bee, self.count)
            buttons.append(UIButtonSlot(slot, pygame.Rect(0, 0, 64, 64), '', self.ui_manager, container=container, is_inspectable=False))
        buttons.insert(2, UIButton(pygame.Rect(0, 0, 64, 64), '', self.ui_manager, container=container, object_id='#mating_history_plus_button'))
        buttons.insert(5, UIButton(pygame.Rect(0, 0, 64, 64), '', self.ui_manager, container=container, object_id='#mating_history_right_arrow_button'))
        return buttons