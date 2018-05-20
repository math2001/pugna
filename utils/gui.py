"""A simple event based gui library"""

from pygame import Color, Surface
from pygame.locals import *
import pygame.freetype
from contextlib import contextmanager
from collections import deque
import copy
import logging

pygame.freetype.init()

log = logging.getLogger(__name__)

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

def word_wrap(surf, font, text, opt):
    """Stolen from the pygame documentation freetype.Font.render_to
    I tweaked it a bit to support \n
    """
    origin = font.origin
    font.origin = True
    width, height = surf.get_size()
    line_spacing = font.get_sized_height()
    x = 0
    y = line_spacing
    space = font.get_rect(' ')
    for line in text.splitlines():
        for word in line.split(' '):
            bounds = font.get_rect(word)
            if x + bounds.width + bounds.x >= width:
                x, y = 0, y + line_spacing
            if x + bounds.width + bounds.x >= width:
                raise ValueError("word too wide for the surface")
            if y + bounds.height - bounds.y >= height:
                return
                raise ValueError("text to long for the surface")
            font.render_to(surf, (x, y), None, opt.fg)
            x += bounds.width + space.width
        x, y = 0, y + line_spacing
    font.origin = origin
    return x, y

class Options(dict):

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            pass
        raise AttributeError(f"No attribute {attr!r}")

    def __setattr__(self, attr, value):
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

class GuiElement:

    OPT = Options(
        fg=Color('white'),
        borderwidth=1,
        bordercolor=Color(30, 30, 30),
        bounds={},
        font=None,
        size=None
    )

    def __init__(self, gui, **useropts):
        # the common gui elements options
        self.opt = copy.deepcopy(GuiElement.OPT)
        # the default options for this specific gui element
        self.opt.update(copy.deepcopy(self.OPT))
        # the given options
        self.opt.update(useropts)

        try:
            useropts.bounds
        except AttributeError:
            optstobounds(self.opt)

        self.gui = gui

        self.updateimg()

    def render(self):
        self.gui.screen.blit(self.image, self.rect)

    def updateimg(self):
        with fontopt(self.gui.fonts[self.opt.font], size=self.opt.size,
                     fgcolor=self.opt.fg) as font:
            font.origin = False
            self._updateimg(font)

    def __repr__(self):
        return str(self)

    def setopt(self, **kwargs):
        self.opt.update(kwargs)
        self.updateimg()

    def setbounds(self, **kwargs):
        """You shouldn't use guiel.rect = ..., but set bounds, as it'll make
        sure to keep the same position after guiel.setopt() calls"""
        self.opt.bounds = kwargs
        self.updatefrombounds()

    def debug(self, color, rect, surf=None):
        pygame.draw.rect(surf or self.gui.screen, Color(color), rect, 1)

    def copy(self):
        return getattr(self.gui, self.__class__.__name__)(**self.opt)

    def drawborder(self):
        if self.opt.borderwidth is None:
            return 0

        borderwidth = (self.opt.borderwidth - self.opt.borderwidth % 2) * -2
        pygame.draw.rect(self.image, self.opt.bordercolor,
                         self.rect.inflate(borderwidth, borderwidth),
                         self.opt.borderwidth)
        return borderwidth

    def updatefrombounds(self):
        for attr in self.opt.bounds:
            setattr(self.rect, attr, self.opt.bounds[attr])


