from typing import Dict, List, Optional, Union

import pygame
import pygame_gui
from pygame_gui.core import ObjectID, UIElement
from pygame_gui.elements import UIButton, UILabel, UIPanel

from config import UI_MESSAGE_SIZE, dominant, genes_enums, local
from forestry import Bee, dom_local

from ..custom_events import TUTORIAL_STAGE_CHANGED
from ..elements import UILocationFindingMessageWindow
from .tutorial_stage import CurrentTutorialStage, TutorialStage


def colorize(text, color):
    return f'<font color={color}>{text}</font>'

class BeeStats(UIPanel):
    def __init__(self, bee: Bee, relative_rect: pygame.Rect, manager=None, wrap_to_height: bool = False, layer_starting_height: int = 1, container = None, parent_element = None, object_id: Union[ObjectID, str, None] = None, anchors: Dict[str, str] = None, visible: int = 1, resizable=False):
        self.bee = bee
        self.resizable = resizable
        self.table_contents : Optional[List[List[UIElement]]] = None
        self.original_rect = relative_rect
        self.buttons = []
        super().__init__(relative_rect, layer_starting_height, manager, container=container, parent_element=parent_element, object_id=object_id, anchors=anchors, visible=visible)
        self.rebuild()

    def rebuild(self):
        super().rebuild()

        if self.table_contents is not None:
            for row in self.table_contents:
                for element in row:
                    element.kill()

        if self.bee is None:
            if hasattr(self, 'panel_container'):
                self.set_dimensions(self.original_rect.size)
            return
        if not hasattr(self, 'panel_container'):
            # has not __init__ed yet, skipping
            return

        def create_uilabel(text='', is_local=False, object_id=None, visible=True):
            return UILabel(pygame.Rect(0,0,-1,-1), local[text] if is_local else text, container=self, object_id=ObjectID('@SmallFont', object_id), visible=visible)
        def create_button(gene_name='', text='?', is_local=False, object_id=None, visible=True):
            b = UIButton(pygame.Rect(0,0,-1,-1), local[text] if is_local else text, container=self, object_id=ObjectID('@SmallFont', object_id), visible=visible)
            b._gene_name = gene_name
            self.buttons.append(b)
            return b
        self.table_contents = []
        if not self.bee.inspected:
            self.table_contents.append([create_uilabel(self.bee.small_str())])
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

        top_margin = 2
        heights = [max(map(lambda x: x.get_abs_rect().height, row)) + top_margin for row in self.table_contents]
        left_margin = 2
        transposed = zip(*self.table_contents)
        widths = [max(map(lambda x: x.get_abs_rect().width, row)) + left_margin for row in transposed]
        # print(len(widths), len(heights))
        # for row_n in range(len(res)):
        #     for el_n in range(len(res[row_n])):
        #         print(f'({widths[el_n]:4} {heights[row_n]:4})', end=' ')
        #     print()
        # print()

        for row_n in range(len(self.table_contents)):
            for el_n in range(len(self.table_contents[row_n])):
                center_x = sum(widths[:el_n]) + widths[el_n]/2 + left_margin * (el_n + 1)
                center_y = sum(heights[:row_n]) + heights[row_n]/2 + top_margin * (row_n + 1)
                element = self.table_contents[row_n][el_n]
                rel_rect = element.get_relative_rect()
                rel_rect.center = center_x, center_y
                element.set_relative_position(rel_rect.topleft)

        if self.resizable:
            new_dimensions = (sum(widths) + left_margin * (len(self.table_contents[0]) + 1) + (self.container_margins['left'] + self.container_margins['right']),
                            sum(heights) + top_margin * (len(self.table_contents) + 1) + (self.container_margins['top'] + self.container_margins['bottom']))

            self.set_dimensions(new_dimensions)

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
