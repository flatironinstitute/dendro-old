from typing import List, Union
from .... import BaseModel
from fastapi import APIRouter, Header
from ....common.dendro_types import DendroProject, DendroFile, DendroJob
from ...clients.db import fetch_project, fetch_project_files, fetch_project_jobs, fetch_compute_resource
from ..common import api_route_wrapper
from ....common.dendro_types import CreateJobRequest, CreateJobResponse, DendroComputeResource
from ..gui.create_job_route import create_job_handler
from ...core.settings import get_settings
from ..gui._authenticate_gui_request import _authenticate_gui_request
from ...core._get_project_role import _check_user_can_edit_project
from ...services.gui.set_file import set_file as service_set_file, set_file_metadata as service_set_file_metadata
from ...services.processor.get_upload_url import _get_upload_url_for_object_key

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

# set project file
class SetProjectFileRequest(BaseModel):
    content: str
    metadata: dict = {}
    size: Union[int, None] = None


class SetProjectFileResponse(BaseModel):
    success: bool

@router.put("/projects/{project_id}/files/{file_name:path}")
@api_route_wrapper
async def set_project_file(project_id, file_name, data: SetProjectFileRequest, dendro_api_key: Union[str, None] = Header(None)) -> SetProjectFileResponse:
    size = data.size
    content = data.content
    metadata = data.metadata

    user_id = await _authenticate_gui_request(
        github_access_token=None,
        dendro_api_key=dendro_api_key,
        raise_on_not_authenticated=True
    )
    if user_id is None:
        raise Exception("User not authenticated")

    if size is None:
        if content.startswith("url:"):
            # if the content is a URL, we can get the size from the URL
            headers = {
                'Accept-Encoding': 'identity' # don't accept encoding in order to get the actual size
            }
            from aiohttp import ClientSession
            async with ClientSession() as session:
                async with session.head(content[len("url:"):], headers=headers) as response:
                    size = int(response.headers['Content-Length'])
        else:
            raise Exception("size must be specified")

    project = await fetch_project(project_id)
    assert project is not None, f"No project with ID {project_id}"

    _check_user_can_edit_project(project, user_id)

    await service_set_file(
        project_id=project_id,
        user_id=user_id,
        file_name=file_name,
        content=content,
        job_id=None,
        size=size,
        metadata=metadata,
        is_folder=False
    )

    return SetProjectFileResponse(success=True)


# set project file metadata
class SetProjectFileMetadataRequest(BaseModel):
    metadata: dict

class SetProjectFileMetadataResponse(BaseModel):
    success: bool

@router.put("/projects/{project_id}/files-metadata/{file_name:path}")
@api_route_wrapper
async def set_project_file_metadata(project_id, file_name, data: SetProjectFileMetadataRequest, dendro_api_key: Union[str, None] = Header(None)) -> SetProjectFileMetadataResponse:
    metadata = data.metadata

    user_id = await _authenticate_gui_request(
        github_access_token=None,
        dendro_api_key=dendro_api_key,
        raise_on_not_authenticated=True
    )
    if user_id is None:
        raise Exception("User not authenticated")

    project = await fetch_project(project_id)
    assert project is not None, f"No project with ID {project_id}"

    _check_user_can_edit_project(project, user_id)

    await service_set_file_metadata(
        project_id=project_id,
        file_name=file_name,
        metadata=metadata
    )

    return SetProjectFileMetadataResponse(success=True)


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
        github_access_token=None,
        force_require_approval=True  # force require approval for all jobs created via client API
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

# Initiate blob upload
class InitiateBlobUploadRequest(BaseModel):
    size: int
    sha1: str

class InitiateBlobUploadResponse(BaseModel):
    downloadUrl: str
    uploadUrl: str
    success: bool

@router.post("/projects/{project_id}/initiate_blob_upload")
@api_route_wrapper
async def initiate_blob_upload(project_id, data: InitiateBlobUploadRequest, dendro_api_key: Union[str, None] = Header(None)):
    # authenticate the request
    user_id = await _authenticate_gui_request(dendro_api_key=dendro_api_key, raise_on_not_authenticated=True)
    assert user_id

    # parse the request
    size = data.size
    sha1 = data.sha1

    assert size is not None, "size must be specified"
    assert sha1 is not None, "sha1 must be specified"

    if size > 2 * 1024 * 1024 * 1024:
        raise Exception("File size limit exceeded")

    project = await fetch_project(project_id)
    assert project is not None, f"No project with ID {project_id}"

    _check_user_can_edit_project(project, user_id)

    s = sha1
    object_key = f'dendro-uploads/{project_id}/sha1/{s[:2]}/{s[2:4]}/{s[4:6]}/{s}'
    a = await _get_upload_url_for_object_key(object_key, size=size)
    upload_url, download_url = a

    return InitiateBlobUploadResponse(downloadUrl=download_url, uploadUrl=upload_url, success=True)
