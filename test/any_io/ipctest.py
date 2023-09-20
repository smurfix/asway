from contextlib import asynccontextmanager
from subprocess import Popen
import pytest
import anyio

from i3ipc.anyio import Connection
from i3ipc import CommandReply

import math
import os,sys
from random import random

from .window import Window

SWAY = bool(int(os.environ.get("USE_SWAY","0")))  # use SWAY
TMP = os.environ.get("XDG_RUNTIME_DIR",os.environ.get("TMPDIR","/tmp"))

class IpcTest:
    conn = None

    @asynccontextmanager
    async def run(self):
        sock = os.environ["SWAYSOCK"] = os.environ["I3SOCK"] = f"{TMP}/i3ipc-test-{os.getpid()}"

        try:
            p = 'sway' if SWAY else 'i3'
            async with await anyio.open_process([p, '-c', f'test/{p}.config']) as process:

                # wait for i3 to start up
                #async with Connection().connect() as IpcTest.i3_conn:
                if True:
                    try:
                        #yield IpcTest.i3_conn
                        self.conn = Connection()
                        yield self
                    finally:
#                       try:
#                           tree = await IpcTest.i3_conn.get_tree()
#                           for l in tree.leaves():
#                               await l.command('kill')
#                           await IpcTest.i3_conn.command('exit')
#                       except OSError:
#                           pass
#                       finally:
                            process.kill()
#                           await process.wait()
        finally:
            self.conn = None
            try:
                os.unlink(sock)
            except OSError:
                pass

    async def command_checked(self, cmd):
        i3 = self.conn
        assert i3

        result = await i3.command(cmd)

        assert type(result) is list
        assert result

        for r in result:
            assert type(r) is CommandReply
            assert r.success is True, r.error

        return result

    @asynccontextmanager
    async def open_window(self):
        window = Window()
        async with anyio.create_task_group() as tg:
            yield await tg.start(window.run, self.conn)
            tg.cancel_scope.cancel()

    async def fresh_workspace(self):
        i3 = self.conn
        assert i3

        workspaces = await i3.get_workspaces()
        while True:
            new_name = str(math.floor(random() * 100000))
            if not any(w for w in workspaces if w.name == new_name):
                await i3.command('workspace %s' % new_name)
                return new_name

@pytest.fixture # (scope='class')
async def i3():
    ipc = IpcTest()
    async with ipc.run():
        try:
            conn = ipc.conn
            conn.ipc = ipc
            yield conn
        finally:
            conn.ipc = None

