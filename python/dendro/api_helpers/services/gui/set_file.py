import time
from typing import Union
from ...clients.db import fetch_file, delete_file, insert_file, update_project
from ....common.dendro_types import DendroFile
from ...core._create_random_id import _create_random_id
from .._remove_detached_files_and_jobs import _remove_detached_files_and_jobs


async def set_file(
    user_id: str,
    project_id: str,
    file_name: str,
    content: str, # for example, url:https://...
    job_id: Union[str, None],
    size: int,
    metadata: dict
):
    existing_file = await fetch_file(project_id, file_name)
    if existing_file is not None:
        await delete_file(project_id, file_name)
        deleted_old_file = True
    else:
        deleted_old_file = False

    new_file = DendroFile(
        projectId=project_id,
        fileId=_create_random_id(8),
        userId=user_id,
        fileName=file_name,
        size=size,
        timestampCreated=time.time(),
        content=content,
        metadata=metadata,
        jobId=job_id
    )
    await insert_file(new_file)

    if deleted_old_file:
        await _remove_detached_files_and_jobs(project_id)

    await update_project(
        project_id=project_id,
        update={
            'timestampModified': time.time()
        }
    )

    return new_file.fileId
