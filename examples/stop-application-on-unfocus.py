#!/usr/bin/env python3
"""
Stop an application when unfocused using SIGSTOP
Restart it when focused again using SIGCONT
Useful to save battery / reduce CPU load when running browsers.

Warning: if more than one process with the same name are being run, they
will all be stopped/restarted

Federico Ceratto <federico@firelet.net>
License: GPLv3
"""

import atexit
import asway
import psutil
import asyncclick as click
from argparse import ArgumentParser


class FocusMonitor(object):

    def stop_cont(self, cont=True):
        """Send SIGSTOP/SIGCONT to processes called <name>
        """
        for proc in psutil.process_iter():
            if proc.name() == self.process_name:
                sig = psutil.signal.SIGCONT if cont else psutil.signal.SIGSTOP
                proc.send_signal(sig)
                if self.debug:
                    sig = 'CONT' if cont else 'STOP'
                    print("Sent SIG%s to process %d" % (sig, proc.pid))

    def focus_change(self, event):
        """Detect focus change on a process with class class_name.
        On change, stop/continue the process called process_name
        """
        has_focus_now = (event.container.window_class == self.class_name)
        if self.had_focus ^ has_focus_now:
            # The monitored application changed focus state
            self.had_focus = has_focus_now
            self.stop_cont(has_focus_now)

    def continue_at_exit(self):
        """Send SIGCONT on script termination"""
        self.stop_cont(True)

    def run(self, class_name, process_name, debug):
        async with asway.Connection() as self.conn:
            self.had_focus = False
            self.class_name = class_name
            self.process_name = process_name
            self.debug = debug
            self.conn.on('window::focus', self.focus_change)
            atexit.register(self.continue_at_exit)
            try:
                await self.conn.main()
            except KeyboardInterrupt:
                print('Exiting on keyboard interrupt')


@click.command()
@click.option('--class_name')
@click.option('--process_name')
@click.option('-d', '--debug', is_flag=True)
async def main(**kw)
    fm = FocusMonitor()
    await fm.run(**kw)

if __name__ == '__main__':
    main()
