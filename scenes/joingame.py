import logging
import pygame
from constants import *
from utils.client import Client, Response
from constants import *

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

STATE_INPUT = 'Waiting for user input'
STATE_OPENING_CO = 'Opening connection'
STATE_WAITING_OWNER = 'Waiting for the owner\'s response'
STATE_ERROR = 'Looks like an error occurred'

class JoinGame:

    def __init__(self, m):
        self.m = m

        self.input = self.m.gui.Input(initialtext='192.168.1.',
                                      onsend=self.onsend)

        iwidth = self.input.rect.width

        self.send = self.m.gui.Button(text='Send request',
                                    centerx=self.input.rect.centerx,
                                    top=self.input.rect.bottom + 10,
                                    onsend=self.onsend)

        kwidth = self.send.rect.width

        width = iwidth + kwidth + 10
        top = 100

        self.input.setbounds(left=self.m.rect.centerx - width / 2,
                             top=top)
        self.send.setbounds(left=self.input.rect.right + 10,
                          top=top)
        self.send.savestate('disabled', fg=TEXT_DISABLED_FG, onmouseenter=None,
                          onmouseleave=None, text='Sending request...',
                          onsend=None)
        self.send.savestate('normal')

        ok = self.m.gui.Button(text='Oh! Ok...')
        self.messagebox = self.m.gui.MessageBox(center=self.m.rect.center,
                                                ok=ok, onsend=self.onmsgboxsend,
                                                height=240)

        self.task = None

    async def on_focus(self):
        self.m.state = STATE_INPUT
        self.m.gui.activate(self.input, self.send)

    async def on_blur(self, scene):
        self.m.gui.deactivate(self.input, self.send)

    def handle_exception(self, response):
        self.messagebox.setopt(msg=response.msg,
                               titlecolor=pygame.Color('tomato'),
                               title='Error')
        self.m.gui.activate(self.messagebox)

    async def onsend(self, element, e):
        self.m.state = STATE_OPENING_CO
        self.task = self.m.schedule(Client.new(self.input.text, PORT))
        self.send.applystate('disabled')

    async def onmsgboxsend(self, element, e):
        """We have displayed an error and the user clicked 'ok' """
        self.m.state = STATE_INPUT
        self.task = None
        self.m.gui.deactivate(self.messagebox)
        self.send.applystate('normal')

    async def update(self):
        if self.task is None or not self.task.done():
            return

        res = self.task.result()

        if self.m.state == STATE_OPENING_CO:
            if isinstance(res, Response):
                # we have an exception
                self.m.state = STATE_ERROR
                self.handle_exception(res)
                self.task = None
                return
            self.m.state = STATE_WAITING_OWNER
            self.task = self.m.schedule(self.m.client.newrequest())

    def render(self):
        self.m.fancyfont.size = TITLE_SIZE
        r = self.m.writetext('fancy', 'Join a game', centerx='centerx', top=20)

        # display the state
        self.m.uifont.origin = True
        rect = self.m.writetext('ui', self.m.state, top=self.m.rect.bottom - 20,
                                centerx='centerx')

        self.m.writetext('ui', '.' * self.m.animdots, left=rect.right + 2,
                         top=rect.top)
