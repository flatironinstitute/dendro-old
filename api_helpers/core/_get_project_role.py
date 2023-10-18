from typing import Union
from .protocaas_types import ProtocaasProject


def _get_project_role(project: ProtocaasProject, user_id: Union[str, None]) -> str:
    if user_id:
        if user_id.startswith('admin|'):
            return 'admin'
        if project.ownerId == user_id:
            return 'admin'
        user = next((x for x in project.users if x.userId == user_id), None)
        if user:
            return user.role
    if project.publiclyReadable:
        return 'viewer'
    else:
        return 'none'

def _project_is_readable(project: ProtocaasProject, user_id: Union[str, None]) -> bool:
    return _get_project_role(project, user_id) in ['admin', 'editor', 'viewer']

def _project_is_editable(project: ProtocaasProject, user_id: Union[str, None]) -> bool:
    return _get_project_role(project, user_id) in ['admin', 'editor']

def _user_is_project_admin(project: ProtocaasProject, user_id: Union[str, None]) -> bool:
    return _get_project_role(project, user_id) == 'admin'