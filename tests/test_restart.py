from .ipctest import i3

import pytest


class TestRestart:
    @pytest.mark.anyio
    async def test_auto_reconnect(self, i3):
        async with i3.connect():
            i3._auto_reconnect = True
            await i3.command('restart')
            assert await i3.command('nop')
