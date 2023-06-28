from typing import List

import pygame
import pygame_gui
from pygame_gui.elements import (UIButton, UILabel, UIPanel, UIStatusBar,
                                 UITextBox, UIWindow)

from config import (BeeFertility, BeeLifespan, BeeSpeed, dominant, local,
                    mendel_text)
from forestry import Bee, BeeSpecies, Drone, Genes, MatingEntry, Princess, Slot
from ui.elements.ui_grid_window import UIGridPanel
from ui.elements.ui_table import UITable
from ui.game_components.bee_stats import BeeStats, colorize
from ui.game_components.mating_entry_panel import MatingEntryPanel
from ui.game_components.ui_button_slot import UIButtonSlot


class BeeHighlight(UITable):
    def __init__(self, bee: Bee, relative_rect: pygame.Rect, starting_layer_height: int = 1, manager = None, *, element_id: str = 'panel', margins = None, container = None, parent_element = None, object_id = None, anchors = None, visible: int = 1):
        relative_rect.size = 134, 66
        self.bee = bee
        super().__init__(relative_rect, starting_layer_height, manager, element_id=element_id, margins=margins, container=container, parent_element=parent_element, object_id=object_id, anchors=anchors, visible=visible, resizable=True)

    def populate_table_contents(self):
        super().populate_table_contents()
        self.table_contents.append([
            UIButtonSlot(
                Slot(Drone(Genes((self.bee.genes.species[0], self.bee.genes.species[0])), self.bee.inspected), 1),
                pygame.Rect(0, 0, 64, 64),
                '',
                self.ui_manager,
                self,
                is_inspectable=False,
                allow_popup=False),
            UIButtonSlot(
                Slot(Drone(Genes((self.bee.genes.species[1], self.bee.genes.species[1])), self.bee.inspected), 1),
                pygame.Rect(64, 0, 64, 64),
                '',
                self.ui_manager,
                self,
                is_inspectable=False,
                allow_popup=False)
        ])

class NamedBeeHighlight(UITable):
    def __init__(self, name: str, bee: Bee, relative_rect: pygame.Rect, starting_layer_height: int = 1, manager = None, *, element_id: str = 'panel', margins = None, container = None, parent_element = None, object_id = None, anchors = None, visible: int = 1):
        relative_rect.size = 134, 66
        self.bee = bee
        self.name = name
        super().__init__(relative_rect, starting_layer_height, manager, element_id=element_id, margins=margins, container=container, parent_element=parent_element, object_id=object_id, anchors=anchors, visible=visible, resizable=True)

    def populate_table_contents(self):
        super().populate_table_contents()
        self.table_contents.append([UITextBox(self.name, pygame.Rect(0, 0, 128, 44), object_id='@Centered', container=self)])
        self.table_contents.append([BeeHighlight(self.bee, pygame.Rect(0, 0, 0, 0), container=self)])


