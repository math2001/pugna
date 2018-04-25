import pygame
import pygame.freetype
from pygame.locals import *

class Options(dict):

    def __init__(self, **kwargs):
        self.update(kwargs)

    def __getattr__(self, attr):
        return self[attr]

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
            elif e.unicode != '\r':
                self.text += e.unicode

    def render(self):
        surface = pygame.Surface((self.opt.size[0] + self.opt.thickness,
                                 self.opt.size[1] + self.opt.thickness))
        rect = surface.get_rect()
        bordercolor = self.opt.bordercolor if self.focused \
                      else self.opt.focusedbordercolor
        pygame.draw.rect(surface, bordercolor, rect,
                         self.opt.thickness)
        origin = (rect.left + self.opt.margin[0],
                 rect.bottom - self.opt.margin[1])
        self.font.render_to(surface, origin, self.text,
                            self.opt.fgcolor, self.opt.bgcolor, self.opt.style,
                            size=self.opt.fontsize)
        return surface, rect

class Button(pygame.sprite.Sprite):

    '''not working yet'''

    def __init__(self, font, text, onclick, opt):
        pygame.sprite.Sprite.__init__(self)

        default_opt = Options()
        default_opt.margin = 3, 5
        default_opt.thickness = 1
        default_opt.bordercolor = 33, 33, 33
        default_opt.fgcolor = 33, 33, 33
        default_opt.bgcolor = None
        default_opt.style = STYLE_DEFAULT
        opt = default_opt.update(opt)

        self.rect = font.get_size(text).inflate(opt.margin[0] + opt.thickness, opt.margin[1] + opt.thickness)
        self.image = pygame.Surface(self.rect)
        pygame.draw.rect(self.image, opt.bordercolor, self.rect.inflate(-opt.thickness, -opt.thickness), opt.thickness)

        surface, rect = font.render(text, opt.fgcolor, opt.bgcolor, opt.style)
        rect.center = self.rect.center
        self.image.blit(surface, rect)

    def mouseevent(self, e):
        if e.type == MOUSEBUTTONDOWN and e.button == 1 and self.rect.collidepoint(e.pos):
            self.onclick()

