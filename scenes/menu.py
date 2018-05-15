class Menu:

    def __init__(self, m):
        self.m = m

        top = 50

        self.btns = []
        for txt in ['host game', 'join game', 'about']:
            btn = self.m.gui.Button(txt, onclick=self.clickbtn)
            btn.centerx = self.m.rect.centerx
            btn.top = top
            top += 20

    async def on_focus(self):
        pass

    async def clickbtn(self, btn, e):
        print(f'Clicked on a button: {btn} {e}')

