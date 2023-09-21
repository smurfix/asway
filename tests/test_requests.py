from .ipctest import i3

from asynci3 import (VersionReply, BarConfigReply, OutputReply, WorkspaceReply, ConfigReply,
                   TickReply, Con)

import pytest
import anyio


class TestResquests:
    @pytest.mark.anyio
    async def test_requests(self, i3):
        async with i3.connect():
            await anyio.sleep(0.2)
            resp = await i3.get_version()
            assert type(resp) is VersionReply

            resp = await i3.get_bar_config_list()
            assert type(resp) is list
            assert 'bar-0' in resp

            resp = await i3.get_bar_config('bar-0')
            assert type(resp) is BarConfigReply

            resp = await i3.get_outputs()
            assert type(resp) is list
            assert resp
            assert type(resp[0]) is OutputReply

            resp = await i3.get_workspaces()
            assert type(resp) is list
            assert resp
            assert type(resp[0]) is WorkspaceReply

            resp = await i3.get_tree()
            assert type(resp) is Con

            resp = await i3.get_marks()
            assert type(resp) is list

            resp = await i3.get_binding_modes()
            assert type(resp) is list

            resp = await i3.get_config()
            assert type(resp) is ConfigReply

            resp = await i3.send_tick()
            assert type(resp) is TickReply
