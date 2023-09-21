from .ipctest import i3

import pytest
import anyio


class TestGetMarks:
    @pytest.mark.anyio
    async def test_get_marks(self, i3):
        async with i3.connect(), i3.ipc.open_window():
            await i3.ipc.command_checked('mark a')
            await i3.ipc.command_checked('mark --add b')
            async with i3.ipc.open_window():
                await i3.ipc.command_checked('mark "(╯°□°）╯︵ ┻━┻"')

                marks = await i3.get_marks()
                assert isinstance(marks, list)
                assert len(marks) == 3
                assert 'a' in marks
                assert 'b' in marks
                assert '(╯°□°）╯︵ ┻━┻' in marks
