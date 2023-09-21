asway
=====

An async Python library to control `sway <https://swaywm.org/>`__ (and `i3wm <http://i3wm.org>`__).

About
-----

Sway's interprocess communication (or `IPC <https://man.archlinux.org/man/sway-ipc.7.en>`__) is the interface sway uses to receive `commands <https://man.archlinux.org/man/sway.5#COMMANDS>`__ from client applications such as ``swaymsg``. It also features a publish/subscribe mechanism for notifying interested parties of window manager events.

asway is an asynchronous Python library for controlling the window manager.
This project is intended to be useful for general scripting, and for
applications that interact with the window manager like status line
generators, notification daemons, and window pagers.

If you have an idea for a script to extend asway, you can add your script to the `examples folder <https://github.com/smurfix/asway/tree/main/examples>`__.

For details on how to use the library, see the `reference documentation <https://asway.readthedocs.io/en/latest/>`__.

asway is based on `i3ipc-python <https://github.com/altdesktop/i3ipc-python>`__. It was forked because structured async code requires a couple of modifications that didn't work well with the original code base.

Installation
------------

asway is on `PyPI <https://pypi.python.org/pypi/asway>`__.

``pip3 install asway``

Example
-------

.. code:: python3

    from asway import Connection, Event
    import anyio

    # Create the Connection object that can be used to send commands and subscribe
    # to events.
    async def main():
      async with asway.Connection() as wm:

        # Print the name of the focused window
        focused = await wm.get_tree().find_focused()
        print('Focused window %s is on workspace %s' %
            (focused.name, focused.workspace().name))

        # Query the ipc for outputs. The result is a list that represents the parsed
        # reply of a command like `swaymsg -t get_outputs`.
        outputs = await wm.get_outputs()

        print('Active outputs:')

        for output in filter(lambda o: o.active, outputs):
            print(output.name)

        # Send a command to be executed synchronously.
        await wm.command('focus left')

        # Take all fullscreen windows out of fullscreen
        for container in (await wm.get_tree().find_fullscreen()):
            container.command('fullscreen')

        # Print the names of all the containers in the tree
        root = await wm.get_tree()
        print(root.name)
        for con in root:
            print(con.name)

        # Define a callback to be called when you switch workspaces.
        def on_workspace_focus(self, e):
            # The first parameter is the connection to the ipc and the second is an object
            # with the data of the event sent from sway.
            if e.current:
                print('Windows on this workspace:')
                for w in e.current.leaves():
                    print(w.name)

        # Dynamically name your workspaces after the current window class
        def on_window_focus(e):
            focused = await wm.get_tree().find_focused()
            ws_name = "%s:%s" % (focused.workspace().num, focused.window_class)
            await wm.command('rename workspace to "%s"' % ws_name)

        # Subscribe to events
        wm.on(Event.WORKSPACE_FOCUS, on_workspace_focus)
        wm.on(Event.WINDOW_FOCUS, on_window_focus)

        # just wait for events to come in.
        import math
        anyio.sleep(math.inf)

    # You can use the asyncio backend if you must, but I recommend Trio
    # if you don't depend on libraries that are asyncio-only.
    anyio.run(main, backend="trio")


Debug Logging
-------------

asway uses the standard logging module under the `asway` namespace.

.. code:: python3

    import logging
    logging.basicConfig(level=logging.DEBUG)


Contributing
------------

Development happens on `Github <https://github.com/smurfix/asway>`__. Please feel free to report bugs, request features or add examples by submitting a pull request.

License
-------

This work is available under a BSD-3-Clause license (see LICENSE).

Copyright © 2015, Tony Crisci
Copyright © 2023, Matthias Urlichs (and contributors)

