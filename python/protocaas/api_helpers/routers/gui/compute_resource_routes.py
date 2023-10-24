from typing import List, Any
import traceback
import time
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Header
from ...services._crypto_keys import _verify_signature
from ...core.protocaas_types import ProtocaasComputeResource, ProtocaasComputeResourceApp, PubsubSubscription
from ._authenticate_gui_request import _authenticate_gui_request
from ...clients.db import fetch_compute_resource, fetch_compute_resources_for_user, update_compute_resource, fetch_compute_resource_jobs
from ...clients.db import register_compute_resource as db_register_compute_resource
from ...core.settings import get_settings


router = APIRouter()

_globals = {
    '_use_gui_mock_pubsub': False
}
def _set_use_gui_mock_pubsub(use_mock_pubsub: bool):
    _globals['_use_gui_mock_pubsub'] = use_mock_pubsub

# get compute resource
class GetComputeResourceResponse(BaseModel):
    computeResource: ProtocaasComputeResource
    success: bool

class ComputeResourceNotFoundException(Exception):
    pass

@router.get("/{compute_resource_id}")
async def get_compute_resource(compute_resource_id) -> GetComputeResourceResponse:
    try:
        compute_resource = await fetch_compute_resource(compute_resource_id)
        if compute_resource is None:
            raise ComputeResourceNotFoundException(f"No compute resource with ID {compute_resource_id}")
        return GetComputeResourceResponse(computeResource=compute_resource, success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

# get compute resources
class GetComputeResourcesResponse(BaseModel):
    computeResources: List[ProtocaasComputeResource]
    success: bool

class AuthException(Exception):
    pass

@router.get("")
async def get_compute_resources(github_access_token: str = Header(...)):
    try:
        # authenticate the request
        user_id = await _authenticate_gui_request(github_access_token)
        if not user_id:
            raise AuthException('User is not authenticated')

        compute_resources = await fetch_compute_resources_for_user(user_id)

        return GetComputeResourcesResponse(computeResources=compute_resources, success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

# set compute resource apps
class SetComputeResourceAppsRequest(BaseModel):
    apps: List[ProtocaasComputeResourceApp]

class SetComputeResourceAppsResponse(BaseModel):
    success: bool

@router.put("/{compute_resource_id}/apps")
async def set_compute_resource_apps(compute_resource_id, data: SetComputeResourceAppsRequest, github_access_token: str = Header(...)) -> SetComputeResourceAppsResponse:
    try:
        # authenticate the request
        user_id = await _authenticate_gui_request(github_access_token)
        if not user_id:
            raise AuthException('User is not authenticated')

        # parse the request
        apps = data.apps

        compute_resource = await fetch_compute_resource(compute_resource_id)
        if compute_resource is None:
            raise ComputeResourceNotFoundException(f"No compute resource with ID {compute_resource_id}")

        if compute_resource.ownerId != user_id:
            raise AuthException('User does not have permission to admin this compute resource')

        await update_compute_resource(compute_resource_id, update={
            'apps': [app.dict(exclude_none=True) for app in apps],
            'timestampModified': time.time()
        })

        return SetComputeResourceAppsResponse(success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

# delete compute resource
class DeleteComputeResourceResponse(BaseModel):
    success: bool

@router.delete("/{compute_resource_id}")
async def delete_compute_resource(compute_resource_id, github_access_token: str = Header(...)) -> DeleteComputeResourceResponse:
    try:
        # authenticate the request
        user_id = await _authenticate_gui_request(github_access_token)
        if not user_id:
            raise AuthException('User is not authenticated')

        compute_resource = await fetch_compute_resource(compute_resource_id)
        if compute_resource is None:
            raise ComputeResourceNotFoundException(f"No compute resource with ID {compute_resource_id}")
        if compute_resource.ownerId != user_id:
            raise AuthException('User does not have permission to delete this compute resource')

        await delete_compute_resource(compute_resource_id)

        return DeleteComputeResourceResponse(success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

# get pubsub subscription
class GetPubsubSubscriptionResponse(BaseModel):
    subscription: PubsubSubscription
    success: bool

@router.get("/{compute_resource_id}/pubsub_subscription")
async def get_pubsub_subscription(compute_resource_id):
    try:
        compute_resource = await fetch_compute_resource(compute_resource_id)
        if compute_resource is None:
            raise ComputeResourceNotFoundException(f"No compute resource with ID {compute_resource_id}")

        if _globals['_use_gui_mock_pubsub']:
            subscription = PubsubSubscription(
                pubnubSubscribeKey='mock-subscribe-key',
                pubnubChannel=compute_resource_id,
                pubnubUser=compute_resource_id
            )
        else:
            VITE_PUBNUB_SUBSCRIBE_KEY = get_settings().PUBNUB_SUBSCRIBE_KEY
            if VITE_PUBNUB_SUBSCRIBE_KEY is None:
                raise KeyError('Environment variable not set: VITE_PUBNUB_SUBSCRIBE_KEY (gui)')
            subscription = PubsubSubscription(
                pubnubSubscribeKey=VITE_PUBNUB_SUBSCRIBE_KEY,
                pubnubChannel=compute_resource_id,
                pubnubUser=compute_resource_id
            )
        return GetPubsubSubscriptionResponse(subscription=subscription, success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

# register compute resource
class RegisterComputeResourceRequest(BaseModel):
    computeResourceId: str
    resourceCode: str
    name: str

class RegisterComputeResourceResponse(BaseModel):
    success: bool

@router.post("/register")
async def register_compute_resource(data: RegisterComputeResourceRequest, github_access_token: str = Header(...)) -> RegisterComputeResourceResponse:
    try:
        # authenticate the request
        user_id = await _authenticate_gui_request(github_access_token)
        if user_id is None:
            raise AuthException('User is not authenticated')

        # parse the request
        compute_resource_id = data.computeResourceId
        resource_code = data.resourceCode
        name = data.name

        ok = _verify_resource_code(compute_resource_id, resource_code)
        if not ok:
            raise AuthException('Invalid resource code')

        await db_register_compute_resource(compute_resource_id=compute_resource_id, name=name, user_id=user_id)

        return RegisterComputeResourceResponse(success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

# get jobs for compute resource
class GetJobsForComputeResourceResponse(BaseModel):
    jobs: List[Any]
    success: bool

@router.get("/{compute_resource_id}/jobs")
async def get_jobs_for_compute_resource(compute_resource_id, github_access_token: str = Header(...)) -> GetJobsForComputeResourceResponse:
    try:
        # authenticate the request
        user_id = await _authenticate_gui_request(github_access_token)
        if not user_id:
            raise AuthException('User is not authenticated')

        compute_resource = await fetch_compute_resource(compute_resource_id)
        if compute_resource is None:
            raise ComputeResourceNotFoundException(f"No compute resource with ID {compute_resource_id}")
        if compute_resource.ownerId != user_id:
            raise AuthException('User does not have permission to view jobs for this compute resource')

        jobs = await fetch_compute_resource_jobs(compute_resource_id, statuses=None, include_private_keys=False)

        return GetJobsForComputeResourceResponse(jobs=jobs, success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

def _verify_resource_code(compute_resource_id: str, resource_code: str) -> bool:
    # check that timestamp is within 5 minutes of current time
    timestamp = int(resource_code.split('-')[0])
    if abs(timestamp - time.time()) > 300:
        return False
    signature = resource_code.split('-')[1]
    if not _verify_signature({'timestamp': timestamp}, compute_resource_id, signature):
        return False
    return True
