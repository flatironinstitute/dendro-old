from typing import List, Union, Type, get_type_hints
import os
import json
import shutil
import tempfile
from .InputFile import InputFile
from .AppProcessor import AppProcessor
from .Job import Job
from ._run_job import _run_job
from ..common.dendro_types import ComputeResourceSlurmOpts, ComputeResourceAwsBatchOpts
from ..common._api_request import _processor_get_api_request
from ._load_spec_from_uri import _load_spec_from_uri
from .ProcessorBase import ProcessorBase


class DendroAppException(Exception):
    pass

class App:
    """An app"""
    def __init__(
        self,
        name: str,
        *,
        description: str,
        app_image: Union[str, None] = None,
        app_executable: Union[str, None] = None,
        requires_gpu: bool = False
    ) -> None:
        """Construct a new Dendro App

        Args:
            name (str): The name of the app
            description (str): A description of the app
            app_image (Union[str, None], optional): The URI for the docker image, or None if no image is to be used. Defaults to None.
            app_executable (Union[str, None], optional): The app executable within the docker image, or on the local file system if app_image=None. If app_image is set, this will default to /app/main.py. If app_image is not set, then an exception with be thrown if this is not set.
            requires_gpu (bool, optional): Whether the app requires a GPU. Defaults to False.
        """
        if not app_image:
            if not app_executable:
                raise DendroAppException('You must set app_executable if app_image is not set')

        self._name = name
        self._description = description
        self._app_image = app_image
        self._app_executable = app_executable
        self._requires_gpu = requires_gpu
        self._processors: List[AppProcessor] = []

        self._spec_dict: Union[dict, None] = None # this is set when the app is loaded from a spec (internal use only)
        self._spec_uri: Union[str, None] = None # this is set when the app is loaded from a spec_uri (internal use only)
        self._aws_batch_opts: Union[ComputeResourceAwsBatchOpts, None] = None # this is set when the app is loaded from a spec_uri (internal use only)
        self._slurm_opts: Union[ComputeResourceSlurmOpts, None] = None # this is set when the app is loaded from a spec_uri (internal use only)

    def add_processor(self, processor_class: Type[ProcessorBase]):
        """Add a processor to the app

        Args:
            processor_class (Type[ProcessorBase]): The processor class for the processor
        """
        P = AppProcessor.from_processor_class(processor_class)
        self._processors.append(P)

    def run(self):
        """This function should be called once in main.py"""
        SPEC_OUTPUT_FILE = os.environ.get('SPEC_OUTPUT_FILE', None)
        if SPEC_OUTPUT_FILE is not None:
            if os.environ.get('JOB_ID', None) is not None:
                raise Exception('Cannot set both JOB_ID and SPEC_OUTPUT_FILE')
            with open(SPEC_OUTPUT_FILE, 'w') as f:
                json.dump(self.get_spec(), f, indent=4)
            return
        JOB_ID = os.environ.get('JOB_ID', None)
        if JOB_ID is not None:
            JOB_PRIVATE_KEY = os.environ.get('JOB_PRIVATE_KEY', None)
            JOB_INTERNAL = os.environ.get('JOB_INTERNAL', None)
            APP_EXECUTABLE = os.environ.get('APP_EXECUTABLE', None)
            if JOB_PRIVATE_KEY is None:
                raise KeyError('JOB_PRIVATE_KEY is not set')
            if JOB_INTERNAL == '1':
                # In this mode, we run the job directly
                # This is called internally by the other run mode (need to explain this better)
                return self._run_job(job_id=JOB_ID, job_private_key=JOB_PRIVATE_KEY)

            # In this mode we run the job, including the top-level interactions with the dendro API, such as setting the status and the console output, and checking whether the job has been canceled/deleted
            if APP_EXECUTABLE is None:
                raise KeyError('APP_EXECUTABLE is not set')
            return _run_job(
                job_id=JOB_ID,
                job_private_key=JOB_PRIVATE_KEY,
                app_executable=APP_EXECUTABLE
            )
        TEST_APP_PROCESSOR = os.environ.get('TEST_APP_PROCESSOR', None)
        if TEST_APP_PROCESSOR is not None:
            PROCESSOR_NAME = os.environ.get('PROCESSOR_NAME', None)
            CONTEXT_FILE = os.environ.get('CONTEXT_FILE', None)
            if PROCESSOR_NAME is None:
                raise KeyError('PROCESSOR_NAME is not set')
            if CONTEXT_FILE is None:
                raise KeyError('CONTEXT_FILE is not set')
            if CONTEXT_FILE.endswith('.json'):
                with open(CONTEXT_FILE, 'r') as f:
                    context = json.load(f)
            elif CONTEXT_FILE.endswith('.yml') or CONTEXT_FILE.endswith('.yaml'):
                import yaml
                with open(CONTEXT_FILE, 'r') as f:
                    context = yaml.safe_load(f)
            else:
                raise Exception(f'Unrecognized file extension: {CONTEXT_FILE}')
            processor = next((p for p in self._processors if p._name == PROCESSOR_NAME), None)
            if not processor:
                raise Exception(f'Processor not found: {PROCESSOR_NAME}')
            processor_class = processor._processor_class
            assert processor_class, f'Processor does not have a processor_class: {PROCESSOR_NAME}'
            context_type = _get_type_of_context_in_processor_class(processor_class)
            assert context_type, f'Processor does not have a context type: {PROCESSOR_NAME}'
            context = context_type(**context)
            processor_class.run(context)
            return
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
            'description': self._description,
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
            description=spec['description'],
            app_image=spec.get('appImage', None),
            app_executable=spec.get('appExecutable', None)
        )
        app._spec_dict = spec
        for processor_spec in spec['processors']:
            processor = AppProcessor.from_spec(processor_spec)
            app._processors.append(processor)
        return app

    @staticmethod
    def from_spec_uri(
        spec_uri: str,
        aws_batch_opts: Union[ComputeResourceAwsBatchOpts, None] = None,
        slurm_opts: Union[ComputeResourceSlurmOpts, None] = None
    ):
        """Define an app from a spec URI (e.g., a gh url to the spec.json blob). This is called internally."""
        spec: dict = _load_spec_from_uri(spec_uri)
        a = App.from_spec(spec)
        a._spec_uri = spec_uri
        a._aws_batch_opts = aws_batch_opts
        a._slurm_opts = slurm_opts
        return a

    def _run_job(self, *, job_id: str, job_private_key: str):
        """
        Used internally to actually run the job by calling the processor function.
        If an app image is being used, this will occur within the container.
        """
        # Get a job from the remote dendro API
        job: Job = _get_job(job_id=job_id, job_private_key=job_private_key)

        # Find the registered processor and the associated processor function
        processor_name = job.processor_name
        processor = next((p for p in self._processors if p._name == processor_name), None)
        assert processor, f'Processor not found: {processor_name}'
        if not processor._processor_class:
            raise Exception(f'Processor does not have a processor_class: {processor_name}')
        processor_class = processor._processor_class

        # Assemble the context for the processor function
        context = ContextObject()
        for input in processor._inputs:
            if not input.list:
                # this input is not a list
                input_file = next((i for i in job.inputs if i.name == input.name), None)
                assert input_file, f'Input not found: {input.name}'
                setattr(context, input.name, input_file)
            else:
                # this input is a list
                the_list: List[InputFile] = []
                ii = 0
                while True:
                    # find a job input of the form <input_name>[ii]
                    input_file = next((i for i in job.inputs if i.name == f'{input.name}[{ii}]'), None)
                    if input_file is None:
                        # if not found, we must be at the end of the list
                        break
                    the_list.append(input_file)
                    ii += 1
                setattr(context, input.name, the_list)
        for output in processor._outputs:
            output_file = next((o for o in job.outputs if o.name == output.name), None)
            assert output_file is not None, f'Output not found: {output.name}'
            setattr(context, output.name, output_file)
        for parameter in processor._parameters:
            job_parameter = next((p for p in job.parameters if p.name == parameter.name), None)
            parameter_value = parameter.default if job_parameter is None else job_parameter.value
            _setattr_where_name_may_have_dots(context, parameter.name, parameter_value)

        _set_custom_kachery_storage_backend(job_id=job_id, job_private_key=job_private_key)

        # Run the processor function
        processor_class.run(context)

        # Check that all outputs were set
        for output in processor._outputs:
            output_file = next((o for o in job.outputs if o.name == output.name), None)
            assert output_file is not None, f'Output not found: {output.name}'
            assert output_file.was_uploaded, f'Output was not uploaded: {output.name}'

