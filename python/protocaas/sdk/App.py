from typing import List, Any, Union
import os
import json
import shutil
import tempfile
from dataclasses import dataclass
from .InputFile import InputFile
from .OutputFile import OutputFile
from .AppProcessor import AppProcessor
from .Job import Job
from ._run_job import _run_job
from ..common.protocaas_types import ComputeResourceSlurmOpts
from ._load_spec_from_uri import _load_spec_from_uri


class App:
    """An app"""
    def __init__(self, name, *, help: str) -> None:
        self._name = name
        self._help = help
        self._processors: List[AppProcessor] = []
        self._executable_path: str = None
        self._executable_container: str = None
        self._aws_batch_job_queue: str = None
        self._aws_batch_job_definition: str = None
        self._slurm_opts: Union[ComputeResourceSlurmOpts, None] = None
    def add_processor(self, processor_func):
        P = AppProcessor.from_func(processor_func)
        self._processors.append(P)
    def run(self):
        JOB_ID = os.environ.get('JOB_ID', None)
        JOB_PRIVATE_KEY = os.environ.get('JOB_PRIVATE_KEY', None)
        JOB_INTERNAL = os.environ.get('JOB_INTERNAL', None)
        APP_EXECUTABLE = os.environ.get('APP_EXECUTABLE', None)
        SPEC_OUTPUT_FILE = os.environ.get('SPEC_OUTPUT_FILE', None)
        if SPEC_OUTPUT_FILE is not None:
            if JOB_ID is not None:
                raise Exception('Cannot set both JOB_ID and SPEC_OUTPUT_FILE')
            with open(SPEC_OUTPUT_FILE, 'w') as f:
                json.dump(self.get_spec(), f, indent=4)
            return
        if JOB_ID is not None:
            if JOB_PRIVATE_KEY is None:
                raise Exception('JOB_PRIVATE_KEY is not set')
            if JOB_INTERNAL == '1':
                # In this mode, we run the job directly
                # This is called internally by the other run mode (need to explain this better)
                return self._run_job(job_id=JOB_ID, job_private_key=JOB_PRIVATE_KEY)
            else:
                # In this mode we run the job, including the top-level interactions with the protocaas API, such as setting the status and the console output, and checking whether the job has been canceled/deleted
                if APP_EXECUTABLE is None:
                    raise Exception('APP_EXECUTABLE is not set')
                return _run_job(
                    job_id=JOB_ID,
                    job_private_key=JOB_PRIVATE_KEY,
                    app_executable=APP_EXECUTABLE
                )
        raise Exception('You must set one of the following environment variables: JOB_ID, SPEC_OUTPUT_FILE')
    def get_spec(self):
        processors = []
        for processor in self._processors:
            processors.append(
                processor.get_spec()
            )
        spec = {
            'name': self._name,
            'help': self._help,
            'image': os.getenv('APP_IMAGE', ''),
            'executable': os.getenv('APP_EXECUTABLE', ''),
            'processors': processors
        }
        return spec
    @staticmethod
    def from_spec(spec):
        app = App(
            name=spec['name'],
            help=spec['help']
        )
        for processor_spec in spec['processors']:
            processor = AppProcessor.from_spec(processor_spec)
            app._processors.append(processor)
        return app
    @staticmethod
    def from_spec_uri(
        spec_uri: str,
        aws_batch_job_queue: str=None,
        aws_batch_job_definition: str=None,
        slurm_opts: ComputeResourceSlurmOpts=None
    ):
        spec: dict = _load_spec_from_uri(spec_uri)
        a = App.from_spec(spec)
        setattr(a, '_executable_path', spec.get('executable', None))
        setattr(a, "_executable_container", spec.get('image', None))
        setattr(a, "_aws_batch_job_queue", aws_batch_job_queue)
        setattr(a, "_aws_batch_job_definition", aws_batch_job_definition)
        setattr(a, "_slurm_opts", slurm_opts)
        return a
    def _run_job(self, *, job_id: str, job_private_key: str):
        job: Job = _get_job(job_id=job_id, job_private_key=job_private_key)
        processor_name = job.processor_name
        processor = next((p for p in self._processors if p._name == processor_name), None)
        if not hasattr(processor, '_processor_func'):
            raise Exception(f'Processor does not have a _processor_func attribute: {processor_name}')
        processor_func = processor._processor_func
        if processor_func is None:
            raise Exception(f'processor_func is None')

        kwargs = {}
        for input in processor._inputs:
            if not input.list:
                input_file = next((i for i in job.inputs if i._name == input.name), None)
                if input_file is None:
                    raise Exception(f'Input not found: {input.name}')
                kwargs[input.name] = input_file
            else:
                the_list: List[InputFile] = []
                ii = 0
                while True:
                    input_file = next((i for i in job.inputs if i._name == f'{input.name}[{ii}]'), None)
                    if input_file is None:
                        break
                    the_list.append(input_file)
                    ii += 1
                kwargs[input.name] = the_list
        for output in processor._outputs:
            output_file = next((o for o in job.outputs if o._name == output.name), None)
            if output_file is None:
                raise Exception(f'Output not found: {output.name}')
            kwargs[output.name] = output_file
        for parameter in processor._parameters:
            job_parameter = next((p for p in job.parameters if p.name == parameter.name), None)
            if job_parameter is None:
                kwargs[parameter.name] = parameter.default
            else:
                kwargs[parameter.name] = job_parameter.value
        
        processor_func(**kwargs)

        for output in processor._outputs:
            output_file = next((o for o in job.outputs if o._name == output.name), None)
            if output_file is None:
                raise Exception(f'Output not found: {output.name}')
            if not output_file._was_set:
                raise Exception(f'Output was not set: {output.name}')

class TemporaryDirectory:
    """A context manager for temporary directories"""
    def __init__(self):
        self._dir = None
    def __enter__(self):
        self._dir = tempfile.mkdtemp()
        return self._dir
    def __exit__(self, exc_type, exc_value, traceback):
        shutil.rmtree(self._dir)

def _get_job(*, job_id: str, job_private_key: str) -> str:
    """Get a job from the protocaas API"""
    job = Job(
        job_id=job_id,
        job_private_key=job_private_key
    )
    return job
