from .ipctest import i3

import pytest
import anyio


class TestOutput:
    @pytest.mark.anyio
    async def test_output(self, i3):
        async with i3.connect():
            await i3.command('workspace 12')
            await anyio.sleep(0.2)
            outputs = await i3.get_outputs()
            assert len(outputs) == 1
            screen = outputs[0]
            assert screen.current_workspace == '12'
            assert screen.primary is False
