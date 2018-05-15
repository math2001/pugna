import pygame

class Menu:

    def __init__(self, m):
        self.m = m

        top = 50

        self.btns = []
        for txt in ['host game', 'join game', 'about']:
            btn = self.m.gui.Button(txt, onclick=self.btnclick,
                                    onmouseenter=self.btnmouseenter,
                                    onmouseleave=self.btnmouseleave,
                                    font='fancy', paddingy=40, width=250,
                                    centerx=self.m.rect.centerx, top=top)
            top += 70

    async def on_focus(self):
        pass

    async def btnclick(self, btn, e):
        print(f'Clicked on a button: {btn} {e}')

    async def btnmouseenter(self, btn, e):
        btn.setopt(bordercolor=pygame.Color("Tomato"))

    async def btnmouseleave(self, btn, e):
        btn.setopt(bordercolor=pygame.Color(30, 30, 30))
