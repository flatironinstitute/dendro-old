import os
import tempfile
from ..common._api_request import _client_post_api_request
from pydantic import BaseModel

############################################
# These could be imported from ..api_helpers.routers.client.router
# however, we don't want this part of the code to be dependent on fastapi
class InitiateBlobUploadRequest(BaseModel):
    size: int
    sha1: str

class InitiateBlobUploadResponse(BaseModel):
    downloadUrl: str
    uploadUrl: str
    success: bool
############################################


def upload_text_blob(*,
    project_id: str,
    text: str
):
    with tempfile.TemporaryDirectory() as tmpdirname:
        file_name = os.path.join(tmpdirname, 'blob.txt')
        with open(file_name, 'w') as f:
            f.write(text)
        return upload_file_blob(project_id=project_id, file_name=file_name)


def upload_bytes_blob(*,
    project_id: str,
    bytes: bytes
):
    with tempfile.TemporaryDirectory() as tmpdirname:
        file_name = os.path.join(tmpdirname, 'blob.bin')
        with open(file_name, 'wb') as f:
            f.write(bytes)
        return upload_file_blob(project_id=project_id, file_name=file_name)


def upload_json_blob(*,
    project_id: str,
    json: dict
):
    with tempfile.TemporaryDirectory() as tmpdirname:
        file_name = os.path.join(tmpdirname, 'blob.json')
        import json as json_lib
        with open(file_name, 'w') as f:
            json_lib.dump(json, f)
        return upload_file_blob(project_id=project_id, file_name=file_name)


def upload_file_blob(*,
    project_id: str,
    file_name: str
):
    size = os.path.getsize(file_name)
    sha1 = _compute_sha1_of_file(file_name)
    req = InitiateBlobUploadRequest(
        size=size,
        sha1=sha1
    )
    dendro_api_key = os.environ.get('DENDRO_API_KEY', None)
    if not dendro_api_key:
        raise ValueError('DENDRO_API_KEY environment variable is not set')
    url_path = f'/api/client/projects/{project_id}/initiate_blob_upload'
    response = _client_post_api_request(
        url_path=url_path,
        data=_model_dump(req),
        dendro_api_key=dendro_api_key
    )
    resp = InitiateBlobUploadResponse(**response)
    download_url = resp.downloadUrl
    # check if file already exists at download location
    if _url_exists(download_url):
        return download_url
    upload_url = resp.uploadUrl
    _put_file(file_name, upload_url)
    return download_url


def _compute_sha1_of_file(file_path: str):
    import hashlib
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(2**16)
            if not chunk:
                break
            sha1.update(chunk)
    return sha1.hexdigest()

def _model_dump(model, exclude_none=False):
    # handle both pydantic v1 and v2
    if hasattr(model, 'model_dump'):
        return model.model_dump(exclude_none=exclude_none)
    else:
        return model.dict(exclude_none=exclude_none)

def _url_exists(url: str):
    import requests
    response = requests.head(url)
    return response.status_code == 200


def _put_file(file_path: str, url: str):
    import requests
    with open(file_path, 'rb') as f:
        response = requests.put(url, data=f, timeout=60 * 60 * 24 * 7)
    if response.status_code != 200:
        raise Exception(f"Failed to upload file: {response.text}")
