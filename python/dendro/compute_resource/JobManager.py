from typing import Dict, List, Union, TYPE_CHECKING
from .SlurmJobHandler import SlurmJobHandler
from ..common.dendro_types import DendroJob
from ..sdk.App import App
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
        # Local jobs
        local_jobs = [job for job in jobs if self._is_local_job(job)]
        num_non_pending_local_jobs = len([job for job in local_jobs if job.status != 'pending'])
        if num_non_pending_local_jobs < max_simultaneous_local_jobs:
            pending_local_jobs = [job for job in local_jobs if job.status == 'pending']
            pending_local_jobs = _sort_jobs_by_timestamp_created(pending_local_jobs)
            num_to_start = min(max_simultaneous_local_jobs - num_non_pending_local_jobs, len(pending_local_jobs))
            local_jobs_to_start = pending_local_jobs[:num_to_start]
            for job in local_jobs_to_start:
                self._start_job(job)

        # AWS Batch jobs
        aws_batch_jobs = [job for job in jobs if self._is_aws_batch_job(job)]
        for job in aws_batch_jobs:
            self._start_job(job)

        # SLURM jobs
        slurm_jobs = [job for job in jobs if self._is_slurm_job(job) and self._job_is_pending(job)]
        for job in slurm_jobs:
            processor_name = job.processorName
            if processor_name not in self._slurm_job_handlers_by_processor:
                app = self._app_manager.find_app_with_processor(processor_name)
                if not app:
                    raise ComputeResourceException(f'Could not find app for processor {processor_name}')
                if not app._slurm_opts:
                    raise ComputeResourceException(f'Unexpected: Could not find slurm opts for app {app._name}')
                self._slurm_job_handlers_by_processor[processor_name] = SlurmJobHandler(job_manager=self, slurm_opts=app._slurm_opts)
            self._slurm_job_handlers_by_processor[processor_name].add_job(job)
    def do_work(self):
        for slurm_job_handler in self._slurm_job_handlers_by_processor.values():
            slurm_job_handler.do_work()
    def _get_job_resource_type(self, job: DendroJob) -> Union[str, None]:
        processor_name = job.processorName
        app: Union[App, None] = self._app_manager.find_app_with_processor(processor_name)
        if app is None:
            return None
        # if app._aws_batch_opts is not None and app._aws_batch_opts.jobQueue is not None:
        #     return 'aws_batch'
        if app._aws_batch_opts and app._aws_batch_opts.useAwsBatch:
            return 'aws_batch'
        if app._slurm_opts is not None:
            return 'slurm'
        return 'local'
    def _is_local_job(self, job: DendroJob) -> bool:
        return self._get_job_resource_type(job) == 'local'

    def _is_aws_batch_job(self, job: DendroJob) -> bool:
        return self._get_job_resource_type(job) == 'aws_batch'

    def _is_slurm_job(self, job: DendroJob) -> bool:
        return self._get_job_resource_type(job) == 'slurm'

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
            return _start_job(
                job_id=job_id,
                job_private_key=job_private_key,
                processor_name=processor_name,
                app=app,
                run_process=run_process,
                return_shell_command=return_shell_command
            )
        except Exception as e: # pylint: disable=broad-except
            # do a traceback
            import traceback
            traceback.print_exc()
            msg = f'Failed to start job: {str(e)}'
            print(msg)
            _set_job_status(job_id=job_id, job_private_key=job_private_key, status='failed', error=msg)
            return ''

def _sort_jobs_by_timestamp_created(jobs: List[DendroJob]) -> List[DendroJob]:
    return sorted(jobs, key=lambda job: job.timestampCreated)
