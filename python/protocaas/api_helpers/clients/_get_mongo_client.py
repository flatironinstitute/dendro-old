from typing import Union
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from ..core.settings import get_settings
from .MockMongoClient import MockMongoClient


def _set_use_mock_mongo_client(use_mock: bool) -> None: # For testing
    loop = asyncio.get_event_loop()
    setattr(loop, '_use_mock_mongo_client', use_mock)

def _get_mongo_client() -> Union[AsyncIOMotorClient, MockMongoClient]:
    # We want one async mongo client per event loop
    loop = asyncio.get_event_loop()
    if hasattr(loop, '_mongo_client'):
        return loop._mongo_client # type: ignore

    # If we're using a mock client, return it
    if hasattr(loop, '_use_mock_mongo_client') and loop._use_mock_mongo_client: # type: ignore
        client = MockMongoClient()
    else:
        # Otherwise, create a new client and store it in the global variable
        mongo_uri = get_settings().MONGO_URI
        if mongo_uri is None:
            print('MONGO_URI environment variable not set')
            raise KeyError("MONGO_URI environment variable not set")

        client = AsyncIOMotorClient(mongo_uri)

    setattr(loop, '_mongo_client', client)

    return client
