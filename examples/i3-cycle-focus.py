#!/usr/bin/env python3
#
# provides alt+tab functionality between windows, switching
# between n windows; example i3 conf to use:
#     exec_always --no-startup-id i3-cycle-focus.py --history 2
#     bindsym $mod1+Tab exec --no-startup-id i3-cycle-focus.py --switch

import os
import anyio
from argparse import ArgumentParser
import logging

from asway import Connection
import asyncclick as click

SOCKET_FILE = '/tmp/.i3-cycle-focus.sock'
MAX_WIN_HISTORY = 16
UPDATE_DELAY = 2.0


def on_shutdown(e):
    os._exit(0)


class FocusWatcher:
    def __init__(self):
        self.i3 = None
        self.window_list = []
        self.update_task = None
        self.window_index = 1

    async def update_window_list(self, window_id, *, task_status):
        with anyio.CancelScope() as sc:
            task_status.started(sc)
            await anyio.sleep(UPDATE_DELAY)  # yes even if it is zero
            self.update_task = None

            logging.info('updating window list')
            if window_id in self.window_list:
                self.window_list.remove(window_id)

            self.window_list.insert(0, window_id)

            if len(self.window_list) > MAX_WIN_HISTORY:
                del self.window_list[MAX_WIN_HISTORY:]

            self.window_index = 1
            logging.info('new window list: {}'.format(self.window_list))

    async def get_valid_windows(self):
        tree = await self.i3.get_tree()
        if active_workspace:
            return set(w.id for w in tree.find_focused().workspace().leaves())
        elif visible_workspaces:
            ws_list = []
            w_set = set()
            outputs = await self.i3.get_outputs()
            for item in outputs:
                if item.active:
                    ws_list.append(item.current_workspace)
            for ws in tree.workspaces():
                if str(ws.name) in ws_list:
                    for w in ws.leaves():
                        w_set.add(w.id)
            return w_set
        else:
            return set(w.id for w in tree.leaves())

    async def on_window_focus(self, event):
        logging.info('got window focus event')
        if ignore_floating and (event.container.floating == "user_on"
                                     or event.container.floating == "auto_on"):
            logging.info('not handling this floating window')
            return

        if self.update_task is not None:
            self.update_task.cancel()

        logging.info('scheduling task to update window list')
        self.update_task = await self.tg.start(self.update_window_list, event.container.id)

    async def run(self):
        async with Connection() as self.i3:
            self.i3.on('window::focus', self.on_window_focus)
            self.i3.on('shutdown', on_shutdown)
            listener = await anyio.create_unix_listener(SOCKET_FILE)
            await listener.serve(self._handle_switch)

    async def _handle_switch(self, conn):
        async with conn:
            data = await conn.receive(1024)
            logging.info('received data: %r',data)
            if data == b'switch':
                logging.info('switching window')
                windows = await self.get_valid_windows()
                logging.info('valid windows = {}'.format(windows))
                for window_id in self.window_list[self.window_index:]:
                    if window_id not in windows:
                        self.window_list.remove(window_id)
                    else:
                        if self.window_index < (len(self.window_list) - 1):
                            self.window_index += 1
                        else:
                            self.window_index = 0
                        logging.info('focusing window id={}'.format(window_id))
                        await self.i3.command('[con_id={}] focus'.format(window_id))
                        break


async def send_switch():
    async with await anyio.connect_unix(SOCKET_FILE) as client:
        logging.info('sending switch message')
        await client.send('switch'.encode())
        logging.info('closing the connection')


async def run_server():
    focus_watcher = FocusWatcher()
    await focus_watcher.run()


@click.command(prog='i3-cycle-focus.py',
                            description="""
        Cycle backwards through the history of focused windows (aka Alt-Tab).
        This script should be launched from ~/.xsession or ~/.xinitrc.
        Use the `--history` option to set the maximum number of windows to be
        stored in the focus history (Default 16 windows).
        Use the `--delay` option to set the delay between focusing the
        selected window and updating the focus history (Default 2.0 seconds).
        Use a value of 0.0 seconds to toggle focus only between the current
        and the previously focused window.
        se the `--visible-workspaces` option to include windows on
        visible workspaces only when cycling the focus history. Use the
        `--active-workspace` option to include windows on the active workspace
        only when cycling the focus history.

        To trigger focus switching, execute the script from a keybinding with
        the `--switch` option.""")
@click.option('--history',
                        help='Maximum number of windows in the focus history',
                        type=int)
@click.option('--delay',
                        help='Delay before updating focus history',
                        type=float)
@click.option('--ignore-floating',
                        action='store_true',
                        help='Ignore floating windows')
@click.option('--visible-workspaces',
                        action='store_true',
                        help='Include only windows on visible workspaces')
@click.option('--active-workspace',
                        action='store_true',
                        help='Include only windows on the active workspace')
@click.option('--switch',
                        is_flag=True,
                        help='Switch to the previous window')
@click.option('--debug', is_flag=True, help='Turn on debug logging')
async def main(history, delay, ignore_floating, visible_workspaces, active_workspace, switch, debug):
    logging.basicConfig(level=logging.DEBUG if debug else logging.WARNING)

    if history:
        MAX_WIN_HISTORY = history
    if delay:
        UPDATE_DELAY = delay
    else:
        if delay == 0.0:
            UPDATE_DELAY = delay
    if switch:
        await send_switch()
    else:
        await run_server()
