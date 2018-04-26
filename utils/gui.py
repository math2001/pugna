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

class TextBox:

    def __init__(self, font, user_opt={}):
        opt = Options()
        opt.initialtext = ""
        opt.bordercolor = 33, 33, 33
        opt.focusedbordercolor = 150, 150, 150
        opt.fgcolor = 150, 150, 150
        opt.bgcolor = None
        opt.margin = 10, 10
        opt.style = pygame.freetype.STYLE_DEFAULT
        opt.fontsize = 20
        opt.size = 200, font.get_sized_height(getattr(user_opt, 'fontsize',
                                                      opt.fontsize)) + 10
        opt.thickness = 1
        opt.update(user_opt)

        self.opt = opt

        self.text = self.opt.initialtext
        self.font = font
        self.focused = False

    def event(self, e):
        if not self.focused:
            return
        if e.type == KEYDOWN:
            if e.unicode == '\x08':
                if len(self.text) > 0:
                    self.text = self.text[:-1]
            elif e.unicode == '\r':
                return True
            else:
                self.text += e.unicode

    def render(self):
        surface = pygame.Surface((self.opt.size[0] + self.opt.thickness,
                                 self.opt.size[1] + self.opt.thickness))
        rect = surface.get_rect()
        bordercolor = self.opt.bordercolor if self.focused \
                      else self.opt.focusedbordercolor
        pygame.draw.rect(surface, bordercolor, rect.inflate(-self.opt.thickness,
            -self.opt.thickness), self.opt.thickness)
        origin = (rect.left + self.opt.margin[0],
                 rect.bottom - self.opt.margin[1])
        self.font.render_to(surface, origin, self.text,
                            self.opt.fgcolor, self.opt.bgcolor, self.opt.style,
                            size=self.opt.fontsize)
        return surface, rect

    def __str__(self):
        return '<TextBox text={!r}>'.format(self.text)

    def __repr__(self):
        return self.__str__()

class Button(pygame.sprite.Sprite):

    def __init__(self, font, text, user_opt={}):
        pygame.sprite.Sprite.__init__(self)

        self.text = text

        opt = Options()
        opt.margin = 3, 5
        opt.thickness = 0
        opt.bordercolor = 33, 33, 33
        opt.fgcolor = font.fgcolor
        opt.bgcolor = None
        opt.fontsize = font.size
        opt.style = pygame.freetype.STYLE_DEFAULT
        opt.size = 200, 50
        opt.update(user_opt)

        self.image = pygame.Surface((
            opt.size[0] + opt.thickness + opt.margin[0],
            opt.size[1] + opt.thickness + opt.margin[1]))
        self.rect = self.image.get_rect()

        pygame.draw.rect(self.image, opt.bordercolor,
                         self.rect.inflate(-opt.thickness,
                                           -opt.thickness),
                         opt.thickness)

        with origin(font, False) as font:
            r = font.get_rect(text, size=opt.fontsize)
            r.center = self.rect.center
            font.render_to(self.image, r, None, opt.fgcolor, opt.bgcolor,
                    opt.style, size=opt.fontsize)

    def event(self, e):
        return e.type == MOUSEBUTTONDOWN and e.button == 1 \
                and self.rect.collidepoint(e.pos)

    def __str__(self):
        return '<Button text={!r}>'.format(self.text)

    def __repr__(self):
        return self.__str__()


class ConfirmBox:

    def __init__(self, title, ok, cancel):
        self.title = title
        self.ok = ok
        self.cancel = cancel

    def __str__(self):
        return "<ConfirmBox {!r}>".format(self.title)

    def __repr__(self):
        return self.__str__()

