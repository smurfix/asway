#!/usr/bin/env python3

import asway
import re
import asyncclick as click

@click.command(help='''
    Simple script to go to a new workspace. It will switch to a workspace with the lowest available number.
        ''')
async def main():
    async with asway.Connection() as i3:

        workspaces = await i3.get_workspaces()
        numbered_workspaces = filter(lambda w: w.name[0].isdigit(), workspaces)
        numbers = list(map(lambda w: int(re.search(r'^([0-9]+)', w.name).group(0)),
                        numbered_workspaces))

        new = 0

        for i in range(1, max(numbers) + 2):
            if i not in numbers:
                new = i
                break

        await i3.command("workspace %s" % new)


if __name__ == '__main__':
    main()
