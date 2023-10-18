from typing import Any, List
import time
from dataclasses import dataclass
from .InputFile import InputFile
from .OutputFile import OutputFile
from ..common._api_request import _processor_get_api_request
from ..common.protocaas_types import ProcessorGetJobResponse


@dataclass
class JobParameter:
    """A parameter passed to a job"""
    name: str
    value: Any

class Job:
    """A job that is passed to a processor"""
    def __init__(self,
        job_id: str,
        job_private_key: str
    ) -> None:
        self._job_id = job_id
        self._job_private_key = job_private_key
        self._api_request_job_response: ProcessorGetJobResponse = None
        self._api_request_job_timestamp = 0
        self._api_request_job_if_needed()
        # important to set these only once here because these objects will be passed into the processor function
        self._inputs = [InputFile(name=i.name, job=self) for i in self._api_request_job_response.inputs]
        self._outputs = [OutputFile(name=o.name, job=self) for o in self._api_request_job_response.outputs]
        self._parameters = [JobParameter(name=p.name, value=p.value) for p in self._api_request_job_response.parameters]
    def add_input_file(self, name: str):
        """Add an input file to the job"""
        input_file = InputFile(name=name, job=self)
        self._inputs.append(input_file)
    def add_output_file(self, name: str):
        """Add an output file to the job"""
        output_file = OutputFile(name=name, job=self)
        self._outputs.append(output_file)
    def add_parameter(self, name: str, value: Any):
        """Add a parameter to the job"""
        parameter = JobParameter(name=name, value=value)
        self._parameters.append(parameter)
    @property
    def job_id(self) -> str:
        """The ID of the job"""
        return self._job_id
    @property
    def status(self) -> str:
        """The status of the job"""
        self._api_request_job_if_needed()
        return self._api_request_job_response.status
    @property
    def processor_name(self) -> str:
        """The name of the processor"""
        self._api_request_job_if_needed()
        return self._api_request_job_response.processorName
    @property
    def inputs(self) -> List[InputFile]:
        """The input files of the job"""
        return self._inputs
    @property
    def outputs(self) -> List[OutputFile]:
        """The output files of the job"""
        return self._outputs
    @property
    def parameters(self) -> List[JobParameter]:
        """The parameters of the job"""
        return self._parameters
    def _get_upload_url_for_output_file(self, *, name: str) -> str:
        """Get a signed upload URL for an output file"""

        url_path = f'/api/processor/jobs/{self._job_id}/outputs/{name}/upload_url'
        headers = {
            'job-private-key': self._job_private_key
        }
        resp = _processor_get_api_request(
            url_path=url_path,
            headers=headers
        )
        upload_url = resp['uploadUrl'] # This will be a presigned AWS S3 URL
        return upload_url
    def _get_download_url_for_input_file(self, *, name: str) -> str:
        """Get a signed download URL for an input file"""
        self._api_request_job_if_needed()
        resp_inputs = self._api_request_job_response.inputs
        resp_input = next((i for i in resp_inputs if i.name == name), None)
        if resp_input is None:
            raise Exception(f'Input not found when trying to get download URL: {name}')
        download_url = resp_input.url
        return download_url
    def _api_request_job_if_needed(self):
        """Get the job info from the protocaas API"""
        elapsed = time.time() - self._api_request_job_timestamp
        if elapsed < 30 * 60:
            # typically, signed download URLs will expire after an hour
            return
        url_path = f'/api/processor/jobs/{self._job_id}'
        headers = {
            'job-private-key': self._job_private_key
        }
        resp_dict = _processor_get_api_request(
            url_path=url_path,
            headers=headers
        )
        resp = ProcessorGetJobResponse(**resp_dict)
        self._api_request_job_response = resp
        self._api_request_job_timestamp = time.time()