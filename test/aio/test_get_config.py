from .ipctest import IpcTest
import asway
import io

import pytest


class TestGetConfig(IpcTest):
    @pytest.mark.asyncio
    async def test_get_config(self, i3):
        config = await i3.get_config()
        assert isinstance(config, asway.ConfigReply)
        with io.open('test/i3.config', 'r', encoding='utf-8') as f:
            assert config.config == f.read()
