import pygame

from .ui_button_slot import UIButtonSlot


class Cursor(UIButtonSlot):
    def __init__(self, slot, *args, **kwargs):
        super().__init__(slot, *args, **kwargs)

    def process_event(self, event: pygame.event.Event) -> bool:
        return False

    def update(self, time_delta: float):
        pos = pygame.mouse.get_pos()
        self.relative_rect.topleft = pos
        self.rect.topleft = pos

        self.text_box.rect.size = 30, 30
        self.text_box.rect.bottomright = self.rect.bottomright
        if self.inspected_status is not None:
            self.inspected_status.rect.topright = self.rect.topright

        if self.slot.is_empty():
            self.hide()
        else:
            self.show()
        return super().update(time_delta)

    def process_cursor_slot_interaction(self, event, slot):
        if event.mouse_button == pygame.BUTTON_LEFT:
            if self.slot.slot == slot.slot:
                slot.put(*self.slot.take_all()) # stack
            else:
                self.slot.swap(slot) # swap
        elif event.mouse_button == pygame.BUTTON_RIGHT:
            if self.slot.is_empty():
                bee, amt = slot.take_all() # take half
                amt2 = amt//2
                self.slot.put(bee, amt-amt2)
                slot.put(bee, amt2)
            else:
                slot.put(self.slot.slot) # put one
                self.slot.take()
