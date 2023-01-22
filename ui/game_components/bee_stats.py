from typing import Dict, Union

import pygame
import pygame_gui
from pygame_gui.core import ObjectID
from pygame_gui.elements import UITextBox
from pygame_gui.windows import UIMessageWindow

from config import dominant, local
from forestry import Bee, dom_local

from ..custom_events import TUTORIAL_STAGE_CHANGED
from .tutorial_stage import TutorialStage, CurrentTutorialStage


class BeeStats(UITextBox):
    def __init__(self, bee: Bee, relative_rect: pygame.Rect, manager, wrap_to_height: bool = False, layer_starting_height: int = 1, container = None, parent_element = None, object_id: Union[ObjectID, str, None] = None, anchors: Dict[str, str] = None, visible: int = 1):
        self.bee = bee
        super().__init__('', relative_rect, manager, wrap_to_height, layer_starting_height, container, parent_element, object_id, anchors, visible)
        self.process_inspect()

    def process_inspect(self):
        if self.bee is None:
            self.set_text('')
            return
        res = []
        if not self.bee.inspected:
            res.append(self.bee.small_str())
        else:
            name, bee_species_index = local[self.bee.type_str]
            res.append(name)
            genes = self.bee.genes.asdict()
            res.append(local['trait'])
            for key in genes:
                try:
                    allele0 = local[genes[key][0]][bee_species_index]
                    allele1 = local[genes[key][1]][bee_species_index]
                except IndexError:
                    allele0 = local[genes[key][0]][0] # TODO: remove [0]
                    allele1 = local[genes[key][1]][0]
                dom0 = dominant[genes[key][0]]
                dom1 = dominant[genes[key][1]]
                res.append(f'  {local[key]} <a href=\'{key}\'>(?)</a>: <font color={"#ec3661" if dominant[genes[key][0]] else "#3687ec"}>{dom_local(allele0, dom0)}</font>, <font color={"#ec3661" if dominant[genes[key][1]] else "#3687ec"}>{dom_local(allele1, dom1)}</font>')
        self.set_text('<br>'.join(res))

    def open_gene_helper(self, gene):
        if CurrentTutorialStage.current_tutorial_stage == TutorialStage.INSPECT_AVAILABLE:
            CurrentTutorialStage.current_tutorial_stage = TutorialStage.GENE_HELPER_TEXT_CLICKED
            pygame.event.post(pygame.event.Event(TUTORIAL_STAGE_CHANGED, {}))
        return UIMessageWindow(pygame.Rect(self.ui_manager.get_mouse_position(), (260, 200)),
                               local[gene+'_helper_text'], self.ui_manager)

    def process_event(self, event: pygame.event.Event) -> bool:
        consumed = super().process_event(event)
        if event.type == pygame_gui.UI_TEXT_BOX_LINK_CLICKED:
            if event.ui_element == self:
                try:
                    self.open_gene_helper(event.link_target)
                    consumed = True
                except KeyError:
                    pass
        return consumed
