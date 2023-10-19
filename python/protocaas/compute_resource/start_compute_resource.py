from typing import List, Dict
import os
import yaml
import time
import subprocess
from pathlib import Path
import shutil
import multiprocessing
from ..common._api_request import _compute_resource_get_api_request, _compute_resource_put_api_request
from .register_compute_resource import env_var_keys
from ..sdk.App import App
from ..sdk._run_job import _set_job_status
from .PubsubClient import PubsubClient
from ..sdk.App import App
from ._start_job import _start_job
from ..common.protocaas_types import ProtocaasComputeResourceApp, ComputeResourceSlurmOpts, ProtocaasJob


max_simultaneous_local_jobs = 2

class Daemon:
    def __init__(self, *, dir: str):
        self._compute_resource_id = os.getenv('COMPUTE_RESOURCE_ID', None)
        self._compute_resource_private_key = os.getenv('COMPUTE_RESOURCE_PRIVATE_KEY', None)
        self._node_id = os.getenv('NODE_ID', None)
        self._node_name = os.getenv('NODE_NAME', None)
        if self._compute_resource_id is None:
            raise ValueError('Compute resource has not been initialized in this directory, and the environment variable COMPUTE_RESOURCE_ID is not set.')
        if self._compute_resource_private_key is None:
            raise ValueError('Compute resource has not been initialized in this directory, and the environment variable COMPUTE_RESOURCE_PRIVATE_KEY is not set.')
        self._apps: List[App] = _load_apps(
            compute_resource_id=self._compute_resource_id,
            compute_resource_private_key=self._compute_resource_private_key,
            compute_resource_node_name=self._node_name,
            compute_resource_node_id=self._node_id
        )

        # important to keep track of which jobs we attempted to start
        # so that we don't attempt multiple times in the case where starting failed
        self._attempted_to_start_job_ids = set()

        print(f'Loaded apps: {", ".join([app._name for app in self._apps])}')

        self._slurm_job_handlers_by_processor: Dict[str, SlurmJobHandler] = {}
        for app in self._apps:
            for processor in app._processors:
                if app._slurm_opts is not None:
                    self._slurm_job_handlers_by_processor[processor._name] = SlurmJobHandler(self, app._slurm_opts)

        spec_apps = []
        for app in self._apps:
            spec_apps.append(app.get_spec())

        # Report the compute resource spec
        print('Reporting the compute resource spec')
        url_path = f'/api/compute_resource/compute_resources/{self._compute_resource_id}/spec'
        spec = {
            'apps': spec_apps
        }
        _compute_resource_put_api_request(
            url_path=url_path,
            compute_resource_id=self._compute_resource_id,
            compute_resource_private_key=self._compute_resource_private_key,
            data={
                'spec': spec
            }
        )

        print('Getting pubsub info')
        pubsub_subscription = get_pubsub_subscription(
            compute_resource_id=self._compute_resource_id,
            compute_resource_private_key=self._compute_resource_private_key,
            compute_resource_node_name=self._node_name,
            compute_resource_node_id=self._node_id
        )
        self._pubsub_client = PubsubClient(
            pubnub_subscribe_key=pubsub_subscription['pubnubSubscribeKey'],
            pubnub_channel=pubsub_subscription['pubnubChannel'],
            pubnub_user=pubsub_subscription['pubnubUser'],
            compute_resource_id=self._compute_resource_id
        )
    def start(self):
        timer_handle_jobs = 0

        # Start cleaning up old job directories
        # It's important to do this in a separate process
        # because it can take a long time to delete all the files in the tmp directories (remfile is the culprit)
        # and we don't want to block the main process from handling jobs
        multiprocessing.Process(target=_cleanup_old_job_working_directories, args=(os.getcwd() + '/jobs',)).start()

        print('Starting compute resource')
        while True:
            elapsed_handle_jobs = time.time() - timer_handle_jobs
            need_to_handle_jobs = elapsed_handle_jobs > 60 * 10 # normally we will get pubsub messages for updates, but if we don't, we should check every 10 minutes
            messages = self._pubsub_client.take_messages()
            for msg in messages:
                if msg['type'] == 'newPendingJob':
                    need_to_handle_jobs = True
                if msg['type'] == 'jobStatusChaged':
                    need_to_handle_jobs = True
            if need_to_handle_jobs:
                timer_handle_jobs = time.time()
                self._handle_jobs()
            
            for slurm_job_handler in self._slurm_job_handlers_by_processor.values():
                slurm_job_handler.do_work()

            time.sleep(2)
    def _handle_jobs(self):
        url_path = f'/api/compute_resource/compute_resources/{self._compute_resource_id}/unfinished_jobs'
        resp = _compute_resource_get_api_request(
            url_path=url_path,
            compute_resource_id=self._compute_resource_id,
            compute_resource_private_key=self._compute_resource_private_key,
            compute_resource_node_name=self._node_name,
            compute_resource_node_id=self._node_id
        )
        jobs = resp['jobs']
        jobs = [ProtocaasJob(**job) for job in jobs] # validation

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
                raise Exception(f'Unexpected: Could not find slurm job handler for processor {processor_name}')
            self._slurm_job_handlers_by_processor[processor_name].add_job(job)

    def _get_job_resource_type(self, job: ProtocaasJob) -> str:
        processor_name = job.processorName
        app: App = self._find_app_with_processor(processor_name)
        if app is None:
            return None
        if app._aws_batch_job_queue is not None:
            return 'aws_batch'
        elif app._slurm_opts is not None:
            return 'slurm'
        else:
            return 'local'
    def _is_local_job(self, job: ProtocaasJob) -> bool:
        return self._get_job_resource_type(job) == 'local'
    def _is_aws_batch_job(self, job: ProtocaasJob) -> bool:
        return self._get_job_resource_type(job) == 'aws_batch'
    def _is_slurm_job(self, job: ProtocaasJob) -> bool:
        return self._get_job_resource_type(job) == 'slurm'
    def _job_is_pending(self, job: ProtocaasJob) -> bool:
        return job.status == 'pending'
    def _start_job(self, job: ProtocaasJob, run_process: bool = True, return_shell_command: bool = False):
        job_id = job.jobId
        if job_id in self._attempted_to_start_job_ids:
            return '' # see above comment about why this is necessary
        self._attempted_to_start_job_ids.add(job_id)
        job_private_key = job.jobPrivateKey
        processor_name = job.processorName
        app = self._find_app_with_processor(processor_name)
        if app is None:
            msg = f'Could not find app with processor name {processor_name}'
            print(msg)
            _set_job_status(job_id=job_id, job_private_key=job_private_key, status='failed', error=msg)
            return ''
        try:
            print(f'Starting job {job_id} {processor_name}')
            return _start_job(
                job_id=job_id,
                job_private_key=job_private_key,
                processor_name=processor_name,
                app=app,
                run_process=run_process,
                return_shell_command=return_shell_command
            )
        except Exception as e:
            msg = f'Failed to start job: {str(e)}'
            print(msg)
            _set_job_status(job_id=job_id, job_private_key=job_private_key, status='failed', error=msg)
            return ''

    def _find_app_with_processor(self, processor_name: str) -> App:
        for app in self._apps:
            for p in app._processors:
                if p._name == processor_name:
                    return app
        return None

