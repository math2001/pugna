import pygame
from constants import *
from utils.gui import Button, Options

class Menu:

    menubtn = False

    async def on_focus(self, manager):
        self.m = manager

        self.title = self.m.fancyfont.render("PUGNA",
                                             fgcolor=TEXT_HOVER_FG,
                                             size=150)
        self.title[1].midtop = self.m.rect.midtop
        self.title[1].top += 50

        opts = Options(thickness=1, width=300, height=60,
                       hover_fgcolor=TEXT_HOVER_FG,
                       hover_bordercolor=pygame.Color("tomato"))
        self.buttons = []
        top = self.title[1].bottom + 100
        for s in ['Host game', 'Join game', 'About', 'Quit']:
            b = Button(self.m.fancyfont, s, opts)
            b.rect.centerx = self.m.rect.centerx
            b.rect.top = top
            top += b.rect.height + 20
            self.buttons.append(b)

    async def event(self, e):
        for btn in self.buttons:
            if btn.event(e):
                if btn.text == "Quit":
                    return self.m.quit()
                await self.m.focus(btn.text)

    async def render(self):
        self.m.screen.blit(*self.title)
        for btn in self.buttons:
            btn.render(self.m.screen)

