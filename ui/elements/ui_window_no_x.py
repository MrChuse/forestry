from pygame_gui.elements import UIWindow


class UIWindowNoX(UIWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enable_close_button = False
        self.title_bar_close_button_width = 0
        self.rebuild()