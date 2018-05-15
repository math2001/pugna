"""A simple event based gui library"""

from pygame import Color, Surface
from pygame.locals import *
import pygame.freetype
from contextlib import contextmanager
from collections import deque
import copy

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
            pass
        raise AttributeError(f"No attribute {attr!r}")

    def __setattr__(self, attr, value):
        if self.ONSETATTR:
            self.ONSETATTR(attr, value)
        self[attr] = value

_rect_attrs = ('x', 'y', 'top', 'left', 'bottom', 'right', 'topleft',
               'bottomleft', 'topright', 'bottomright', 'midtop', 'midleft',
               'midbottom', 'midright', 'center', 'centerx', 'centery')

def optstobounds(opts):
    for key in _rect_attrs:
        try:
            opts.bounds[key] = opts[key]
            opts.pop(key)
        except KeyError:
            pass

class Button:

    """Text in a button isn't wrapped"""

    OPT = Options(
        width=None,
        height=None,
        fg=Color("white"),
        bordercolor=Color(30, 30, 30),
        borderwidth=1,
        size=None,
        font=None, # a string
        paddingx=20,
        paddingy=30,
        onclick=None,
        onmouseleave=None,
        onmouseenter=None,
        # when the size of the button will change, these arguments
        # will be given to get_rect
        bounds={}
    )

    def __init__(self, fonts, screen, text, **useropts):
        self.opt = copy.deepcopy(self.OPT)
        self.opt.update(useropts)

        try:
            useropts.bounds
        except AttributeError:
            optstobounds(self.opt)

        self.text = text
        self.screen = screen
        self.fonts = fonts

        self.hovered = False

        self.updateimg()

    def updateimg(self):
        with fontopt(self.fonts[self.opt.font], size=self.opt.size,
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

        for attr in self.opt.bounds:
            setattr(self.rect, attr, self.opt.bounds[attr])

    def setopt(self, **kwargs):
        self.opt.update(kwargs)
        self.updateimg()

    async def feed(self, e):
        if self.opt.onclick and e.type == MOUSEBUTTONDOWN \
            and self.rect.collidepoint(e.pos) and not e.captured:
            e.captured = True
            await self.opt.onclick(self, e)
        elif e.type == MOUSEMOTION:
            if not e.captured and self.rect.collidepoint(e.pos):
                e.captured = True
                if not self.hovered and self.opt.onmouseenter:
                    await self.opt.onmouseenter(self, e)
                self.hovered = True
            else:
                if self.hovered and self.opt.onmouseleave:
                    await self.opt.onmouseleave(self, e)
                self.hovered = False

    def render(self):
        self.screen.blit(self.image, self.rect)

    def __str__(self):
        active = 'on' if self.active else 'off'
        return f"<Button {active} text={self.text!r} @ {self.rect}>"

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
            await el.feed(e)

    def render(self):
        for el in self.elements:
            el.render()

    def activate(self, el):
        self.elements.append(el)

    def deactivate(self, el):
        self.elements.remove(el)

    def Button(self, *args, **kwargs):
        return Button(self.fonts, self.screen, *args, **kwargs)
