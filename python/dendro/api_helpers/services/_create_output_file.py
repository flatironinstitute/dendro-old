from typing import Union
import time
import aiohttp
from ..clients._get_mongo_client import _get_mongo_client
from ..core._create_random_id import _create_random_id
from ._remove_detached_files_and_jobs import _remove_detached_files_and_jobs
from ...common.dendro_types import DendroFile
from ..core._model_dump import _model_dump
from ...mock import using_mock


async def _create_output_file(*,
    file_name: str,
    url: str,
    project_id: str,
    user_id: str,
    job_id: str,
    is_folder: Union[bool, None] = None,
    replace_pending: bool = False
) -> str: # returns the ID of the created file
    if url == 'pending':
        if replace_pending:
            raise Exception('Cannot replace pending file with another pending file')
        # this is the output of a job that has not completed yet
        size = 0
    else:
        if not using_mock():
            if not is_folder:
                size = await _get_size_for_remote_file(url)
            else:
                size = await _get_size_from_file_manifest_json(url)
        else:
            size = 1 # size of mock file

    client = _get_mongo_client()
    projects_collection = client['dendro']['projects']
    files_collection = client['dendro']['files']

    existing_file = await files_collection.find_one({
        'projectId': project_id,
        'fileName': file_name
    })
    existing_file = DendroFile(**existing_file) if existing_file is not None else None
    deleted_old_file = False
    if existing_file is not None:
        if replace_pending:
            if existing_file.content != 'pending':
                raise Exception('Error replacing pending file: existing file is not pending')
            file_id = existing_file.fileId # we will replace this file and it's important to use the same file ID
            await files_collection.delete_one({
                'projectId': project_id,
                'fileId': file_id
            })
        else:
            deleted_old_file = True
            file_id = _create_random_id(8)
            await files_collection.delete_one({
                'projectId': project_id,
                'fileName': file_name
            })
    else:
        if replace_pending:
            raise Exception('Cannot replace pending file because it does not exist')
        file_id = _create_random_id(8)

    new_file = DendroFile(
        projectId=project_id,
        fileId=file_id,
        userId=user_id,
        fileName=file_name,
        size=size,
        timestampCreated=time.time(),
        content=f'url:{url}' if url != 'pending' else 'pending',
        metadata={},
        isFolder=is_folder,
        jobId=job_id
    )
    await files_collection.insert_one(_model_dump(new_file, exclude_none=True))

    if deleted_old_file:
        await _remove_detached_files_and_jobs(project_id)

    await projects_collection.update_one({
        'projectId': project_id
    }, {
        '$set': {
            'timestampModified': time.time()
        }
    })

    return new_file.fileId

class GetSizeForRemoteFileException(Exception):
    pass

async def _get_size_for_remote_file(url: str) -> int:
    response = await _head_request(url)
    if response is None:
        raise GetSizeForRemoteFileException(f"Unable to HEAD {url}")
    size = response.headers.get('content-length')
    if size is None:
        raise GetSizeForRemoteFileException(f"Unable to get content-length for {url}")
    return int(size)

async def _head_request(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.head(url) as response:
            return response

async def _get_size_from_file_manifest_json(url: str) -> int:
    file_manifest_url = url + '/file_manifest.json'
    try:
        # load the file manifest
        async with aiohttp.ClientSession() as session:
            async with session.get(file_manifest_url) as response:
                if response.status != 200:
                    raise Exception(f"Error getting file manifest: {response.status}")
                file_manifest = await response.json()
        size = 0
        for f in file_manifest['files']:
            size += f['size']
        return size
    except Exception as e:
        print(f'Problem reading file manifest at {file_manifest_url}: {e}')
        return 0
