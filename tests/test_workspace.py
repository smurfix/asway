from .ipctest import i3

import pytest
import anyio
from asynci3 import Event, TickEvent


class TestWorkspace:
    async def on_workspace(self, e):
        await self.events.send(e)

    async def on_tick(self, e):
        await self.events.send(e)

    @pytest.mark.anyio
    async def test_workspace(self, i3):
        self.events,rd = anyio.create_memory_object_stream(3)
        async with i3.connect():
            await i3.command('workspace 0')
            await i3.subscribe([Event.WORKSPACE, Event.TICK])

            i3.on(Event.WORKSPACE_FOCUS, self.on_workspace)
            i3.on(Event.TICK, self.on_tick)

            await i3.send_tick()
            assert isinstance(await rd.receive(), TickEvent)
            assert isinstance(await rd.receive(), TickEvent)

            await i3.command('workspace 12')
            e = await rd.receive()

            workspaces = await i3.get_workspaces()

            assert len(workspaces) == 1
            ws = workspaces[0]
            assert ws.name == '12'

            assert e is not None
            assert e.current.name == '12'
