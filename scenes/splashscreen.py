import pygame.color
import pygame

class SplashScreen:

    """Gives you this nice little animation at the beginning"""

    TITLE_SIZE = 150
    TITLE = 'PUGNA'

    SUBTITLE = 'Get ready for fighting, pain, death, and worse.'
    SUBTITLE_SIZE = 25

    def __init__(self, manager):
        self.m = manager
        self.size = 295

        self.title_color = pygame.Color(0, 0, 0, 255)
        self.state = 0

    async def render(self):
        self.m.screen.fill(0)
        if self.state >= 1:
            tr = self.m.fancyfont.get_rect(self.TITLE, size=self.TITLE_SIZE)
            tr.center = self.m.rect.center
            tr.top -= 50
            self.m.fancyfont.render_to(self.m.screen, tr, None,
                                       size=self.TITLE_SIZE,
                                       fgcolor=self.title_color)

        if self.state >= 2:
            sr = self.m.fancyfont.get_rect(self.SUBTITLE,
                                           size=self.SUBTITLE_SIZE)
            sr.midtop = tr.midbottom
            sr.top += 20
            self.m.fancyfont.render_to(self.m.screen, sr, None,
                                       size=self.SUBTITLE_SIZE,
                                       fgcolor=pygame.Color(150, 150, 150, 255))

    async def update(self):
        title = 10
        color = 255 // 2

        if self.m.frames_count == title:
            self.state = 1

        if self.state == 1 and self.m.frames_count < title + color:
            self.title_color += pygame.Color(2, 2, 2, 255)

        if self.m.frames_count == title + color:
            self.state = 2

    async def on_event(self, e):
        if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.m.schedule(self.m.focus('Menu'))
