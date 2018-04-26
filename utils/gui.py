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

def word_wrap(surf, text, font, opt):
    """Stolen from the pygame documentation freetype.Font.render_to"""
    font.origin = True
    words = text.split(' ')
    width, height = surf.get_size()
    line_spacing = font.get_sized_height() + 2
    x, y = 0, line_spacing
    space = font.get_rect(' ')
    for word in words:
        bounds = font.get_rect(word)
        if x + bounds.width + bounds.x >= width:
            x, y = 0, y + line_spacing
        if x + bounds.width + bounds.x >= width:
            raise ValueError("word too wide for the surface")
        if y + bounds.height - bounds.y >= height:
            raise ValueError("text to long for the surface")
        font.render_to(surf, (x, y), opt.bgcolor, opt.fgcolor)
        x += bounds.width + space.width
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

    """A simple button
    Nothing fancy here... Notice that when the height/width is explicit
    the margin for that specific option isn't taken into account, and the
    border are drawn *inside* the button (so that the actually button size
    is the size you wanted)
    Make sure you put the rect (btn.rect) where you want it and render it!
    (s.blit(btn.image, btn.rect) or with pygame.sprite.Sprite)
    Call event() with the an Event, and it'll return True if the user clicked
    on it.
    """

    def __init__(self, font, text, useropt={}):
        pygame.sprite.Sprite.__init__(self)
        self.text = text

        opt = Options()
        opt.margin = 20, 10
        opt.thickness = 0
        opt.bordercolor = 33, 33, 33
        opt.fgcolor = font.fgcolor
        opt.bgcolor = None
        opt.fontsize = font.size
        opt.style = pygame.freetype.STYLE_DEFAULT
        # if theses are None, they are automatically generated
        opt.width = None
        opt.height = None
        opt.update(useropt)

        fontrect = font.get_rect(text)
        width = opt.width
        height = opt.height
        if opt.width is None:
            width = fontrect.width + opt.margin[0] + opt.thickness
        if opt.height is None:
            height = fontrect.height + opt.margin[1] + opt.thickness
        self.image = pygame.Surface((width, height))
        self.rect = self.image.get_rect()

        fontrect.center = self.rect.center

        pygame.draw.rect(self.image, opt.bordercolor,
                    self.rect.inflate(-opt.thickness * 2, -opt.thickness * 2),
                    opt.thickness)

        font.render_to(self.image, fontrect, text, opt.fgcolor, opt.bgcolor,
                       opt.style, size=opt.fontsize)

    def event(self, e):
        return e.type == MOUSEBUTTONDOWN and e.button == 1 \
                and self.rect.collidepoint(e.pos)

    def __str__(self):
        return '<Button text={!r}>'.format(self.text)

    def __repr__(self):
        return self.__str__()


class ConfirmBox:

    """Creates a little popup
    Place the cb.rect where you want it and render with s.blit(cb.image, cb.rect)
    Call event() with an Event and it'll return True if the user cliked ok and 
    return False if the user clicked cancel
    """

    @classmethod
    def new(cls, font, title, ok, cancel, useropt={}):
        """A shortcut to automatically create the buttons from text"""
        return cls(font, title, Button(font, ok), Button(font, cancel), useropt)

    def __init__(self, font, title, ok, cancel, useropt={}):
        self.ok = ok
        self.cancel = cancel

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
        word_wrap(text, title, font, opt)
        self.image.blit(text, opt.margin)

        pygame.draw.rect(self.image, opt.bordercolor,
                         self.rect.inflate(-opt.thickness * 2, -opt.thickness * 2),
                         opt.thickness)

        ok.rect.bottomright = pygame.math.Vector2(self.rect.bottomright) \
                              - pygame.math.Vector2(opt.margin)
        self.image.blit(ok.image, ok.rect)

        cancel.rect.midright = ok.rect.midleft
        cancel.rect.left -= 10
        self.image.blit(cancel.image, cancel.rect)

    def event(self, e):
        if e.type == MOUSEBUTTONDOWN:
            if self.ok.event(e):
                return True
            if self.cancel.event(e):
                return False

    def __str__(self):
        return f"<ConfirmBox {self.title!r}>"

    def __repr__(self):
        return self.__str__()

