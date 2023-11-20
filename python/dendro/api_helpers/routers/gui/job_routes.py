from fastapi import APIRouter, Header
from .... import BaseModel
from ...services._remove_detached_files_and_jobs import _remove_detached_files_and_jobs
from ....common.dendro_types import DendroJob
from ._authenticate_gui_request import _authenticate_gui_request
from ...core._get_project_role import _check_user_can_edit_project
from ...clients.db import fetch_job, fetch_project, delete_job as db_delete_job
from ..common import api_route_wrapper


router = APIRouter()

# get job
class GetJobResponse(BaseModel):
    job: DendroJob
    success: bool

class JobNotFoundException(Exception):
    pass

@router.get("/{job_id}")
@api_route_wrapper
async def get_job(job_id) -> GetJobResponse:
    job = await fetch_job(job_id, raise_on_not_found=True)
    assert job
    return GetJobResponse(job=job, success=True)

# delete job
class DeleteJobResponse(BaseModel):
    success: bool

@router.delete("/{job_id}")
@api_route_wrapper
async def delete_job(job_id, github_access_token: str = Header(...)) -> DeleteJobResponse:
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    job = await fetch_job(job_id, raise_on_not_found=True)
    assert job

    project = await fetch_project(job.projectId, raise_on_not_found=True)
    assert project

    _check_user_can_edit_project(project, user_id)

    await db_delete_job(job_id)

    # remove detached files and jobs
    await _remove_detached_files_and_jobs(job.projectId)

    return DeleteJobResponse(success=True)
