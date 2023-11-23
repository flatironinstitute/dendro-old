from typing import List
import time

from ...clients.pubsub import publish_pubsub_message
from .... import BaseModel
from fastapi import APIRouter, Header
from ...services._crypto_keys import _verify_signature
from ....common.dendro_types import DendroComputeResource, DendroComputeResourceApp, DendroJob, PubsubSubscription
from ._authenticate_gui_request import _authenticate_gui_request
from ...clients.db import fetch_compute_resource, fetch_compute_resources_for_user, update_compute_resource, fetch_compute_resource_jobs
from ...clients.db import register_compute_resource as db_register_compute_resource
from ...clients.db import delete_compute_resource as db_delete_compute_resource
from ...core.settings import get_settings
from ...core._model_dump import _model_dump
from ....mock import using_mock
from ..common import api_route_wrapper, AuthException


router = APIRouter()

# get compute resource
class GetComputeResourceResponse(BaseModel):
    computeResource: DendroComputeResource
    success: bool

class ComputeResourceNotFoundException(Exception):
    pass

@router.get("/{compute_resource_id}")
@api_route_wrapper
async def get_compute_resource(compute_resource_id) -> GetComputeResourceResponse:
    compute_resource = await fetch_compute_resource(compute_resource_id, raise_on_not_found=True)
    assert compute_resource
    return GetComputeResourceResponse(computeResource=compute_resource, success=True)

# get compute resources
class GetComputeResourcesResponse(BaseModel):
    computeResources: List[DendroComputeResource]
    success: bool

@router.get("")
@api_route_wrapper
async def get_compute_resources(github_access_token: str = Header(...)):
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    compute_resources = await fetch_compute_resources_for_user(user_id)

    return GetComputeResourcesResponse(computeResources=compute_resources, success=True)

# set compute resource apps
class SetComputeResourceAppsRequest(BaseModel):
    apps: List[DendroComputeResourceApp]

class SetComputeResourceAppsResponse(BaseModel):
    success: bool

@router.put("/{compute_resource_id}/apps")
@api_route_wrapper
async def set_compute_resource_apps(compute_resource_id, data: SetComputeResourceAppsRequest, github_access_token: str = Header(...)) -> SetComputeResourceAppsResponse:
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    # parse the request
    apps = data.apps

    compute_resource = await fetch_compute_resource(compute_resource_id, raise_on_not_found=True)
    assert compute_resource

    if compute_resource.ownerId != user_id:
        raise AuthException('User does not have permission to admin this compute resource')

    await update_compute_resource(compute_resource_id, update={
        'apps': [_model_dump(app, exclude_none=True) for app in apps],
        'timestampModified': time.time()
    })

    await publish_pubsub_message(
        channel=compute_resource_id,
        message={
            'type': 'computeResourceAppsChanaged',
            'computeResourceId': compute_resource_id
        }
    )

    return SetComputeResourceAppsResponse(success=True)

# delete compute resource
class DeleteComputeResourceResponse(BaseModel):
    success: bool

@router.delete("/{compute_resource_id}")
@api_route_wrapper
async def delete_compute_resource(compute_resource_id, github_access_token: str = Header(...)) -> DeleteComputeResourceResponse:
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    compute_resource = await fetch_compute_resource(compute_resource_id, raise_on_not_found=True)
    assert compute_resource
    if compute_resource.ownerId != user_id:
        raise AuthException('User does not have permission to delete this compute resource')

    await db_delete_compute_resource(compute_resource_id)

    return DeleteComputeResourceResponse(success=True)

# get pubsub subscription
class GetPubsubSubscriptionResponse(BaseModel):
    subscription: PubsubSubscription
    success: bool

@router.get("/{compute_resource_id}/pubsub_subscription")
@api_route_wrapper
async def get_pubsub_subscription(compute_resource_id):
    compute_resource = await fetch_compute_resource(compute_resource_id, raise_on_not_found=True)
    assert compute_resource

    if using_mock():
        subscription = PubsubSubscription(
            pubnubSubscribeKey='mock-subscribe-key',
            pubnubChannel=compute_resource_id,
            pubnubUser=compute_resource_id
        )
    else: # pragma: no cover
        VITE_PUBNUB_SUBSCRIBE_KEY = get_settings().PUBNUB_SUBSCRIBE_KEY
        if VITE_PUBNUB_SUBSCRIBE_KEY is None:
            raise KeyError('Environment variable not set: VITE_PUBNUB_SUBSCRIBE_KEY (gui)')
        subscription = PubsubSubscription(
            pubnubSubscribeKey=VITE_PUBNUB_SUBSCRIBE_KEY,
            pubnubChannel=compute_resource_id,
            pubnubUser=compute_resource_id
        )
    return GetPubsubSubscriptionResponse(subscription=subscription, success=True)

# register compute resource
class RegisterComputeResourceRequest(BaseModel):
    computeResourceId: str
    resourceCode: str
    name: str

class RegisterComputeResourceResponse(BaseModel):
    success: bool

@router.post("/register")
@api_route_wrapper
async def register_compute_resource(data: RegisterComputeResourceRequest, github_access_token: str = Header(...)) -> RegisterComputeResourceResponse:
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    # parse the request
    compute_resource_id = data.computeResourceId
    resource_code = data.resourceCode
    name = data.name

    ok = _verify_resource_code(compute_resource_id, resource_code)
    if not ok:
        raise AuthException('Invalid resource code')

    await db_register_compute_resource(compute_resource_id=compute_resource_id, name=name, user_id=user_id)

    return RegisterComputeResourceResponse(success=True)

# get jobs for compute resource
class GetJobsForComputeResourceResponse(BaseModel):
    jobs: List[DendroJob]
    success: bool

@router.get("/{compute_resource_id}/jobs")
@api_route_wrapper
async def get_jobs_for_compute_resource(compute_resource_id, github_access_token: str = Header(...)) -> GetJobsForComputeResourceResponse:
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    compute_resource = await fetch_compute_resource(compute_resource_id, raise_on_not_found=True)
    assert compute_resource
    if compute_resource.ownerId != user_id:
        raise AuthException('User does not have permission to view jobs for this compute resource')

    jobs = await fetch_compute_resource_jobs(compute_resource_id, statuses=None, include_private_keys=False)

    return GetJobsForComputeResourceResponse(jobs=jobs, success=True)

def _verify_resource_code(compute_resource_id: str, resource_code: str) -> bool:
    # check that timestamp is within 5 minutes of current time
    try:
        timestamp = int(resource_code.split('-')[0])
        if abs(timestamp - time.time()) > 300:
            return False
        signature = resource_code.split('-')[1]
        if not _verify_signature({'timestamp': timestamp}, compute_resource_id, signature):
            return False
        return True
    except Exception:
        print(f'Error verifying resource code: {resource_code}')
        return False
