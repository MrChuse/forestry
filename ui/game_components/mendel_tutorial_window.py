from typing import List

import pygame
import pygame_gui
from pygame_gui.elements import (UIButton, UIPanel, UIStatusBar, UITextBox,
                                 UIWindow)

from config import local, mendel_text
from forestry import Bee, BeeSpecies, Drone, Genes, MatingEntry, Princess, Slot
from ui.elements.ui_grid_window import UIGridPanel
from ui.game_components.mating_entry_panel import MatingEntryPanel
from ui.game_components.ui_button_slot import UIButtonSlot


class MendelTutorialWindow(UIWindow):
    def __init__(self, rect: pygame.Rect, manager):
        super().__init__(rect, manager, local['Mendelian Inheritance'])
        self.set_minimum_dimensions((700, 500))
        self.interactive_panel_height = self.get_container().get_rect().height//2
        self.arrow_buttons_height = 40
        size = self.get_container().get_size()
        self.text_boxes : List[UITextBox] = []
        for text in mendel_text:
            text_box = UITextBox(text, pygame.Rect((0,0), (size[0], size[1] - self.interactive_panel_height - self.arrow_buttons_height)), self.ui_manager, container=self)
            self.text_boxes.append(text_box)

        self.panels = [UIPanel(pygame.Rect((0,0), (size[0], self.interactive_panel_height)), manager=self.ui_manager, container=self,
            anchors={
                'left': 'left',
                'right': 'right',
                'top': 'top',
                'bottom': 'bottom',
                'top_target': text_box
            }) for text_box in self.text_boxes]
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

    def _fill_panels(self):
        # 0
        # 1
        # 2

        # 3
        def setup_3():
            panel = self.panels[3]
            class BeeHighlight(UIPanel):
                def __init__(self, bee: Bee, relative_rect: pygame.Rect, starting_layer_height: int = 1, manager = None, *, element_id: str = 'panel', margins = None, container = None, parent_element = None, object_id = None, anchors = None, visible: int = 1):
                    relative_rect.size = 134, 134
                    super().__init__(relative_rect, starting_layer_height, manager, element_id=element_id, margins=margins, container=container, parent_element=parent_element, object_id=object_id, anchors=anchors, visible=visible)
                    UIButtonSlot(
                        Slot(Drone(Genes(bee.genes.species, None, None, None), bee.inspected), 1),
                        pygame.Rect(32, 0, 64, 64),
                        '',
                        self.ui_manager,
                        self,
                        is_inspectable=False)
                    UIButtonSlot(
                        Slot(Drone(Genes((bee.genes.species[0], bee.genes.species[0]), None, None, None), bee.inspected), 1),
                        pygame.Rect(0, 64, 64, 64),
                        '',
                        self.ui_manager,
                        self,
                        is_inspectable=False)
                    UIButtonSlot(
                        Slot(Drone(Genes((bee.genes.species[1], bee.genes.species[1]), None, None, None), bee.inspected), 1),
                        pygame.Rect(64, 64, 64, 64),
                        '',
                        self.ui_manager,
                        self,
                        is_inspectable=False)
            def create_beehighlight(species, container, inspected=False):
                return BeeHighlight(Drone(Genes(species, None, None, None), inspected), pygame.Rect(0,0,0,0), 1, self.ui_manager, container=container)
            def create_highlights(container):
                return [
                    create_beehighlight((BeeSpecies.FOREST, BeeSpecies.FOREST), container),
                    create_beehighlight((BeeSpecies.MEADOWS, BeeSpecies.MEADOWS), container),
                    create_beehighlight((BeeSpecies.NOBLE, BeeSpecies.NOBLE), container),
                    create_beehighlight((BeeSpecies.DILIGENT, BeeSpecies.DILIGENT), container),
                    create_beehighlight((BeeSpecies.FOREST, BeeSpecies.MEADOWS), container, True),
                    create_beehighlight((BeeSpecies.MEADOWS, BeeSpecies.FOREST), container, True),
                    create_beehighlight((BeeSpecies.NOBLE, BeeSpecies.DILIGENT), container, True),
                    create_beehighlight((BeeSpecies.DILIGENT, BeeSpecies.NOBLE), container, True),
                ]
            self.panels[3].kill()
            self.panels[3] = UIGridPanel(panel.relative_rect, panel.starting_height, self.ui_manager, container=self, subelements_function=create_highlights,
                anchors={
                    'left': 'left',
                    'right': 'right',
                    'top': 'top',
                    'bottom': 'bottom',
                    'top_target': self.text_boxes[3]
                })
        setup_3() # this is to hide code in the editor

        # 4
        def setup_4():
            panel = self.panels[4]
            # set up 6 mating entries:
            mating_entries = []
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST), None, None, None)),
                    Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.MEADOWS), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST), None, None, None)),
                    Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.MEADOWS), None, None, None)),
                    Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.FOREST), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST), None, None, None)),
                    Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST), None, None, None)),
                    Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.NOBLE, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.DILIGENT, BeeSpecies.DILIGENT), None, None, None)),
                    Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.DILIGENT), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.NOBLE, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.DILIGENT, BeeSpecies.DILIGENT), None, None, None)),
                    Drone(Genes((BeeSpecies.DILIGENT, BeeSpecies.NOBLE), None, None, None)),
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
        setup_4()

        # 5
        def setup_5():
            panel = self.panels[5]
            # set up 6 mating entries:
            mating_entries = []
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS), None, None, None)),
                    Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.FOREST), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS), None, None, None)),
                    Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.MEADOWS), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.NOBLE), None, None, None)),
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
        setup_5()

        # 6
        def setup_6():
            panel = self.panels[6]
            # set up 6 mating entries:
            mating_entries = []
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.FOREST), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.NOBLE), None, None, None)),
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
        setup_6()

        # 7
        def setup_7():
            panel = self.panels[7]
            # set up 6 mating entries:
            mating_entries = []
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS), None, None, None)),
                    Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.DILIGENT), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS), None, None, None)),
                    Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.DILIGENT), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.DILIGENT), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS), None, None, None)),
                    Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.DILIGENT), None, None, None)),
                    Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.NOBLE), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS), None, None, None)),
                    Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.DILIGENT), None, None, None)),
                    Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.DILIGENT), None, None, None)),
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
        setup_7()

        # 8
        def setup_8():
            panel = self.panels[8]
            # set up 6 mating entries:
            mating_entries = []
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.DILIGENT), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.MEADOWS), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.DILIGENT), None, None, None)),
                    Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.FOREST), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.DILIGENT), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.DILIGENT), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.DILIGENT), None, None, None)),
                    Drone(Genes((BeeSpecies.FOREST, BeeSpecies.DILIGENT), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.DILIGENT), None, None, None)),
                    Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.NOBLE), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.DILIGENT), None, None, None)),
                    Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.NOBLE), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.DILIGENT), None, None, None)),
                    Drone(Genes((BeeSpecies.NOBLE, BeeSpecies.DILIGENT), None, None, None)),
                    force_inspect=True
                )
            )
            mating_entries.append(MatingEntry.from_bees(
                    Princess(Genes((BeeSpecies.FOREST, BeeSpecies.NOBLE), None, None, None)),
                    Drone(Genes((BeeSpecies.MEADOWS, BeeSpecies.DILIGENT), None, None, None)),
                    Drone(Genes((BeeSpecies.DILIGENT, BeeSpecies.NOBLE), None, None, None)),
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
        setup_8()

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
        for panel in self.panels:
            panel.hide()
        self.text_boxes[self.current_page].show()
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
