from typing import Dict, List, TYPE_CHECKING
from .SlurmJobHandler import SlurmJobHandler
from ..common.dendro_types import DendroJob
from ..sdk._run_job import _set_job_status
from .ComputeResourceException import ComputeResourceException
if TYPE_CHECKING:
    from .AppManager import AppManager


max_simultaneous_local_jobs = 2

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

        self._slurm_job_handlers_by_processor: Dict[str, SlurmJobHandler] = {}
    def handle_jobs(self, jobs: List[DendroJob]):
        for job in jobs:
            if job.runMethod is None:
                self._fail_job(job, 'runMethod is None')

        # Local jobs
        local_jobs = [job for job in jobs if job.runMethod == 'local']
        num_non_pending_local_jobs = len([job for job in local_jobs if job.status != 'pending'])
        if num_non_pending_local_jobs < max_simultaneous_local_jobs:
            pending_local_jobs = [job for job in local_jobs if job.status == 'pending']
            pending_local_jobs = _sort_jobs_by_timestamp_created(pending_local_jobs)
            num_to_start = min(max_simultaneous_local_jobs - num_non_pending_local_jobs, len(pending_local_jobs))
            local_jobs_to_start = pending_local_jobs[:num_to_start]
            for job in local_jobs_to_start:
                self._start_job(job)

        # AWS Batch jobs
        aws_batch_jobs = [job for job in jobs if job.runMethod == 'aws_batch']
        pending_aws_batch_jobs = [job for job in aws_batch_jobs if self._job_is_pending(job)]
        for job in pending_aws_batch_jobs:
            self._start_job(job)

        # SLURM jobs
        slurm_jobs = [job for job in jobs if job.runMethod == 'slurm' and self._job_is_pending(job)]
        for job in slurm_jobs:
            processor_name = job.processorName
            if processor_name not in self._slurm_job_handlers_by_processor:
                app = self._app_manager.find_app_with_processor(processor_name)
                if not app:
                    raise ComputeResourceException(f'Could not find app for processor {processor_name}')
                self._slurm_job_handlers_by_processor[processor_name] = SlurmJobHandler(job_manager=self)
            self._slurm_job_handlers_by_processor[processor_name].add_job(job)
    def do_work(self):
        for slurm_job_handler in self._slurm_job_handlers_by_processor.values():
            slurm_job_handler.do_work()
    def _job_is_pending(self, job: DendroJob) -> bool:
        return job.status == 'pending'
    def _start_job(self, job: DendroJob, run_process: bool = True, return_shell_command: bool = False):
        job_id = job.jobId
        if job_id in self._attempted_to_start_job_ids:
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
        job_private_key = job.jobPrivateKey
        print(f'Failing job {job_id}: {error}')
        _set_job_status(job_id=job_id, job_private_key=job_private_key, status='failed', error=error)

def _sort_jobs_by_timestamp_created(jobs: List[DendroJob]) -> List[DendroJob]:
    return sorted(jobs, key=lambda job: job.timestampCreated)
