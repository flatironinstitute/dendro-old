import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from ..core.settings import get_settings


def _get_mongo_client() -> AsyncIOMotorClient:
    # We want one async mongo client per event loop
    loop = asyncio.get_event_loop()
    if hasattr(loop, '_mongo_client'):
        return loop._mongo_client
    
    # Otherwise, create a new client and store it in the global variable
    mongo_uri = get_settings().MONGO_URI
    if mongo_uri is None:
        print('MONGO_URI environment variable not set')
        raise Exception("MONGO_URI environment variable not set")
    
    client = AsyncIOMotorClient(mongo_uri)
    setattr(loop, '_mongo_client', client)

    return client