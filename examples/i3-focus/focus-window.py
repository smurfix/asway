#!/usr/bin/env python3

import re
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
@click.option('--socket', default='/tmp/i3-app-focus.socket', help='Socket file path')
@click.option('--menu', default='dmenu', help='The menu command to run (ex: --menu=rofi)')
@click.argument("args", nargs=-1)
async def main(socket, menu, args):
    async with asway.Connection() as i3:
        sockets = Sockets(socket)
        containers_info = sockets.get_containers_history()

        menu = Menu(i3, menu, args)
        menu.show_menu_container_info(containers_info)
anyio.run(main)
