import pygame
import pygame.freetype
from pygame.locals import *
from contextlib import contextmanager

@contextmanager
def origin(font, enabled):
    default = font.origin
    font.origin = enabled
    yield font
    font.origin = default

def word_wrap(surf, text, font, x=0, y=0, **opt):
    """Stolen from the pygame documentation freetype.Font.render_to
    I tweaked it a bit to support \n
    """
    opt = Options(**opt)
    with origin(font, True):
        width, height = surf.get_size()
        line_spacing = font.get_sized_height()
        y += line_spacing
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
                font.render_to(surf, (x, y), opt.bgcolor, opt.fgcolor)
                x += bounds.width + space.width
            x, y = 0, y + line_spacing
        return x, y

class Options(dict):

    def __init__(self, **kwargs):
        self.update(kwargs)

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError("No attribute %s" % attr)

    def __setattr__(self, attr, value):
        self[attr] = value

class Button:

    """A simple button
    Nothing fancy here... Notice that when the height/width is explicit
    the margin for that specific option isn't taken into account, and the
    border are drawn *inside* the button (so that the actually button size
    is the size you wanted)
    Make sure you put the rect (btn.rect) where you want it and render it!
    Call event() with the an Event, and it'll return True if the user clicked
    on it.
    """

    def __init__(self, font, text, **useropt):
        pygame.sprite.Sprite.__init__(self)
        self.text = text
        self.font = font

        self.disabled = False

        opt = Options()
        opt.margin = 30, 20
        opt.thickness = 1
        opt.bordercolor = pygame.Color(20, 20, 20)
        opt.fgcolor = font.fgcolor
        opt.bgcolor = None
        opt.fontsize = font.size
        opt.style = pygame.freetype.STYLE_DEFAULT
        # if theses are None, they are automatically generated
        opt.width = None
        opt.height = None
        opt.update(useropt)

        opt.hover_fgcolor = font.fgcolor + pygame.Color(100, 100, 100)
        opt.hover_bgcolor = opt.bgcolor
        opt.hover_bordercolor = opt.bordercolor + pygame.Color(10, 10, 10)
        opt.hover_thickness = opt.thickness

        opt.disabled_fgcolor = opt.fgcolor - pygame.Color(80, 80, 80)
        opt.disabled_fgcolor.a = 255
        opt.disabled_bgcolor = opt.bgcolor
        opt.disabled_bordercolor = opt.bordercolor - pygame.Color(10, 10, 10)
        opt.disabled_thickness = opt.thickness + 1

        opt.update(useropt)

        self.fontrect = self.font.get_rect(self.text, style=opt.style,
                                           size=opt.fontsize)
        width = opt.width
        height = opt.height
        if opt.width is None:
            width = self.fontrect.width + opt.margin[0] + opt.thickness
        if opt.height is None:
            height = self.fontrect.height + opt.margin[1] + opt.thickness
        size = width, height
        self.rect = pygame.Rect(0, 0, width, height)
        self.fontrect.center = self.rect.center

        self.normal = self._render_state(size, "", opt)
        self.hover = self._render_state(size, "hover_", opt)
        self.disabled = self._render_state(size, "disabled_", opt)

        self.enabled = True # this'll set self.image

    def _render_state(self, size, state, opt):
        bordercolor = opt[state + "bordercolor"]
        thickness = opt[state + "thickness"]
        fgcolor = opt[state + "fgcolor"]
        bgcolor = opt[state + "bgcolor"]

        s = pygame.Surface(size)
        # takes the even number below if odd, otherwise do nothing
        # because we can't deflate with an odd number (it's always going to be
        # on more or one less). So here, we try to inflate as less as possible.
        t = (opt.thickness - opt.thickness % 2) * -2
        pygame.draw.rect(s, bordercolor, self.rect.inflate(t, t), thickness)

        with origin(self.font, False):
            self.font.render_to(s, self.fontrect, self.text, fgcolor, bgcolor,
                                style=opt.style, size=opt.fontsize)
        return s

    def event(self, e):
        if not self.enabled:
            return
        if e.type == MOUSEMOTION:
            if self.rect.collidepoint(e.pos):
                self.image = self.hover
            else:
                self.image = self.normal
        return (e.type == MOUSEBUTTONDOWN
                and e.button == 1
                and self.rect.collidepoint(e.pos))

    def render(self, s):
        s.blit(self.image, self.rect)

    def __str__(self):
        return '<Button text={!r}>'.format(self.text)

    def __repr__(self):
        return self.__str__()

    def setenabled(self, val):
        self._enabled = val
        if val:
            self.image = self.normal
        else:
            self.image = self.disabled

    enabled = property(lambda self: self._enabled, setenabled)

