#!/usr/bin/env python3
# This module is an example of how to use asway. It
# implements an i3status wrapper that handles a special keybinding to switch
# keyboard layout, while also displaying current layout in i3bar.
#
# The keyboard layout switcher can be activated by adding something like this
# to i3 config:
#
#       bindsym KEYS nop switch_layout

import collections
import json
import subprocess
import sys
import tempfile
import asyncclick as click
import asway

configure_i3_status = False
try:
    # Unfortunately i3status does not have a simple way to set the
    # output_format outside of its configuration file. If not set, it will
    # guess the output format in a very hacky way by looking at the parent
    # process name which is horrible for embedders. So, we try to "fool" it
    # into using i3bar output format by changing the process title with
    # setproctitle module (install with pip3 install --user setproctitle).

    # Of course, this is not needed if output_format is set explicitly in the
    # config file. This is only done for demonstration purposes.
    import setproctitle
    setproctitle.setproctitle('i3bar')
except ImportError:
    # Configure i3status by explicitly setting "i3bar" as output_format
    configure_i3_status = True

    I3STATUS_CFG = '''
    general {
            output_format = "i3bar"
            colors = true
            interval = 5
    }

    order += "disk /"
    order += "load"
    order += "tztime local"

    tztime local {
            format = "%Y-%m-%d %H:%M:%S"
    }

    load {
            format = "%1min"
    }

    disk "/" {
            format = "%avail"
    }
    '''


class Status(object):
    def __init__(self):
        self.current_status = collections.OrderedDict()
        # the first write does not contain a leading newline since it
        # represents the first item in a json array.
        self.first_write = True
        self.layouts = ['us', 'us intl']
        self.current_layout = -1
        self.command_handlers = {'switch_layout': lambda: self.switch_layout()}
        # perform a switch now, which will force the keyboard layout to be
        # shown before other data
        self.switch_layout()

    async def switch_layout(self):
        self.current_layout = (self.current_layout + 1) % len(self.layouts)
        new_layout = self.layouts[self.current_layout]
        await anyio.run_process(['setxkbmap', new_layout])
        self.update([{'name': 'keyboard_layout', 'markup': 'none', 'full_text': new_layout}])

    async def dispatch_command(self, command):
        c = command.split(' ')
        if (len(c) < 2 or c[0] != 'nop' or c[1] not in self.command_handlers):
            return
        await self.command_handlers[c[1]]()
        self.repaint()

    def merge(self, status_update):
        for item in status_update:
            self.current_status[item['name']] = item

    def update(self, new_status):
        self.merge(new_status)

    def repaint(self):
        template = '{}' if self.first_write else ',{}'
        self.first_write = False
        sys.stdout.write(
            template.format(
                json.dumps([item for item in self.current_status.values() if item],
                           separators=(',', ':'))))
        sys.stdout.write('\n')
        sys.stdout.flush()

    async def i3status_reader(self):
        from anyio.streams.text import TextReceiveStream

        def handle_i3status_payload(line):
            self.update(json.loads(line))
            self.repaint()

        proc_cmd = ["i3status"]
        if configure_i3_status:
            # use a custom i3 status configuration to ensure we get json output
            cfg_file = tempfile.NamedTemporaryFile(mode='w+b')
            cfg_file.write(I3STATUS_CFG.encode('utf8'))
            cfg_file.flush()
            proc_cmd.extend(['-c', cfg_file.name])
        async with await anyio.open_process(proc_cmd) as proc:
            lines = aiter(TextReceiveStream(process.stdout))
            # forward first line, version information
            sys.stdout.write(await anext(lines))
            # forward second line, an opening list bracket (no idea why this
            # exists)
            sys.stdout.write(await anext(lines))
            # third line is a json payload
            handle_i3status_payload(await anext(lines))
            for l in lines:
                # all subsequent lines are json payload with a leading comma
                handle_i3status_payload((await anext(lines))[1:])

@click.command()
async def main():
    async with asway.Connection() as i3:
        status = Status(i3)
        i3.on('binding::run', lambda e: status.dispatch_command(e.binding.command))
        await status.i3status_reader()

if __name__ == "__main__":
    main()
