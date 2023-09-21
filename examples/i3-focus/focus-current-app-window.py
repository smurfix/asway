#!/usr/bin/env python3

import re
from argparse import ArgumentParser
from functools import reduce
import asway
from tools import App, Lists, Menu, Sockets
import asyncclick as click
import anyio

@click.command(name='i3-app-focus.py',
                        help='''
        i3-app-focus.py is dmenu-based script for creating dynamic app switcher.
        ''',
                        epilog='''
        Additional arguments found after "--" will be passed to dmenu.
        ''')
@click.option('--menu', default='dmenu', help='The menu command to run (ex: --menu=rofi)')
@click.option('--socket', default='/tmp/i3-app-focus.socket', help='Socket file path')
@click.argument("args", nargs=-1)
async def main(menu,socket,args):
    async with asway.Connection() as i3:
        sockets = Sockets(socket)
        containers_info = sockets.get_containers_history()
        containers_info_by_focused_app = Lists.find_all_by_focused_app(containers_info)

        menu = Menu(i3, menu, args)
        await menu.show_menu_container_info(containers_info_by_focused_app)
anyio.run(main)
