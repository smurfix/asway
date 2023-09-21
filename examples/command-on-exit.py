#!/usr/bin/env python3

# This example shows how to run a command when i3 exits
#
# https://faq.i3wm.org/question/3468/run-a-command-when-i3-exits/

# This is the command to run

import asway
import anyio
import math
import asyncclick as click


@click.command
@click.argument("cmd", nargs=-1)
async def main(cmd):
    async def on_shutdown(e):
        await anyio.run_process(cmd)

    async with asway.Connection() as i3:
        i3.on('ipc_shutdown', on_shutdown)

    await anyio.sleep(math.inf)

main()
