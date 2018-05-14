DEBUG = True

import pygame
import pygame.freetype
import asyncio
import logging
import sys, os
import scenes

from constants import *

os.environ['SDL_VIDEO_CENTERED'] = '1'

logging.basicConfig(level=logging.INFO,
                    filename='logs/app.log',
                    filemode='w',
                    format='{levelname:<8} {name:<15} {message}',
                    style='{')

log = logging.getLogger(__name__)

if DEBUG:
    # log to the stderr as well
    logging.getLogger().addHandler(logging.StreamHandler())

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
    log.debug(f"{self.__class__.__name__}{{{state}}}")
    self._state = state

getstate = lambda self: self._state

pygame.display.init()
pygame.freetype.init()

class SceneManager:

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.screen = pygame.display.set_mode((800, 600))
        self.rect = self.screen.get_rect()

        self.scene = None

        self.frames_count = 0

        # load fonts
        self.uifont = pygame.freetype.Font('media/fonts/poorstory.ttf')
        self.fancyfont = pygame.freetype.Font('media/fonts/sigmar.ttf')
        self.resetfonts()

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

        scene = getattr(scenes, scenename)(self)

        if hasattr(self.scene, 'on_blur'):
            await self.scene.on_blur(scene)

        self.scene = scene

        if hasattr(self.scene, 'on_focus'):
            await scene.on_focus()

    def schedule(self, coro):
        """A simple wrapper do simplify a scene's code"""
        task = self.loop.create_task(coro)
        task.add_done_callback(handle_task)
        return task

    async def gameloop(self):
        clock = pygame.time.Clock()

        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    if hasattr(self.scene, 'on_blur'):
                        await self.scene.on_blur(scene)
                    return

                if hasattr(self.scene, 'on_event'):
                    await self.scene.on_event(e)

            await self.scene.update()
            await self.scene.render()

            self.frames_count += 1

            # give the hand back to the loop
            await asyncio.sleep(0)
            pygame.display.flip()

            clock.tick(30)

    def run(self, scenename):
        self.loop.run_until_complete(self.focus(scenename))
        self.loop.run_until_complete(self.gameloop())

    state = property(getstate, setstate)

SceneManager().run("SplashScreen")
pygame.quit()
