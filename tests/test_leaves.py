from .ipctest import i3

import pytest
import anyio

class TestLeaves:
    @pytest.mark.anyio
    async def test_workspace_leaves(self, i3):
        async with i3.connect():
            ws_name = await i3.ipc.fresh_workspace()
            async with i3.ipc.open_window() as con1:
                await anyio.sleep(0.2)
                assert not (await i3.get_tree()).find_focused().is_floating()
                await i3.ipc.command_checked(f'[id={con1}] floating enable')
                await anyio.sleep(0.2)
                assert (await i3.get_tree()).find_focused().is_floating()
                async with i3.ipc.open_window(), i3.ipc.open_window():

                    await anyio.sleep(0.2)
                    tree = await i3.get_tree()
                    ws = [w for w in tree.workspaces() if w.name == ws_name][0]
                    assert (len(ws.leaves()) == 3)
