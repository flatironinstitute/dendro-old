import traceback
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from ...services._remove_detached_files_and_jobs import _remove_detached_files_and_jobs
from ...core.protocaas_types import ProtocaasJob
from ._authenticate_gui_request import _authenticate_gui_request
from ...core._get_project_role import _project_is_editable
from ...clients.db import fetch_job, fetch_project, delete_job as db_delete_job


router = APIRouter()

# get job
class GetJobResponse(BaseModel):
    job: ProtocaasJob
    success: bool

@router.get("/{job_id}")
async def get_job(job_id) -> GetJobResponse:
    try:
        job = await fetch_job(job_id)
        if job is None:
            raise Exception(f"No job with ID {job_id}")
        return GetJobResponse(job=job, success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# delete job
class DeleteJobResponse(BaseModel):
    success: bool

@router.delete("/{job_id}")
async def delete_job(job_id, github_access_token: str=Header(...)) -> DeleteJobResponse:
    try:
        # authenticate the request
        user_id = await _authenticate_gui_request(github_access_token)
        if not user_id:
            raise Exception('User is not authenticated')

        job = await fetch_job(job_id)
        if job is None:
            raise Exception(f"No job with ID {job_id}")

        project = await fetch_project(job.projectId)

        if not _project_is_editable(project, user_id):
            raise Exception('User does not have permission to delete jobs in this project')

        await db_delete_job(job_id)

        # remove detached files and jobs
        await _remove_detached_files_and_jobs(job.projectId)

        return DeleteJobResponse(success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
