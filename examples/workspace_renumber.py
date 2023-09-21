#!/usr/bin/env python3

import asway
import anyio


# check if workspaces are all in order
async def workspaces_ordered(i3conn):
    last_workspace = 0
    for i in sorted((await i3conn.get_workspaces()), key=lambda x: x.num):
        number = int(i.num)
        if number != last_workspace + 1:
            return False
        last_workspace += 1
    return True


# find all the workspaces that are out of order and
# the least possible valid workspace number that is unassigned
async def find_disordered(i3conn):
    disordered = []
    least_number = None
    workspaces = sorted((await i3conn.get_workspaces()), key=lambda x: x.num)
    occupied_workspaces = [int(x.num) for x in workspaces]
    last_workspace = 0
    for i in workspaces:
        number = int(i.num)
        if number != last_workspace + 1:
            disordered.append(number)
            if least_number is None and last_workspace + 1 not in occupied_workspaces:
                least_number = last_workspace + 1
        last_workspace += 1
    return (disordered, least_number)


# renumber all the workspaces that appear out of order from the others
async def fix_ordering(i3conn):
    if await workspaces_ordered(i3conn):
        return
    else:
        workspaces = (await i3conn.get_tree()).workspaces()
        disordered_workspaces, least_number = await find_disordered(i3conn)
        containers = list(filter(lambda x: x.num in disordered_workspaces, workspaces))
        for c in containers:
            for i in c.leaves():
                i.command("move container to workspace %s" % least_number)
            least_number += 1
    return


async def main():
    async with asway.Connection() as i3:

        # callback for when workspace focus changes
        async def on_workspace_focus(e):
            await fix_ordering(i3)

        i3.on('workspace::focus', on_workspace_focus)
        await i3.main()


if __name__ == '__main__':
    anyio.run(main)
