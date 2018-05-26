from heros import HEROS
from pygame import Color, Rect, Surface
from pygame.locals import *
from pygame.draw import rect as drect
from utils.gui import word_wrap

class SelectHero:

    def __init__(self, m):
        self.m = m
        self.task = None
        ok = self.m.gui.Button(text='Oh no!')
        self.messagebox = self.m.gui.MessageBox(title='Error',
                                                titlecolor=Color("tomato"),
                                                center=self.m.rect.center,
                                                ok=ok)
        self.heros = {
            # name: description
        }

        self.title = self.m.fancyfont.render("Who are you?", size=60)
        self.title[1].midtop = self.m.rect.midtop
        self.title[1].top += 40

    async def on_focus(self):
        self.m.state = 'Loading heros'
        # self.task = self.m.schedule(self.m.client.get_heros_names())
        # debug
        async def getheros():
            from utils.client import Response
            return Response(names=list(HEROS.keys()))
        self.task = self.m.schedule(getheros())

    async def update(self):
        if self.task is None or not self.task.done():
            return

        self.m.state = 'Waiting for user input'
        result = self.task.result()
        self.task = None
        if result.error:
            self.messagebox.setopt(msg=result.msg)
            self.m.gui.activate(self.messagebox)
            return
        for name in result.names:
            self.heros[name] = HEROS[name].description

        self.agence_cards()

    def agence_cards(self):
        """Creates and puts the cards at the right place"""

        self.cards = []
        cardrect = Rect(0, 0, 330, 150)

        # marge between the cards
        margin = 20
        # margin in the cards (just like CSS)
        padding = 10

        # render every card and add it the self.cards
        for name, description in self.heros.items():
            surf = Surface(cardrect.size)
            rect = self.m.fancyfont.render_to(surf, (padding, 15), name.upper(),
                                              size=15)
            paddedsurf = Surface(cardrect.inflate(padding * -2,
                                                  padding * -2 - rect.height \
                                                  - 10).size)
            word_wrap(paddedsurf, self.m.uifont, description)
            surf.blit(paddedsurf, (padding, rect.bottom + padding))
            drect(surf, (33, 33, 33), cardrect, 1)
            self.cards.append((name, surf, cardrect.copy()))

        self.cardscontainer = Surface((cardrect.width * 2 + margin,
                                       int(len(self.cards) / 2 + .5) \
                                       * (cardrect.height + margin) - margin))

        self.ccrect = self.cardscontainer.get_rect(centerx=self.m.rect.centerx)
        self.ccrect.top = self.title[1].bottom + 40

        self.originaltop = self.ccrect.top

        top = 0
        for i, (name, surf, rect) in enumerate(self.cards):
            # if it's a second card, we display it on the right
            if i % 2 == 1:
                rect.left = cardrect.width + margin
            rect.top = top
            self.cardscontainer.blit(surf, rect)
            if i % 2 == 1:
                top += cardrect.height + margin

        self.scrollspeed = 10
        self.clip = self.ccrect.clip(self.m.rect)
        self.clip.height -= 50
        self.hovered = None

    async def on_event(self, e):
        # returns if we're loading the heros as well
        if e.type not in (MOUSEMOTION, MOUSEBUTTONDOWN) or not self.heros:
            return

        # if we're not in the clip (the scrollable area) return
        if not self.clip.collidepoint(e.pos):
            self.hovered = None
            return

        clicked = scrolled = False
        if e.type == MOUSEBUTTONDOWN:
            # scroll
            if e.button == 4 and self.ccrect.top < self.originaltop:
                scrolled = True
                self.ccrect.top += self.scrollspeed
                # scroll the hover rect as well
                if self.hovered:
                    self.hovered.top += self.scrollspeed
            elif e.button == 5 and self.ccrect.bottom > self.clip.bottom:
                scrolled = True
                self.ccrect.top -= self.scrollspeed
                if self.hovered:
                    self.hovered.top -= self.scrollspeed

            elif e.button == 1:
                clicked = True

        if e.type == MOUSEMOTION or scrolled:
            self.hovered = None
            for name, _, rect in self.cards:
                # move the rect relative to the scroll of the container
                r = rect.move(self.ccrect.topleft)
                if not r.collidepoint(e.pos):
                    continue
                self.hovered = r
                if clicked:
                    self.chose_hero(name)

    def render(self):
        self.m.screen.blit(*self.title)
        if self.heros:
            self.m.screen.set_clip(self.clip)
            self.m.screen.blit(self.cardscontainer, self.ccrect)
            if self.hovered:
                drect(self.m.screen, Color("tomato"), self.hovered, 1)
            self.m.screen.set_clip(None)

        # display the state
        self.m.uifont.origin = True
        rect = self.m.writetext('ui', self.m.state, top=self.m.rect.bottom - 20,
                                centerx='centerx')

        self.m.writetext('ui', '.' * self.m.animdots, left=rect.right + 2,
                         top=rect.top)
