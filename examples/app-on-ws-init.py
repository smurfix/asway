#!/usr/bin/env python3

import asway
import asyncclick as click
import math
import anyio

description="""Open the given application each time the
    given workspace is created. For instance, running 'app-on-ws-init.py 6
    foot' should open a terminal as soon as you create the workspace 6.
    """
@click.command(help=description)
@click.option("--workspace","-w", type=str, multiple=True, help='Workspace to run the command on')
@click.option("--command","-c", type=str, help='command to run')
async def main(workspace, command):
    if not workspace:
        raise click.UsageError("requires at least one workspace")
    workspace = set(workspace)

    async with asway.Connection() as i3:

        async def on_workspace(e):
            if e.current.name in workspace and not len(e.current.leaves()):
                await i3.command(f'exec {command}')

        i3.on('workspace::focus', on_workspace)
        await anyio.sleep(math.inf)

if __name__ == "__main__":
    main()
