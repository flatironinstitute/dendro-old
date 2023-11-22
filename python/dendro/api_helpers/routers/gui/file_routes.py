from typing import Union, List
from .... import BaseModel
from fastapi import APIRouter, Header
from ...services._remove_detached_files_and_jobs import _remove_detached_files_and_jobs
from ....common.dendro_types import DendroFile
from ._authenticate_gui_request import _authenticate_gui_request
from ...core._get_project_role import _check_user_can_edit_project
from ...clients.db import fetch_file, fetch_project_files, fetch_project, delete_file as db_delete_file
from ...services.gui.set_file import set_file as service_set_file
from ..common import api_route_wrapper
from ...core._create_random_id import _create_random_id
from ...services.processor.get_upload_url import _get_upload_url_for_object_key

router = APIRouter()

# get file
class GetFileResponse(BaseModel):
    file: DendroFile
    success: bool

@router.get("/projects/{project_id}/files/{file_name:path}")
@api_route_wrapper
async def get_file(project_id, file_name):
    file = await fetch_file(project_id, file_name)
    assert file is not None, f"No file with name {file_name} in project with ID {project_id}"
    return GetFileResponse(file=file, success=True)

# get files
class GetFilesResponse(BaseModel):
    files: List[DendroFile]
    success: bool

@router.get("/projects/{project_id}/files")
@api_route_wrapper
async def get_files(project_id):
    files = await fetch_project_files(project_id)
    return GetFilesResponse(files=files, success=True)

# set file
class SetFileRequest(BaseModel):
    content: str # for example, url:https://...
    jobId: Union[str, None] = None
    size: Union[int, None] = None
    metadata: dict = {}

class SetFileResponse(BaseModel):
    fileId: str
    success: bool

@router.put("/projects/{project_id}/files/{file_name:path}")
@api_route_wrapper
async def set_file(project_id, file_name, data: SetFileRequest, github_access_token: str = Header(...)):
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    # parse the request
    content = data.content
    job_id = data.jobId
    size = data.size
    metadata = data.metadata

    assert size is not None, "size must be specified"

    project = await fetch_project(project_id)
    assert project is not None, f"No project with ID {project_id}"

    _check_user_can_edit_project(project, user_id)

    file_id = await service_set_file(project_id=project_id, user_id=user_id, file_name=file_name, content=content, job_id=job_id, size=size, metadata=metadata)

    return SetFileResponse(fileId=file_id, success=True)

# delete file
class DeleteFileResponse(BaseModel):
    success: bool

@router.delete("/projects/{project_id}/files/{file_name:path}")
@api_route_wrapper
async def delete_file(project_id, file_name, github_access_token: str = Header(...)):
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    project = await fetch_project(project_id)
    assert project is not None, f"No project with ID {project_id}"

    _check_user_can_edit_project(project, user_id)

    await db_delete_file(project_id, file_name)

    # remove detached files and jobs
    await _remove_detached_files_and_jobs(project_id)

    return DeleteFileResponse(success=True)

# initiate file upload
class CreateFileAndInitiateUploadRequest(BaseModel):
    fileName: str # file name within the project
    size: int
    metadata: dict = {}

class CreateFileAndInitiateUploadResponse(BaseModel):
    fileId: str
    uploadUrl: str
    success: bool

@router.post("/projects/{project_id}/create_file_and_initiate_upload")
@api_route_wrapper
async def create_file_and_initiate_upload(project_id, data: CreateFileAndInitiateUploadRequest, github_access_token: str = Header(...)):
    # Generate a signed URL for uploading a file to the output bucket and set the file in the project.
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    # parse the request
    file_name = data.fileName
    size = data.size
    metadata = data.metadata

    assert size is not None, "size must be specified"

    if size > 100e6:
        raise Exception("File size limit exceeded")

    project = await fetch_project(project_id)
    assert project is not None, f"No project with ID {project_id}"

    _check_user_can_edit_project(project, user_id)

    # it would be nice to use the file name here, but that could cause a problem if the user renames a file, or makes a copy within the project
    _random_file_name = f'{_create_random_id(12)}'
    object_key = f'dendro-uploads/{project_id}/{_random_file_name}'
    upload_url, download_url = await _get_upload_url_for_object_key(object_key, size=size)

    content = f'url:{download_url}'
    file_id = await service_set_file(project_id=project_id, user_id=user_id, file_name=file_name, content=content, job_id=None, size=size, metadata=metadata)

    return CreateFileAndInitiateUploadResponse(fileId=file_id, uploadUrl=upload_url, success=True)
