#!/usr/bin/env python3

# This example shows how to run a command when i3 exits
#
# https://faq.i3wm.org/question/3468/run-a-command-when-i3-exits/

# This is the command to run
COMMAND = ['echo', 'hello, world']

from subprocess import Popen
import asway


def on_shutdown(i3):
    Popen(COMMAND)


i3 = asway.Connection()

i3.on('ipc_shutdown', on_shutdown)

i3.main()
