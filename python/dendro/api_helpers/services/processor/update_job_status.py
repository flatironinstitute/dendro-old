import time
from typing import Union

from dendro.mock import using_mock
from ....common.dendro_types import DendroJob
from ...core.settings import get_settings
from ...core._model_dump import _model_dump
from .._create_output_file import _create_output_file
from ...clients.db import update_job
from ...clients.pubsub import publish_pubsub_message


async def update_job_status(job: DendroJob, status: str, error: Union[str, None], force_update: Union[bool, None] = None):
    old_status = job.status

    new_status = status
    new_error = error

    if not force_update:
        if new_status == 'starting':
            if old_status != 'pending':
                raise Exception(f"Cannot set job status to starting when status is {old_status}")
        elif new_status == 'running':
            if old_status != 'starting':
                raise Exception(f"Cannot set job status to running when status is {old_status}")
        elif new_status == 'completed':
            if old_status != 'running':
                raise Exception(f"Cannot set job status to completed when status is {old_status}")
        elif new_status == 'failed':
            if (old_status != 'running') and (old_status != 'starting') and (old_status != 'pending'):
                raise Exception(f"Cannot set job status to failed when status is {old_status}")

    update = {}
    if new_error:
        if new_status != 'failed':
            raise Exception(f"Cannot set job error when status is {new_status}")
    if new_status == 'completed':
        # we need to create the output files before marking the job as completed
        output_bucket_base_url = get_settings().OUTPUT_BUCKET_BASE_URL
        if using_mock():
            output_bucket_base_url = 'https://mock-bucket'
        if output_bucket_base_url is None:
            raise Exception('Environment variable not set: OUTPUT_BUCKET_BASE_URL')
        output_file_ids = []
        for output_file in job.outputFiles:
            output_file_url = f"{output_bucket_base_url}/dendro-outputs/{job.jobId}/{output_file.name}"
            output_file_id = await _create_output_file(
                file_name=output_file.fileName,
                url=output_file_url,
                project_id=job.projectId,
                user_id=job.userId,
                job_id=job.jobId
            )
            output_file_ids.append(output_file_id)
            output_file.fileId = output_file_id
        update['outputFileIds'] = output_file_ids
        update['outputFiles'] = [_model_dump(f, exclude_none=True) for f in job.outputFiles]

    update['status'] = new_status
    if new_error:
        update['error'] = new_error
    if new_status == 'queued':
        update['timestampQueued'] = time.time()
    elif new_status == 'starting':
        update['timestampStarting'] = time.time()
    elif new_status == 'running':
        update['timestampStarted'] = time.time()
    elif new_status == 'completed':
        update['timestampFinished'] = time.time()
    elif new_status == 'failed':
        update['timestampFinished'] = time.time()

    # if update is non-empty, then update the job
    if len(update) > 0:
        await update_job(job_id=job.jobId, update=update)

    await publish_pubsub_message(
        channel=job.computeResourceId,
        message={
            'type': 'jobStatusChanged',
            'projectId': job.projectId,
            'computeResourceId': job.computeResourceId,
            'jobId': job.jobId,
            'status': new_status
        }
    )
