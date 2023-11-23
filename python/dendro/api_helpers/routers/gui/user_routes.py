import hashlib
import uuid
from fastapi import APIRouter, Header
from pydantic import BaseModel
from ..common import api_route_wrapper
from ._authenticate_gui_request import _authenticate_gui_request
from ...clients.db import set_dendro_api_key_for_user


router = APIRouter()

class CreateDendroApiKeyResponse(BaseModel):
    dendroApiKey: str
    success: bool

@router.post("/{user_id}/dendro_api_key")
@api_route_wrapper
async def create_dendro_api_key(user_id, github_access_token: str = Header(...)):
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    # create the api key as the sha1 hash a of uuid
    new_dendro_api_key = hashlib.sha1(str(uuid.uuid4()).encode('utf-8')).hexdigest()

    # set the api key for the user
    await set_dendro_api_key_for_user(user_id, new_dendro_api_key)

    return CreateDendroApiKeyResponse(dendroApiKey=new_dendro_api_key, success=True)