def _load_apps(*, compute_resource_id: str, compute_resource_private_key: str, compute_resource_node_name: str=None, compute_resource_node_id: str=None) -> List[App]:
    url_path = f'/api/compute_resource/compute_resources/{compute_resource_id}/apps'
    resp = _compute_resource_get_api_request(
        url_path=url_path,
        compute_resource_id=compute_resource_id,
        compute_resource_private_key=compute_resource_private_key,
        compute_resource_node_name=compute_resource_node_name,
        compute_resource_node_id=compute_resource_node_id
    )
    apps = resp['apps']
    apps = [ProtocaasComputeResourceApp(**app) for app in apps] # validation
    ret = []
    for a in apps:
        container = a.container
        aws_batch_opts = a.awsBatch
        slurm_opts = a.slurm
        s = []
        if container is not None:
            s.append(f'container: {container}')
        if aws_batch_opts is not None:
            if slurm_opts is not None:
                raise Exception(f'App has awsBatch opts but also has slurm opts')
            aws_batch_job_queue = aws_batch_opts.jobQueue
            aws_batch_job_definition = aws_batch_opts.jobDefinition
            s.append(f'awsBatchJobQueue: {aws_batch_job_queue}')
            s.append(f'awsBatchJobDefinition: {aws_batch_job_definition}')
        else:
            aws_batch_job_queue = None
            aws_batch_job_definition = None
        if slurm_opts is not None:
            slurm_cpus_per_task = slurm_opts.cpusPerTask
            slurm_partition = slurm_opts.partition
            slurm_time = slurm_opts.time
            slurm_other_opts = slurm_opts.otherOpts
            s.append(f'slurmCpusPerTask: {slurm_cpus_per_task}')
            s.append(f'slurmPartition: {slurm_partition}')
            s.append(f'slurmTime: {slurm_time}')
            s.append(f'slurmOtherOpts: {slurm_other_opts}')
        else:
            slurm_cpus_per_task = None
            slurm_partition = None
            slurm_time = None
            slurm_other_opts = None
        print(f'Loading app {a.specUri} | {" | ".join(s)}')
        app = App.from_spec_uri(
            spec_uri=a.specUri,
            aws_batch_job_queue=aws_batch_job_queue,
            aws_batch_job_definition=aws_batch_job_definition,
            slurm_opts=slurm_opts
        )
        print(f'  {len(app._processors)} processors')
        ret.append(app)
    return ret

