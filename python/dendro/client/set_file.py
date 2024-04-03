from typing import Union
import os
import json
from .Project import Project
from ..common._api_request import _client_put_api_request
from pydantic import BaseModel

############################################
# These could be imported from ..api_helpers.routers.client.router
# however, we don't want this part of the code to be dependent on fastapi
class SetProjectFileRequest(BaseModel):
    content: str
    metadata: dict = {}
    size: Union[int, None] = None

class SetProjectFileMetadataRequest(BaseModel):
    metadata: dict
############################################


def set_file(*,
    project: Project,
    file_name: str,
    url: str,
    metadata: dict = {}
):
    # check if a file already exists
    for file in project._files:
        if file.file_name == file_name:
            if file._file_data.content == f'url:{url}':
                if _metadata_is_same(file._file_data.metadata, metadata):
                    return
                else:
                    # Let's just update the metadata
                    # It's important not to replace the entire file because it would
                    # trigger deleting of jobs and other files
                    set_file_metadata(
                        project=project,
                        file_name=file_name,
                        metadata=metadata
                    )
                    return

    req = SetProjectFileRequest(
        content=f'url:{url}',
        metadata=metadata
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

def set_file_metadata(*,
    project: Project,
    file_name: str,
    metadata: dict
):
    # Check if file already exists
    for file in project._files:
        if file.file_name == file_name:
            if _metadata_is_same(file._file_data.metadata, metadata):
                return

    req = SetProjectFileMetadataRequest(
        metadata=metadata
    )
    dendro_api_key = os.environ.get('DENDRO_API_KEY', None)
    if not dendro_api_key:
        raise ValueError('DENDRO_API_KEY environment variable is not set')
    url_path = f'/api/client/projects/{project._project_id}/files-metadata/{file_name}'
    _client_put_api_request(
        url_path=url_path,
        data=_model_dump(req),
        dendro_api_key=dendro_api_key
    )
    print(f'File {file_name} metadata updated')

def _model_dump(model, exclude_none=False):
    # handle both pydantic v1 and v2
    if hasattr(model, 'model_dump'):
        return model.model_dump(exclude_none=exclude_none)
    else:
        return model.dict(exclude_none=exclude_none)

def _metadata_is_same(metadata1, metadata2):
    return json.dumps(metadata1, sort_keys=True) == json.dumps(metadata2, sort_keys=True)
