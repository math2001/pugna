import pygame
import pygame.freetype
from pygame.locals import *
import scenes

pygame.init()

class Manager:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, 800, 600)

        self.uifont = pygame.freetype.Font('media/fonts/poorstory.ttf')
        self.uifont.origin = True

        self.screen = pygame.display.set_mode(self.rect.size)
        self.current = None

    def focus(self, scene):
        getattr(self.current, 'on_blur', lambda: None)()
        self.current = scene
        scene.on_focus(self)

    def run(self):
        self.screen.fill(0)
        for e in pygame.event.get():
            if e.type == QUIT:
                return True
            self.current.event(e)
        self.current.update()
        self.current.render(self.screen, self.rect)
        pygame.display.flip()

manager = Manager()
manager.focus(scenes.Username())

going = True
while going:
    going = manager.run() is None

pygame.quit()

