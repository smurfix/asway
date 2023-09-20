from .ipctest import i3

import pytest


class TestBindingModes:
    @pytest.mark.anyio
    async def test_binding_modes(self, i3):
        async with i3.connect():
            binding_modes = await i3.get_binding_modes()
            assert isinstance(binding_modes, list)
            assert len(binding_modes) == 2
            assert 'default' in binding_modes
            assert 'resize' in binding_modes
