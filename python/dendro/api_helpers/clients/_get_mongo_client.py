from typing import Union, TYPE_CHECKING
import asyncio
from ..core.settings import get_settings
from .MockMongoClient import MockMongoClient
from ...mock import using_mock

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorClient # pragma: no cover


_globals = {
    'mock_mongo_client': None
}

def _get_mongo_client() -> Union['AsyncIOMotorClient', MockMongoClient]:
    # We want one async mongo client per event loop
    loop = asyncio.get_event_loop()
    if hasattr(loop, '_mongo_client'):
        return loop._mongo_client # type: ignore

    mongo_uri = get_settings().MONGO_URI

    # If we're using a mock client, return it
    if using_mock():
        client = _globals['mock_mongo_client'] # type: ignore
        if client is None:
            client = MockMongoClient()
            _globals['mock_mongo_client'] = client # type: ignore
    else: # pragma: no cover
        # Otherwise, create a new client
        assert mongo_uri is not None, 'MONGO_URI environment variable not set'
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(mongo_uri)

    # Store the client on the event loop
    setattr(loop, '_mongo_client', client)

    return client

def _clear_mock_mongo_databases():
    client: MockMongoClient = _globals['mock_mongo_client'] # type: ignore
    if client is not None:
        client.clear_databases()
