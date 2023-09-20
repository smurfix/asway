from .ipctest import i3

import pytest
import anyio


class TestTicks:
    events = []

    async def on_tick(self, e):
        self.events.append(e)
        if len(self.events) == 3:
            self.evt.set()

    @pytest.mark.anyio
    async def test_tick_event(self, i3):
        async with i3.connect():
            i3.on('tick', self.on_tick)
            self.evt = anyio.Event()
            await anyio.sleep(0.2)

            await i3.send_tick()
            await i3.send_tick('hello world')
            await self.evt.wait()

            assert len(self.events) == 3
            assert self.events[0].first
            assert self.events[0].payload == ''
            assert not self.events[1].first
            assert self.events[1].payload == ''
            assert not self.events[2].first
            assert self.events[2].payload == 'hello world'
