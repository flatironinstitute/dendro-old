from typing import Any, List, Dict
import time
from dataclasses import dataclass
from .InputFile import InputFile
from .InputFolder import InputFolder
from .OutputFile import OutputFile
from .OutputFolder import OutputFolder
from ..common._api_request import _processor_get_api_request
from ..common.dendro_types import ProcessorGetJobResponse, ProcessorGetJobV2Response, GetJobFileInfoResponse
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
        resp = _job_info_manager.get_job_info_v2(job_id=job_id, job_private_key=job_private_key)
        # important to set these only once here because these objects will be passed into the processor function
        self._inputs = [InputFile(name=i.name, job_id=self._job_id, job_private_key=self._job_private_key) for i in resp.inputs]
        self._input_folders = [InputFolder(name=i.name, job_id=self._job_id, job_private_key=self._job_private_key) for i in resp.inputFolders] if resp.inputFolders else None
        self._outputs = [OutputFile(name=o.name, job_id=self._job_id, job_private_key=self._job_private_key) for o in resp.outputs]
        self._output_folders = [OutputFolder(name=o.name, job_id=self._job_id, job_private_key=self._job_private_key) for o in resp.outputFolders] if resp.outputFolders else None
        self._parameters = [JobParameter(name=p.name, value=p.value) for p in resp.parameters]
        self._processor_name = resp.processorName

        for input in self._inputs:
            input._check_file_cache()
    @property
    def job_id(self) -> str:
        """The ID of the job"""
        return self._job_id
    @property
    def processor_name(self) -> str:
        """The name of the processor"""
        resp = _job_info_manager.get_job_info_v2(job_id=self._job_id, job_private_key=self._job_private_key)
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

def _get_file_id_for_output_file(*, name: str, job_id: str, job_private_key: str) -> str:
    """Get the file ID for an output file"""

    url_path = f'/api/processor/jobs/{job_id}/outputs/{name}/file_id'
    headers = {
        'job-private-key': job_private_key
    }
    resp = _processor_get_api_request(
        url_path=url_path,
        headers=headers
    )
    file_id = resp['fileId']
    return file_id

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

@dataclass
class JobInfoRecordV2:
    job_id: str
    job_private_key: str
    resp: ProcessorGetJobV2Response
    timestamp: float

@dataclass
class FileDownloadRecord:
    job_id: str
    job_private_key: str
    file_id: str
    download_url: str
    timestamp: float

@dataclass
class FolderDownloadRecord:
    job_id: str
    job_private_key: str
    file_id: str
    download_url: str
    timestamp: float

class JobInfoManager:
    def __init__(self) -> None:
        self._info_records: Dict[str, JobInfoRecord] = {}
        self._info_records_v2: Dict[str, JobInfoRecordV2] = {}
        self._file_download_records: Dict[str, FileDownloadRecord] = {}
        self._folder_download_records: Dict[str, FolderDownloadRecord] = {}
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
    def get_job_info_v2(self, *, job_id: str, job_private_key: str) -> ProcessorGetJobV2Response:
        if job_id in self._info_records:
            rec = self._info_records_v2[job_id]
            elapsed = time.time() - rec.timestamp
            if elapsed < 30 * 60:
                return rec.resp
        url_path = f'/api/processor/jobs_v2/{job_id}'
        headers = {
            'job-private-key': job_private_key
        }
        resp_dict = _processor_get_api_request(
            url_path=url_path,
            headers=headers
        )
        resp = ProcessorGetJobV2Response(**resp_dict)
        rec = JobInfoRecordV2(job_id=job_id, job_private_key=job_private_key, resp=resp, timestamp=time.time())
        self._info_records_v2[job_id] = rec
        return resp
    def get_file_download_url(self, *, file_id: str, job_id: str, job_private_key: str) -> str:
        k = f'{job_id}:{file_id}'
        if k in self._file_download_records:
            rec = self._file_download_records[k]
            elapsed = time.time() - rec.timestamp
            if elapsed < 30 * 60:
                return rec.download_url
        url_path = f'/api/processor/jobs/{job_id}/files/{file_id}'
        headers = {
            'job-private-key': job_private_key
        }
        resp = _processor_get_api_request(
            url_path=url_path,
            headers=headers
        )
        resp = GetJobFileInfoResponse(**resp)
        if resp.isFolder:
            raise Exception(f'File is a folder when trying to get download URL: {file_id}')
        download_url = resp.downloadUrl
        rec = FileDownloadRecord(job_id=job_id, job_private_key=job_private_key, file_id=file_id, download_url=download_url, timestamp=time.time())
        self._file_download_records[k] = rec
        return download_url
    def get_folder_download_url(self, *, file_id: str, job_id: str, job_private_key: str) -> str:
        k = f'{job_id}:{file_id}'
        if k in self._folder_download_records:
            rec = self._folder_download_records[k]
            elapsed = time.time() - rec.timestamp
            if elapsed < 30 * 60:
                return rec.download_url
        url_path = f'/api/processor/jobs/{job_id}/folders/{file_id}'
        headers = {
            'job-private-key': job_private_key
        }
        resp = _processor_get_api_request(
            url_path=url_path,
            headers=headers
        )
        resp = GetJobFileInfoResponse(**resp)
        if not resp.isFolder:
            raise Exception(f'File is not a folder when trying to get download URL: {file_id}')
        download_url = resp.downloadUrl
        rec = FolderDownloadRecord(job_id=job_id, job_private_key=job_private_key, file_id=file_id, download_url=download_url, timestamp=time.time())
        self._folder_download_records[k] = rec
        return download_url

