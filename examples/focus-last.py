#!/usr/bin/env python3

import os
import socket
import tempfile
import asway
import anyio
import asyncclick as click

SOCKET_DIR = '{}/i3_focus_last.{}{}'.format(tempfile.gettempdir(), os.geteuid(),
                                            os.getenv("DISPLAY"))
SOCKET_FILE = '{}/socket'.format(SOCKET_DIR)
MAX_WIN_HISTORY = 15


class FocusWatcher:
    def run(self):
        async with asway.Connection() as self.i3 :
            self.i3.on('window::focus', self.on_window_focus)
            # Make a directory with permissions that restrict access to
            # the user only.
            if os.path.exists(SOCKET_FILE):
                os.remove(SOCKET_FILE)
            self.window_list = []
            self.window_list_lock = anyio.Lock()
            await self._run_server()

    def on_window_focus(self, event):
        async with self.window_list_lock:
            window_id = event.container.id
            if window_id in self.window_list:
                self.window_list.remove(window_id)
            self.window_list.insert(0, window_id)
            if len(self.window_list) > MAX_WIN_HISTORY:
                del self.window_list[MAX_WIN_HISTORY:]

    async def _run_server(self):
        async def handle(client):
            async with client:
                data = client.recv(1024)
                if data == b'switch':
                    async with self.window_list_lock:
                        tree = await self.i3.get_tree()
                        windows = set(w.id for w in tree.leaves())
                        for window_id in self.window_list[1:]:
                            if window_id not in windows:
                                self.window_list.remove(window_id)
                            else:
                                await self.i3.command('[con_id=%s] focus' % window_id)
                                break
            elif not data:
                selector.unregister(conn)
                conn.close()

        listener = await anyio.create_unix_listener(self.socket_file)
        await listener.serve(handle)


@click.command(name='focus-last.py',
                        help='''
    Focus last focused window.

    This script should be launch from the .xsessionrc without argument.

    Then you can bind this script with the `--switch` option to one of your
    i3 keybinding.
    ''')
@click.option('--switch', is_flag=True, help='Switch to the previous window')
async def main(switch):
    if not switch:
        focus_watcher = FocusWatcher()
        await focus_watcher.run()
    else:
        client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_socket.connect(SOCKET_FILE)
        client_socket.send(b'switch')
        client_socket.close()

if __name__ == '__main__':
    main()
