from fastapi import APIRouter, Header
from .... import BaseModel
from ....common.dendro_types import DendroScript
from ._authenticate_gui_request import _authenticate_gui_request
from ...core._get_project_role import _check_user_can_edit_project
from ..common import api_route_wrapper
from ...clients.db import fetch_script as db_fetch_script, delete_script as db_delete_script, set_script_content as db_set_script_content, rename_script as db_rename_script
from ...clients.db import fetch_project as db_fetch_project

router = APIRouter()

# get script
class GetScriptResponse(BaseModel):
    script: DendroScript
    success: bool

class ScriptNotFoundException(Exception):
    pass

@router.get("/{script_id}")
@api_route_wrapper
async def get_script(script_id) -> GetScriptResponse:
    script = await db_fetch_script(script_id)
    assert script
    return GetScriptResponse(script=script, success=True)

# delete script
class DeleteScriptResponse(BaseModel):
    success: bool

@router.delete("/{script_id}")
@api_route_wrapper
async def delete_script(script_id, github_access_token: str = Header(...)) -> DeleteScriptResponse:
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    script = await db_fetch_script(script_id)
    assert script

    project = await db_fetch_project(script.projectId, raise_on_not_found=True)
    assert project

    _check_user_can_edit_project(project, user_id)

    await db_delete_script(script_id)

    return DeleteScriptResponse(success=True)

# Set script content
class SetScriptContentRequest(BaseModel):
    content: str

class SetScriptContentResponse(BaseModel):
    success: bool

@router.put("/{script_id}/content")
@api_route_wrapper
async def set_script_content(script_id, data: SetScriptContentRequest, github_access_token: str = Header(...)) -> SetScriptContentResponse:
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    script = await db_fetch_script(script_id)
    assert script

    project = await db_fetch_project(script.projectId, raise_on_not_found=True)
    assert project

    _check_user_can_edit_project(project, user_id)

    await db_set_script_content(script_id, data.content)

    return SetScriptContentResponse(success=True)

# Rename script
class RenameScriptRequest(BaseModel):
    name: str

class RenameScriptResponse(BaseModel):
    success: bool

@router.put("/{script_id}/name")
@api_route_wrapper
async def rename_script(script_id, data: RenameScriptRequest, github_access_token: str = Header(...)) -> RenameScriptResponse:
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token=github_access_token, raise_on_not_authenticated=True)
    assert user_id

    script = await db_fetch_script(script_id)
    assert script

    project = await db_fetch_project(script.projectId, raise_on_not_found=True)
    assert project

    _check_user_can_edit_project(project, user_id)

    await db_rename_script(script_id, data.name)

    return RenameScriptResponse(success=True)
