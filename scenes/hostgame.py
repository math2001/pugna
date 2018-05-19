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

        self.requestbox = self.m.gui.ConfirmBox(
            title="Someone wants to fight ya...", msg="Msg",
            ok=okbtn, cancel="Na...", font='ui',
            onsend=self.requestsend)

        self.messagebox = self.m.gui.MessageBox(
            title="Error", msg='Some message', ok=okbtn, font='ui',
            onsend=self.onmessageok, center=self.m.rect.center
        )

    async def on_focus(self):
        self.messagebox.setopt(msg="Hello world, this is mathieu paturel!\nyep!")
        self.m.gui.activate(self.messagebox)
        return
        self.server = Server(self.m.uuid, self.m.loop)

        self.m.state = STATE_CREATING

        self.m.client = await Client.new('localhost', PORT)

        self.m.state = STATE_STARTING
        await self.server.start(PORT)

        self.m.state = STATE_LOGGING
        self.task = self.m.schedule(self.client.login(self.m.uuid))

    async def requestsend(self, oked):
        if oked:
            self.task = self.m.client.accept_request()
            self.state = STATE_WAITING_SERVER
        else:
            self.state = STATE_WAITING_PLAYER
            self.task = self.m.client.refuse_request()


    def _task_exception(self, fut):
        exception = fut.exception()
        if not exception:
            return
        self.messagebox.setopt(title="Error")

    def schedule(self, coro):
        """A wrapper to handle exception raised by coroutines"""
        task = self.m.schedule(coro)
        task.add_done_callback(self._task_exception)
        return task

    async def onmessageok(self):
        """Called when the error popup ok btn has been clicked"""
        raise NotImplementedError("Do something depending on the state")

    async def update(self):
        return
        if self.task.done():

            res = self.task.result()
            if res.error is True:
                log.error(f"Got error: {res.msg!r}")
                self.messagebox.setopt(msg=res.msg)
                self.m.gui.activate(self.messagebox)
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


    async def on_blur(self, scene):
        await self.m.client
        await self.server.shutdown()
