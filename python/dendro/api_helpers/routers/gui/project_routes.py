import os
import json
from typing import List, Optional
import time
from fastapi import APIRouter, Header
from .... import BaseModel
from ...core._create_random_id import _create_random_id
from ....common.dendro_types import DendroJob, DendroProject, DendroProjectUser
from ._authenticate_gui_request import _authenticate_gui_request
from ...core._get_project_role import _check_user_can_edit_project, _check_user_is_project_admin
from ...clients.db import fetch_project, insert_project, update_project, fetch_project_jobs, fetch_projects_for_user, fetch_all_projects, fetch_projects_with_tag
from ...services.gui.delete_project import delete_project as service_delete_project
from ..common import api_route_wrapper


router = APIRouter()

# get project
class GetProjectResponse(BaseModel):
    project: DendroProject
    success: bool

@router.get("/{project_id}")
@api_route_wrapper
async def get_project(project_id):
    project = await fetch_project(project_id, raise_on_not_found=True)
    assert project
    return GetProjectResponse(project=project, success=True)

# get projects
class GetProjectsResponse(BaseModel):
    projects: List[DendroProject]
    success: bool

@router.get("")
@api_route_wrapper
async def get_projects(github_access_token: str = Header(...), tag: Optional[str] = None):
    if tag is None:
        user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=False)
        # note: user may be None if they are not authenticated
        projects = await fetch_projects_for_user(user_id)
        return GetProjectsResponse(projects=projects, success=True)
    else:
        projects = await fetch_projects_with_tag(tag)
        return GetProjectsResponse(projects=projects, success=True)

# create project
class CreateProjectRequest(BaseModel):
    name: str

class CreateProjectResponse(BaseModel):
    projectId: str
    success: bool

@router.post("")
@api_route_wrapper
async def create_project(data: CreateProjectRequest, github_access_token: str = Header(...)) -> CreateProjectResponse:
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    # parse the request
    name = data.name

    project_id = _create_random_id(8)
    project = DendroProject(
        projectId=project_id,
        name=name,
        description='',
        ownerId=user_id,
        users=[],
        publiclyReadable=True,
        computeResourceId=None,
        tags=[],
        timestampCreated=time.time(),
        timestampModified=time.time()
    )

    await insert_project(project)

    return CreateProjectResponse(projectId=project_id, success=True)

# set project name
class SetProjectNameRequest(BaseModel):
    name: str

class SetProjectNameResponse(BaseModel):
    success: bool

@router.put("/{project_id}/name")
@api_route_wrapper
async def set_project_name(project_id, data: SetProjectNameRequest, github_access_token: str = Header(...)) -> SetProjectNameResponse:
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    project = await fetch_project(project_id, raise_on_not_found=True)
    assert project

    _check_user_can_edit_project(project, user_id)

    # parse the request
    name = data.name

    await update_project(project_id, update={
        'name': name,
        'timestampModified': time.time()
    })

    return SetProjectNameResponse(success=True)

# set project description
class SetProjectDescriptionRequest(BaseModel):
    description: str

class SetProjectDescriptionResponse(BaseModel):
    success: bool

@router.put("/{project_id}/description")
@api_route_wrapper
async def set_project_description(project_id, data: SetProjectDescriptionRequest, github_access_token: str = Header(...)) -> SetProjectDescriptionResponse:
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    project = await fetch_project(project_id, raise_on_not_found=True)
    assert project

    _check_user_can_edit_project(project, user_id)

    # parse the request
    description = data.description

    await update_project(project_id, update={
        'description': description,
        'timestampModified': time.time()
    })

    return SetProjectDescriptionResponse(success=True)

# set project tags
class SetProjectTagsRequest(BaseModel):
    tags: List[str]

class SetProjectTagsResponse(BaseModel):
    success: bool

