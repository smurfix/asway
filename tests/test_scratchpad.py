from .ipctest import i3

import pytest


class TestScratchpad:
    @pytest.mark.anyio
    async def test_scratchpad(self, i3):
        async with i3.connect():
            scratchpad = (await i3.get_tree()).scratchpad()
            assert scratchpad is not None
            assert scratchpad.name == '__i3_scratch'
            assert scratchpad.type == 'workspace'
            assert not scratchpad.floating_nodes
            async with i3.ipc.open_window() as win:
                await i3.command('move scratchpad')
                scratchpad = (await i3.get_tree()).scratchpad()
                assert scratchpad is not None
                assert scratchpad.floating_nodes