# An empty object that we can set attributes on
class ContextObject:
    pass

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
    """Get a job from the dendro API"""
    job = Job(
        job_id=job_id,
        job_private_key=job_private_key
    )
    return job

def _setattr_where_name_may_have_dots(obj, name, value):
    """Set an attribute on an object, where the name may have dots in it"""
    if '.' not in name:
        setattr(obj, name, value)
        return
    parts = name.split('.')
    for part in parts[:-1]:
        if not hasattr(obj, part):
            setattr(obj, part, ContextObject())
        obj = getattr(obj, part)
    setattr(obj, parts[-1], value)

def _get_type_of_context_in_processor_class(processor_class):
    # Retrieve the 'run' method from the processor class
    run_method = getattr(processor_class, 'run', None)
    if not run_method:
        raise Exception(f'Processor class does not have a run method: {processor_class}')
    # Get the type hints of the 'run' method
    type_hints = get_type_hints(run_method)
    # Return the type hint for the 'context' parameter
    return type_hints.get('context')

class CustomKacheryStorageBackend:
    def __init__(self, *, job_id: str, job_private_key: str):
        self._job_id = job_id
        self._job_private_key = job_private_key
    def store_file(self, file_path: str, *, label: str):
        sha1 = _compute_sha1_of_file(file_path)

        url_path = f'/api/processor/jobs/{self._job_id}/additional_uploads/sha1/{sha1}/upload_url'
        headers = {
            'job-private-key': self._job_private_key
        }
        res = _processor_get_api_request(
            url_path=url_path,
            headers=headers
        )
        upload_url = res['uploadUrl']
        download_url = res['downloadUrl']

        import requests
        with open(file_path, 'rb') as f:
            resp_upload = requests.put(upload_url, data=f, timeout=60 * 60 * 24 * 7)
        if resp_upload.status_code != 200:
            raise Exception(f'Error uploading file to bucket ({resp_upload.status_code}) {resp_upload.reason}: {resp_upload.text}')
        return download_url

def _set_custom_kachery_storage_backend(*, job_id: str, job_private_key: str):
    try:
        import kachery_cloud as kcl
    except ImportError:
        # if we don't have kachery installed, then let's not worry about it
        return

    try:
        custom_storage_backend = CustomKacheryStorageBackend(job_id=job_id, job_private_key=job_private_key)
        kcl.set_custom_storage_backend(custom_storage_backend)
    except Exception as e:
        print('WARNING: Problem setting custom kachery storage backend:', e)
        return

def _compute_sha1_of_file(file_path: str):
    import hashlib
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(2**16)
            if not chunk:
                break
            sha1.update(chunk)
    return sha1.hexdigest()
