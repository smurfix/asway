import pytest

@pytest.fixture
def anyio_backend():
#   return 'asyncio'
    return 'trio'

#import logging
#logging.basicConfig(level=logging.DEBUG)
