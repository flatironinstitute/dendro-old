from typing import Union, List
import traceback
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Header
from ...services._remove_detached_files_and_jobs import _remove_detached_files_and_jobs
from ...core.protocaas_types import ProtocaasFile
from ._authenticate_gui_request import _authenticate_gui_request
from ...core._get_project_role import _project_is_editable
from ...clients.db import fetch_file, fetch_project_files, fetch_project, delete_file as db_delete_file
from ...services.gui.set_file import set_file as service_set_file

router = APIRouter()

# get file
class GetFileResponse(BaseModel):
    file: ProtocaasFile
    success: bool

@router.get("/projects/{project_id}/files/{file_name:path}")
async def get_file(project_id, file_name):
    try:
        file = await fetch_file(project_id, file_name)
        if file is None:
            raise Exception(f"No file with name {file_name} in project with ID {project_id}")
        return GetFileResponse(file=file, success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# get files
class GetFilesResponse(BaseModel):
    files: List[ProtocaasFile]
    success: bool

@router.get("/projects/{project_id}/files")
async def get_files(project_id):
    try:
        files = await fetch_project_files(project_id)
        return GetFilesResponse(files=files, success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# set file
class SetFileRequest(BaseModel):
    content: str
    jobId: Union[str, None] = None
    size: Union[int, None] = None
    metadata: dict = {}

class SetFileResponse(BaseModel):
    fileId: str
    success: bool

@router.put("/projects/{project_id}/files/{file_name:path}")
async def set_file(project_id, file_name, data: SetFileRequest, github_access_token: str=Header(...)):
    try:
        # authenticate the request
        user_id = await _authenticate_gui_request(github_access_token)
        if not user_id:
            raise Exception('User not authenticated')

        # parse the request
        content = data.content
        job_id = data.jobId
        size = data.size
        metadata = data.metadata

        project = await fetch_project(project_id)
        if project is None:
            raise Exception(f"No project with ID {project_id}")
        
        if not _project_is_editable(project, user_id):
            raise Exception('User does not have permission to set file content in this project')
        
        file_id = await service_set_file(project_id=project_id, user_id=user_id, file_name=file_name, content=content, job_id=job_id, size=size, metadata=metadata)

        return SetFileResponse(fileId=file_id, success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# delete file
class DeleteFileResponse(BaseModel):
    success: bool

@router.delete("/projects/{project_id}/files/{file_name:path}")
async def delete_file(project_id, file_name, github_access_token: str=Header(...)):
    try:
        # authenticate the request
        user_id = await _authenticate_gui_request(github_access_token)
        if not user_id:
            raise Exception('User not authenticated')
        
        project = await fetch_project(project_id)
        if project is None:
            raise Exception(f"No project with ID {project_id}")
        
        if not _project_is_editable(project, user_id):
            raise Exception('User does not have permission to delete files in this project')
        
        await db_delete_file(project_id, file_name)

        # remove detached files and jobs
        await _remove_detached_files_and_jobs(project_id)

        return DeleteFileResponse(success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))