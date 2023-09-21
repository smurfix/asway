#!/usr/bin/python3

import asway
from argparse import ArgumentParser
from subprocess import CalledProcessError
from sys import exit
from os.path import basename
import asyncclick as click
import anyio

history = []

try:
    with open('/tmp/i3-cmd-history') as f:
        history = f.read().split('\n')
except FileNotFoundError:
    pass

@click.command(name='i3-cmd',
                        help='''
                        i3-cmd is a dmenu-based script that sends the given
                        command to i3.
                        ''',
                        epilog='''
                        Additional arguments (if in doubt, use '--') will be passed to the menu command.
                        ''')

@click.option('--menu', default='dmenu', help='The menu command to run (demnu or rofi)')
@click.argument("args", nargs=-1)
async def main(menu, args):
    async with asway.Connection() as i3:
        # set default menu args for supported menus
        args = list(args)
        if basename(menu) == 'dmenu':
            cmd = [menu, '-i', '-f']
        elif basename(menu) == 'rofi':
            cmd = [menu, '-show', '-dmenu', '-p', 'i3-cmd: ']
        else:
            raise click.UsageError("I only understand dmenu or rofi")

        res = ''

        try:
            proc = await anyio.run_process(cmd+args, input=('\n'.join(history)).encode('utf-8'))
            res = proc.stdout.decode("utf-8").strip()
        except CalledProcessError as e:
            exit(e.returncode)

        if not res:
            # nothing to do
            return

        result = await i3.command(res)

        cmd_success = True

        for r in result:
            if not r.success:
                cmd_success = False
                await anyio.run_process(['notify-send', 'i3-cmd error', r.error])

        if cmd_success:
            with open('/tmp/i3-cmd-history', 'w') as f:
                try:
                    history.remove(cmd)
                except ValueError:
                    pass
                history.insert(0, cmd)
                f.write('\n'.join(history))

if __name__ == "__main__":
    main()
