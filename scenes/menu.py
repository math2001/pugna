import pygame
from utils.gui import Button, Options

class Menu:

    def on_focus(self, manager):
        self.m = manager

        self.title = self.m.fancyfont.render("PUGNA", size=150)
        self.title[1].midtop = self.m.rect.midtop
        self.title[1].top += 10

        opts = Options(thickness=0)
        self.buttons = []
        for s in ['Host game', 'Join game', 'About']:
            self.buttons.append(Button(self.m.fancyfont, s, opts))
            break
        # self.buttonsprites = pygame.sprite.RenderPlain(buttons)

    def render(self):
        self.m.screen.blit(*self.title)
        # self.buttonsprites.draw(self.m.screen)
        self.m.screen.blit(self.buttons[0].image, self.buttons[0].rect)

