#!/usr/bin/env python3

import os
import socket
import json
from contextlib import asynccontextmanager
import asway
import anyio
import asyncclick as click

MAX_WIN_HISTORY = 15



class FocusWatcher:
    def __init__(self, socket_file):
        self.socket_file = socket_file

    async def run(self):
        async with asway.Connection() as self.i3:
            self.i3.on(asway.Event.WINDOW_FOCUS, self._on_window_focus)
            self.i3.on(asway.Event.WINDOW_CLOSE, self._on_window_close)
            if os.path.exists(self.socket_file):
                os.remove(self.socket_file)
            self.window_list = []
            self.window_list_lock = anyio.Lock()

            await self._run_server()

    def _on_window_focus(self, event):
        window_id = event.container.id
        con = self.i3.get_tree().find_by_id(window_id)
        if not self._is_window(con):
            return

        with self.window_list_lock:
            if window_id in self.window_list:
                self.window_list.remove(window_id)

            self.window_list.insert(0, window_id)

            if len(self.window_list) > MAX_WIN_HISTORY:
                del self.window_list[MAX_WIN_HISTORY:]

    def _on_window_close(self, event):
        window_id = event.container.id
        with self.window_list_lock:
            if window_id in self.window_list:
                self.window_list.remove(window_id)

    async def _run_server(self):
        async def handle(client):
            async with client:
                tree = await self.i3.get_tree()
                info = []
                with self.window_list_lock:
                    for window_id in self.window_list:
                        con = tree.find_by_id(window_id)
                        if con:
                            info.append({
                                "id": con.id,
                                "window": con.window,
                                "window_title": con.window_title,
                                "window_class": con.window_class,
                                "window_role": con.window_role,
                                "focused": con.focused
                            })

                await conn.send(json.dumps(info).encode())

        listener = await anyio.create_unix_listener(self.socket_file)
        await listener.serve(handle)

    @staticmethod
    def _is_window(con):
        return not con.nodes and con.type == "con" and (con.parent and con.parent.type != "dockarea"
                                                        or True)
@click.command(name="i3-focus-server")
@click.option("--socket","-S", default='/tmp/i3-app-focus.socket', help='Socket file path')
async def main(**kw):
    await FocusWatcher(**kw).run()

main()