_job_info_manager = JobInfoManager()

def _get_download_url_for_input_file_v1(*, name: str, job_id: str, job_private_key: str) -> str:
    resp = _job_info_manager.get_job_info(job_id=job_id, job_private_key=job_private_key)
    input = next((i for i in resp.inputs if i.name == name), None)
    if input is None:
        raise Exception(f'Input not found when trying to get download URL: {name}')
    download_url = input.url
    return download_url

def _get_uri_and_label_for_input_file(*, name: str, job_id: str, job_private_key: str):
    resp = _job_info_manager.get_job_info_v2(job_id=job_id, job_private_key=job_private_key)
    input = next((i for i in resp.inputs if i.name == name), None)
    if input is None:
        raise Exception(f'Input not found when trying to get download URL: {name}')
    file_id, is_folder, label = _parse_dendro_uri(input.dendro_uri)
    if is_folder:
        raise Exception(f'Input is a folder when trying to get download URL: {name}')
    return input.dendro_uri, label

def _get_download_url_for_uri(*, uri: str, job_id: str, job_private_key: str):
    file_id, is_folder, label = _parse_dendro_uri(uri)
    download_url = _job_info_manager.get_file_download_url(file_id=file_id, job_id=job_id, job_private_key=job_private_key)
    return download_url

def _get_download_url_and_label_for_input_folder_file_v2(*, name: str, job_id: str, job_private_key: str, relative_file_name: str):
    resp = _job_info_manager.get_job_info_v2(job_id=job_id, job_private_key=job_private_key)
    input_folders = resp.inputFolders
    if input_folders is None:
        raise Exception(f'Input folders not found when trying to get download URL: {name}')
    input_folder = next((i for i in input_folders if i.name == name), None)
    if input_folder is None:
        raise Exception(f'Input folder not found when trying to get download URL: {name}')
    file_id, is_folder, label = _parse_dendro_uri(input_folder.dendro_uri)
    if not is_folder:
        raise Exception(f'Input is not a folder when trying to get download URL: {name}')
    folder_download_url = _job_info_manager.get_folder_download_url(file_id=file_id, job_id=job_id, job_private_key=job_private_key)
    download_url = folder_download_url + '/' + relative_file_name
    return download_url, label

def _parse_dendro_uri(dendro_uri: str):
    """Parse a Dendro URI and return the file ID, whether it's a folder, and the label"""
    # dendro uri looks like this: dendro:?file_id=[file_id]&label=[label]&folder=[true/false]
    parts = dendro_uri.split('?')
    if len(parts) != 2:
        raise Exception(f'Invalid Dendro URI: {dendro_uri}')
    part1 = parts[0]
    if part1 != 'dendro:':
        raise Exception(f'Invalid Dendro URI: {dendro_uri}')
    part2 = parts[1]
    params0 = [p.split('=') for p in part2.split('&')]
    params = {p[0]: p[1] for p in params0}
    if 'file_id' not in params:
        raise Exception(f'Invalid Dendro URI (no file_id parameter): {dendro_uri}')
    file_id = params['file_id']
    is_folder = params.get('folder', 'false') == 'true' or params.get('folder', 'False') == 'True'
    label = params.get('label', '')
    return file_id, is_folder, label

def _get_file_manifest_for_input_folder_v1(*, name: str, job_id: str, job_private_key: str) -> FileManifest:
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
