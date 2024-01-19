from typing import Any, List, Dict
import time
from dataclasses import dataclass
from .InputFile import InputFile
from .InputFolder import InputFolder
from .OutputFile import OutputFile
from .OutputFolder import OutputFolder
from ..common._api_request import _processor_get_api_request
from ..common.dendro_types import ProcessorGetJobResponse
from .FileManifest import FileManifest, FileManifestFile


@dataclass
class JobParameter:
    """A parameter passed to a job"""
    name: str
    value: Any

class JobApiRequestException(Exception):
    pass

class Job:
    """A job that is passed to a processor"""
    def __init__(self,
        job_id: str,
        job_private_key: str
    ) -> None:
        self._job_id = job_id
        self._job_private_key = job_private_key
        resp = _job_info_manager.get_job_info(job_id=job_id, job_private_key=job_private_key)
        # important to set these only once here because these objects will be passed into the processor function
        self._inputs = [InputFile(name=i.name, job_id=self._job_id, job_private_key=self._job_private_key) for i in resp.inputs]
        self._input_folders = [InputFolder(name=i.name, job_id=self._job_id, job_private_key=self._job_private_key) for i in resp.inputFolders] if resp.inputFolders else None
        self._outputs = [OutputFile(name=o.name, job_id=self._job_id, job_private_key=self._job_private_key) for o in resp.outputs]
        self._output_folders = [OutputFolder(name=o.name, job_id=self._job_id, job_private_key=self._job_private_key) for o in resp.outputFolders] if resp.outputFolders else None
        self._parameters = [JobParameter(name=p.name, value=p.value) for p in resp.parameters]
        self._processor_name = resp.processorName
    @property
    def job_id(self) -> str:
        """The ID of the job"""
        return self._job_id
    @property
    def processor_name(self) -> str:
        """The name of the processor"""
        resp = _job_info_manager.get_job_info(job_id=self._job_id, job_private_key=self._job_private_key)
        return resp.processorName
    @property
    def inputs(self) -> List[InputFile]:
        """The input files of the job"""
        return self._inputs
    @property
    def input_folders(self) -> List[InputFolder]:
        """The input folders of the job"""
        return self._input_folders if self._input_folders is not None else []
    @property
    def outputs(self) -> List[OutputFile]:
        """The output files of the job"""
        return self._outputs
    @property
    def output_folders(self) -> List[OutputFolder]:
        """The output folders of the job"""
        return self._output_folders if self._output_folders is not None else []
    @property
    def parameters(self) -> List[JobParameter]:
        """The parameters of the job"""
        return self._parameters

def _get_upload_url_for_output_file(*, name: str, job_id: str, job_private_key: str) -> str:
    """Get a signed upload URL for an output file"""

    url_path = f'/api/processor/jobs/{job_id}/outputs/{name}/upload_url'
    headers = {
        'job-private-key': job_private_key
    }
    resp = _processor_get_api_request(
        url_path=url_path,
        headers=headers
    )
    upload_url = resp['uploadUrl'] # This will be a presigned AWS S3 URL
    return upload_url

def _get_upload_url_for_output_folder_file(*, name: str, relative_file_name: str, job_id: str, job_private_key: str) -> str:
    """Get a signed upload URL for an output folder file"""

    url_path = f'/api/processor/jobs/{job_id}/output_folders/{name}/files/{relative_file_name}/upload_url'
    headers = {
        'job-private-key': job_private_key
    }
    resp = _processor_get_api_request(
        url_path=url_path,
        headers=headers
    )
    upload_url = resp['uploadUrl'] # This will be a presigned AWS S3 URL
    return upload_url

@dataclass
class JobInfoRecord:
    job_id: str
    job_private_key: str
    resp: ProcessorGetJobResponse
    timestamp: float

class JobInfoManager:
    def __init__(self) -> None:
        self._info_records: Dict[str, JobInfoRecord] = {}
    def get_job_info(self, *, job_id: str, job_private_key: str) -> ProcessorGetJobResponse:
        if job_id in self._info_records:
            rec = self._info_records[job_id]
            elapsed = time.time() - rec.timestamp
            if elapsed < 30 * 60:
                return rec.resp
        url_path = f'/api/processor/jobs/{job_id}'
        headers = {
            'job-private-key': job_private_key
        }
        resp_dict = _processor_get_api_request(
            url_path=url_path,
            headers=headers
        )
        resp = ProcessorGetJobResponse(**resp_dict)
        rec = JobInfoRecord(job_id=job_id, job_private_key=job_private_key, resp=resp, timestamp=time.time())
        self._info_records[job_id] = rec
        return resp

_job_info_manager = JobInfoManager()

def _get_download_url_for_input_file(*, name: str, job_id: str, job_private_key: str) -> str:
    resp = _job_info_manager.get_job_info(job_id=job_id, job_private_key=job_private_key)
    input = next((i for i in resp.inputs if i.name == name), None)
    if input is None:
        raise Exception(f'Input not found when trying to get download URL: {name}')
    download_url = input.url
    return download_url

def _get_file_manifest_for_input_folder(*, name: str, job_id: str, job_private_key: str) -> FileManifest:
    resp = _job_info_manager.get_job_info(job_id=job_id, job_private_key=job_private_key)
    if resp.inputFolders is None:
        raise Exception(f'Input folders not found when trying to get file manifest: {name}')
    input_folder = next((i for i in resp.inputFolders if i.name == name), None)
    if input_folder is None:
        raise Exception(f'Input folder not found when trying to get file manifest: {name}')
    manifest = FileManifest(
        files=[
            FileManifestFile(
                name=f.name,
                url=f.url,
                size=f.size
            )
            for f in input_folder.files
        ]
    )
    return manifest
