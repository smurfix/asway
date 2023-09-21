#!/usr/bin/env python3
"""
focus-next-visible.py - cycles input focus between visible windows on workspace

- requires the `xprop` utility

 Usage:

    # focus next visible window
    bindsym $mod+n exec --no-startup-id focus-next-visible.py

    # focus previous visible window
    bindsym $mod+Shift+n exec --no-startup-id focus-next-visible.py reverse


https://faq.i3wm.org/question/6937/move-focus-from-tabbed-container-to-win...

"""

from sys import argv
from itertools import cycle
from subprocess import check_output

import asway
import anyio


def get_windows_on_ws(tree):
    return filter(lambda x: x.window, tree.find_focused().workspace().descendents())


def find_visible_windows(windows_on_workspace):
    visible_windows = []
    for w in windows_on_workspace:

        try:
            xprop = check_output(['xprop', '-id', str(w.window)]).decode()
        except FileNotFoundError:
            raise SystemExit("The `xprop` utility is not found!" " Please install it and retry.")

        if '_NET_WM_STATE_HIDDEN' not in xprop:
            visible_windows.append(w)

    return visible_windows

async def main()
    async with asway.Connection() as conn:

        visible_windows = find_visible_windows(get_windows_on_ws(await conn.get_tree()))

        if len(argv) > 1 and argv[1] == "reverse":
            cycle_windows = cycle(reversed(visible_windows))
        else:
            cycle_windows = cycle(visible_windows)

        for window in cycle_windows:
            if window.focused:
                focus_to = next(cycle_windows)
                await conn.command('[id="%d"] focus' % focus_to.window)
                break

if __name__ == '__main__':
    anyio.run(main)
