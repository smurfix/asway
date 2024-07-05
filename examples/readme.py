from asway import Connection, Event
import anyio

# Create the Connection object that can be used to send commands and subscribe
# to events.
async def main():
  async with Connection() as wm:

    # Print the name of the focused window
    focused = (await wm.get_tree()).find_focused()
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
    for container in (await wm.get_tree()).find_fullscreen():
        container.command('fullscreen')

    # Print the names of all the containers in the tree
    print('Containers:')
    root = await wm.get_tree()
    print(root.name)
    for con in root:
        print(con.name)

    # Define a callback to be called when you switch workspaces.
    def on_workspace_focus(e):
        if e.current:
            print('Windows on this workspace:')
            for w in e.current.leaves():
                print(w.name)

    # Dynamically name your workspaces after the current window class
    async def on_window_focus(e):
        focused = e.container
        breakpoint()
        print("Focus:", focused.window_class)
        ws = focused.workspace()
        if ws is not None:
            ws_name = "%s:%s" % (ws.num, focused.window_class)
            await wm.command('rename workspace to "%s"' % ws_name)

    # Subscribe to events
    wm.on(Event.WORKSPACE_FOCUS, on_workspace_focus)
    wm.on(Event.WINDOW_FOCUS, on_window_focus)

    # just wait for events to come in.
    import math
    await anyio.sleep(math.inf)

# I recommend Trio if you don't depend on libraries that are asyncio-only.
if __name__ == "__main__":
    anyio.run(main, backend="trio")
