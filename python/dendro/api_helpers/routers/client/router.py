from typing import List
from .... import BaseModel
from fastapi import APIRouter
from ....common.dendro_types import DendroProject, DendroFile, DendroJob
from ...clients.db import fetch_project, fetch_project_files, fetch_project_jobs
from ..common import api_route_wrapper

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
