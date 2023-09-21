#!/usr/bin/env python3

import re
from argparse import ArgumentParser
from functools import reduce
import asway
import anyio
from tools import App, Lists, Menu, Sockets
import asyncclick as click

@click.command(name='i3-app-focus.py',
               help='''
        i3-app-focus.py is dmenu-based script for creating dynamic app switcher.
        ''',
               epilog='''
        Additional arguments found after "--" will be passed to dmenu.
        ''')
@click.option('--menu', default='dmenu', help='The menu command to run (ex: --menu=rofi)')
@click.option('--socket', default='/tmp/i3-app-focus.socket', help='Socket path')
@click.argument("args", nargs=-1)
async def main(menu,socket,args):
    sockets = Sockets(socket)
    containers_info = sockets.get_containers_history()

    apps = list(map(App, containers_info))
    apps_uniq = reduce(Lists.accum_uniq_apps, apps, [])

    async with asway.Connection() as i3:
        menu = Menu(i3, menu, args)
        await menu.show_menu_app(apps_uniq)
anyio.run(main)
