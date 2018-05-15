"""A simple event based gui library"""

from pygame import Color, Surface
from pygame.locals import *
import pygame.freetype
from contextlib import contextmanager
from collections import deque

pygame.freetype.init()

@contextmanager
def fontopt(font, **opts):
    previous = {}
    for key, value in opts.items():
        if value is None:
            continue
        previous[key] = getattr(font, key)
        setattr(font, key, value)
    yield font
    for key, value in previous.items():
        setattr(font, key, value)


class Options(dict):

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError("No attribute %s" % attr)

    def __setattr__(self, attr, value):
        self[attr] = value

    def copy(self):
        return Options(self.items())

class Button:

    """Text in a button isn't wrapped"""

    OPT = Options(
        width=None,
        height=None,
        fg=Color("white"),
        bordercolor=Color(30, 30, 30),
        borderwidth=1,
        size=None,
        fontname=None,
        paddingx=20,
        paddingy=30,
        onclick=None,
        onhover=None,
    )

    def __init__(self, fonts, screen, text, **useropts):
        self.opt = self.OPT.copy()
        self.opt.update(useropts)
        self.text = text
        self.screen = screen
        self.fonts = fonts

        self.updateimg()

    def updateimg(self):
        with fontopt(self.fonts[self.opt.fontname], size=self.opt.size,
                     fgcolor=self.opt.fg) as font:
            self._updateimg(font)

    def _updateimg(self, font):

        fontrect = font.get_rect(self.text)

        width = self.opt.width
        if width is None:
            width = fontrect.width + self.opt.paddingx + self.opt.borderwidth

        height = self.opt.height
        if height is None:
            height = fontrect.height + self.opt.paddingy + self.opt.borderwidth

        self.image = Surface((width, height))
        self.rect = self.image.get_rect()

        if self.opt.borderwidth != -1 is not None:
            # inflates as less as possible
            borderwidth = (self.opt.borderwidth - self.opt.borderwidth % 2) * -2
            pygame.draw.rect(self.image, self.opt.bordercolor,
                             self.rect.inflate(borderwidth, borderwidth),
                             self.opt.borderwidth)

        r = font.get_rect(self.text)
        r.center = self.rect.center
        font.render_to(self.image, r, None)

    async def feed(self, e):
        e.captured = True
        if self.opt.onclick and e.type == MOUSEBUTTONDOWN \
            and self.rect.collidepoint(e.pos):
            await self.opt.onclick(self, e)
        elif self.opt.onhover and e.type == MOUSEMOTION \
            and self.rect.collidepoint(e.pos):
            await self.opt.onhover(self, e)
        else:
            e.captured = False

    def render(self):
        self.screen.blit(self.image, self.rect)

    def __str__(self):
        return f"<Button text={self.text} @ {self.rect}>"

    def __repr__(self):
        return str(self)

class GUI:

    def __init__(self, loop, screen, **fonts):
        self.loop = loop
        self.screen = screen
        self.rect = self.screen.get_rect()
        self.fonts = fonts
        self.fonts[None] = pygame.freetype.Font(None, size=20)

        self.elements = []

    async def feed(self, e):
        e.captured = False
        for el in reversed(self.elements):
            if e.captured:
                return
            await el.feed(e)

    def render(self):
        for el in self.elements:
            el.render()

    def Button(self, *args, **kwargs):
        btn = Button(self.fonts, self.screen, *args, **kwargs)
        self.elements.append(btn)
        return btn
