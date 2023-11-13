from ..clients._get_mongo_client import _get_mongo_client
from ..clients._remove_id_field import _remove_id_field
from ...common.dendro_types import DendroFile, DendroJob


async def _remove_detached_files_and_jobs(project_id: str):
    client = _get_mongo_client()
    files_collection = client['dendro']['files']
    jobs_collection = client['dendro']['jobs']

    files = await files_collection.find({
        'projectId': project_id
    }).to_list(length=None) # type: ignore
    jobs = await jobs_collection.find({
        'projectId': project_id
    }).to_list(length=None) # type: ignore

    for file in files:
        _remove_id_field(file)
    for job in jobs:
        _remove_id_field(job)
    files = [DendroFile(**x) for x in files]
    jobs = [DendroJob(**x) for x in jobs]

    something_changed = True
    while something_changed:
        file_ids = set(x.fileId for x in files)
        job_ids = set(x.jobId for x in jobs)

        job_ids_to_delete = set()
        for job in jobs:
            if any(x not in file_ids for x in job.inputFileIds):
                job_ids_to_delete.add(job.jobId)
            if job.outputFileIds:
                if any(x not in file_ids for x in job.outputFileIds):
                    job_ids_to_delete.add(job.jobId)
        file_ids_to_delete = set()
        for file in files:
            if file.jobId:
                if file.jobId not in job_ids:
                    file_ids_to_delete.add(file.fileId)
        something_changed = False
        if len(job_ids_to_delete) > 0:
            something_changed = True
            await jobs_collection.delete_many({
                'jobId': {'$in': list(job_ids_to_delete)}
            })
            jobs = [x for x in jobs if x.jobId not in job_ids_to_delete]
        if len(file_ids_to_delete) > 0:
            something_changed = True
            await files_collection.delete_many({
                'fileId': {'$in': list(file_ids_to_delete)}
            })
            files = [x for x in files if x.fileId not in file_ids_to_delete]
