from typing import List, Union, Type
import os
import json
import shutil
import tempfile
from .InputFile import InputFile
from .AppProcessor import AppProcessor
from .Job import Job
from ._run_job import _run_job
from ..common.protocaas_types import ComputeResourceSlurmOpts
from ._load_spec_from_uri import _load_spec_from_uri
from .ProcessorBase import ProcessorBase


class ProtocaasAppException(Exception):
    pass

class App:
    """An app"""
    def __init__(
        self, 
        name: str, 
        *, 
        help: str, 
        app_image: Union[str, None] = None, 
        app_executable: Union[str, None] = None
    ) -> None:
        """Construct a new Protocaas App

        Args:
            name (str): The name of the app
            help (str): A description of the app
            app_image (Union[str, None], optional): The URI for the docker image, or None if no image is to be used. Defaults to None.
            app_executable (Union[str, None], optional): The app executable within the docker image, or on the local file system if app_image=None. If app_image is set, this will default to /app/main.py. If app_image is not set, then an exception with be thrown if this is not set.
        """
        if not app_image:
            if not app_executable:
                raise ProtocaasAppException('You must set app_executable if app_image is not set')

        self._name = name
        self._help = help
        self._app_image = app_image
        self._app_executable = app_executable
        self._processors: List[AppProcessor] = []
        self._aws_batch_job_queue: Union[str, None] = None
        self._aws_batch_job_definition: Union[str, None] = None
        self._slurm_opts: Union[ComputeResourceSlurmOpts, None] = None

    def add_processor(self, processor_class: Type[ProcessorBase]):
        """Add a processor to the app

        Args:
            processor_class (Type[ProcessorBase]): The processor class for the processor
        """
        P = AppProcessor.from_processor_class(processor_class)
        self._processors.append(P)

    def run(self):
        """This function should be called once in main.py"""
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
                raise KeyError('JOB_PRIVATE_KEY is not set')
            if JOB_INTERNAL == '1':
                # In this mode, we run the job directly
                # This is called internally by the other run mode (need to explain this better)
                return self._run_job(job_id=JOB_ID, job_private_key=JOB_PRIVATE_KEY)

            # In this mode we run the job, including the top-level interactions with the protocaas API, such as setting the status and the console output, and checking whether the job has been canceled/deleted
            if APP_EXECUTABLE is None:
                raise KeyError('APP_EXECUTABLE is not set')
            return _run_job(
                job_id=JOB_ID,
                job_private_key=JOB_PRIVATE_KEY,
                app_executable=APP_EXECUTABLE
            )
        raise KeyError('You must set JOB_ID as an environment variable to run a job')

    def make_spec_file(self, spec_output_file: str = 'spec.json'):
        """Create a spec.json file. This is called internally."""
        with open(spec_output_file, 'w', encoding='utf-8') as f:
            json.dump(self.get_spec(), f, indent=4)

    def get_spec(self):
        """Get the spec for this app. This is called internally."""
        processors = []
        for processor in self._processors:
            processors.append(
                processor.get_spec()
            )
        spec = {
            'name': self._name,
            'help': self._help,
            'appImage': self._app_image,
            'appExecutable': self._app_executable,
            'executable': self._app_executable,
            'processors': processors
        }
        return spec

    @staticmethod
    def from_spec(spec):
        """Define an app from a spec. This is called internally."""
        app = App(
            name=spec['name'],
            help=spec['help'],
            app_image=spec.get('appImage', None),
            app_executable=spec.get('appExecutable', None)
        )
        for processor_spec in spec['processors']:
            processor = AppProcessor.from_spec(processor_spec)
            app._processors.append(processor)
        return app

    @staticmethod
    def from_spec_uri(
        spec_uri: str,
        aws_batch_job_queue: Union[str, None] = None,
        aws_batch_job_definition: Union[str, None] = None,
        slurm_opts: Union[ComputeResourceSlurmOpts, None] = None
    ):
        """Define an app from a spec URI (e.g., a gh url to the spec.json blob). This is called internally."""
        spec: dict = _load_spec_from_uri(spec_uri)
        a = App.from_spec(spec)
        setattr(a, "_aws_batch_job_queue", aws_batch_job_queue)
        setattr(a, "_aws_batch_job_definition", aws_batch_job_definition)
        setattr(a, "_slurm_opts", slurm_opts)
        return a

    def _run_job(self, *, job_id: str, job_private_key: str):
        """
        Used internally to actually run the job by calling the processor function.
        If an app image is being used, this will occur within the container.
        """
        # Get a job from the remote protocaas API
        job: Job = _get_job(job_id=job_id, job_private_key=job_private_key)

        # Find the registered processor and the associated processor function
        processor_name = job.processor_name
        processor = next((p for p in self._processors if p._name == processor_name), None)
        assert processor, f'Processor not found: {processor_name}'
        if not processor._processor_class:
            raise Exception(f'Processor does not have a processor_class: {processor_name}')
        processor_class = processor._processor_class

        # Assemble the context for the processor function
        context = object()
        for input in processor._inputs:
            if not input.list:
                # this input is not a list
                input_file = next((i for i in job.inputs if i._name == input.name), None)
                assert input_file, f'Input not found: {input.name}'
                setattr(context, input.name, input_file)
            else:
                # this input is a list
                the_list: List[InputFile] = []
                ii = 0
                while True:
                    # find a job input of the form <input_name>[ii]
                    input_file = next((i for i in job.inputs if i._name == f'{input.name}[{ii}]'), None)
                    if input_file is None:
                        # if not found, we must be at the end of the list
                        break
                    the_list.append(input_file)
                    ii += 1
                setattr(context, input.name, the_list)
        for output in processor._outputs:
            output_file = next((o for o in job.outputs if o._name == output.name), None)
            assert output_file is not None, f'Output not found: {output.name}'
            setattr(context, output.name, output_file)
        for parameter in processor._parameters:
            job_parameter = next((p for p in job.parameters if p.name == parameter.name), None)
            if job_parameter is None:
                # The parameter was not set, so use the default
                setattr(context, parameter.name, parameter.default)
            else:
                setattr(context, parameter.name, job_parameter.value)

        # Run the processor function
        processor_class.run(context)

        # Check that all outputs were set
        for output in processor._outputs:
            output_file = next((o for o in job.outputs if o._name == output.name), None)
            assert output_file is not None, f'Output not found: {output.name}'
            assert output_file._was_set, f'Output was not set: {output.name}'

class TemporaryDirectory:
    """A context manager for temporary directories"""
    def __init__(self):
        self._dir = None
    def __enter__(self):
        self._dir = tempfile.mkdtemp()
        return self._dir
    def __exit__(self, exc_type, exc_value, traceback):
        if self._dir:
            shutil.rmtree(self._dir)

def _get_job(*, job_id: str, job_private_key: str) -> Job:
    """Get a job from the protocaas API"""
    job = Job(
        job_id=job_id,
        job_private_key=job_private_key
    )
    return job
