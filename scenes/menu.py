import pygame
from utils.gui import Button, Options

class Menu:

    def on_focus(self, manager):
        self.m = manager

        self.title = self.m.fancyfont.render("PUGNA", size=150)
        self.title[1].midtop = self.m.rect.midtop
        self.title[1].top += 50

        opts = Options(thickness=0, margin=(10, 10))
        buttons = []
        top = self.title[1].bottom + 100
        for s in ['Host game', 'Join game', 'About']:
            b = Button(self.m.fancyfont, s, opts)
            b.rect.centerx = self.m.rect.centerx
            b.rect.top = top
            top += b.rect.height + 20
            buttons.append(b)
        self.buttonsprites = pygame.sprite.RenderPlain(buttons)

    def event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN:
            for btn in self.buttonsprites.sprites():
                if btn.mouseevent(e):
                    self.m.focus(btn.text.title().replace(" ", ""))


    def render(self):
        self.m.screen.blit(*self.title)
        self.buttonsprites.draw(self.m.screen)