def start_compute_resource(dir: str):
    config_fname = os.path.join(dir, '.protocaas-compute-resource-node.yaml')
    
    if os.path.exists(config_fname):
        with open(config_fname, 'r') as f:
            the_config = yaml.safe_load(f)
    else:
        the_config = {}
    for k in env_var_keys:
        if k in the_config:
            os.environ[k] = the_config[k]

    daemon = Daemon(dir=dir)
    daemon.start()

def get_pubsub_subscription(*, compute_resource_id: str, compute_resource_private_key: str, compute_resource_node_name: str=None, compute_resource_node_id: str=None):
    url_path = f'/api/compute_resource/compute_resources/{compute_resource_id}/pubsub_subscription'
    resp = _compute_resource_get_api_request(
        url_path=url_path,
        compute_resource_id=compute_resource_id,
        compute_resource_private_key=compute_resource_private_key,
        compute_resource_node_name=compute_resource_node_name,
        compute_resource_node_id=compute_resource_node_id
    )
    return resp['subscription']

def _sort_jobs_by_timestamp_created(jobs: List[ProtocaasJob]) -> List[dict]:
    return sorted(jobs, key=lambda job: job.timestampCreated)

def _cleanup_old_job_working_directories(dir: str):
    """Delete working dirs that are more than 24 hours old"""
    jobs_dir = Path(dir)
    while True:
        if not jobs_dir.exists():
            continue
        for job_dir in jobs_dir.iterdir():
            if job_dir.is_dir():
                elapsed = time.time() - job_dir.stat().st_mtime
                if elapsed > 24 * 60 * 60:
                    print(f'Removing old working dir {job_dir}')
                    shutil.rmtree(job_dir)
        time.sleep(60)

class SlurmJobHandler:
    def __init__(self, daemon: Daemon, slurm_opts: ComputeResourceSlurmOpts):
        self._daemon = daemon
        self._slurm_opts = slurm_opts
        self._jobs: List[ProtocaasJob] = []
        self._job_ids = set()
        self._time_of_last_job_added = 0
    def add_job(self, job: ProtocaasJob):
        job_id = job.jobId
        if job_id not in self._job_ids:
            self._jobs.append(job)
            self._job_ids.add(job_id)
            self._time_of_last_job_added = time.time()
    def do_work(self):
        if len(self._jobs) == 0:
            return
        elapsed_since_last_job_added = time.time() - self._time_of_last_job_added
        # wait a bit before starting jobs because maybe more will be added, and we want to start them all at once
        if elapsed_since_last_job_added < 5:
            return
        max_jobs_in_batch = 20
        num_jobs_to_start = min(max_jobs_in_batch, len(self._jobs))
        if num_jobs_to_start > 0:
            jobs_to_start = self._jobs[:num_jobs_to_start]
            self._jobs = self._jobs[num_jobs_to_start:]
            for job in jobs_to_start:
                self._job_ids.remove(job.jobId)
            self._run_slurm_batch(jobs_to_start)
    def _run_slurm_batch(self, jobs: List[dict]):
        if not os.path.exists('slurm_scripts'):
            os.mkdir('slurm_scripts')
        random_str = os.urandom(16).hex()
        slurm_script_fname = f'slurm_scripts/slurm_batch_{random_str}.sh'
        script_has_at_least_one_job = False # important to do this so we don't run an empty script
        with open(slurm_script_fname, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('\n')
            f.write('set -e\n')
            f.write('\n')
            for ii, job in enumerate(jobs):
                cmd = self._daemon._start_job(job, run_process=False, return_shell_command=True)
                if cmd:
                    f.write(f'if [ "$SLURM_PROCID" == "{ii}" ]; then\n')
                    f.write(f'    {cmd}\n')
                    f.write('fi\n')
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
            cmd = f'srun -n {len(jobs)} {slurm_opts_str} bash {slurm_script_fname}'
            print(f'Running slurm batch: {cmd}')
            subprocess.Popen(
                cmd.split(' '),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )