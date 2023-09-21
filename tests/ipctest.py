from contextlib import asynccontextmanager
from subprocess import Popen
import pytest
import anyio
from anyio.streams.text import TextReceiveStream

from asway import Connection, CommandReply

import math
import os,sys,io
from random import random

from .window import Window

SWAY = bool(int(os.environ.get("USE_SWAY","0")))  # use SWAY
TMP = os.environ.get("XDG_RUNTIME_DIR",os.environ.get("TMPDIR","/tmp"))

class IpcTest:
    conn = None

    @asynccontextmanager
    async def run(self):
        sock = os.environ["SWAYSOCK"] = os.environ["I3SOCK"] = f"{TMP}/asway-test-{os.getpid()}"

        p = 'sway' if SWAY else 'i3'
        killed = False

        so = io.StringIO()
        se = io.StringIO()
        async def _cp(i,o):
            try:
                async for txt in TextReceiveStream(i):
                    o.write(txt)
            except anyio.ClosedResourceError:
                pass
        async def _run(tg, task_status):
            async with await anyio.open_process([p, '-c', f'tests/{p}.config']) as process:
                task_status.started(process)
                tg.start_soon(_cp,process.stdout,so)
                tg.start_soon(_cp,process.stderr,se)
            nonlocal killed
            if not killed and process.returncode != 0:
                raise RuntimeError(f"{p} died: {process.returncode}")

        try:
            async with anyio.create_task_group() as tg:
                process = await tg.start(_run, tg)

                try:
                    self.conn = Connection(socket_path=sock)
                    yield self
                finally:
                    if process.returncode is None:
                        killed = True
                        process.kill()
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

