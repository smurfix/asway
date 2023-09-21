asway Documentation
===================

.. module:: asway

.. toctree::
   :maxdepth: 2
   :caption: Reference:

   connection
   con
   aio-connection
   aio-con
   anyio-connection
   anyio-con
   events
   replies


.. codeauthor:: acrisci

Overview
++++++++

asway is an async library for controlling `sway <https://swaywm.org>`_ and `i3 window manager <https://i3wm.org>`_. sway and i3 users can use this library to create their own plugin scripts to customize their desktop or integrate sway / i3 into other applications. With this library, you can query the state of the window manager, listen to events, and send commands to sway / i3 to perform window manager actions such as focusing or closing windows.

The main entry point into the features of the library is the :class:`Connection <asway.Connection>` class. This class manages a Unix socket connection to the ipc interface exposed by the window manager. By default, the ``Connection`` will attempt to connect to the running instance of sway / i3 by using information present in the environment.

.. code-block:: python3

    from asway import Connection

    async with await Connection() as wm:
        ...

You can use the ``Connection`` to query window manager state such as the names of the workspaces and outputs.

.. code-block:: python3

    workspaces = await wm.get_workspaces()
    outputs = await wm.get_outputs()

    for workspace in workspaces:
        print(f'workspace: {workspace.name}')

    for output in outputs:
        print(f'output: {output.name}')

You can use it to send commands to sway / i3 to control the window manager in an automated fashion with the same command syntax as the sway config file or ``swaymsg``.

.. code-block:: python3

    await wm.command('workspace 5')
    await wm.command('focus left')
    await wm.command('kill')

You can use it to query the windows to find specific applications, get information about their windows, and send them window manager commands. The sway / i3 layout tree is represented by the :class:`Con <asway.aio.Con>` class.

.. code-block:: python3

    # get_tree() returns the root container
    tree = await wm.get_tree()

    # get some information about the focused window
    focused = tree.find_focused()
    print(f'Focused window: {focused.name}')
    workspace = focused.workspace()
    print(f'Focused workspace: {workspace.name}')

    # focus a firefox window and set it to fullscreen mode
    ff = workspace.find_classed('Firefox')[0]
    await ff.command('focus')
    await ff.command('fullscreen')

    # iterate through all the container windows (or use tree.leaves() for just
    # application windows)
    for container in workspace:
        print(f'On the focused workspace: {container.name}')

And you can use it to subscribe to window manager events and call a handler when they occur.

.. code-block:: python3

    from asway import Event

    def on_new_window(e):
        print(f'a new window opened: {e.container.name}')

    def on_workspace_focus(e):
        print(f'workspace just got focus: {e.current.name}')

    wm.on(Event.WINDOW_NEW, on_new_window)
    wm.on(Event.WORKSPACE_FOCUS, on_workspace_focus)
    # TODO that's queued, add a way to wait until registered
    # TODO support context managers and async loops

    await anyio.sleep(math.inf)

For more examples, see the `examples <https://github.com/smurfix/asway/tree/master/examples>`_ folder in the repository for useful scripts people have contributed.

Installation
++++++++++++

This library is available on PyPi as `asway <https://pypi.org/project/asway/>`_.

.. code-block:: bash

    pip3 install asway

Contributing
++++++++++++

Development for this library happens on `Github <https://github.com/smurfix/asway>`_. Report bugs or request features there. Contributions are welcome.

License
++++++++

This library is available under a `BSD-3-Clause License <https://github.com/smurfix/asway/blob/master/LICENCE>`_.

© 2015, Tony Crisci

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
