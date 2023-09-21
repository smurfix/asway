from .ipctest import i3

from asynci3 import Event

import pytest
import anyio


class TestWindow:
    @pytest.mark.anyio
    async def test_window_event(self, i3):
        event = None
        evt = anyio.Event()

        def on_window(e):
            nonlocal event
            event = e
            evt.set()

        async with i3.connect():
            await i3.subscribe([Event.WINDOW])
            i3.on(Event.WINDOW, on_window)

            async with i3.ipc.open_window():
                await evt.wait()

                assert event

            i3.off(on_window)

    @pytest.mark.anyio
    async def test_detailed_window_event(self, i3):
        events = []

        def on_window(e):
            events.append(e)

        async def generate_events():
            async with i3.ipc.open_window() as win1, i3.ipc.open_window() as win2:
                await i3.command(f'[id={win1}] kill; [id={win2}] kill')
                # TODO sync protocol
                await anyio.sleep(0.01)
                self.evt.set()

        async with i3.connect():
            await i3.subscribe([Event.WINDOW])

            i3.on(Event.WINDOW_NEW, on_window)
            async with anyio.create_task_group() as tg:
                self.evt = anyio.Event()
                tg.start_soon(generate_events)
                await self.evt.wait()
                i3.off(on_window)

                assert len(events)
                for e in events:
                    assert e.change == 'new'

                events.clear()

                i3.on(Event.WINDOW_FOCUS, on_window)

                tg.start_soon(generate_events)
                self.evt = anyio.Event()
                tg.start_soon(generate_events)
                await self.evt.wait()
                i3.off(on_window)

                assert len(events)
                for e in events:
                    assert e.change == 'focus'

    @pytest.mark.anyio
    async def test_detailed_window_event_decorator(self, i3):
        events = []
        evt = anyio.Event()

        async def generate_events():
            async with i3.ipc.open_window() as win1, i3.ipc.open_window() as win2:
                await anyio.sleep(0.2)
                await i3.command(f'[id={win1}] kill; [id={win2}] kill')
                # TODO sync protocol
                await anyio.sleep(0.2)
                evt.set()

        async with i3.connect():
            @i3.on(Event.WINDOW_NEW)
            @i3.on(Event.WINDOW_FOCUS)
            async def on_window(e):
                nonlocal events
                events.append(e)

            async with anyio.create_task_group() as tg:
                evt = anyio.Event()
                tg.start_soon(generate_events)
                await evt.wait()

                assert len(events)
                for e in events:
                    assert e.change in ['new', 'focus']
                assert len([e for e in events if e.change == 'new'])
                assert len([e for e in events if e.change == 'focus'])

                i3.off(on_window)

    @pytest.mark.anyio
    async def test_marks(self, i3):
        async with i3.connect():
            await i3.ipc.fresh_workspace()
            async with i3.ipc.open_window():
                await i3.command('mark foo')
                tree = await i3.get_tree()
                assert 'foo' in tree.find_focused().marks

    @pytest.mark.anyio
    async def test_resize(self, i3):

        async with i3.connect():
            ws1 = await i3.ipc.fresh_workspace()
            async with i3.ipc.open_window() as win:
                await i3.ipc.command_checked(f'[id="{win}"] floating enable')

                # XXX: uncomment and it will fail
                # ws2 = await i3.ipc.fresh_workspace()

                def height_width(c):
                    return c.rect.height + c.deco_rect.height, c.rect.width

                async def do_resize(h, w):
                    result = await i3.ipc.command_checked(f'[id="{win}"] resize set {w}px {h}px')

                size1 = 200, 250
                size2 = 350, 300

                await do_resize(*size1)
                con = (await i3.get_tree()).find_by_window(win)

                await do_resize(*size2)
                con2 = (await i3.get_tree()).find_by_window(win)

                assert height_width(con) == size1
                assert height_width(con2) == size2
