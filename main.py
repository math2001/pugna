import os
import logging
import pygame
import pygame.freetype
from pygame.locals import *
from constants import CAPTION
import scenes
from uuid import uuid4

logging.basicConfig(level=logging.DEBUG)

l = logging.getLogger(__name__)

pygame.init()

class Manager:

    def __init__(self):
        self.rect = pygame.Rect(0, 0, 800, 600)

        self.uifont = pygame.freetype.Font('media/fonts/poorstory.ttf')
        self.uifont.fgcolor = 150, 150, 150 # real original :D
        self.uifont.size = 20

        self.fancyfont = pygame.freetype.Font('media/fonts/sigmar.ttf')
        self.fancyfont.fgcolor = 200, 200, 200
        self.fancyfont.size = 25

        self.screen = pygame.display.set_mode(self.rect.size)
        self.current = None

        pygame.display.set_caption(CAPTION)

        self.uuid = uuid4().hex # used to identify clients
        self.username = 'dev' + self.uuid[:6] # so we can skip the Username scene

        pygame.key.set_repeat(300, 50)

    def focus(self, scene):
        try:
            scene = getattr(scenes, scene)()
        except AttributeError:
            raise ValueError("No such scene as {!r}".format(scene))
        l.debug("Switch scene to {!r}".format(scene.__class__.__name__))
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

os.environ["SDL_VIDEO_CENTERED"] = "1"

manager = Manager()
manager.focus("HostGame")

going = True
while going:
    going = manager.run() is None

pygame.quit()

