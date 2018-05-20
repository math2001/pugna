VERSION = '0.1.0'
DEBUG = True

import pygame
import pygame.freetype
import asyncio
import logging
import sys, os
import scenes
import utils.gui
import uuid
import math

from constants import *

os.environ['SDL_VIDEO_CENTERED'] = '1'
format = '{levelname:<8} {name:<15} {message}'
logging.basicConfig(level=logging.WARNING, style='{',
                    format=format)

filehandler = logging.FileHandler('logs/app.log')
filehandler.setFormatter(logging.Formatter(format, style='{'))

root = logging.getLogger()
root.addHandler(filehandler)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# only use absoute imports. The dirname of the current script is always added
# to sys.path, which I don't want. I just want the root directory of the
# project, and I import from there
for i, path in enumerate(sys.path):
    if path == os.path.dirname(os.path.abspath(__file__)):
        sys.path[i] = os.getcwd()


def handle_task(fut):
    if fut.exception():
        fut.result() # raise exception

def setstate(self, state):
    log.info(f"{self.__class__.__name__}{{{state}}}")
    self._state = state

async def void(*args, **kwargs):
    pass

getstate = lambda self: self._state

pygame.display.init()
pygame.freetype.init()

async def btnmouseenter(btn, e):
    btn.setopt(bordercolor=pygame.Color(100, 100, 100))

async def btnmouseleave(btn, e):
    btn.setopt(bordercolor=pygame.Color(30, 30, 30))

class SceneManager:

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.screen = pygame.display.set_mode((800, 600))
        self.rect = self.screen.get_rect()

        self.scene = None

        self.frames_count = 0

        pygame.key.set_repeat(300, 50)
        pygame.mouse.set_visible(False)
        pygame.display.set_caption(CAPTION)

        # load fonts
        self.uifont = pygame.freetype.Font('media/fonts/poorstory.ttf')
        self.fancyfont = pygame.freetype.Font('media/fonts/sigmar.ttf')
        self.resetfonts()

        self.cursor = pygame.image.load('media/images/cursor.png').convert_alpha()

        self.gui = utils.gui.GUI(
            self.loop,
            self.screen,
            ui=self.uifont,
            fancy=self.fancyfont
        )

        # set defaults for gui elements
        utils.gui.GuiElement.OPT.font = 'ui'
        utils.gui.GuiElement.OPT.fg = pygame.Color(200, 200, 200)
        utils.gui.Button.OPT.onmouseenter = btnmouseenter
        utils.gui.Button.OPT.onmouseleave = btnmouseleave

        self.uuid = uuid.uuid4().hex

        # for dev purposes
        self.dev_username = True
        self.username = f'dev {self.uuid}'

    def resetfonts(self):
        self.uifont.fgcolor = TEXT_FG
        self.uifont.size = 20
        self.uifont.origin = False

        self.fancyfont.fgcolor = TEXT_HOVER_FG
        self.fancyfont.size = 25
        self.fancyfont.origin = False

    async def focus(self, scenename):
        if not hasattr(scenes, scenename):
            raise ValueError(f"No such scene as {scenename!r}")

        log.info(f"-> {scenename}")

        scene = getattr(scenes, scenename)(self)

        if hasattr(self.scene, 'on_blur'):
            await self.scene.on_blur(scene)

        self.scene = scene

        if not hasattr(self.scene, 'on_event'):
            self.scene.on_event = void
        if not hasattr(self.scene, 'update'):
            self.scene.update = void
        if not hasattr(self.scene, 'render'):
            self.scene.render = void

        if hasattr(self.scene, 'on_focus'):
            await scene.on_focus()

    def schedule(self, coro):
        """A simple wrapper do simplify a scene's code"""
        task = self.loop.create_task(coro)
        task.add_done_callback(handle_task)
        return task

    async def quit(self):
        if hasattr(self.scene, 'on_blur'):
            await self.scene.on_blur(self.scene)
            self.going = False

    def rendercursor(self):
        if not pygame.mouse.get_focused():
            return
        self.screen.blit(self.cursor, self.cursor_position)

    async def gameloop(self):
        clock = pygame.time.Clock()

        self.going = True
        self.cursor_position = pygame.mouse.get_pos()

        while self.going:
            for e in pygame.event.get():
                if e.type == pygame.MOUSEMOTION:
                    self.cursor_position = e.pos
                await self.gui.feed(e)
                if e.type == pygame.QUIT:
                    return await self.quit()

                await self.scene.on_event(e)

            await self.scene.update()

            self.screen.fill(pygame.Color('black'))

            await self.scene.render()
            self.gui.render()
            self.rendercursor()

            self.frames_count += 1

            # give the hand back to the loop
            await asyncio.sleep(0)
            pygame.display.flip()

            clock.tick(30)
            if DEBUG:
                pygame.display.set_caption(f"{CAPTION} v{VERSION} | "
                                           f"{round(clock.get_fps())}")

    def run(self, scenename):
        self.loop.run_until_complete(self.focus(scenename))
        self.loop.run_until_complete(self.gameloop())

    state = property(getstate, setstate)

SceneManager().run("HostGame")
