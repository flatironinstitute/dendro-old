from typing import List, Optional
import time
import traceback
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from ...core._create_random_id import _create_random_id
from ...core.protocaas_types import ProtocaasJob, ProtocaasProject, ProtocaasProjectUser
from ._authenticate_gui_request import _authenticate_gui_request
from ...core._get_project_role import _project_is_editable, _user_is_project_admin
from ...clients.db import fetch_project, insert_project, update_project, fetch_project_jobs, fetch_projects_for_user, fetch_projects_with_tag
from ...services.gui.delete_project import delete_project as service_delete_project


router = APIRouter()

# get project
class GetProjectResponse(BaseModel):
    project: ProtocaasProject
    success: bool

@router.get("/{project_id}")
async def get_project(project_id):
    try:
        project = await fetch_project(project_id)
        assert project is not None, f"No project with ID {project_id}"
        return GetProjectResponse(project=project, success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

# get projects
class GetProjectsResponse(BaseModel):
    projects: List[ProtocaasProject]
    success: bool

@router.get("")
async def get_projects(github_access_token: str = Header(...), tag: Optional[str] = None):
    try:
        if tag is None:
            user_id = await _authenticate_gui_request(github_access_token)
            projects = await fetch_projects_for_user(user_id)
            return GetProjectsResponse(projects=projects, success=True)
        else:
            projects = await fetch_projects_with_tag(tag)
            return GetProjectsResponse(projects=projects, success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

# create project
class CreateProjectRequest(BaseModel):
    name: str

class CreateProjectResponse(BaseModel):
    projectId: str
    success: bool

class AuthException(Exception):
    pass

@router.post("")
async def create_project(data: CreateProjectRequest, github_access_token: str = Header(...)) -> CreateProjectResponse:
    try:
        # authenticate the request
        user_id = await _authenticate_gui_request(github_access_token)
        if not user_id:
            raise AuthException('User is not authenticated')

        # parse the request
        name = data.name

        project_id = _create_random_id(8)
        project = ProtocaasProject(
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
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

# set project name
class SetProjectNameRequest(BaseModel):
    name: str

class SetProjectNameResponse(BaseModel):
    success: bool

@router.put("/{project_id}/name")
async def set_project_name(project_id, data: SetProjectNameRequest, github_access_token: str = Header(...)) -> SetProjectNameResponse:
    try:
        # authenticate the request
        user_id = await _authenticate_gui_request(github_access_token)
        if not user_id:
            raise AuthException('User is not authenticated')

        project = await fetch_project(project_id)
        assert project is not None, f"No project with ID {project_id}"

        if not _project_is_editable(project, user_id):
            raise AuthException('User does not have permission to set project name')

        # parse the request
        name = data.name

        await update_project(project_id, update={
            'name': name,
            'timestampModified': time.time()
        })

        return SetProjectNameResponse(success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

# set project description
class SetProjectDescriptionRequest(BaseModel):
    description: str

class SetProjectDescriptionResponse(BaseModel):
    success: bool

@router.put("/{project_id}/description")
async def set_project_description(project_id, data: SetProjectDescriptionRequest, github_access_token: str = Header(...)) -> SetProjectDescriptionResponse:
    try:
        # authenticate the request
        user_id = await _authenticate_gui_request(github_access_token)
        if not user_id:
            raise AuthException('User is not authenticated')

        project = await fetch_project(project_id)
        assert project is not None, f"No project with ID {project_id}"

        if not _project_is_editable(project, user_id):
            raise AuthException('User does not have permission to set project description')

        # parse the request
        description = data.description

        await update_project(project_id, update={
            'description': description,
            'timestampModified': time.time()
        })

        return SetProjectDescriptionResponse(success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

# set project tags
class SetProjectTagsRequest(BaseModel):
    tags: List[str]

class SetProjectTagsResponse(BaseModel):
    success: bool

@router.put("/{project_id}/tags")
async def set_project_tags(project_id, data: SetProjectTagsRequest, github_access_token: str = Header(...)) -> SetProjectTagsResponse:
    try:
        # authenticate the request
        user_id = await _authenticate_gui_request(github_access_token)
        if not user_id:
            raise AuthException('User is not authenticated')

        project = await fetch_project(project_id)
        assert project is not None, f"No project with ID {project_id}"

        if not _project_is_editable(project, user_id):
            raise AuthException('User does not have permission to set project tags')

        # parse the request
        tags = data.tags

        await update_project(project_id, update={
            'tags': tags,
            'timestampModified': time.time()
        })

        return SetProjectTagsResponse(success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

# delete project
class DeleteProjectResponse(BaseModel):
    success: bool

@router.delete("/{project_id}")
async def delete_project(project_id, github_access_token: str = Header(...)) -> DeleteProjectResponse:
    try:
        # authenticate the request
        user_id = await _authenticate_gui_request(github_access_token)
        if not user_id:
            raise AuthException('User is not authenticated')

        project = await fetch_project(project_id)
        assert project is not None, f"No project with ID {project_id}"

        if not _user_is_project_admin(project, user_id):
            raise AuthException('User does not have permission to delete this project')

        await service_delete_project(project)

        return DeleteProjectResponse(success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

# get jobs
class GetJobsResponse(BaseModel):
    jobs: List[ProtocaasJob]
    success: bool

@router.get("/{project_id}/jobs")
async def get_jobs(project_id):
    try:
        jobs = await fetch_project_jobs(project_id, include_private_keys=False)
        return GetJobsResponse(jobs=jobs, success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

# set project publicly readable
class SetProjectPubliclyReadableRequest(BaseModel):
    publiclyReadable: bool

class SetProjectPubliclyReadableResponse(BaseModel):
    success: bool

@router.put("/{project_id}/publicly_readable")
async def set_project_public(project_id, data: SetProjectPubliclyReadableRequest, github_access_token: str = Header(...)):
    try:
        # authenticate the request
        user_id = await _authenticate_gui_request(github_access_token)
        if not user_id:
            raise AuthException('User is not authenticated')

        project = await fetch_project(project_id)
        assert project is not None, f"No project with ID {project_id}"
        if not _user_is_project_admin(project, user_id):
            raise AuthException('User does not have permission to admin this project')

        # parse the request
        publicly_readable = data.publiclyReadable

        await update_project(project_id, update={
            'publiclyReadable': publicly_readable,
            'timestampModified': time.time()
        })

        return SetProjectPubliclyReadableResponse(success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e


# set project compute resource id
class SetProjectComputeResourceIdRequest(BaseModel):
    computeResourceId: str

class SetProjectComputeResourceIdResponse(BaseModel):
    success: bool

@router.put("/{project_id}/compute_resource_id")
async def set_project_compute_resource_id(project_id, data: SetProjectComputeResourceIdRequest, github_access_token: str = Header(...)):
    try:
        # authenticate the request
        user_id = await _authenticate_gui_request(github_access_token)
        if not user_id:
            raise AuthException('User is not authenticated')

        project = await fetch_project(project_id)
        assert project is not None, f"No project with ID {project_id}"
        if not _user_is_project_admin(project, user_id):
            raise AuthException('User does not have permission to admin this project')

        # parse the request
        compute_resource_id = data.computeResourceId

        await update_project(project_id, update={
            'computeResourceId': compute_resource_id,
            'timestampModified': time.time()
        })

        return SetProjectComputeResourceIdResponse(success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

# set project users
class SetProjectUsersRequest(BaseModel):
    users: List[ProtocaasProjectUser]

class SetProjectUsersResponse(BaseModel):
    success: bool

@router.put("/{project_id}/users")
async def set_project_users(project_id, data: SetProjectUsersRequest, github_access_token: str = Header(...)):
    try:
        # authenticate the request
        user_id = await _authenticate_gui_request(github_access_token)
        if not user_id:
            raise AuthException('User is not authenticated')

        project = await fetch_project(project_id)
        assert project is not None, f"No project with ID {project_id}"
        if not _user_is_project_admin(project, user_id):
            raise AuthException('User does not have permission to admin this project')

        # parse the request
        users = data.users

        await update_project(project_id, update={
            'users': users,
            'timestampModified': time.time()
        })

        return SetProjectUsersResponse(success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e
