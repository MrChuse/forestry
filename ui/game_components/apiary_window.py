import math

import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UIStatusBar, UIWindow

from config import local
from forestry import Apiary, Drone, Queen, SlotOccupiedError

from .cursor import Cursor
from .ui_button_slot import UIButtonSlot


class ApiaryWindow(UIWindow):
    def __init__(self, game, apiary: Apiary, cursor: Cursor, relative_rect: pygame.Rect, manager, *args, **kwargs):
        self.game = game
        self.apiary = apiary
        self.cursor = cursor
        self.size = relative_rect.size
        super().__init__(relative_rect, manager, local['Apiary'] + ' ' + apiary.name, *args, **kwargs)

        self.button_size = (64, 64)
        self.top_margin2 = 15
        self.side_margin2 = 63
        self.princess_button = UIButtonSlot(self.apiary.princess, pygame.Rect((self.side_margin2, self.top_margin2), self.button_size),
            '', manager, self)
        self.princess_button.empty_object_id = '#PrincessEmpty'
        drone_rect = pygame.Rect((self.size[0] - self.button_size[0] - self.side_margin2 - 32, self.top_margin2), self.button_size)
        self.drone_button = UIButtonSlot(self.apiary.drone, drone_rect,
                                     text='', manager=manager,
                                     container=self)
        self.drone_button.empty_object_id = '#DroneEmpty'

        queen_health_rect = pygame.Rect(0, self.princess_button.relative_rect.bottom + 14, self.size[0] - self.side_margin2 * 2, 10)
        queen_health_rect.centerx = self.size[0] / 2 - 16
        self.queen_health = UIStatusBar(queen_health_rect, manager, container=self)
        self.queen_health.percent_full = 0

        self.problem = 'NO_QUEEN'
        self.problems_indicator = None
        self.create_problems_indicator()

        self.margin3 = (self.size[0] - 32 - 3 * self.button_size[0]) / 4
        radius = self.margin3 + self.button_size[0]
        center_rect = pygame.Rect((0, 0), self.button_size)
        center_rect.center = (self.size[0]/2 - 32/2, self.size[1]/2 + 15) # 30
        self.buttons = [UIButtonSlot(self.apiary.inv[0], center_rect, '', manager, self)]
        for i in range(6):
            angle = 2 * math.pi / 6 * i
            dx = radius * math.cos(angle)
            dy = radius * math.sin(angle)

            rect = center_rect.copy()
            rect.x += dx
            rect.y += dy
            self.buttons.append(UIButtonSlot(self.apiary.inv[i+1], rect, '', manager, self))
        take_all_button_rect = pygame.Rect(0, 0, self.size[0] - self.side_margin2 * 2, 30)
        take_all_button_rect.centerx = rect.centerx - 40 # no clue why 40
        self.take_all_button = UIButton(take_all_button_rect, local['Take'], manager, self,
            anchors={
                'left': 'left',
                'right': 'right',
                'top': 'top',
                'bottom': 'bottom',
                'top_target': self.buttons[3]
            })

    def create_problems_indicator(self, problem='NO_QUEEN'):
        if self.problems_indicator is not None:
            self.problems_indicator.kill()

        self.problems_indicator = UIButton(pygame.Rect(6, -23, 36, 36), '', self.ui_manager, container=self, tool_tip_text=local['Apiary_problem_'+problem],object_id='#Apiary_problem_'+problem,
            anchors={
                'left': 'left',
                'right': 'left',
                'top': 'top',
                'bottom': 'top',
                'left_target': self.queen_health,
                'top_target': self.queen_health
            }, generate_click_events_from=[])

    def update_problems_indicator(self):
        problem = self.apiary.get_problem().name
        if problem != self.problem:
            self.problem = problem
            self.create_problems_indicator(problem)

    def update_health_bar(self):
        bee = self.apiary.princess.slot
        if isinstance(bee, Queen):
            self.queen_health.percent_full = bee.remaining_lifespan / bee.lifespan
        else:
            self.queen_health.percent_full = 0

    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_h:
                for b in self.buttons:
                    b.hide()
            if event.key == pygame.K_g:
                for b in self.buttons:
                    b.show()
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.take_all_button:
                r = []
                for b in self.buttons:
                    if not b.slot.is_empty():
                        r.append(b.slot)
                self.game.most_recent_inventory.place_bees(r)
            elif event.ui_element == self.princess_button:
                if self.cursor.slot.is_empty():
                    self.cursor.slot.put(*self.apiary.take_princess()) # just take it from apiary
                else:
                    # cursor not empty
                    if self.apiary.princess.is_empty():
                        bee = self.cursor.slot.take()
                        try:
                            self.apiary.put_princess(bee)
                        except TypeError as e:
                            self.cursor.slot.put(bee)
                            raise e
                    else:
                        if self.cursor.slot.amount > 1:
                            raise ValueError("Can't put more than 1 princess into apiary")
                        bee1 = self.apiary.take_princess()
                        bee2 = self.cursor.slot.take_all()
                        try:
                            self.apiary.put_princess(*bee2)
                        except TypeError as e:
                            self.cursor.slot.put(*bee2)
                            self.apiary.put_princess(*bee1)
                            raise e
                        self.cursor.slot.put(*bee1)
            elif event.ui_element == self.drone_button:
                if isinstance(self.cursor.slot.slot, (Drone, type(None))):
                    self.cursor.process_cursor_slot_interaction(event, self.drone_button.slot)
                    self.apiary.try_breed()
                else:
                    raise ValueError('Bee should be a Drone')
            for index, b in enumerate(self.buttons):
                if event.ui_element == b:
                    mods = pygame.key.get_mods()
                    if mods & pygame.KMOD_LSHIFT:
                        bee, amt = self.apiary.take(index)
                        self.game.most_recent_inventory.place_bees([bee]*amt)
                    elif mods & pygame.KMOD_LCTRL:
                        if self.apiary.inv[index].is_empty():
                            break

                        bee, amt = self.apiary.take(index)
                        try:
                            self.apiary.put(bee, amt)
                        except SlotOccupiedError:
                            self.apiary.inv[index].put(bee, amt)
                    else:
                        self.cursor.process_cursor_slot_interaction(event, b.slot)
        return super().process_event(event)

    def update(self, time_delta):
        self.update_health_bar()
        self.update_problems_indicator()
        super().update(time_delta)
