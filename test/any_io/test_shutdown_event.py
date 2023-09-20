from .ipctest import i3

import pytest
import anyio

import os
if os.environ.get("SWAYSOCK"):
    # Sway cannot restart; TODO test reloading or whatever
    pytestmark = pytest.mark.skip

import sys

class TestShutdownEvent:
    events = []

    async def restart_func(self, i3):
        print("REST",file=sys.stderr)
        await anyio.sleep(0.1)
        self.tg.start_soon(i3.command,'reload')

    def on_shutdown(self, e):
        print("ONS",e,file=sys.stderr)
        self.events.append(e)
        if len(self.events) == 1:
            self.tg.start_soon(self.restart_func, i3)
        elif len(self.events) == 2:
            self.evt.set()

    @pytest.mark.anyio
    async def test_shutdown_event_reconnect(self, i3):
        async with i3.connect(), anyio.create_task_group() as self.tg:
            self.evt = anyio.Event()
            i3._auto_reconnect = True
            self.events = []
            i3.on('shutdown::restart', self.on_shutdown)
            self.tg.start_soon(self.restart_func, i3)
            await self.evt.wait()
            assert len(self.events) == 2
