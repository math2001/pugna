import os
import asyncio
import logging
import pygame
import pygame.freetype
from pygame.locals import *
from constants import CAPTION
from utils.gui import Button
import scenes
from uuid import uuid4

logging.basicConfig(level=logging.DEBUG, format='{asctime} {levelname:<5} {name} {message}', style='{')

log = logging.getLogger(__name__)

pygame.display.init()
pygame.freetype.init()

class Manager:

    def __init__(self, scene):
        self.rect = pygame.Rect(0, 0, 800, 600)

        self.uifont = pygame.freetype.Font('media/fonts/poorstory.ttf')
        self.reset_uifont()

        self.fancyfont = pygame.freetype.Font('media/fonts/sigmar.ttf')
        self.reset_fancyfont()

        self.screen = pygame.display.set_mode(self.rect.size)
        self.current = None

        pygame.display.set_caption(CAPTION)

        # used to identify clients
        self.uuid = uuid4().hex
        # so we can skip the Username scene (for dev)
        self.username = 'dev' + self.uuid[:6]

        # this is a simple counter that iterates between 1 and 3 to display
        # an animation suspension dots after messages
        self.animdots = 0

        self.going = True

        self.clock = pygame.time.Clock()
        self.frames_count = 0

        self.menubtn = Button(self.uifont, "Menu", {"size": (70, 30)})
        self.menubtn.rect.topright = self.rect.topright
        self.menubtn.rect.top += 5
        self.menubtn.rect.left -= 5

        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.focus(scene))
        self.loop.run_until_complete(self.run())


        # used for communicating with server
        self.writer = None
        self.reader = None

        pygame.key.set_repeat(300, 50)

    def suspensiondots(self, surface, rect, font):
        """font.origin should be True"""
        r = font.get_rect('.' * self.animdots)
        r.topleft = rect.topright
        font.render_to(surface, r, None)

    def reset_fonts(self):
        self.reset_uifont()
        self.reset_fancyfont()

    def reset_uifont(self):
        self.uifont.fgcolor = 150, 150, 150 # real original :D
        self.uifont.size = 20
        self.uifont.origin = False

    def reset_fancyfont(self):
        self.fancyfont.fgcolor = 200, 200, 200
        self.fancyfont.size = 25
        self.fancyfont.origin = False

    async def focus(self, scene):
        self.reset_uifont()
        self.reset_fancyfont()
        scene = scene.title().replace(' ', '')
        try:
            scene = getattr(scenes, scene)()
        except AttributeError:
            raise ValueError("No such scene as {!r}".format(scene))
        log.debug("Switch scene to {!r}".format(scene.__class__.__name__))
        if hasattr(self.current, 'on_blur'):
            await self.current.on_blur()
        # self.loop.create_task(scene.on_focus(self))
        await scene.on_focus(self)
        self.current = scene

    async def run(self):
        while self.going:
            self.frames_count += 1

            if self.frames_count % 20 == 0:
                self.animdots += 1
                if self.animdots == 4:
                    self.animdots = 0

            self.screen.fill(0)
            for e in pygame.event.get():
                if e.type == QUIT:
                    self.going = False
                if hasattr(self.current, 'event'):
                    await self.current.event(e)
                if self.menubtn.event(e):
                    await self.focus("menu")
            if hasattr(self.current, 'update'):
                await self.current.update()
            await self.current.render()
            if getattr(self.current, 'menubtn', True):
                self.screen.blit(self.menubtn.image, self.menubtn.rect)
            # give control back to the event loop, so that other tasks can run
            await asyncio.sleep(0)
            pygame.display.flip()

os.environ["SDL_VIDEO_CENTERED"] = "1"

manager = Manager("Host Game")
pygame.quit()

