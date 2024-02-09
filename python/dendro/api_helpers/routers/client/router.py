from typing import List, Union, Optional
from .... import BaseModel
from fastapi import APIRouter, Header
from ....common.dendro_types import DendroProject, DendroFile, DendroJob
from ...clients.db import fetch_project, fetch_project_files, fetch_project_jobs, fetch_compute_resource
from ..common import api_route_wrapper
from ....common.dendro_types import CreateJobRequest, CreateJobResponse, DendroComputeResource
from ..gui.create_job_route import create_job_handler
from ...core.settings import get_settings
from ..processor.router import _resolve_dandi_url
from ...clients.db import fetch_file_by_id, fetch_job

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

# get project file download url
class GetProjectFileDownloadUrlResponse(BaseModel):
    downloadUrl: str
    success: bool

@router.get("/projects/{project_id}/files/{file_id}/download_url")
@api_route_wrapper
async def get_project_file_download_url(project_id, file_id, job_id: Optional[str] = Header(...), job_private_key: Optional[str] = Header(...), dandi_api_key: Optional[str] = Header(...)) -> GetProjectFileDownloadUrlResponse:
    # we use the file id rather than its name within the project in case we want
    # to support renaming of files in the future
    if job_id:
        if dandi_api_key:
            raise Exception("Dandi API key should not be provided when job ID is provided")
        job = await fetch_job(job_id, include_dandi_api_key=True, include_secret_params=True, include_private_key=True)
        if job is None:
            raise Exception(f"No job with ID {job_id}")
        if job.jobPrivateKey != job_private_key:
            raise Exception("Invalid job private key")
        if job.projectId != project_id:
            raise Exception(f"Job {job_id} does not belong to project {project_id}")
        # IMPORTANT: Ideally we would check that the job has access to the file.
        # Primarily we want to allow the job to access all of its inputs. But we
        # also want to allow it to access other files that are ancestors of the
        # inputs, because it could be that the files are json files with
        # embedded URIs that point to those other files. But this is somewhat
        # annoying to implement efficiently, so for now the job will have access
        # to all files in the project. That's not such a huge deal. It's
        # read-only access. So it will probably stay like this for a while, I am
        # guessing.
        dandi_api_key = job.dandiApiKey
    file = await fetch_file_by_id(project_id=project_id, file_id=file_id)
    if not file:
        raise Exception(f"No file with ID {file_id} in project {project_id}")
    if not file.content.startswith('url:'):
        raise Exception(f"Project file {file_id} is not a URL")
    url = file.content[len('url:'):]
    if dandi_api_key:
        url = await _resolve_dandi_url(url, dandi_api_key=dandi_api_key)
    return GetProjectFileDownloadUrlResponse(downloadUrl=url, success=True)