class TextBox:

    def __init__(self, font, **useropt):
        opt = Options()
        opt.initialtext = ''
        opt.bordercolor = 33, 33, 33
        opt.origin = 10, 10
        opt.thickness = 1
        opt.fgcolor = font.fgcolor
        opt.bgcolor = None
        opt.style = pygame.freetype.STYLE_DEFAULT
        opt.fontsize = font.size
        opt.maxlength = None
        opt.update(useropt)

        if opt.maxlength is not None and len(opt.initialtext) > opt.maxlength:
            raise ValueError("Initial text is greater than the maximum length")

        opt.width = 200
        opt.height = font.get_sized_height(opt.fontsize) + 10
        opt.update(useropt)

        opt.hover_bordercolor = opt.bordercolor
        opt.hover_fgcolor = opt.fgcolor
        opt.hover_bgcolor = opt.bgcolor
        opt.hover_thickness = opt.thickness

        self.opt = opt

        self.text = self.opt.initialtext
        self.font = font
        self.rect = pygame.Rect(0, 0, opt.width, opt.height)

        self.state = ''
        self.normal = self._render_state("")
        self.hover = self._render_state("hover_")

        self.image = self.normal

    def _render_state(self, state):
        bd = self.opt[state + 'bordercolor']
        fg = self.opt[state + 'fgcolor']
        bg = self.opt[state + 'bgcolor']
        thck = self.opt[state + 'thickness']

        s = pygame.Surface((self.opt.width, self.opt.height))
        # see the Button._render_state
        t = (thck - thck % 2) * -2
        pygame.draw.rect(s, bd, self.rect.inflate(t, t), thck)
        return s

    def event(self, e):
        if e.type == KEYDOWN:
            if e.unicode == '\x08':
                if len(self.text) > 0:
                    self.text = self.text[:-1]
            elif e.unicode == '\r':
                return True
            elif self.opt.maxlength is None or \
                len(self.text) < self.opt.maxlength:
                self.text += e.unicode
        elif e.type == MOUSEMOTION:
            self.state = 'hover_' if self.rect.collidepoint(e.pos) else ''
            self.image = self.hover if self.state == 'hover_' else self.normal

    def render(self, s):
        origin = (self.rect.left + self.opt.origin[0],
                  self.rect.bottom - self.opt.origin[1])
        fg = self.opt[self.state + 'fgcolor']
        bg = self.opt[self.state + 'bgcolor']
        s.blit(self.image, self.rect)
        self.font.render_to(s, origin, self.text, fg, bg,
                            self.opt.style, size=self.opt.fontsize)

    def __str__(self):
        return '<TextBox text={!r}>'.format(self.text)

    def __repr__(self):
        return self.__str__()

class MessageBox:

    """Creates a little popup
    Place the mb.rect where you want it and render it.
    Call event() with an Event and it'll return True if the user
    cliked ok and return False if the user clicked cancel.
    If you do move the rect, make sure you call calibre() after it,
    otherwise they will be off (since they are relative to the window)
    and the click detection won't work properly.

    run pygame.draw.rect(s, (255, 0, 0), mb.ok.rect, 1) to see what I mean

    """

    @classmethod
    def new(cls, font, message, ok, **useropt):
        """A shortcut to automatically create the button from text"""
        return cls(font, message, Button(font, ok), **useropt)

    def __init__(self, font, message, ok, **useropt):
        self.ok = ok

        opt = Options()
        opt.width = 350
        opt.height = 150
        opt.thickness = 1
        opt.bordercolor = 33, 33, 33
        opt.bgcolor = None
        opt.fgcolor = font.fgcolor
        opt.margin = 20, 20
        opt.update(useropt)

        self.image = pygame.Surface((opt.width, opt.height))
        self.rect = self.image.get_rect()
        if opt.bgcolor:
            self.image.fill(opt.bgcolor)

        text = pygame.Surface((opt.width - opt.margin[0] * 2,
                               opt.height - opt.margin[1] * 2))
        word_wrap(text, message, font, **opt)
        self.image.blit(text, opt.margin)

        pygame.draw.rect(self.image, opt.bordercolor,
                         self.rect.inflate(-opt.thickness * 2,
                                            -opt.thickness * 2),
                         opt.thickness)

        ok.rect.bottomright = pygame.math.Vector2(self.rect.bottomright) \
                              - pygame.math.Vector2(opt.margin)

    def calibre(self):
        # set button's rect absolute position to be able to detect collsion
        self.ok.rect.topleft = (self.rect.left + self.ok.rect.left,
                                self.rect.top + self.ok.rect.top)

    def event(self, e):
        if self.ok.event(e):
            return True

    def render(self, s):
        """You don't *have* to use this method"""
        s.blit(self.image, self.rect)
        self.ok.render(s)

    def __str__(self):
        return f"<MessageBox {self.message!r}>"

    def __repr__(self):
        return self.__str__()

class ConfirmBox(MessageBox):

    @classmethod
    def new(cls, font, message, ok, cancel, **useropt):
        """A shortct to automatically create the buttons from text"""
        return cls(font, message, Button(font, ok),
                   Button(font, cancel), **useropt)

    def __init__(self, font, message, ok, cancel, **useropt):
        super().__init__(font, message, ok, **useropt)
        self.cancel = cancel
        self.cancel.rect.midright = self.ok.rect.midleft
        self.cancel.rect.left -= 10

    def calibre(self):
        super().calibre()
        self.cancel.rect.topleft = (self.rect.left + self.cancel.rect.left,
                                    self.rect.top + self.cancel.rect.top)

    def event(self, e):
        if self.ok.event(e):
            return True
        elif self.cancel.event(e):
            return False

    def render(self, s):
        super().render(s)
        self.cancel.render(s)

    def __str__(self):
        return f"<ConfirmBox {self.message!r}>"
