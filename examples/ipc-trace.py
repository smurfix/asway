#!/usr/bin/env python3

import asway
import anyio
from time import strftime, gmtime

def print_separator():
    print('-----')


def print_time():
    print(strftime(strftime("%Y-%m-%d %H:%M:%S", gmtime())))


def print_con_info(con):
    print('  Id: %s' % con.id)
    print('  Name: %s' % con.name)


def on_evt(e):
    print_separator()
    if (chg := getattr(e,"change",None)) is not None:
        print(f'Got {e.__class__.__name__}::{e.change}')
    else:
        print(f'Got {e.__class__.__name__}')
    print_time()
    for k,v in vars(e).items():
        if k[0] == "_":
            continue
        if k in {"ipc_data","change"}:
            continue
        if isinstance(v,asway.Con):
            print(f'* {k.capitalize()}: {v.type}')
            print_con_info(v)
        else:
            print(f'{k.capitalize()}: {v}')


# subscribe to all events

async def main():
    async with asway.Connection() as i3:
        for s in dir(asway.Event):
            if s[0] == "_":
                continue
            v = getattr(asway.Event,s).value
            if not isinstance(v,str):
                continue
            if "::" in v:
                continue
            i3.on(v, on_evt)

        await i3.main()

if __name__ == "__main__":
    anyio.run(main)
