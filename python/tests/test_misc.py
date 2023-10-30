import pytest
from dendro.api_helpers.core._get_project_role import _check_user_can_edit_project, _check_user_can_read_project, _check_user_is_project_admin, _project_has_user, AuthException
from dendro.api_helpers.core.dendro_types import DendroProject, DendroProjectUser

def test_get_project_role():
    project = DendroProject(
        projectId='test-project-id',
        name='test-project-name',
        description='test-project-description',
        ownerId='github|test-owner-id',
        users=[
            DendroProjectUser(
                userId='github|admin-user',
                role='admin'
            ),
            DendroProjectUser(
                userId='github|editor-user',
                role='editor'
            ),
            DendroProjectUser(
                userId='github|viewer-user',
                role='viewer'
            )
        ],
        publiclyReadable=False,
        tags=[],
        timestampCreated=0,
        timestampModified=0,
        computeResourceId=None
    )
    _check_user_can_read_project(project, 'github|admin-user')
    _check_user_can_read_project(project, 'github|editor-user')
    _check_user_can_read_project(project, 'github|viewer-user')
    _check_user_can_read_project(project, 'admin|the-system-admin')

    with pytest.raises(AuthException):
        _check_user_can_read_project(project, 'github|non-user')
    with pytest.raises(AuthException):
        _check_user_can_read_project(project, None)
    _check_user_can_edit_project(project, 'github|admin-user')
    _check_user_can_edit_project(project, 'github|editor-user')
    _check_user_can_edit_project(project, 'admin|the-system-admin')

    with pytest.raises(AuthException):
        _check_user_can_edit_project(project, 'github|viewer-user')
    with pytest.raises(AuthException):
        _check_user_can_edit_project(project, 'github|non-user')
    with pytest.raises(AuthException):
        _check_user_can_edit_project(project, None)
    _check_user_is_project_admin(project, 'github|admin-user')
    with pytest.raises(AuthException):
        _check_user_is_project_admin(project, 'github|editor-user')
    with pytest.raises(AuthException):
        _check_user_is_project_admin(project, 'github|viewer-user')
    with pytest.raises(AuthException):
        _check_user_is_project_admin(project, 'github|non-user')
    with pytest.raises(AuthException):
        _check_user_is_project_admin(project, None)
    _check_user_is_project_admin(project, 'admin|the-system-admin')

    assert _project_has_user(project, 'github|admin-user')
    assert _project_has_user(project, 'github|editor-user')
    assert _project_has_user(project, 'github|viewer-user')
    assert not _project_has_user(project, 'github|non-user')
    assert not _project_has_user(project, None)
    assert not _project_has_user(project, 'admin|the-system-admin')

    project.publiclyReadable = True
    _check_user_can_read_project(project, 'github|admin-user')
    _check_user_can_read_project(project, 'github|editor-user')
    _check_user_can_read_project(project, 'github|viewer-user')
    _check_user_can_read_project(project, 'github|non-user')
    _check_user_can_read_project(project, None)
    _check_user_can_read_project(project, 'admin|the-system-admin')

    _check_user_can_edit_project(project, 'github|admin-user')
    _check_user_can_edit_project(project, 'github|editor-user')
    with pytest.raises(AuthException):
        _check_user_can_edit_project(project, 'github|viewer-user')
    with pytest.raises(AuthException):
        _check_user_can_edit_project(project, 'github|non-user')
    with pytest.raises(AuthException):
        _check_user_can_edit_project(project, None)
