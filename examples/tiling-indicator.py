#!/usr/bin/env python3
import asway
import anyio

splitv_text = 'V'
splith_text = 'H'
last = ''

async def main():
    async with asway.Connection() as i3:
        async def on_event(_):
            global last
            layout = i3.get_tree().find_focused().parent.layout
            if layout == 'splitv' and not layout == last:
                print(splitv_text)
            elif layout == 'splith' and not layout == last:
                print(splith_text)
            elif layout != last:
                print(' ')
            last = layout


        # Subscribe to events
        i3.on("window::focus", on_event)
        i3.on("binding", on_event)

        # Start the main loop and wait for events to come in.
        await i3.main()

if __name__ == "__main__":
    anyio.run(main)
