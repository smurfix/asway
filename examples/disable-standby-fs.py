#!/usr/bin/env python3

from argparse import ArgumentParser
from subprocess import call
import asyncclick as click
import asway


@click.command(prog='disable-standby-fs',
               help='''
        Disable standby (dpms) and screensaver when a window becomes fullscreen
        or exits fullscreen-mode. Requires `xorg-xset`.
        ''')
async def main():

    def find_fullscreen(con):
        # XXX remove me when this method is available on the con in a release
        return [c for c in con.descendents() if c.type == 'con' and c.fullscreen_mode]


    def set_dpms(state):
        if state:
            print('setting dpms on')
            call(['xset', 's', 'on'])
            call(['xset', '+dpms'])
        else:
            print('setting dpms off')
            call(['xset', 's', 'off'])
            call(['xset', '-dpms'])


    def on_fullscreen_mode(e):
        set_dpms(not len(await find_fullscreen(i3.get_tree())))


    def on_window_close(e):
        if not len(find_fullscreen(await i3.get_tree())):
            set_dpms(True)

    async with asway.Connection() as i3:
        i3.on('window::fullscreen_mode', on_fullscreen_mode)
        i3.on('window::close', on_window_close)
        await i3.main()


if __name__ == "__main__":
    main()
