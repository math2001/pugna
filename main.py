import os
import asyncio
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

focus_lock = asyncio.Lock()

class Manager:

    def __init__(self, scene):
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

        # used to identify clients
        self.uuid = uuid4().hex
        # so we can skip the Username scene
        self.username = 'dev' + self.uuid[:6]

        self.going = True
        self.clock = pygame.time.Clock()
        self.frames_count = 0

        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.focus(scene))
        self.loop.run_until_complete(self.run())

        self.focusing_scene = False

        pygame.key.set_repeat(300, 50)

    async def focus(self, scene):
        try:
            scene = getattr(scenes, scene)()
        except AttributeError:
            raise ValueError("No such scene as {!r}".format(scene))
        l.debug("Switch scene to {!r}".format(scene.__class__.__name__))
        if hasattr(self.current, 'on_blur'):
            await self.current.on_blur()
        # self.loop.create_task(scene.on_focus(self))
        self.focusing_scene = await scene.on_focus(self)
        self.current = scene

    async def run(self):
        while self.going:
            self.frames_count += 1
            self.screen.fill(0)
            for e in pygame.event.get():
                if e.type == QUIT:
                    self.going = False
                if hasattr(self.current, 'event'):
                    await self.current.event(e)
            if hasattr(self.current, 'update'):
                await self.current.update()
            await self.current.render()
            pygame.display.flip()

os.environ["SDL_VIDEO_CENTERED"] = "1"

manager = Manager("Username")
pygame.quit()

