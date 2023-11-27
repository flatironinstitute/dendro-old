import os
import json
from fastapi import APIRouter, Header
from .... import BaseModel
from ....common.dendro_types import ComputeResourceUserUsage
from ._authenticate_gui_request import _authenticate_gui_request
from ..common import api_route_wrapper
from ...services.gui.get_compute_resource_user_usage import get_compute_resource_user_usage


router = APIRouter()

# get usage
class GetUsageResponse(BaseModel):
    usage: ComputeResourceUserUsage
    success: bool

@router.get("/compute_resource/{compute_resource_id}/user/{user_id}")
@api_route_wrapper
async def get_usage(compute_resource_id, user_id, github_access_token: str = Header(...)):
    # url decode the %7C in the user_id
    user_id = user_id.replace('%7C', '|')

    # authenticate the request
    auth_user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert auth_user_id

    if user_id != auth_user_id:
        ADMIN_USER_IDS_JSON = os.getenv('ADMIN_USER_IDS', '[]')
        ADMIN_USER_IDS = json.loads(ADMIN_USER_IDS_JSON)

        if user_id not in ADMIN_USER_IDS:
            raise Exception(f'User is not admin and cannot view usage for other users ({user_id} != {auth_user_id})')

    # get usage
    usage = await get_compute_resource_user_usage(compute_resource_id=compute_resource_id, user_id=user_id)

    return GetUsageResponse(usage=usage, success=True)
