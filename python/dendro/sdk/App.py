from typing import List, Union, Type, get_type_hints
import os
import json
from .AppProcessor import AppProcessor
from ._run_job_parent_process import _run_job_parent_process
from ._run_job_child_process import _run_job_child_process
from ._load_spec_from_uri import _load_spec_from_uri
from .ProcessorBase import ProcessorBase
from .InputFile import InputFile
from .InputFolder import InputFolder
from .OutputFile import OutputFile
from .OutputFolder import OutputFolder


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
        app_executable: Union[str, None] = None
    ) -> None:
        """Construct a new Dendro App

        Args:
            name (str): The name of the app
            description (str): A description of the app
            app_image (Union[str, None], optional): The URI for the docker image, or None if no image is to be used. Defaults to None.
            app_executable (Union[str, None], optional): The app executable within the docker image, or on the local file system if app_image=None. If app_image is set, this will default to /app/main.py. If app_image is not set, then an exception with be thrown if this is not set.
        """
        if not app_image:
            if not app_executable:
                raise DendroAppException('You must set app_executable if app_image is not set')

        if len(description) > 1000:
            raise Exception('Description for app must be less than 1000 characters')

        self._name = name
        self._description = description
        self._app_image = app_image
        self._app_executable = app_executable
        self._processors: List[AppProcessor] = []

        self._spec_dict: Union[dict, None] = None # this is set when the app is loaded from a spec (internal use only)
        self._spec_uri: Union[str, None] = None # this is set when the app is loaded from a spec_uri (internal use only)

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
            JOB_TIMEOUT_SEC = os.environ.get('JOB_TIMEOUT_SEC', None)
            if JOB_TIMEOUT_SEC is not None:
                JOB_TIMEOUT_SEC = int(JOB_TIMEOUT_SEC)
            if JOB_PRIVATE_KEY is None:
                raise KeyError('JOB_PRIVATE_KEY is not set')
            if JOB_INTERNAL == '1':
                # In this mode, we run the job directly
                # This is called internally by the other run mode (need to explain this better)
                return _run_job_child_process(job_id=JOB_ID, job_private_key=JOB_PRIVATE_KEY, processors=self._processors)

            # In this mode we run the job, including the top-level interactions with the dendro API, such as setting the status and the console output, and checking whether the job has been canceled/deleted
            if APP_EXECUTABLE is None:
                raise KeyError('APP_EXECUTABLE is not set')
            return _run_job_parent_process(
                job_id=JOB_ID,
                job_private_key=JOB_PRIVATE_KEY,
                app_executable=APP_EXECUTABLE,
                job_timeout_sec=JOB_TIMEOUT_SEC
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

            # handle input files coming in as url's
            for input in processor._inputs:
                input_value = _get_in_dict_where_key_may_have_dots(context, input.name)
                if input_value.startswith('http://') or input_value.startswith('https://'):
                    _set_in_dict_where_key_may_have_dots(context, input.name, InputFile(name=input.name, url=input_value))
                elif input_value.startswith('/') or input_value.startswith('./') or input_value.startswith('../'):
                    _set_in_dict_where_key_may_have_dots(context, input.name, InputFile(name=input.name, local_file_name=input_value))
                else:
                    raise Exception(f'Input value for {input.name} must either be a URL or a local path starting with /, ./ or ../. Got: {input_value}')

            # handle input folders coming in as url's
            for input_folder in processor._input_folders:
                input_folder_value = _get_in_dict_where_key_may_have_dots(context, input_folder.name)
                if input_folder_value.startswith('http://') or input_folder_value.startswith('https://'):
                    _set_in_dict_where_key_may_have_dots(context, input_folder.name, InputFolder(name=input_folder.name, url=input_folder_value))
                elif input_folder_value.startswith('/') or input_folder_value.startswith('./') or input_folder_value.startswith('../'):
                    _set_in_dict_where_key_may_have_dots(context, input_folder.name, InputFolder(name=input_folder.name, local_folder_name=input_folder_value))
                else:
                    raise Exception(f'Input folder value for {input_folder.name} must either be a URL or a local path starting with /, ./ or ../. Got: {input_folder_value}')

            # handle output files coming in as file paths
            for output in processor._outputs:
                output_value = _get_in_dict_where_key_may_have_dots(context, output.name)
                if output_value.startswith('https://') or output_value.startswith('http://'):
                    raise Exception(f'Output value for {output.name} cannot be a URL. Should be local file path. Got: {output_value}')
                elif output_value.startswith('/') or output_value.startswith('./') or output_value.startswith('../'):
                    _set_in_dict_where_key_may_have_dots(context, output.name, OutputFile(name=output.name, output_file_name=output_value))
                else:
                    raise Exception(f'Output value for {output.name} must be a local path starting with /, ./ or ../. Got: {output_value}')

            # handle output folders coming in as file paths
            for output_folder in processor._output_folders:
                output_folder_value = _get_in_dict_where_key_may_have_dots(context, output_folder.name)
                if output_folder_value.startswith('https://') or output_folder_value.startswith('http://'):
                    raise Exception(f'Output folder value for {output_folder.name} cannot be a URL. Should be local folder path. Got: {output_folder_value}')
                elif output_folder_value.startswith('/') or output_folder_value.startswith('./') or output_folder_value.startswith('../'):
                    _set_in_dict_where_key_may_have_dots(context, output_folder.name, OutputFolder(name=output_folder.name, output_folder_name=output_folder_value))
                else:
                    raise Exception(f'Output folder value for {output_folder.name} must be a local path starting with /, ./ or ../. Got: {output_folder_value}')

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
            app_executable=spec.get('appExecutable', None),
        )
        app._spec_dict = spec
        for processor_spec in spec['processors']:
            processor = AppProcessor.from_spec(processor_spec)
            app._processors.append(processor)
        return app

    @staticmethod
    def from_spec_uri(
        spec_uri: str
    ):
        """Define an app from a spec URI (e.g., a gh url to the spec.json blob). This is called internally."""
        spec: dict = _load_spec_from_uri(spec_uri)
        a = App.from_spec(spec)
        a._spec_uri = spec_uri
        return a

def _get_type_of_context_in_processor_class(processor_class):
    # Retrieve the 'run' method from the processor class
    run_method = getattr(processor_class, 'run', None)
    if not run_method:
        raise Exception(f'Processor class does not have a run method: {processor_class}')
    # Get the type hints of the 'run' method
    type_hints = get_type_hints(run_method)
    # Return the type hint for the 'context' parameter
    return type_hints.get('context')

def _get_in_dict_where_key_may_have_dots(d: dict, key: str):
    if '.' in key:
        key_parts = key.split('.')
        for key_part in key_parts[:-1]:
            d = d[key_part]
        return d[key_parts[-1]]
    else:
        return d[key]

def _set_in_dict_where_key_may_have_dots(d: dict, key: str, value):
    if '.' in key:
        key_parts = key.split('.')
        for key_part in key_parts[:-1]:
            d = d[key_part]
        d[key_parts[-1]] = value
    else:
        d[key] = value
