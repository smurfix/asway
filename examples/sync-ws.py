#!/usr/bin/env python3

import asway
import anyio
import math

class SyncWS:
    switching = True

    def __init__(self, wm):
        self.wm = wm
        self.tick = 92837  # TODO
        self.screens = set()
        self.cur_name = None

    # this assumes that workspaces are named "somename-theirscreen".
    def split_name(self, ws):
        return ws.name.rsplit("-",1)
    def gen_name(self, name, screen):
        return f"{name}-{screen}"

    def get_nr(self, ws):
        i = ws.name.index("-")
        return ws.name[:i]

    async def run(self):
        self.switching = True
        async with anyio.create_task_group() as self.tg:
            try:
                self.wm.on(asway.Event.WORKSPACE_FOCUS, self.on_switch)
                self.wm.on(asway.Event.TICK, self.on_tick)
                ws = await self.wm.get_workspaces()
                cur = None
                for w in ws:
                    try:
                        name,screen = self.split_name(w)
                    except ValueError:
                        pass
                    else:
                        self.screens.add(screen)
                        if w.focused:
                            self.cur_name = name
                            cur = w

                if cur is None:
                    raise RuntimeError("No focused workspace?")
                self.tg.start_soon(self.switched_to, cur, True)
                await anyio.sleep(math.inf)
            finally:
                self.wm.off(self.on_switch)
                self.wm.off(self.on_tick)
    
    async def switched_to(self, ws, force=False, task_status=None):
        if task_status is not None:
            task_status.started()
        if self.switching and not force:
            return
        self.switching = anyio.Event()
        try:
            name,screen = self.split_name(ws)
            self.cur_name = name
            for s in self.screens:
                if s == screen:
                    continue
                await self.wm.command(f"workspace {name}-{s}")
            await self.wm.command(f"workspace {name}-{screen}")
            await self.wm.send_tick(str(self.tick))
            await self.switching.wait()

        finally:
            self.switching = None

    async def on_tick(self, e):
        try:
            if int(e.payload) != self.tick:
                return
        except ValueError:
            return
        if self.switching is not None:
            self.switching.set()

    async def on_switch(self, e):
        if self.switching:
            return
        if self.cur_name != e.current.name:
            await self.tg.start(self.switched_to,e.current)


if __name__ == "__main__":

    async def main():
        async with asway.Connection() as wm:
            # otherwise this will be an exercise in frustration
            await wm.command("mouse_warping none")

            sw = SyncWS(wm)
            await sw.run()

    anyio.run(main)
