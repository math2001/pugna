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
            self.cards.append((surface, cardrect.copy()))

        self.allcards = pygame.Surface((cardrect.width * 2 + margin,
            int(len(self.cards) / 2 + .5) * (cardrect.height + margin) - margin))
        self.allcardsrect = self.allcards.get_rect(centerx=self.m.rect.centerx)
        self.allcardsrect.top = self.titlerect.bottom + 40

        self.scrollspeed = 5
        self.originaltop = self.allcardsrect.top

        top = 0
        for i, (s, r) in enumerate(self.cards):
            if i % 2 == 1:
                r.left = cardrect.width + 20
            r.top = top
            self.allcards.blit(s, r)
            if i % 2 == 1:
                top += cardrect.height + 20

        self.clip = self.allcardsrect.clip(self.m.rect)
        self.hovered = None

    async def event(self, e):
        # we check only clicks in the hero selector, and we shouldn't
        # be able to click hero that aren't in clipped area (that we already
        # scrolled)
        if e.type not in (MOUSEMOTION, MOUSEBUTTONDOWN):
            return
        if not self.clip.collidepoint(e.pos):
            self.hovered = None
            return
        checkcollide = False
        if e.type == MOUSEBUTTONDOWN:
            if e.button == 5 \
                    and self.allcardsrect.top < self.originaltop:
                self.allcardsrect.top += self.scrollspeed
                if self.hovered:
                    self.hovered.top += self.scrollspeed
                checkcollide = True
            elif e.button == 4 \
                    and self.allcardsrect.bottom > self.m.rect.bottom:
                self.allcardsrect.top -= self.scrollspeed
                if self.hovered:
                    self.hovered.top -= self.scrollspeed
                checkcollide = True

        if e.type == MOUSEMOTION or checkcollide:
            self.hovered = None
            for _, r in self.cards:
                r = r.move(self.allcardsrect.topleft)
                if r.collidepoint(e.pos):
                    self.hovered = r

    async def render(self):
        self.m.screen.blit(self.title, self.titlerect)
        self.m.screen.set_clip(self.clip)
        self.m.screen.blit(self.allcards, self.allcardsrect)
        if self.hovered:
            pygame.draw.rect(self.m.screen, pygame.Color('red'), self.hovered, 1)
        self.m.screen.set_clip(None)