@router.put("/{project_id}/tags")
@api_route_wrapper
async def set_project_tags(project_id, data: SetProjectTagsRequest, github_access_token: str = Header(...)) -> SetProjectTagsResponse:
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    project = await fetch_project(project_id, raise_on_not_found=True)
    assert project

    _check_user_can_edit_project(project, user_id)

    # parse the request
    tags = data.tags

    await update_project(project_id, update={
        'tags': tags,
        'timestampModified': time.time()
    })

    return SetProjectTagsResponse(success=True)

# delete project
class DeleteProjectResponse(BaseModel):
    success: bool

@router.delete("/{project_id}")
@api_route_wrapper
async def delete_project(project_id, github_access_token: str = Header(...)) -> DeleteProjectResponse:
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    project = await fetch_project(project_id, raise_on_not_found=True)
    assert project

    _check_user_is_project_admin(project, user_id)

    await service_delete_project(project)

    return DeleteProjectResponse(success=True)

# get jobs
class GetJobsResponse(BaseModel):
    jobs: List[DendroJob]
    success: bool

@router.get("/{project_id}/jobs")
@api_route_wrapper
async def get_jobs(project_id):
    jobs = await fetch_project_jobs(project_id, include_private_keys=False)
    return GetJobsResponse(jobs=jobs, success=True)

# set project publicly readable
class SetProjectPubliclyReadableRequest(BaseModel):
    publiclyReadable: bool

class SetProjectPubliclyReadableResponse(BaseModel):
    success: bool

@router.put("/{project_id}/publicly_readable")
@api_route_wrapper
async def set_project_public(project_id, data: SetProjectPubliclyReadableRequest, github_access_token: str = Header(...)):
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    project = await fetch_project(project_id, raise_on_not_found=True)
    assert project

    _check_user_is_project_admin(project, user_id)

    # parse the request
    publicly_readable = data.publiclyReadable

    await update_project(project_id, update={
        'publiclyReadable': publicly_readable,
        'timestampModified': time.time()
    })

    return SetProjectPubliclyReadableResponse(success=True)

# set project compute resource id
class SetProjectComputeResourceIdRequest(BaseModel):
    computeResourceId: str

class SetProjectComputeResourceIdResponse(BaseModel):
    success: bool

@router.put("/{project_id}/compute_resource_id")
@api_route_wrapper
async def set_project_compute_resource_id(project_id, data: SetProjectComputeResourceIdRequest, github_access_token: str = Header(...)):
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    project = await fetch_project(project_id, raise_on_not_found=True)
    assert project

    _check_user_is_project_admin(project, user_id)

    # parse the request
    compute_resource_id = data.computeResourceId

    await update_project(project_id, update={
        'computeResourceId': compute_resource_id,
        'timestampModified': time.time()
    })

    return SetProjectComputeResourceIdResponse(success=True)

# set project users
class SetProjectUsersRequest(BaseModel):
    users: List[DendroProjectUser]

class SetProjectUsersResponse(BaseModel):
    success: bool

@router.put("/{project_id}/users")
@api_route_wrapper
async def set_project_users(project_id, data: SetProjectUsersRequest, github_access_token: str = Header(...)):
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    project = await fetch_project(project_id, raise_on_not_found=True)
    assert project

    _check_user_is_project_admin(project, user_id)

    # parse the request
    users = data.users

    await update_project(project_id, update={
        'users': users,
        'timestampModified': time.time()
    })

    return SetProjectUsersResponse(success=True)

# Admin get all projects
class AdminGetAllProjectsResponse(BaseModel):
    projects: List[DendroProject]
    success: bool

@router.get("/admin/get_all_projects")
@api_route_wrapper
async def admin_get_all_projects(github_access_token: str = Header(...)):
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    ADMIN_USER_IDS_JSON = os.getenv('ADMIN_USER_IDS', '[]')
    ADMIN_USER_IDS = json.loads(ADMIN_USER_IDS_JSON)

    if user_id not in ADMIN_USER_IDS:
        raise Exception('User is not admin')

    projects = await fetch_all_projects()
    return AdminGetAllProjectsResponse(projects=projects, success=True)
