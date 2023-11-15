from typing import List, TYPE_CHECKING
import os
import time
import subprocess

from ..mock import using_mock
from ..common.dendro_types import ComputeResourceSlurmOpts, DendroJob

if TYPE_CHECKING:
    from .JobManager import JobManager


class SlurmJobHandler:
    def __init__(self, *, job_manager: 'JobManager', slurm_opts: ComputeResourceSlurmOpts):
        self._job_manager = job_manager
        self._slurm_opts = slurm_opts
        self._jobs: List[DendroJob] = []
        self._job_ids = set()
        self._time_of_last_job_added = 0
    def add_job(self, job: DendroJob):
        job_id = job.jobId
        if job_id not in self._job_ids:
            self._jobs.append(job)
            self._job_ids.add(job_id)
            self._time_of_last_job_added = time.time()
    def do_work(self):
        if len(self._jobs) == 0:
            return

        time_scale_factor = 1 if not using_mock() else 10000

        elapsed_since_last_job_added = time.time() - self._time_of_last_job_added
        # wait a bit before starting jobs because maybe more will be added, and we want to start them all at once
        if elapsed_since_last_job_added < 5 / time_scale_factor:
            return

        max_jobs_in_batch = 20
        num_jobs_to_start = min(max_jobs_in_batch, len(self._jobs))
        if num_jobs_to_start > 0:
            jobs_to_start = self._jobs[:num_jobs_to_start]
            self._jobs = self._jobs[num_jobs_to_start:]
            for job in jobs_to_start:
                self._job_ids.remove(job.jobId)
            self._run_slurm_batch(jobs_to_start)
    def _run_slurm_batch(self, jobs: List[DendroJob]):
        if not os.path.exists('slurm_scripts'):
            os.mkdir('slurm_scripts')
        random_str = os.urandom(16).hex()
        slurm_script_fname = f'slurm_scripts/slurm_batch_{random_str}.sh'
        script_has_at_least_one_job = False # important to do this so we don't run an empty script
        with open(slurm_script_fname, 'w', encoding='utf8') as f:
            f.write('#!/bin/bash\n')
            f.write('\n')
            f.write('set -e\n')
            f.write('\n')
            for ii, job in enumerate(jobs):
                cmd = self._job_manager._start_job(job, run_process=False, return_shell_command=True)
                if cmd:
                    if not using_mock():
                        f.write(f'if [ "$SLURM_PROCID" == "{ii}" ]; then\n')
                        f.write(f'    {cmd}\n')
                        f.write('fi\n')
                        f.write('\n')
                    else:
                        f.write(f'{cmd}\n')
                        f.write('\n')
                    script_has_at_least_one_job = True
            f.write('\n')
        if script_has_at_least_one_job:
            # run the slurm script with srun
            slurm_cpus_per_task = self._slurm_opts.cpusPerTask
            slurm_partition = self._slurm_opts.partition
            slurm_time = self._slurm_opts.time
            slurm_other_opts = self._slurm_opts.otherOpts
            oo = []
            if slurm_cpus_per_task is not None:
                oo.append(f'--cpus-per-task={slurm_cpus_per_task}')
            if slurm_partition is not None:
                oo.append(f'--partition={slurm_partition}')
            if slurm_time is not None:
                oo.append(f'--time={slurm_time}')
            if slurm_other_opts is not None:
                for opt in slurm_other_opts.split(' '):
                    oo.append(opt)
            slurm_opts_str = ' '.join(oo)
            if not using_mock():
                cmd = f'srun -n {len(jobs)} {slurm_opts_str} bash {slurm_script_fname}'
            else:
                cmd = f'bash {slurm_script_fname}'
            print(f'Running slurm batch: {cmd}')
            subprocess.Popen(
                cmd.split(' '),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
