from typing import List, TYPE_CHECKING
from .SlurmJobHandler import SlurmJobHandler
from ..common.dendro_types import DendroJob
from ..sdk._run_job_parent_process import _set_job_status
if TYPE_CHECKING:
    from .AppManager import AppManager


# TODO: make these configurable
max_simultaneous_local_jobs = 2
max_simultaneous_aws_batch_jobs = 20

class JobManager:
    def __init__(self, *,
                 compute_resource_id: str,
                 compute_resource_private_key: str,
                 app_manager: 'AppManager'
                ):
        self._compute_resource_id = compute_resource_id
        self._compute_resource_private_key = compute_resource_private_key
        self._app_manager = app_manager

        # important to keep track of which jobs we attempted to start
        # so that we don't attempt multiple times in the case where starting failed
        self._attempted_to_start_job_ids = set()
        self._attempted_to_fail_job_ids = set()

        self._slurm_job_handler = SlurmJobHandler(job_manager=self)
    def handle_jobs(self, jobs: List[DendroJob]):
        local_jobs = [job for job in jobs if job.runMethod == 'local']
        aws_batch_jobs = [job for job in jobs if job.runMethod == 'aws_batch']
        slurm_jobs = [job for job in jobs if job.runMethod == 'slurm']
        none_jobs = [job for job in jobs if job.runMethod is None]

        for job in none_jobs:
            self._fail_job(job, 'runMethod is None')

        # Local jobs
        if 'local' in self._app_manager._available_job_run_methods:
            local_jobs_to_start = _choose_pending_jobs_to_start(local_jobs, max_simultaneous_local_jobs)
            for job in local_jobs_to_start:
                self._start_job(job)

        # AWS Batch jobs
        if 'aws_batch' in self._app_manager._available_job_run_methods:
            aws_jobs_to_start = _choose_pending_jobs_to_start(aws_batch_jobs, max_simultaneous_aws_batch_jobs)
            for job in aws_jobs_to_start:
                self._start_job(job)

        # SLURM jobs
        # this is more tricky... let's send the to slurm job handler
        if 'slurm' in self._app_manager._available_job_run_methods:
            self._slurm_job_handler.handle_jobs(slurm_jobs)
    def do_work(self):
        self._slurm_job_handler.do_work()
    def _job_is_pending(self, job: DendroJob) -> bool:
        return job.status == 'pending'
    def _start_job(self, job: DendroJob, run_process: bool = True, return_shell_command: bool = False):
        job_id = job.jobId
        if job_id in self._attempted_to_start_job_ids or job_id in self._attempted_to_fail_job_ids:
            return '' # see above comment about why this is necessary
        self._attempted_to_start_job_ids.add(job_id)
        job_private_key = job.jobPrivateKey
        processor_name = job.processorName
        app = self._app_manager.find_app_with_processor(processor_name)
        if app is None:
            msg = f'Could not find app with processor name {processor_name}'
            print(msg)
            _set_job_status(job_id=job_id, job_private_key=job_private_key, status='failed', error=msg)
            return ''
        try:
            print(f'Starting job {job_id} {processor_name}')
            from ._start_job import _start_job
            if job.requiredResources is None:
                raise Exception('Cannot start job... requiredResources is None')
            assert job.runMethod is not None, 'Unexpected: job.runMethod is None'
            return _start_job(
                job_id=job_id,
                job_private_key=job_private_key,
                processor_name=processor_name,
                run_method=job.runMethod,
                app=app,
                run_process=run_process,
                return_shell_command=return_shell_command,
                required_resources=job.requiredResources
            )
        except Exception as e: # pylint: disable=broad-except
            # do a traceback
            import traceback
            traceback.print_exc()
            msg = f'Failed to start job: {str(e)}'
            print(msg)
            self._fail_job(job, msg)
            return ''
    def _fail_job(self, job: DendroJob, error: str):
        job_id = job.jobId
        if job_id in self._attempted_to_fail_job_ids:
            return '' # see above comment about why this is necessary
        self._attempted_to_fail_job_ids.add(job_id)
        job_id = job.jobId
        job_private_key = job.jobPrivateKey
        print(f'Failing job {job_id}: {error}')
        _set_job_status(job_id=job_id, job_private_key=job_private_key, status='failed', error=error)

def _sort_jobs_by_timestamp_created(jobs: List[DendroJob]) -> List[DendroJob]:
    return sorted(jobs, key=lambda job: job.timestampCreated)

def _choose_pending_jobs_to_start(jobs: List[DendroJob], max_num_simultaneous_jobs: int) -> List[DendroJob]:
    num_non_pending_jobs = len([job for job in jobs if job.status != 'pending'])
    if num_non_pending_jobs < max_num_simultaneous_jobs:
        pending_jobs = [job for job in jobs if job.status == 'pending']
        pending_jobs = _sort_jobs_by_timestamp_created(pending_jobs)
        num_to_start = min(max_num_simultaneous_jobs - num_non_pending_jobs, len(pending_jobs))
        jobs_to_start = pending_jobs[:num_to_start]
    else:
        jobs_to_start = []
    return jobs_to_start
