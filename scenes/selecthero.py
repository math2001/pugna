import logging
import pygame
from pygame.locals import *
from constants import *
from utils.network import *
from utils.gui import word_wrap

log = logging.getLogger(__name__)

class SelectHero:

    async def on_focus(self, manager):
        self.m = manager
        # heros_description = dec(await readline(self.m.reader))
        heros_description = {
            "first": "wqer pweproi qnasdf qko anadf af pnapfdaf ",
            "second": "foasdfasdf",
            "third": "third third",
            "fourth": "tests",
            "fifth": "adsfpqwef adsf akjds fn[wqefkjdfnpqekrngj skdfjnu] sadfpadskj afdnasfiunwqefjnadfkjn df aune pernd sg puhreg sdfv",
            "asdfasdf": "wqer pweproi qnasdf qko anadf af pnapfdaf ",
            "wqer": "wqer pweproi qnasdf qko anadf af pnapfdaf ",
            "kmasd": "wqer pweproi qnasdf qko anadf af pnapfdaf ",
            "weqrqwer": "wqer pweproi qnasdf qko anadf af pnapfdaf ",
        }

        rect = self.m.fancyfont.get_rect("Who are you?")
        self.title, self.titlerect = self.m.fancyfont.render("Who are you",
                                                             size=60)
        self.titlerect.midtop = self.m.rect.midtop
        self.titlerect.top += 40

        self.cards = []
        cardrect = pygame.Rect(0, 0, 330, 150)

        # marge between between cards
        margin = 20
        # margin in the cards (just like CSS)
        padding = 10

        for name, description in heros_description.items():
            surface = pygame.Surface(cardrect.size)
            r = self.m.fancyfont.render_to(surface, (25, 15), name.upper(),
                                           size=15)
            paddedsurface = pygame.Surface(
                    cardrect.inflate(-padding * 2, -padding * 2 - r.height - 10).size)
            word_wrap(paddedsurface, description, self.m.uifont,
                fgcolor=TEXT_FG, bgcolor=None)
            surface.blit(paddedsurface, (10, r.bottom + 10))
            pygame.draw.rect(surface, (33, 33, 33), cardrect, 1)
            self.cards.append(surface)

        self.allcards = pygame.Surface((cardrect.width * 2 + margin,
            int(len(self.cards) / 2 + .5) * (cardrect.height + margin) - margin))
        self.allcardsrect = self.allcards.get_rect(centerx=self.m.rect.centerx)
        self.allcardsrect.top = self.titlerect.bottom + 40

        self.scrollspeed = 5
        self.originaltop = self.allcardsrect.top

        top = 0
        for i, s in enumerate(self.cards):
            left = 0
            if i % 2 == 1:
                left += cardrect.width + 20
            self.allcards.blit(s, (left, top))
            if i % 2 == 1:
                top += cardrect.height + 20

        self.clip = self.allcardsrect.clip(self.m.rect)

    async def event(self, e):
        if e.type == MOUSEBUTTONDOWN and self.clip.collidepoint(e.pos):
            if e.button == 5 \
                    and self.allcardsrect.top < self.originaltop:
                self.allcardsrect.top += self.scrollspeed
            elif e.button == 4 \
                    and self.allcardsrect.bottom > self.m.rect.bottom:
                self.allcardsrect.top -= self.scrollspeed

    async def render(self):
        self.m.screen.blit(self.title, self.titlerect)
        self.m.screen.set_clip(self.clip)
        self.m.screen.blit(self.allcards, self.allcardsrect)
        self.m.screen.set_clip(None)
