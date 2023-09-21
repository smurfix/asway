from Xlib import X, Xutil
from Xlib.display import Display
from functools import partial

import anyio
import os

seq = 0

class Window(object):
    def __init__(self, display=None):
        self.display = display
        self.name = None

    def _create(self):
        display = self.display
        if display is None:
            display = Display()

        self.d = display
        self.screen = self.d.screen()
        bgsize = 20
        bgpm = self.screen.root.create_pixmap(bgsize, bgsize, self.screen.root_depth)
        bggc = self.screen.root.create_gc(foreground=self.screen.black_pixel,
                                          background=self.screen.black_pixel)
        bgpm.fill_rectangle(bggc, 0, 0, bgsize, bgsize)
        bggc.change(foreground=self.screen.white_pixel)
        bgpm.arc(bggc, -bgsize // 2, 0, bgsize, bgsize, 0, 360 * 64)
        bgpm.arc(bggc, bgsize // 2, 0, bgsize, bgsize, 0, 360 * 64)
        bgpm.arc(bggc, 0, -bgsize // 2, bgsize, bgsize, 0, 360 * 64)
        bgpm.arc(bggc, 0, bgsize // 2, bgsize, bgsize, 0, 360 * 64)

        self.window = self.screen.root.create_window(100,
                                                     100,
                                                     400,
                                                     300,
                                                     0,
                                                     self.screen.root_depth,
                                                     X.InputOutput,
                                                     X.CopyFromParent,
                                                     background_pixmap=bgpm,
                                                     event_mask=(X.StructureNotifyMask
                                                                 | X.ButtonReleaseMask),
                                                     colormap=X.CopyFromParent)

        self.WM_DELETE_WINDOW = self.d.intern_atom('WM_DELETE_WINDOW')
        self.WM_PROTOCOLS = self.d.intern_atom('WM_PROTOCOLS')

        self.name = f'i3 test window {self.seq}'
        self.window.set_wm_name(self.name)
        self.window.set_wm_class('i3win', 'i3win')

        self.window.set_wm_protocols([self.WM_DELETE_WINDOW])
        self.window.set_wm_hints(flags=Xutil.StateHint, initial_state=Xutil.NormalState)

        self.window.set_wm_normal_hints(flags=(Xutil.PPosition | Xutil.PSize | Xutil.PMinSize),
                                        min_width=50,
                                        min_height=50)

        self.window.map()
        display.flush()

    async def run(self, i3, task_status):
        def loop(evt=None):
            self._create()
            if evt:
                anyio.from_thread.run_sync(evt.set)
            while self.window:
                e = self.d.next_event()
                if self.window is None:
                    break

                if e.type == X.DestroyNotify:
                    break

                elif e.type == X.ClientMessage:
                    if e.client_type == self.WM_PROTOCOLS:
                        fmt, data = e.data
                        if fmt == 32 and data[0] == self.WM_DELETE_WINDOW:
                            self.window.destroy()
                            self.window = None
                            self.d.flush()
                            break

        def kill():
            w, self.window = self.window,None
            if w is not None:
                w.destroy()

        # let's find our DISPLAY envvar
        global seq
        seq += 1
        self.seq = seq

        tmp = os.environ.get("XDG_RUNTIME_DIR","/tmp")
        tf = f"{tmp}/sway.test.{os.getpid()}.display.{self.seq}"
        await i3.command(f'exec "echo $DISPLAY > {tf}"')
        for i in range(10):
            if os.path.exists(tf):
                break
            await anyio.sleep(0.2)
        else:
            raise RuntimeError("no DISPLAY found")
        with open(tf,"r") as tff:
            disp = tff.read().strip()
        os.unlink(tf)
        os.environ["DISPLAY"] = disp

        async def _watch(evt, task_status):
            n = 0
            @i3.on("window")
            def win(w):
                nonlocal n
                if self.name is None:
                    return
                if w.container.window_title != self.name:
                    return
                if w.change == "title":
                    n |= 1
                if w.change == "focus":
                    n |= 2
                if n == 3:
                    evt.set()
                pass
            task_status.started()
            await evt.wait()
            i3.off(win)
            
        async with anyio.create_task_group() as tg:
            evt = anyio.Event()
            await tg.start(_watch, evt)
            tg.start_soon(partial(anyio.to_thread.run_sync,loop, #evt,
                cancellable=True))
            await evt.wait()
            task_status.started(self.window.id)

            try:
                await anyio.sleep(99)
                raise TimeoutError("I took too long")
            except BaseException as e:
                with anyio.fail_after(1, shield=True):
                    await anyio.to_thread.run_sync(kill, cancellable=True)
                raise
