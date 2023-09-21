from .ipctest import i3

import sys
import pytest
import anyio


class HandlerException(Exception):
    pass


class TestEventExceptions:
    def exception_throwing_handler(self, e):
        print("J",file=sys.stderr)
        raise HandlerException()

    @pytest.mark.anyio
    async def test_event_exceptions(self, i3):
        with pytest.raises((HandlerException,ExceptionGroup)) as err:
            async with i3.connect():
                i3.on('tick', self.exception_throwing_handler)
                await anyio.sleep(0.1)
                await i3.send_tick()
                await anyio.sleep(0.2)
        if isinstance(err.value,ExceptionGroup):
            if not len(err.value.exceptions) == 1:
                raise err.value
            if not isinstance(err.value.exceptions[0],HandlerException):
                raise err.value.exceptions[0]
