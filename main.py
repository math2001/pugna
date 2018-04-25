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
        self.uifont.fgcolor = 150, 150, 150 # real original :D
        self.uifont.size = 20

        self.fancyfont = pygame.freetype.Font('media/fonts/sigmar.ttf')
        self.fancyfont.origin = True
        self.fancyfont.fgcolor = 200, 200, 200
        self.fancyfont.size = 30

        self.screen = pygame.display.set_mode(self.rect.size)
        self.current = None

        self.username = 'dev' # so we can skip the Username scene

        pygame.key.set_repeat(300, 50)

    def focus(self, scene):
        scene = getattr(scenes, scene)()
        getattr(self.current, 'on_blur', lambda: None)()
        self.current = scene
        scene.on_focus(self)

    def run(self):
        self.screen.fill(0)
        for e in pygame.event.get():
            if e.type == QUIT:
                return True
            getattr(self.current, 'event', lambda e: None)(e)
        getattr(self.current, 'update', lambda: None)()
        self.current.render()
        pygame.display.flip()

manager = Manager()
manager.focus("Menu")

going = True
while going:
    going = manager.run() is None

pygame.quit()

