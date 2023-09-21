from .. import con
from ..replies import CommandReply

from typing import List

class Con(con.Con):
    """A container of a window and child containers gotten from :func:`i3ipc.Connection.get_tree()` or events.

    .. seealso:: https://i3wm.org/docs/ipc.html#_tree_reply

    :ivar border:
    :vartype border: str
    :ivar current_border_width:
    :vartype current_border_with: int
    :ivar floating: Either "auto_off", "auto_on", "user_off", or "user_on".
    :vartype floating: str
    :ivar focus: The focus stack for this container as a list of container ids.
        The "focused inactive" is at the top of the list which is the container
        that would be focused if this container recieves focus.
    :vartype focus: list(int)
    :ivar focused:
    :vartype focused: bool
    :ivar fullscreen_mode:
    :vartype fullscreen_mode: int
    :ivar ~.id:
    :vartype ~.id: int
    :ivar layout:
    :vartype layout: str
    :ivar marks:
    :vartype marks: list(str)
    :ivar name:
    :vartype name: str
    :ivar num:
    :vartype num: int
    :ivar orientation:
    :vartype orientation: str
    :ivar percent:
    :vartype percent: float
    :ivar scratchpad_state:
    :vartype scratchpad_state: str
    :ivar sticky:
    :vartype sticky: bool
    :ivar type:
    :vartype type: str
    :ivar urgent:
    :vartype urgent: bool
    :ivar window:
    :vartype window: int
    :ivar nodes:
    :vartype nodes: list(:class:`Con <i3ipc.Con>`)
    :ivar floating_nodes:
    :vartype floating_nodes: list(:class:`Con <i3ipc.Con>`)
    :ivar window_class:
    :vartype window_class: str
    :ivar window_instance:
    :vartype window_instance: str
    :ivar window_role:
    :vartype window_role: str
    :ivar window_title:
    :vartype window_title: str
    :ivar rect:
    :vartype rect: :class:`Rect <i3ipc.Rect>`
    :ivar window_rect:
    :vartype window_rect: :class:`Rect <i3ipc.Rect>`
    :ivar deco_rect:
    :vartype deco_rect: :class:`Rect <i3ipc.Rect>`
    :ivar app_id: (sway only)
    :vartype app_id: str
    :ivar pid: (sway only)
    :vartype pid: int
    :ivar gaps: (gaps only)
    :vartype gaps: :class:`Gaps <i3ipc.Gaps>`

    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    async def command(self, command: str) -> List[CommandReply]:
        """Runs a command on this container.

        .. seealso:: https://i3wm.org/docs/userguide.html#list_of_commands

        :returns: A list of replies for each command in the given command
            string.
        :rtype: list(CommandReply)
        """
        return await self._conn.command('[con_id="{}"] {}'.format(self.id, command))

    async def command_children(self, command: str) -> List[CommandReply]:
        """Runs a command on the immediate children of the currently selected
        container.

        .. seealso:: https://i3wm.org/docs/userguide.html#list_of_commands

        :returns: A list of replies for each command that was executed.
        :rtype: list(CommandReply)
        """
        if not len(self.nodes):
            return []

        commands = []
        for c in self.nodes:
            commands.append('[con_id="{}"] {};'.format(c.id, command))

        return await self._conn.command(' '.join(commands))


