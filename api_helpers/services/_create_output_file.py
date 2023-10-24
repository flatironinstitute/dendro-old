import time
import aiohttp
from ..clients._get_mongo_client import _get_mongo_client
from ..core._create_random_id import _create_random_id
from ._remove_detached_files_and_jobs import _remove_detached_files_and_jobs
from ..core.protocaas_types import ProtocaasFile


async def _create_output_file(*,
    file_name: str,
    url: str,
    project_id: str,
    user_id: str,
    job_id: str
) -> str: # returns the ID of the created file
    size = await _get_size_for_remote_file(url)

    client = _get_mongo_client()
    projects_collection = client['protocaas']['projects']
    files_collection = client['protocaas']['files']

    existing_file = await files_collection.find_one({
        'projectId': project_id,
        'fileName': file_name
    })
    if existing_file is not None:
        await files_collection.delete_one({
            'projectId': project_id,
            'fileName': file_name
        })
        deleted_old_file = True
    else:
        deleted_old_file = False

    new_file = ProtocaasFile(
        projectId=project_id,
        fileId=_create_random_id(8),
        userId=user_id,
        fileName=file_name,
        size=size,
        timestampCreated=time.time(),
        content=f'url:{url}',
        metadata={},
        jobId=job_id
    )
    await files_collection.insert_one(new_file.dict(exclude_none=True))

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

async def _get_size_for_remote_file(url: str) -> int:
    response = await _head_request(url)
    if response is None:
        raise Exception(f"Unable to HEAD {url}")
    size = int(response.headers.get('content-length'))
    if size is None:
        raise Exception(f"Unable to get content-length for {url}")
    return size

async def _head_request(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.head(url) as response:
            return response
