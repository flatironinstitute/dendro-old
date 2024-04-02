import os
from .Project import Project
from ..common._api_request import _client_put_api_request
from ..api_helpers.routers.client.router import SetProjectFileRequest


def set_file(*,
    project: Project,
    file_name: str,
    url: str,
):
    # check if a file already exists
    for file in project._files:
        if file.file_name == file_name:
            if file._file_data.content == f'url:{url}':
                return

    req = SetProjectFileRequest(
        content=f'url:{url}',
        metadata={}
    )
    dendro_api_key = os.environ.get('DENDRO_API_KEY', None)
    if not dendro_api_key:
        raise ValueError('DENDRO_API_KEY environment variable is not set')
    url_path = f'/api/client/projects/{project._project_id}/files/{file_name}'
    _client_put_api_request(
        url_path=url_path,
        data=_model_dump(req),
        dendro_api_key=dendro_api_key
    )
    print(f'File {file_name} set to {url}')

def _model_dump(model, exclude_none=False):
    # handle both pydantic v1 and v2
    if hasattr(model, 'model_dump'):
        return model.model_dump(exclude_none=exclude_none)
    else:
        return model.dict(exclude_none=exclude_none)
