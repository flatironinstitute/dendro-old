from typing import List
from .... import BaseModel
from fastapi import APIRouter, Header
from ...services._crypto_keys import _verify_signature_str
from ....common.dendro_types import DendroComputeResourceApp, DendroFile, DendroJob, ComputeResourceSpec, PubsubSubscription
from ...clients.db import fetch_compute_resource, fetch_compute_resource_jobs, fetch_multi_project_files, set_compute_resource_spec
from ...core.settings import get_settings
from ....mock import using_mock
from ..common import api_route_wrapper

router = APIRouter()

# get apps
class GetAppsResponse(BaseModel):
    apps: List[DendroComputeResourceApp]
    success: bool

class ComputeResourceNotFoundException(Exception):
    pass

@router.get("/compute_resources/{compute_resource_id}/apps")
@api_route_wrapper
async def compute_resource_get_apps(
    compute_resource_id: str,
    compute_resource_payload: str = Header(...),
    compute_resource_signature: str = Header(...)
) -> GetAppsResponse:
    # authenticate the request
    expected_payload = f'/api/compute_resource/compute_resources/{compute_resource_id}/apps'
    _authenticate_compute_resource_request(
        compute_resource_id=compute_resource_id,
        compute_resource_payload=compute_resource_payload,
        compute_resource_signature=compute_resource_signature,
        expected_payload=expected_payload
    )

    compute_resource = await fetch_compute_resource(compute_resource_id, raise_on_not_found=True)
    assert compute_resource
    apps = compute_resource.apps
    return GetAppsResponse(apps=apps, success=True)

# get pubsub subscription
class GetPubsubSubscriptionResponse(BaseModel):
    subscription: PubsubSubscription
    success: bool

@router.get("/compute_resources/{compute_resource_id}/pubsub_subscription")
@api_route_wrapper
async def compute_resource_get_pubsub_subscription(
    compute_resource_id: str,
    compute_resource_payload: str = Header(...),
    compute_resource_signature: str = Header(...)
):
    # authenticate the request
    expected_payload = f'/api/compute_resource/compute_resources/{compute_resource_id}/pubsub_subscription'
    _authenticate_compute_resource_request(
        compute_resource_id=compute_resource_id,
        compute_resource_payload=compute_resource_payload,
        compute_resource_signature=compute_resource_signature,
        expected_payload=expected_payload
    )

    compute_resource = await fetch_compute_resource(compute_resource_id, raise_on_not_found=True)
    assert compute_resource
    if using_mock():
        subscription = PubsubSubscription(
            pubnubSubscribeKey='mock-subscribe-key',
            pubnubChannel=compute_resource_id,
            pubnubUser=compute_resource_id
        )
        return GetPubsubSubscriptionResponse(subscription=subscription, success=True)
    else: # pragma: no cover
        VITE_PUBNUB_SUBSCRIBE_KEY = get_settings().PUBNUB_SUBSCRIBE_KEY
        if VITE_PUBNUB_SUBSCRIBE_KEY is None:
            raise KeyError('Environment variable not set: VITE_PUBNUB_SUBSCRIBE_KEY (compute_resource)')
        subscription = PubsubSubscription(
            pubnubSubscribeKey=VITE_PUBNUB_SUBSCRIBE_KEY,
            pubnubChannel=compute_resource_id,
            pubnubUser=compute_resource_id
        )
        return GetPubsubSubscriptionResponse(subscription=subscription, success=True)

# get unfinished jobs
class GetUnfinishedJobsResponse(BaseModel):
    jobs: List[DendroJob]
    success: bool

@router.get("/compute_resources/{compute_resource_id}/unfinished_jobs")
@api_route_wrapper
async def compute_resource_get_unfinished_jobs(
    compute_resource_id: str,
    compute_resource_payload: str = Header(...),
    compute_resource_signature: str = Header(...),
) -> GetUnfinishedJobsResponse:
    # authenticate the request
    expected_payload = f'/api/compute_resource/compute_resources/{compute_resource_id}/unfinished_jobs'
    _authenticate_compute_resource_request(
        compute_resource_id=compute_resource_id,
        compute_resource_payload=compute_resource_payload,
        compute_resource_signature=compute_resource_signature,
        expected_payload=expected_payload
    )

    jobs = await fetch_compute_resource_jobs(compute_resource_id, statuses=['pending', 'queued', 'starting', 'running'], exclude_those_pending_approval=True, include_private_keys=True)

    # exclude those for which the input files are pending
    relevant_project_ids: list[str] = []
    for job in jobs:
        if job.projectId not in relevant_project_ids:
            relevant_project_ids.append(job.projectId)
    pending_output_files: List[DendroFile] = await fetch_multi_project_files(project_ids=relevant_project_ids, pending_only=True)
    pending_output_file_names = set([f.fileName for f in pending_output_files])
    ready_jobs: List[DendroJob] = []
    for job in jobs:
        okay = True
        for input_file in job.inputFiles:
            if input_file.fileName in pending_output_file_names:
                okay = False
                break
        if okay:
            ready_jobs.append(job)

    return GetUnfinishedJobsResponse(jobs=ready_jobs, success=True)

# set spec
class SetSpecRequest(BaseModel):
    spec: ComputeResourceSpec

class SetSpecResponse(BaseModel):
    success: bool

@router.put("/compute_resources/{compute_resource_id}/spec")
@api_route_wrapper
async def compute_resource_set_spec(
    compute_resource_id,
    data: SetSpecRequest,
    compute_resource_payload: str = Header(...),
    compute_resource_signature: str = Header(...)
) -> SetSpecResponse:
    # authenticate the request
    expected_payload = f'/api/compute_resource/compute_resources/{compute_resource_id}/spec'
    _authenticate_compute_resource_request(
        compute_resource_id=compute_resource_id,
        compute_resource_payload=compute_resource_payload,
        compute_resource_signature=compute_resource_signature,
        expected_payload=expected_payload
    )

    spec = data.spec

    await set_compute_resource_spec(compute_resource_id, spec)

    return SetSpecResponse(success=True)

class UnexpectedException(Exception):
    pass

class InvalidSignatureException(Exception):
    pass


def _authenticate_compute_resource_request(
    compute_resource_id: str,
    compute_resource_payload: str,
    compute_resource_signature: str,
    expected_payload: str
):
    if compute_resource_payload != expected_payload:
        raise UnexpectedException('Unexpected payload')
    if not _verify_signature_str(compute_resource_payload, compute_resource_id, compute_resource_signature):
        raise InvalidSignatureException('Invalid signature')
