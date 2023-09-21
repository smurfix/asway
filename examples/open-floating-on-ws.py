#!/usr/bin/env python3

# This example shows how to make any window that opens on a workspace floating

# All workspaces that start with a string in this list will have their windows
# open floating


import asway
import anyio


FLOATING_WORKSPACES = ['3']

def is_ws_floating(name):
    for floating_ws in FLOATING_WORKSPACES:
        if name.startswith(floating_ws):
            return True

    return False


async def main():
    async with asway.Connection() as i3:

        async def on_window_open(e):
            ws = (await i3.get_tree()).find_focused().workspace()
            if is_ws_floating(ws.name):
                e.container.command('floating toggle')

        i3.on('window::new', on_window_open)
        await i3.main()

if __name__ == "__main__":
    anyio.run(main)