class Button(GuiElement):

    """Text in a button isn't wrapped"""

    OPT = Options(
        width=None,
        height=None,
        paddingx=10,
        paddingy=20,
        onclick=None,
        onmouseleave=None,
        onmouseenter=None,
        text=None,
        # when the size of the button will change, these arguments
        # will be given to get_rect
        bounds={}
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hovered = False

        if self.opt.text is None:
            raise ValueError("A buttons need some text. None given")

    def _updateimg(self, font):
        fontrect = font.get_rect(self.opt.text)

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

        r = font.get_rect(self.opt.text)
        r.center = self.rect.center
        font.render_to(self.image, r, None)

        for attr in self.opt.bounds:
            setattr(self.rect, attr, self.opt.bounds[attr])

    async def feed(self, e):
        if self.opt.onclick and e.type == MOUSEBUTTONDOWN \
            and self.rect.collidepoint(e.pos) and not e.captured:
            e.captured = True
            await self.opt.onclick(self, e)
            log.debug(f'Clicked on {self}')
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

    def __str__(self):
        return f"<Button text={self.opt.text!r} @ {self.rect}>"

    def render(self):
        self.gui.screen.blit(self.image, self.rect)

class MessageBox(GuiElement):

    OPT = Options(
        width=350,
        height=200,
        paddingx=10,
        paddingy=10,
        titlepaddingy=10,
        onsend=None,
        text='Popup text',
        ok=None, # this must be a button
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not isinstance(self.opt.ok, Button):
            raise TypeError("opt.ok should be of type Button, got "
                            f"{self.opt.ok.__class__.__name__}")

        if self.opt.ok.opt.onclick is not None:
            raise ValueError("Button shouldn't have onclick event defined, "
                             f"got {self.opt.ok.opt.onclick}")

        self.opt.ok.opt.onclick = self.onsend

    async def onsend(self, btn, e):
        await self.opt.onsend()

    async def feed(self, e):
        await self.opt.ok.feed(e)

    def _updateimg(self, font):
        self.image = pygame.Surface((self.opt.width, self.opt.height))
        self.rect = self.image.get_rect()

        if self.opt.borderwidth != -1 is not None:
            # inflates as less as possible
            borderwidth = (self.opt.borderwidth - self.opt.borderwidth % 2) * -2
            pygame.draw.rect(self.image, self.opt.bordercolor,
                             self.rect.inflate(borderwidth, borderwidth),
                             self.opt.borderwidth)

        titlerect = font.get_rect(self.opt.title)
        titlerect.centerx = self.rect.centerx
        titlerect.top = self.opt.titlepaddingy
        font.render_to(self.image, titlerect, None)

        textsurf = pygame.Surface((self.rect.width - self.opt.paddingx * 2,
            self.rect.height - titlerect.height - self.opt.titlepaddingy * 2 \
            - self.opt.ok.rect.height - self.opt.paddingy * 2))
        # times 2 to give padding between button and text

        word_wrap(textsurf, font, self.opt.msg, self.opt)

        self.image.blit(textsurf, (self.opt.paddingx,
                                   titlerect.height + self.opt.titlepaddingy * 2))

        for attr in self.opt.bounds:
            setattr(self.rect, attr, self.opt.bounds[attr])

        self.opt.ok.rect.bottom = self.rect.bottom - self.opt.paddingy
        self.opt.ok.rect.right = self.rect.right - self.opt.paddingx

    def render(self):
        self.gui.screen.blit(self.image, self.rect)
        self.opt.ok.render()

class ConfirmBox(MessageBox):
    pass

class Input(GuiElement):

    """Just the input element"""

    OPT = Options(
        width=200,
        height=40,
        origin=(10, 10),
        onsend=None,
        initialtext='',
        maxlength=0
    )

    def __init__(self, gui, **opts):
        self.text = opts.get('initialtext', self.OPT.initialtext)
        super().__init__(gui, **opts)

    def _updateimg(self, font):
        self.image = pygame.Surface((self.opt.width, self.opt.height))
        self.rect = self.image.get_rect()

        self.drawborder()

        font.origin = True
        o = self.opt.origin[0], self.rect.bottom - self.opt.origin[1]

        font.render_to(self.image, o, self.text)

        self.updatefrombounds()

    async def feed(self, e):
        if e.type == KEYDOWN:
            if e.unicode == '\x08':
                self.text = self.text[:-1]
            elif e.unicode == '\r':
                if self.opt.onsend:
                    await self.opt.onsend(self, e)
            elif self.opt.maxlength == 0 or len(self.text) < self.opt.maxlength:
                self.text += e.unicode
            self.updateimg()

class InputBox(GuiElement):

    OPT = Options(
        width=350,
        height=170,
        label='Input:',
        paddingx=20,
        paddingy=10,
        titlepaddingy=20,
        onsend=None,
        input=None, # should be gui.Input
        ok=None # should be gui.Button
    )

    def __init__(self, gui, **opts):
        super().__init__(gui, **opts)

        if not isinstance(self.opt.input, Input):
            raise TypeError("Expected 'input' to be of type 'Input', got"
                             f"{self.opt.input.__class__.__name__!r}")

        if self.opt.input.opt.onsend is not None:
            raise ValueError("Input shouldn't have an onsend listener already")

        if not isinstance(self.opt.ok, Button):
            raise TypeError("Expected 'ok' to be of type 'Button', got"
                             f"{self.opt.ok.__class__.__name__!r}")

        if self.opt.ok.opt.onclick is not None:
            raise ValueError("Button shouldn't have an onclick listener already")

        self.opt.input.opt.onsend = self.opt.onsend
        self.opt.ok.opt.onclick = self.opt.onsend

    def _updateimg(self, font):
        self.image = pygame.Surface((self.opt.width, self.opt.height))
        self.rect = self.image.get_rect()

        self.drawborder()

        rect = font.get_rect(self.opt.label)
        rect.top = self.opt.titlepaddingy
        rect.centerx = self.rect.centerx
        font.render_to(self.image, rect, None)

        self.updatefrombounds()

        self.opt.ok.setbounds(bottom=self.rect.bottom - self.opt.paddingy,
                              right=self.rect.right - self.opt.paddingx)

        self.opt.input.setbounds(center=self.rect.center)

    async def feed(self, e):
        await self.opt.input.feed(e)
        await self.opt.ok.feed(e)

    def render(self):
        super().render()
        self.opt.input.render()
        self.opt.ok.render()

    @property
    def text(self):
        return self.opt.input.text

class GUI:

    """Feeds and renders active elements

    It can also be used to create elements (it manages giving fonts for example)
    """

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
        return Button(self, *args, **kwargs)

    def MessageBox(self, *args, **kwargs):
        return MessageBox(self, *args, **kwargs)

    def ConfirmBox(self, *args, **kwargs):
        return ConfirmBox(self, *args, **kwargs)

    def InputBox(self, **opts):
        return InputBox(self, **opts)

    def Input(self, **opts):
        return Input(self, **opts)
