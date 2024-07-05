#!/usr/bin/env python3

from argparse import ArgumentParser
import asway
import asyncclick as click


async def focused_windows(i3):
    tree = await i3.get_tree()

    workspaces = tree.workspaces()
    for workspace in workspaces:
        container = workspace

        while container:
            if not hasattr(container, 'focus') or not container.focus:
                break

            container_id = container.focus[0]
            container = container.find_by_id(container_id)

        if container:
            coname = container.name
            wsname = workspace.name

            print('WS', wsname + ':', coname)

@click.command(help='Print the names of the focused window of each workspace.')
async def main():
    async with asway.Connection() as i3:
        await focused_windows(i3)
if __name__ == '__main__':
    main()
