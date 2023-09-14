from typing import Dict, List, Optional, Union

import pygame
import pygame_gui
from pygame_gui.core import ObjectID, UIElement
from pygame_gui.core.interfaces import (IContainerLikeInterface,
                                        IUIManagerInterface)
from pygame_gui.elements import UIButton, UILabel, UIPanel

from config import UI_MESSAGE_SIZE, dominant, genes_enums, local
from forestry import Bee, Princess, Queen, dom_local

from ..custom_events import TUTORIAL_STAGE_CHANGED
from ..elements import UILocationFindingMessageWindow, UITable
from .tutorial_stage import CurrentTutorialStage, TutorialStage


def colorize(text, color):
    return f'<font color={color}>{text}</font>'

class BeeStats(UITable):
    def __init__(self, bee: Bee, relative_rect: pygame.Rect, starting_layer_height: int = 1, manager: Optional[IUIManagerInterface] = None, *, element_id: str = 'panel', margins: Optional[Dict[str, int]]  = None, container: Optional[IContainerLikeInterface]  = None, parent_element: Optional[UIElement]  = None, object_id: Union[ObjectID, str, None]  = None, anchors: Optional[Dict[str, Union[str, UIElement]]]  = None, visible: int = 1, resizable: bool = False):
        self.bee = bee
        self.resizable = resizable
        self.table_contents : Optional[List[List[UIElement]]] = None
        self.original_rect = relative_rect
        self.buttons = []
        super().__init__(relative_rect, starting_layer_height, manager, element_id=element_id, margins=margins, container=container, parent_element=parent_element, object_id=object_id, anchors=anchors, visible=visible, resizable=resizable)
        self.rebuild()

    def populate_table_contents(self):
        super().populate_table_contents()

        if self.bee is None:
            return # set table contents to []

        def create_uilabel(text='', is_local=False, object_id=None, visible=True, set_32=False):
            label = UILabel(pygame.Rect(0,0,-1,-1), local[text] if is_local else text, container=self, object_id=ObjectID('@SmallFont', object_id), visible=visible)
            if set_32:
                rect = label.get_abs_rect()
                label.set_dimensions((rect.width + 32, rect.height)) # 32 is the inspect_button_height
            return label
        def create_button(gene_name='', text='?', is_local=False, object_id=None, visible=True):
            b = UIButton(pygame.Rect(0,0,-1,-1), local[text] if is_local else text, container=self, object_id=ObjectID('@SmallFont', object_id), visible=visible)
            b._gene_name = gene_name
            self.buttons.append(b)
            return b

        if not self.bee.inspected:
            self.table_contents.append([create_uilabel(self.bee.small_str(), set_32=True)])
            # if isinstance(self.bee, (Queen, Princess)):
            #     self.table_contents.append([create_uilabel(f'{local["generations"]}: {self.bee.generation}', False)])
        else:
            name, bee_species_index = local[self.bee.type_str]
            self.table_contents.append([create_uilabel(name), create_uilabel(visible=False), create_button('active_allele'), create_button('inactive_allele')])
            self.table_contents.append([create_uilabel('trait', True), create_button('dominance'), create_uilabel('active', True), create_uilabel('inactive', True)])
            genes = self.bee.genes.asdict()
            for key in genes:
                try:
                    allele0 = local[genes[key][0]][bee_species_index]
                    allele1 = local[genes[key][1]][bee_species_index]
                except IndexError:
                    allele0 = local[genes[key][0]][0] # TODO: remove [0]
                    allele1 = local[genes[key][1]][0]
                dom0 = dominant[genes[key][0]]
                dom1 = dominant[genes[key][1]]
                self.table_contents.append([create_uilabel(key, True),
                                            create_button(key),
                                            create_uilabel(dom_local(allele0, dom0), False, '@Dominant' if dom0 else '@Recessive'),
                                            create_uilabel(dom_local(allele1, dom1), False, '@Dominant' if dom1 else '@Recessive')])
            # if isinstance(self.bee, (Queen, Princess)): # TODO: think about merging cells in UITable
            #     self.table_contents.append([create_uilabel(f'{local["generations"]}: {self.bee.generation}', False), create_uilabel('', visible=False), create_uilabel('', visible=False), create_uilabel('', visible=False)])

    def open_gene_helper(self, gene):
        if CurrentTutorialStage.current_tutorial_stage == TutorialStage.INSPECT_AVAILABLE:
            CurrentTutorialStage.current_tutorial_stage = TutorialStage.GENE_HELPER_TEXT_CLICKED
            pygame.event.post(pygame.event.Event(TUTORIAL_STAGE_CHANGED, {}))

        text = local[gene+'_helper_text']
        enum_name = {'fertility': 'BeeFertility', 'lifespan': 'BeeLifespan', 'speed': 'BeeSpeed'}.get(gene)
        if enum_name is not None:
            alleles = genes_enums[enum_name]
            text += f'\n\n{local["gene_can_be_alleles"]}'
            for allele in alleles:
                text += f'\n{colorize(local[allele][0], "#ec3661" if dominant[allele] else "#3687ec")}: {allele.value}'
        return UILocationFindingMessageWindow(pygame.Rect(self.ui_manager.get_mouse_position(), UI_MESSAGE_SIZE), text, self.ui_manager)

    def process_event(self, event: pygame.event.Event) -> bool:
        consumed = super().process_event(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if self.table_contents is None:
                return
            for button in self.buttons:
                if event.ui_element == button:
                    try:
                        self.open_gene_helper(button._gene_name)
                        consumed = True
                    except KeyError:
                        pass
        return consumed