class MendelTutorialWindow(UIWindow):
    def __init__(self, rect: pygame.Rect, manager):
        super().__init__(rect, manager, local['Mendelian Inheritance'], resizable=True)
        self.set_minimum_dimensions((700, 500))
        self.interactive_panel_height = self.get_container().get_rect().height//2
        self.arrow_buttons_height = 40
        size = self.get_container().get_size()
        self.text_boxes : List[UITextBox] = []
        for text in mendel_text:
            text_box = UITextBox(text, pygame.Rect((0,0), (size[0], size[1] - self.interactive_panel_height - self.arrow_buttons_height)), self.ui_manager, container=self,
                anchors={
                    'top': 'top',
                    'bottom': 'bottom',
                    'left': 'left',
                    'right': 'right'
                })
            text_box.time_until_full_rebuild_after_changing_size = 0.001
            self.text_boxes.append(text_box)

        self.panels = {}
        self._fill_panels()
        self.left_arrow_button = UIButton(pygame.Rect(0, -self.arrow_buttons_height, self.arrow_buttons_height, self.arrow_buttons_height), '<', self.ui_manager, self,
            anchors={
                'left': 'left',
                'right': 'left',
                'top': 'bottom',
                'bottom': 'bottom'
            })
        self.right_arrow_button = UIButton(pygame.Rect(-self.arrow_buttons_height, -self.arrow_buttons_height, self.arrow_buttons_height, self.arrow_buttons_height), '>', self.ui_manager, self,
            anchors={
                'left': 'right',
                'right': 'right',
                'top': 'bottom',
                'bottom': 'bottom'
            })
        progress_bar_rect = pygame.Rect(0, -self.arrow_buttons_height, 300, self.arrow_buttons_height)
        progress_bar_rect.centerx = self.get_container().get_rect().width//2
        self.progress_bar = UIStatusBar(progress_bar_rect, self.ui_manager, container=self, object_id='#MendelianTutorialProgressBar',
            anchors={
                'left': 'left',
                'right': 'left',
                'top': 'bottom',
                'bottom': 'bottom'
            })
        self.current_page = 0
        self.progress_bar.status_text = lambda : f'{self.current_page+1} / {len(self.text_boxes)}'
        self.progress_bar.redraw()
        self.show_current_page()

    def setup_phenotype_genotype(self, panel_num):
        panel = self.panels[panel_num]
        size = panel.get_abs_rect().size
        table = UITable(pygame.Rect(0, 0, size[0], size[1]), kill_on_repopulation=False, container=self, anchors=panel.anchors)
        table.table_contents.append([
            UILabel(pygame.Rect(0, 0, 120, 30), local['Phenotype'], container=table, object_id='@Centered'),
            UILabel(pygame.Rect(0, 0, 148, 30), local['Genotype'], container=table, object_id='@Centered'),
            UILabel(pygame.Rect(0, 0, 148, 30), local['Allele'], container=table, object_id='@Centered'),
            UILabel(pygame.Rect(0, 0, 148, 30), local['Purebred'], container=table, object_id='@Centered')
        ])
        bee = Drone(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST),
                          (BeeFertility.TWO, BeeFertility.THREE),
                          (BeeLifespan.SHORT, BeeLifespan.SHORTER),
                          (BeeSpeed.SLOW, BeeSpeed.SLOWEST)), True)
        pure_bee = Drone(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST),
                               (BeeFertility.TWO, BeeFertility.TWO),
                               (BeeLifespan.SHORT, BeeLifespan.SHORT),
                               (BeeSpeed.SLOW, BeeSpeed.SLOW)), True)
        text = []
        for allele in BeeSpeed:
            text.append(f'{colorize(local[allele][0], "#ec3661" if dominant[allele] else "#3687ec")}: {allele.value}')
        text = '\n'.join(text)
        table.table_contents.append([
            UIButtonSlot(
                Slot(bee, 1),
                pygame.Rect(0, 0, 64, 64),
                '',
                self.ui_manager,
                table,
                is_inspectable=False,
                allow_popup=False),
            BeeStats(bee, pygame.Rect(0, 0, 1, 1), container=table, resizable=True),
            UITextBox(text, pygame.Rect(0, 0, 250, 218), container=table),
            BeeStats(pure_bee, pygame.Rect(0, 0, 1, 1), container=table, resizable=True),
        ])
        table.rebuild()
        panel.kill()
        self.panels[panel_num] = table

    def setup_bee_highlights(self, panel_num):
        panel = self.panels[panel_num]
        def create_beehighlight(name, species, container, inspected=False):
            return NamedBeeHighlight(name, Drone(Genes(species), inspected), pygame.Rect(0,0,0,0), 1, self.ui_manager, container=container)
        def create_highlights(container):
            return [
                create_beehighlight('<font color=#ec3661>AA</font>', (BeeSpecies.FOREST, BeeSpecies.FOREST), container),
                create_beehighlight('<font color=#ec3661>BB</font>', (BeeSpecies.MEADOWS, BeeSpecies.MEADOWS), container),
                create_beehighlight('<font color=#3687ec>cc</font>', (BeeSpecies.NOBLE, BeeSpecies.NOBLE), container),
                create_beehighlight('<font color=#3687ec>dd</font>', (BeeSpecies.DILIGENT, BeeSpecies.DILIGENT), container),
                create_beehighlight('<font color=#ec3661>AB</font>', (BeeSpecies.FOREST, BeeSpecies.MEADOWS), container),
                create_beehighlight('<font color=#ec3661>BA</font>', (BeeSpecies.MEADOWS, BeeSpecies.FOREST), container),
                create_beehighlight('<font color=#3687ec>cd</font>', (BeeSpecies.NOBLE, BeeSpecies.DILIGENT), container),
                create_beehighlight('<font color=#3687ec>dc</font>', (BeeSpecies.DILIGENT, BeeSpecies.NOBLE), container),
            ]
        self.panels[panel_num].kill()
        self.panels[panel_num] = UIGridPanel(panel.relative_rect, panel.starting_height, self.ui_manager, container=self, subelements_function=create_highlights,
            anchors={
                'left': 'left',
                'right': 'right',
                'top': 'top',
                'bottom': 'bottom',
                'top_target': self.text_boxes[panel_num]
            })

    # 3
    def setup_dominance_and_uniformity(self, panel_num):
        panel = self.panels[panel_num]
        # set up 6 mating entries:
        mating_entries = []
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST))),
                Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.MEADOWS))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST))),
                Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.MEADOWS))),
                Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.FOREST))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.NOBLE, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.DILIGENT, BeeSpecies.DILIGENT))),
                Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.DILIGENT))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.NOBLE, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.DILIGENT, BeeSpecies.DILIGENT))),
                Drone(Genes((BeeSpecies.DILIGENT, BeeSpecies.NOBLE))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST))),
                Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST))),
                Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                force_inspect=True
            )
        )

        # create UIGridPanel
        def subelements_function(container):
            return [MatingEntryPanel(1, entry, pygame.Rect(0,0,0,0), 1, self.ui_manager, container=container) for i, entry in enumerate(mating_entries)]

        width = 524
        height = 73 * len(mating_entries)
        if height > panel.get_container().get_rect().height:
            width += 18
            height = panel.get_container().get_rect().height
        relative_rect = pygame.Rect(0, 0, width, height)
        relative_rect.center = panel.get_container().get_rect().width//2, panel.get_container().get_rect().height//2
        UIGridPanel(relative_rect, 20, self.ui_manager, container=panel, subelements_function=subelements_function)

    # 4
    def setup_segregation(self, panel_num):
        panel = self.panels[panel_num]
        # set up 6 mating entries:
        mating_entries = []
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS))),
                Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.FOREST))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS))),
                Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.MEADOWS))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.NOBLE))),
                force_inspect=True
            )
        )


        # create UIGridPanel
        def subelements_function(container):
            return [MatingEntryPanel(1, entry, pygame.Rect(0,0,0,0), 1, self.ui_manager, container=container) for i, entry in enumerate(mating_entries)]

        width = 524
        height = 73 * len(mating_entries)
        if height > panel.get_container().get_rect().height:
            width += 18
            height = panel.get_container().get_rect().height
        relative_rect = pygame.Rect(0, 0, width, height)
        relative_rect.center = panel.get_container().get_rect().width//2, panel.get_container().get_rect().height//2
        UIGridPanel(relative_rect, 20, self.ui_manager, container=panel, subelements_function=subelements_function)

    # 5
    def setup_purebred_and_F1(self, panel_num):
        panel = self.panels[panel_num]
        # set up 6 mating entries:
        mating_entries = []
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.NOBLE))),
                force_inspect=True
            )
        )
        # create UIGridPanel
        def subelements_function(container):
            return [MatingEntryPanel(1, entry, pygame.Rect(0,0,0,0), 1, self.ui_manager, container=container) for i, entry in enumerate(mating_entries)]

        width = 524
        height = 73 * len(mating_entries)
        if height > panel.get_container().get_rect().height:
            width += 18
            height = panel.get_container().get_rect().height
        relative_rect = pygame.Rect(0, 0, width, height)
        relative_rect.center = panel.get_container().get_rect().width//2, panel.get_container().get_rect().height//2
        UIGridPanel(relative_rect, 20, self.ui_manager, container=panel, subelements_function=subelements_function)

    # 6
    def setup_radically_different_1(self, panel_num):
        panel = self.panels[panel_num]
        # set up 6 mating entries:
        mating_entries = []
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS))),
                Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.DILIGENT))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS))),
                Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.DILIGENT))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.DILIGENT))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS))),
                Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.DILIGENT))),
                Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.NOBLE))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS))),
                Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.DILIGENT))),
                Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.DILIGENT))),
                force_inspect=True
            )
        )
        # create UIGridPanel
        def subelements_function(container):
            return [MatingEntryPanel(1, entry, pygame.Rect(0,0,0,0), 1, self.ui_manager, container=container) for i, entry in enumerate(mating_entries)]

        width = 524
        height = 73 * len(mating_entries)
        if height > panel.get_container().get_rect().height:
            width += 18
            height = panel.get_container().get_rect().height
        relative_rect = pygame.Rect(0, 0, width, height)
        relative_rect.center = panel.get_container().get_rect().width//2, panel.get_container().get_rect().height//2
        UIGridPanel(relative_rect, 20, self.ui_manager, container=panel, subelements_function=subelements_function)

    # 7
    def setup_radically_different_2(self, panel_num):
        panel = self.panels[panel_num]
        # set up 6 mating entries:
        mating_entries = []
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.DILIGENT))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.DILIGENT))),
                Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.FOREST))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.DILIGENT))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.DILIGENT))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.DILIGENT))),
                Drone(Genes((BeeSpecies.FOREST, BeeSpecies.DILIGENT))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.DILIGENT))),
                Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.NOBLE))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.DILIGENT))),
                Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.NOBLE))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.DILIGENT))),
                Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.DILIGENT))),
                force_inspect=True
            )
        )
        mating_entries.append(MatingEntry.from_bees(
                Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE))),
                Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.DILIGENT))),
                Drone(Genes((BeeSpecies.DILIGENT, BeeSpecies.NOBLE))),
                force_inspect=True
            )
        )
        # create UIGridPanel
        def subelements_function(container):
            return [MatingEntryPanel(1, entry, pygame.Rect(0,0,0,0), 1, self.ui_manager, container=container) for i, entry in enumerate(mating_entries)]

        width = 524
        height = 73 * len(mating_entries)
        if height > panel.get_container().get_rect().height:
            width += 18
            height = panel.get_container().get_rect().height
        relative_rect = pygame.Rect(0, 0, width, height)
        relative_rect.center = panel.get_container().get_rect().width//2, panel.get_container().get_rect().height//2
        UIGridPanel(relative_rect, 20, self.ui_manager, container=panel, subelements_function=subelements_function)

    def _fill_panels(self):
        # 0
        # 1

        # 2
        def auto_counter(initial_value=None):
            if initial_value:
                auto_counter.value = initial_value
            if not hasattr(auto_counter, 'value'):
                raise RuntimeError('auto_counter was not called with initial value yet')
            ret = auto_counter.value
            auto_counter.value += 1
            return ret

        self.panel_functions = {}
        self.panel_functions[1] = self.setup_phenotype_genotype
        self.panel_functions[3] = self.setup_bee_highlights
        self.panel_functions[auto_counter(5)] = self.setup_dominance_and_uniformity
        self.panel_functions[auto_counter()] = self.setup_segregation
        self.panel_functions[auto_counter()] = self.setup_purebred_and_F1
        self.panel_functions[auto_counter()] = self.setup_radically_different_1
        self.panel_functions[auto_counter()] = self.setup_radically_different_2

    def add_page(self, amount: int):
        self.current_page += amount
        self.current_page = min(self.current_page, len(mendel_text)-1)
        self.current_page = max(self.current_page, 0) # clamp
        self.show_current_page()

    def set_page(self, page: int):
        self.current_page = page
        self.show_current_page()

    def show_current_page(self):
        for text_box in self.text_boxes:
            text_box.hide()
        for panel in self.panels.values():
            panel.hide()
        self.text_boxes[self.current_page].show()
        if self.panels.get(self.current_page) is None:
            size = self.get_container().get_size()
            self.panels[self.current_page] = UIPanel(pygame.Rect((0,0), (size[0], self.interactive_panel_height)), manager=self.ui_manager, container=self,
                anchors={
                    'left': 'left',
                    'right': 'right',
                    'top': 'top',
                    'bottom': 'bottom',
                    'top_target': text_box
                })

            func = self.panel_functions.get(self.current_page)
            if func is not None:
                func(self.current_page)
        self.panels[self.current_page].show()

    def process_event(self, event: pygame.event.Event) -> bool:
        consumed = super().process_event(event)
        if event.type == pygame_gui. UI_BUTTON_PRESSED:
            if event.ui_element == self.left_arrow_button:
                self.add_page(-1)
                self.progress_bar.percent_full = self.current_page / (len(self.text_boxes)-1)
            elif event.ui_element == self.right_arrow_button:
                self.add_page(1)
                self.progress_bar.percent_full = self.current_page / (len(self.text_boxes)-1)
        return consumed
