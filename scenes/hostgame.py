import socket
import pygame
import logging
from server import Server
from utils.client import *
from constants import *

log = logging.getLogger(__name__)

STATE_CREATING = 'Creating the server'
STATE_STARTING = 'Starting the server'
STATE_LOGGING = 'Logging into the server'
STATE_WAITING_PLAYER = 'Waiting for an other player to join'
STATE_WAITING_INPUT = 'Waiting for user input'
STATE_WAITING_SERVER = 'Waiting for the server'
STATE_ERROR = 'An error has occurred'

class HostGame:

    def __init__(self, m):
        self.m = m

        okbtn = self.m.gui.Button(text="Let's get fighting")
        cancelbtn = self.m.gui.Button(text='Na. Too scared')

        self.requestbox = self.m.gui.ConfirmBox(
            title="Defi!",
            msg="{username} wants to fight you to death",
            ok=okbtn.copy(), cancel=cancelbtn,
            onsend=self.requestsend, center=self.m.rect.center)

        okbtn = self.m.gui.Button(text='Hum... Ok')

        self.messagebox = self.m.gui.MessageBox(
            title="Error", msg='Some message', ok=okbtn, font='ui',
            onsend=self.onmessageok, center=self.m.rect.center,
            width=400, height=240
        )

    async def on_focus(self):
        self.localip = socket.gethostbyname(socket.gethostname())

        self.m.state = STATE_CREATING
        self.server = Server(self.m.uuid, self.m.loop)

        self.m.state = STATE_STARTING
        await self.server.start(PORT)

        self.m.client = await Client.new('localhost', PORT)

        self.m.state = STATE_LOGGING
        self.task = self.m.schedule(self.m.client.login(self.m.username,
                                                        self.m.uuid))

    async def requestsend(self, ok, element, event):
        if ok:
            self.task = self.m.client.accept_request()
            self.state = STATE_WAITING_SERVER
        else:
            self.state = STATE_WAITING_PLAYER
            self.task = self.m.client.refuse_request()

    def _task_exception(self, fut):
        print("!!!!!!!!!!!!!!!!! called")
        exception = fut.exception()
        if not exception:
            return
        self.messagebox.setopt(title="Error")

    async def onmessageok(self, element, e):
        """Called when the error popup ok btn has been clicked"""
        raise NotImplementedError("Do something depending on the state")

    async def update(self):
        # if task is None, this means that an error has occured and no task is
        # currently running (the error is being displayed)
        if self.task is None or not self.task.done():
            return
        res = self.task.result()
        if res.error is True:
            self.messagebox.setopt(msg=res.msg)
            self.m.gui.activate(self.messagebox)
            self.task = None
            return

        if self.m.state == STATE_LOGGING:
            if res.accepted is False:
                log.critical(f"Could not login to the server: {res!r}")
                self.m.errorbox.setopt(msg=res.msg)
                self.m.gui.activate(self.errorbox)
                return

            self.m.state = STATE_WAITING_PLAYER
            self.task = self.m.schedule(self.m.client.findplayer())

        elif self.m.state == STATE_WAITING_PLAYER:
            self.m.state = STATE_WAITING_INPUT
            self.requestbox.setopt(msg=f'{res.by} wants to play with you!')
            self.m.gui.activate(self.requestbox)

    def render(self):
        self.m.fancyfont.size = 80
        rect = self.m.writetext('fancy', 'Hosting a game', top=20,
                                centerx='centerx')

        rect = self.m.writetext('ui', 'Your local IP is:', top=rect.bottom + 50,
                                centerx='centerx')

        self.m.uifont.size = 40
        rect = self.m.writetext('ui', self.localip, top=rect.bottom + 20,
                                centerx='centerx')

        # render the state
        self.m.uifont.origin = True
        self.m.uifont.size = 20
        rect = self.m.writetext('ui', self.m.state, top=self.m.rect.bottom - 20,
                                centerx='centerx')

        self.m.writetext('ui', '.' * self.m.animdots, left=rect.right + 2,
                         top=rect.top)

    async def on_blur(self, scene):
        self.m.client.shutdown()
        await self.server.shutdown()
        self.m.gui.deactivate(self.requestbox)
        self.m.gui.deactivate(self.messagebox)
