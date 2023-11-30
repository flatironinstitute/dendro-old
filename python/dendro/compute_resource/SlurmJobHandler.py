from typing import TYPE_CHECKING, List
import os
import time
import subprocess

from ..mock import using_mock
from ..common.dendro_types import DendroJob, DendroJobRequiredResources

if TYPE_CHECKING:
    from .JobManager import JobManager


max_num_simultaneous_slurm_groups = 5 # TODO: make this configurable

# This will determine how many cpu jobs get grouped together in a single slurm job
num_cpus_per_slurm_node = 100 # TODO: make this configurable

class SlurmJobHandler:
    def __init__(self, *, job_manager: 'JobManager'):
        self._job_manager = job_manager
        self._last_time_we_got_a_new_job = 0
        self._jobs: List[DendroJob] = []
        self._job_ids_attempted_to_start_or_fail = set() # we don't want to attempt to start the same job multiple times
        self._last_disk_cleanup_time = 0
        # We don't want to store any state in memory!
        # so if we restart the compute resource, we don't want that to interrupt the process of knowing when
        # to start new job groups.
    def handle_jobs(self, jobs: List[DendroJob]):
        current_job_ids = set([job.jobId for job in self._jobs])
        for job in jobs:
            if job.jobId not in current_job_ids:
                self._last_time_we_got_a_new_job = time.time()
        self._jobs = jobs
    def do_work(self):
        if time.time() > self._last_disk_cleanup_time + 300:
            _clean_up_old_files()
            self._last_disk_cleanup_time = time.time()

        time_scale_factor = 1 if not using_mock() else 10000

        elapsed_since_got_new_job = time.time() - self._last_time_we_got_a_new_job
        if elapsed_since_got_new_job < 5 / time_scale_factor:
            # wait because we might still have jobs coming in and we need to start them in groups
            return
        if len(self._jobs) == 0:
            # we have no jobs
            return
        pending_jobs = [job for job in self._jobs if job.status == 'pending' and job.jobId not in self._job_ids_attempted_to_start_or_fail]
        pending_job_groups = _split_jobs_into_groups(pending_jobs)

        num_running_groups = self._determine_num_running_groups()

        for job_group in pending_job_groups:
            if num_running_groups >= max_num_simultaneous_slurm_groups:
                break
            self._start_job_group(job_group)
            num_running_groups += 1
    def _start_job_group(self, job_group: 'PendingJobGroup'):
        # a job group is a collection of jobs that should ideally fit in a single node on the cluster
        jobs = job_group._jobs
        required_resources = job_group._required_resources
        for job in jobs:
            self._job_ids_attempted_to_start_or_fail.add(job.jobId)

        if not os.path.exists('slurm_scripts'):
            os.mkdir('slurm_scripts')
        if not os.path.exists('slurm_group_assignments'):
            os.mkdir('slurm_group_assignments')

        num_cpus_per_job = required_resources.numCpus
        num_gpus_per_job = required_resources.numGpus
        memory_gb_per_job = required_resources.memoryGb
        timeout_sec_per_job = required_resources.timeSec

        if num_gpus_per_job > 1:
            self._fail_jobs(jobs, 'numGpus > 1 is not supported (SlurmBatchHandler)')
            return

        random_str = os.urandom(16).hex()
        timestamp = _create_nice_timestamp()

        slurm_group_id = f'{timestamp}_{random_str}'
        slurm_script_fname = f'slurm_scripts/slurm_batch_{slurm_group_id}.sh'
        script_has_at_least_one_job = False # important to do this so we don't ever run an empty script
        with open(slurm_script_fname, 'w', encoding='utf8') as f:
            f.write('#!/bin/bash\n')
            f.write('\n')
            f.write('set -e\n')
            f.write('\n')
            for ii, job in enumerate(jobs):
                # doesn't actually start the job - just returns the shell command - but sets the job status to 'starting'
                # so it's important to run this slurm script right away so that the job doesn't get caught in a starting state
                # forever, for example if the compute resource is restarted
                cmd = self._job_manager._start_job(job, run_process=False, return_shell_command=True)
                if cmd:
                    if not using_mock():
                        # this is how we make sure one and only one job is run in each process
                        f.write(f'if [ "$SLURM_PROCID" == "{ii}" ]; then\n')
                        f.write(f'    {cmd}\n')
                        f.write('fi\n')
                        f.write('\n')
                    else:
                        f.write(f'{cmd}\n')
                        f.write('\n')
                    script_has_at_least_one_job = True

                    # we need to record which slurm group this job went to so we can
                    # later know how many running groups there are
                    with open(f'slurm_group_assignments/{job.jobId}', 'w', encoding='utf8') as f2:
                        f2.write(slurm_group_id)
            f.write('\n')
        if script_has_at_least_one_job:
            # run the slurm script with srun
            # slurm_cpus_per_task = self._slurm_opts.cpusPerTask
            # slurm_partition = self._slurm_opts.partition
            # slurm_time = self._slurm_opts.time
            # slurm_other_opts = self._slurm_opts.otherOpts

            if num_gpus_per_job > 0:
                slurm_partition = 'gpu' # hard-coded for flatiron setup - TODO: make this configurable
            else:
                slurm_partition = 'ccm' # hard-coded for flatiron setup - TODO: make this configurable

            slurm_time = _format_time_for_slurm(timeout_sec_per_job)
            if slurm_time is None:
                self._fail_jobs(jobs, f'Invalid timeout_sec_per_job: {timeout_sec_per_job}')
                return

            oo = [] # the slurm options
            oo.append(f'-n {len(jobs)}') # number of tasks
            oo.append(f'--cpus-per-task={num_cpus_per_job}')
            oo.append(f'--partition={slurm_partition}')
            if num_gpus_per_job > 0:
                oo.append(f'--gpus-per-task={num_gpus_per_job}')
            oo.append(f'--time={slurm_time}')

            # provide memory per cpu
            mem_per_cpu = int(memory_gb_per_job * 1024 / num_cpus_per_job)
            oo.append(f'--mem-per-cpu={mem_per_cpu}')

            slurm_opts_str = ' '.join(oo)
            if not using_mock():
                cmd = f'srun {slurm_opts_str} bash {slurm_script_fname}'
            else:
                cmd = f'bash {slurm_script_fname}'

            print(f'Running slurm batch: {cmd}')
            subprocess.Popen(
                cmd.split(' '),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
    def _fail_jobs(self, jobs: List[DendroJob], reason: str):
        for job in jobs:
            self._job_manager._fail_job(job, reason)
            self._job_ids_attempted_to_start_or_fail.add(job.jobId)
    def _determine_num_running_groups(self) -> int:
        # we need to know how many slurm groups are currently running
        # so we can limit the number of groups we start at once
        all_group_ids = []
        for job in self._jobs:
            if job.status == 'starting' or job.status == 'running':
                if os.path.exists(f'slurm_group_assignments/{job.jobId}'):
                    with open(f'slurm_group_assignments/{job.jobId}', 'r', encoding='utf8') as f:
                        group_id = f.read().strip()
                        all_group_ids.append(group_id)
        return len(set(all_group_ids))

class PendingJobGroup:
    def __init__(self, jobs: List[DendroJob], required_resources: DendroJobRequiredResources):
        self._jobs = jobs
        self._required_resources = required_resources

def _split_jobs_into_groups(jobs: List[DendroJob]) -> List[PendingJobGroup]:
    jobs = [job for job in jobs if job.requiredResources is not None]
    ret: List[PendingJobGroup] = []
    all_batch_ids = set([job.batchId for job in jobs if job.batchId is not None])
    for batch_id in all_batch_ids:
        jobs_in_batch = [job for job in jobs if job.batchId == batch_id]
        assert len(jobs_in_batch) > 0
        job0 = jobs_in_batch[0]
        # we assume that all jobs here have the same required resources
        required_resources = job0.requiredResources
        assert required_resources is not None
        if required_resources.numGpus > 0:
            # every gpu job goes to their own group
            for job in jobs_in_batch:
                ret.append(PendingJobGroup([job], required_resources))
        else:
            # split into groups based on how many can fit on a single node, determined by numCpus
            # TODO: take into account memory requirements
            num_tasks_per_node = num_cpus_per_slurm_node // required_resources.numCpus
            if num_tasks_per_node == 0:
                num_tasks_per_node = 1
            for i in range(0, len(jobs_in_batch), num_tasks_per_node):
                ret.append(PendingJobGroup(jobs_in_batch[i:i + num_tasks_per_node], required_resources))
    for job in jobs:
        if job.batchId is None:
            assert job.requiredResources is not None
            ret.append(PendingJobGroup([job], job.requiredResources))
    return ret

def _format_time_for_slurm(timeout_sec: float):
    # format is d-hh:mm:ss
    timeout_sec = int(timeout_sec)
    if timeout_sec <= 0:
        return None
    d = timeout_sec // (24 * 3600)
    timeout_sec = timeout_sec % (24 * 3600)
    h = timeout_sec // 3600
    timeout_sec %= 3600
    m = timeout_sec // 60
    timeout_sec %= 60
    s = timeout_sec
    if d > 0:
        return f'{d}-{h:02d}:{m:02d}:{s:02d}'
    else:
        return f'{h:02d}:{m:02d}:{s:02d}'

def _create_nice_timestamp():
    return time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime())

def _clean_up_old_files():
    # delete old slurm scripts
    if os.path.exists('slurm_scripts'):
        for fname in os.listdir('slurm_scripts'):
            if fname.startswith('slurm_batch_'):
                full_fname = os.path.join('slurm_scripts', fname)
                if os.path.isfile(full_fname):
                    elapsed_since_modified = time.time() - os.path.getmtime(full_fname)
                    if elapsed_since_modified > 60 * 60 * 48:
                        os.remove(full_fname)
    # delete old slurm group assignments
    if os.path.exists('slurm_group_assignments'):
        for fname in os.listdir('slurm_group_assignments'):
            full_fname = os.path.join('slurm_group_assignments', fname)
            if os.path.isfile(full_fname):
                elapsed_since_modified = time.time() - os.path.getmtime(full_fname)
                if elapsed_since_modified > 60 * 60 * 48:
                    os.remove(full_fname)
