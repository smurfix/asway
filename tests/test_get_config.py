from .ipctest import i3

import asway
import io
import os

import pytest


class TestGetConfig:
    @pytest.mark.anyio
    async def test_get_config(self, i3):
        async with i3.connect():
            config = await i3.get_config()
            assert isinstance(config, asway.ConfigReply)
            p = "sway" if "SWAYSOCK" in os.environ else "i3"
            with io.open(f'tests/{p}.config', 'r', encoding='utf-8') as f:
                assert config.config == f.read()
