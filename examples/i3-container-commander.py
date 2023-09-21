#!/usr/bin/env python3

# This example shows how to implement a simple, but highly configurable window
# switcher (like a much improved "alt-tab") with iterative dmenu calls. This
# script works well for most use cases with no arguments.
#
# https://faq.i3wm.org/question/228/how-do-i-find-an-app-buried-in-some-workspace-by-its-title/

from os.path import basename
import asway
import anyio
import asyncclick as click

@click.command(name='i3-container-commander.py',
                        help='''
        i3-container-commander.py is a simple but highly configurable
        dmenu-based script for creating dynamic context-based commands for
        controlling top-level windows. With no arguments, it is an efficient
        and ergonomical window switcher.
        ''',
                        epilog='''
        Additional arguments (when in doubt, use '--') will be passed to dmenu.
        ''')

@click.argument('--group-by',
                    metavar='PROPERTY',
                    default='window_class',
                    help='''A container property to initially group windows for selection or
        "none" to skip the grouping step. This works best for properties of
        type string. See <http://i3wm.org/docs/ipc.html#_tree_reply> for a list
        of properties. (default: "window_class")''')

@click.argument('--command',
                    metavar='COMMAND',
                    default='focus',
                    help='''The command to execute on the container that you end up
        selecting. The command should be a single command or comma-separated
        list such as what is passed to i3-msg. The command will only affect the
        selected container (it will be selected by criteria). (default: "focus")''')

@click.argument('--item-format',
                    metavar='FORMAT_STRING',
                    default='{workspace.name}: {container.name}',
                    help='''A Python format string to use to display the menu items. The
        format string will have the container and workspace available as
        template variables. (default: '{workspace.name}: {container.name}')
        ''')

@click.argument('--menu', default='dmenu', help='The menu command to run (dmenu or rofi)')
async def main(menu,item_format,command,group_by)
    async with asway.Connection() as i3:

        # set default menu args for supported menus
        if basename(menu) == 'dmenu':
            args += ['-i', '-f']
        elif basename(menu) == 'rofi':
            args += ['-show', '-dmenu']
        else:
            raise click.UsageError("I only understand dmenu or rofi")


        def find_group(container):
            return str(getattr(container, group_by)) if group_by != 'none' else ''


        async def show_menu(items, prompt):
            menu_input = bytes(str.join('\n', items), 'UTF-8')
            menu_cmd = [menu] + ['-l', str(len(items)), '-p', prompt] + args
            proc = await anyio.run_process(menu_cmd, input=menu_input)
            return proc.stdout.decode('utf-8').strip()


        async def show_container_menu(containers):
            def do_format(c):
                return item_format.format(workspace=c.workspace(), container=c)

            items = [do_format(c) for c in containers]
            items.sort()

            menu_result = await show_menu(items, command)
            for c in containers:
                if do_format(c) == menu_result:
                    return c


        containers = (await i3.get_tree()).leaves()

        if group_by:
            groups = dict()

            for c in containers:
                g = find_group(c)
                if g:
                    groups[g] = groups[g] + 1 if g in groups else 1

            if len(groups) > 1:
                chosen_group = await show_menu(['{} ({})'.format(k, v) for k, v in groups.items()], group_by)
                chosen_group = chosen_group[:chosen_group.rindex(' ')]
                containers = list(filter(lambda c: find_group(c) == chosen_group, containers))

        if len(containers):
            chosen_container = containers[0] if len(containers) == 1 else await show_container_menu(containers)

            if chosen_container:
                await chosen_container.command(command)
                return
        print("Not selected or found.")

