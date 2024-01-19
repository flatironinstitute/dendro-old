from typing import List
from .InputFile import InputFile
from .InputFolder import InputFolder
from .Job import Job
from .AppProcessor import AppProcessor
from ..common._api_request import _processor_get_api_request


# An empty object that we can set attributes on
# The user is going to think it's a pydantic model, but it's not
# We'll at least give them a dict() and a model_dump() method
class ContextObject:
    def __init__(self) -> None:
        self._dendro_attributes = {}
    def _dendro_set_attribute(self, name, value):
        self._dendro_attributes[name] = value
        setattr(self, name, value)
    def _denro_set_attribute_where_name_may_have_dots(self, name, value):
        if '.' not in name:
            self._dendro_set_attribute(name, value)
            return
        parts = name.split('.')
        obj = self
        for part in parts[:-1]:
            if not hasattr(obj, part):
                obj._dendro_set_attribute(part, ContextObject())
            obj = getattr(obj, part)
            assert isinstance(obj, ContextObject), f'Unexpected type for {part}'
        obj._dendro_set_attribute(parts[-1], value)
    def dict(self):
        ret = {}
        for k, v in self._dendro_attributes.items():
            if isinstance(v, ContextObject):
                ret[k] = v.dict()
            else:
                ret[k] = v
        return ret
    def model_dump(self):
        return self.dict()

def _run_job_child_process(*, job_id: str, job_private_key: str, processors: List[AppProcessor]):
    """
    Used internally to actually run the job by calling the processor function.
    If an app image is being used, this will occur within the container.
    """

    # print statements here will end up in the console output for the job
    print(f'[dendro] Running job: {job_id}')

    # Get a job from the remote dendro API
    job: Job = _get_job(job_id=job_id, job_private_key=job_private_key)

    # Find the registered processor and the associated processor function
    processor_name = job.processor_name
    print(f'[dendro] Processor: {processor_name}')

    processor = next((p for p in processors if p._name == processor_name), None)
    if not processor:
        raise Exception(f'Processor not found: {processor_name}')
    if not processor._processor_class:
        raise Exception(f'Processor does not have a processor_class: {processor_name}')
    processor_class = processor._processor_class

    # Assemble the context for the processor function
    print('[dendro] Assembling context')
    context = ContextObject()
    for input in processor._inputs:
        if not input.list:
            # this input is not a list
            print(f'[dendro] Input: {input.name}')
            input_file = next((i for i in job.inputs if i.name == input.name), None)
            if not input_file:
                raise Exception(f'Input not found: {input.name}')
            context._dendro_set_attribute(input.name, input_file)
        else:
            # this input is a list
            print(f'[dendro] Input (list): {input.name}')
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
            print(f'[dendro] Input (list): {input.name} (found {len(the_list)} files)')
            context._dendro_set_attribute(input.name, the_list)
    for input_folder in processor._input_folders:
        if not input_folder.list:
            # this input folder is not a list
            print(f'[dendro] Input folder: {input_folder.name}')
            input_folder_object = next((i for i in job.input_folders if i.name == input_folder.name), None)
            if not input_folder_object:
                raise Exception(f'Input folder not found: {input_folder.name}')
            context._dendro_set_attribute(input_folder.name, input_folder_object)
        else:
            # this input folder is a list
            print(f'[dendro] Input folder (list): {input_folder.name}')
            the_folder_list: List[InputFolder] = []
            ii = 0
            while True:
                # find a job input folder of the form <input_folder_name>[ii]
                input_folder_object = next((i for i in job.input_folders if i.name == f'{input_folder.name}[{ii}]'), None)
                if input_folder_object is None:
                    # if not found, we must be at the end of the list
                    break
                the_folder_list.append(input_folder_object)
                ii += 1
            print(f'[dendro] Input folder (list): {input_folder.name} (found {len(the_folder_list)} folders)')
            context._dendro_set_attribute(input_folder.name, the_folder_list)
    for output in processor._outputs:
        print(f'[dendro] Output: {output.name}')
        output_file = next((o for o in job.outputs if o.name == output.name), None)
        if not output_file:
            raise Exception(f'Output not found: {output.name}')
        context._dendro_set_attribute(output.name, output_file)
    for output_folder in processor._output_folders:
        print(f'[dendro] Output folder: {output_folder.name}')
        output_folder_object = next((o for o in job.output_folders if o.name == output_folder.name), None)
        if not output_folder_object:
            raise Exception(f'Output folder not found: {output_folder.name}')
        context._dendro_set_attribute(output_folder.name, output_folder_object)
    for parameter in processor._parameters:
        job_parameter = next((p for p in job.parameters if p.name == parameter.name), None)
        if job_parameter is None:
            parameter_value = parameter.default
        else:
            parameter_value = job_parameter.value
        print(f'[dendro] Parameter: {parameter.name} = {parameter_value}')
        context._denro_set_attribute_where_name_may_have_dots(parameter.name, parameter_value)

    print('[dendro] Preparing to run processor')
    _set_custom_kachery_storage_backend(job_id=job_id, job_private_key=job_private_key)

    # Run the processor function
    print('[dendro] Running processor')
    processor_class.run(context)

    # Check that all outputs were set
    print('[dendro] Checking outputs')
    for output in processor._outputs:
        output_file = next((o for o in job.outputs if o.name == output.name), None)
        assert output_file is not None, f'Output not found: {output.name}'
        if not output_file.was_uploaded:
            raise Exception(f'Output was not uploaded: {output.name}')

    # Print a message indicating that the job is complete
    print(f'[dendro] Job complete: {job_id}')

def _get_job(*, job_id: str, job_private_key: str) -> Job:
    """Get a job from the dendro API"""
    job = Job(
        job_id=job_id,
        job_private_key=job_private_key
    )
    return job

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
