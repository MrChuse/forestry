from traceback import print_exc

import pygame
import pygame_gui
from pygame import mixer

from config import load_settings
from forestry import NotEnoughResourcesError
from ui.custom_events import APPLY_VOLUME_CHANGE
# keep TutorialStage here because needed for backwards compatibility with pickle.load
from ui.game_components import GUI, TutorialStage

def main():
    game = None
    try:
        mixer.init()
        sounds = {
            'click_start': mixer.Sound('assets/ui-click-start.wav'),
            'click_end': mixer.Sound('assets/ui-click-end.wav')
        }
        pygame.init()

        pygame.display.set_caption('Bee Breeding Game')

        settings = load_settings()
        pygame.event.post(pygame.event.Event(APPLY_VOLUME_CHANGE, {'settings': settings}))


        if settings['fullscreen']:
            window_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            window_surface = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
        window_size = window_surface.get_rect().size

        background = pygame.Surface(window_size)
        background.fill(pygame.Color('#000000'))

        manager = pygame_gui.UIManager(window_size, 'theme.json', enable_live_theme_updates=False, starting_language=settings['language'])
        cursor_manager = pygame_gui.UIManager(window_size, 'theme.json', starting_language=settings['language'])

        game = GUI(window_size, manager, cursor_manager)

        # settings = SettingsWindow(pygame.Rect(100, 100, 300, 300), manager, resizable=True)
        clock = pygame.time.Clock()
        is_running = True
        visual_debug = False
        while is_running:
            time_delta = clock.tick(60)/1000.0
            # state = game.get_state()

            for event in pygame.event.get():
                if event.type == pygame_gui.UI_BUTTON_START_PRESS:
                    sounds['click_start'].play()
                elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                    sounds['click_end'].play()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and pygame.key.get_mods() & pygame.KMOD_ALT:
                        visual_debug = not visual_debug
                        manager.set_visual_debug_mode(visual_debug)
                elif event.type == APPLY_VOLUME_CHANGE:
                    for key in ['click_start', 'click_end']:
                        sounds[key].set_volume(event.settings['master_volume'] * event.settings['click_volume'])
                elif event.type == pygame.QUIT:
                    is_running = False
                elif event.type == pygame.WINDOWSIZECHANGED:
                    if event.window is None:
                        manager.set_window_resolution((event.x, event.y))
                        cursor_manager.set_window_resolution((event.x, event.y))
                        background = pygame.Surface((event.x, event.y))
                        background.fill(pygame.Color('#000000'))
                        if game is not None:
                            game.set_dimensions((event.x, event.y))
                try:
                    if game is not None:
                        game.process_event(event)
                    consumed = cursor_manager.process_events(event)
                    if not consumed:
                        manager.process_events(event)
                except NotEnoughResourcesError as e:
                    if game is not None:
                        game.print(e, out=1, floating_text_box_time=5)
                        print_exc()
                    else:
                        print(e)
                        print_exc()
                except Exception as e:
                    if game is not None:
                        game.print(e, out=1)
                        print_exc()
                    else:
                        print(e)
                        print_exc()
            try:
                manager.update(time_delta)
                cursor_manager.update(time_delta)
                if game is not None:
                    game.update(time_delta)
            except NotEnoughResourcesError as e:
                if game is not None:
                    game.print(e, out=1, floating_text_box_time=5)
                    print_exc()
                else:
                    print(e)
                    print_exc()
            except Exception as e:
                if game is not None:
                    game.print(e, out=1)
                    print_exc()
                else:
                    print(e)
                    print_exc()

            window_surface.blit(background, (0, 0))
            manager.draw_ui(window_surface)
            cursor_manager.draw_ui(window_surface)

            pygame.display.update()
    finally:
        if game is not None:
            game.exit()


if __name__ == '__main__':
    main()
