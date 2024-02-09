from typing import List, Union
from .... import BaseModel
from fastapi import APIRouter, Header
from ....common.dendro_types import DendroProject, DendroFile, DendroJob
from ...clients.db import fetch_project, fetch_project_files, fetch_project_jobs, fetch_compute_resource
from ..common import api_route_wrapper
from ....common.dendro_types import CreateJobRequest, CreateJobResponse, DendroComputeResource
from ..gui.create_job_route import create_job_handler
from ...core.settings import get_settings

router = APIRouter()

# get project
class GetProjectResponse(BaseModel):
    project: DendroProject
    success: bool

class ProjectError(Exception):
    pass

@router.get("/projects/{project_id}")
@api_route_wrapper
async def get_project(project_id) -> GetProjectResponse:
    project = await fetch_project(project_id)
    if project is None:
        raise ProjectError(f"No project with ID {project_id}")
    if not project.computeResourceId:
        project.computeResourceId = get_settings().DEFAULT_COMPUTE_RESOURCE_ID
    return GetProjectResponse(project=project, success=True)

# get project files
class GetProjectFilesResponse(BaseModel):
    files: List[DendroFile]
    success: bool

@router.get("/projects/{project_id}/files")
@api_route_wrapper
async def get_project_files(project_id) -> GetProjectFilesResponse:
    files = await fetch_project_files(project_id)
    return GetProjectFilesResponse(files=files, success=True)

# get project jobs
class GetProjectJobsResponse(BaseModel):
    jobs: List[DendroJob]
    success: bool

@router.get("/projects/{project_id}/jobs")
@api_route_wrapper
async def get_project_jobs(project_id) -> GetProjectJobsResponse:
    jobs = await fetch_project_jobs(project_id)
    return GetProjectJobsResponse(jobs=jobs, success=True)

@router.post("/jobs")
@api_route_wrapper
async def create_job(
    data: CreateJobRequest,
    dendro_api_key: Union[str, None] = Header(None)
) -> CreateJobResponse:
    return await create_job_handler(
        data=data,
        dendro_api_key=dendro_api_key,
        github_access_token=None
    )

# get compute resource
class GetComputeResourceResponse(BaseModel):
    computeResource: DendroComputeResource
    success: bool

class ComputeResourceNotFoundException(Exception):
    pass

@router.get("/compute_resources/{compute_resource_id}")
@api_route_wrapper
async def get_compute_resource(compute_resource_id) -> GetComputeResourceResponse:
    compute_resource = await fetch_compute_resource(compute_resource_id, raise_on_not_found=True)
    assert compute_resource
    return GetComputeResourceResponse(computeResource=compute_resource, success=True)
