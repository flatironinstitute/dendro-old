from typing import Union, List
import traceback
import aiohttp
from fastapi import APIRouter, HTTPException, Header
from .... import BaseModel
from ...services.processor.update_job_status import update_job_status
from ...services.processor.get_upload_url import get_upload_url, get_additional_upload_url
from ....common.dendro_types import ProcessorGetJobResponse, ProcessorGetJobResponseInput, ProcessorGetJobResponseOutput, ProcessorGetJobResponseParameter
from ...clients.db import fetch_job, fetch_file

router = APIRouter()

# get job
@router.get("/jobs/{job_id}")
async def processor_get_job(job_id: str, job_private_key: str = Header(...)) -> ProcessorGetJobResponse:
    try:
        job = await fetch_job(job_id, include_dandi_api_key=True, include_secret_params=True, include_private_key=True)
        if job is None:
            raise Exception(f"No job with ID {job_id}")

        if job.jobPrivateKey != job_private_key:
            raise Exception(f"Invalid job private key for job {job_id}")
        # after we are done with it, let's delete the private key from the job object for safety
        job.jobPrivateKey = ''

        inputs: List[ProcessorGetJobResponseInput] = []
        for input in job.inputFiles:
            file = await fetch_file(project_id=job.projectId, file_name=input.fileName)
            if file is None:
                raise Exception(f"Project file not found: {input.fileName}")
            if not file.content.startswith('url:'):
                raise Exception(f"Project file {input.fileName} is not a URL")
            url = file.content[len('url:'):]
            url = await _resolve_dandi_url(url, dandi_api_key=job.dandiApiKey)
            inputs.append(ProcessorGetJobResponseInput(
                name=input.name,
                url=url
            ))

        outputs: List[ProcessorGetJobResponseOutput] = []
        for output in job.outputFiles:
            outputs.append(ProcessorGetJobResponseOutput(
                name=output.name
            ))

        parameters: List[ProcessorGetJobResponseParameter] = []
        for parameter in job.inputParameters:
            parameters.append(ProcessorGetJobResponseParameter(
                name=parameter.name,
                value=parameter.value
            ))

        return ProcessorGetJobResponse(
            jobId=job.jobId,
            status=job.status,
            processorName=job.processorName,
            inputs=inputs,
            outputs=outputs,
            parameters=parameters
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

async def _resolve_dandi_url(url: str, *, dandi_api_key: Union[str, None]) -> str:
    if url.startswith('https://api.dandiarchive.org/api/') or url.startswith('https://api-staging.dandiarchive.org/api/'):
        headers = {}
        if dandi_api_key is not None:
            headers['Authorization'] = f'token {dandi_api_key}'
        async with aiohttp.ClientSession() as session:
            async with session.head(url, allow_redirects=True, headers=headers) as resp:
                return str(resp.url)
    else:
        return url

# update job status
class ProcessorUpdateJobStatusRequest(BaseModel):
    status: str
    error: Union[str, None] = None
    force_update: Union[bool, None] = None

class ProcessorUpdateJobStatusResponse(BaseModel):
    success: bool

@router.put("/jobs/{job_id}/status")
async def processor_update_job_status(job_id: str, data: ProcessorUpdateJobStatusRequest, job_private_key: str = Header(...)) -> ProcessorUpdateJobStatusResponse:
    try:
        job = await fetch_job(job_id, include_private_key=True)
        if job is None:
            raise Exception(f"No job with ID {job_id}")
        if job.jobPrivateKey != job_private_key:
            raise Exception(f"Invalid job private key for job {job_id}")

        await update_job_status(job=job, status=data.status, error=data.error, force_update=data.force_update)

        return ProcessorUpdateJobStatusResponse(success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# get job status
class ProcessorGetJobStatusResponse(BaseModel):
    status: Union[str, None] # return None if job does not exist
    success: bool

@router.get("/jobs/{job_id}/status")
async def processor_get_job_status(job_id: str, job_private_key: str = Header(...)) -> ProcessorGetJobStatusResponse:
    try:
        job = await fetch_job(job_id, include_private_key=True)
        if job is None:
            return ProcessorGetJobStatusResponse(status=None, success=True) # pragma: no cover
        if job.jobPrivateKey != job_private_key:
            raise Exception(f"Invalid job private key for job {job_id}") # pragma: no cover

        return ProcessorGetJobStatusResponse(status=job.status, success=True)
    except Exception as e: # pragma: no cover
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# set job console output
class ProcessorSetJobConsoleOutputRequest(BaseModel):
    consoleOutput: str

class ProcessorSetJobConsoleOutputResponse(BaseModel):
    success: bool

# get job output upload url
class ProcessorGetJobOutputUploadUrlResponse(BaseModel):
    uploadUrl: str
    success: bool

# note that output_name = "_console_output" is a special case
@router.get("/jobs/{job_id}/outputs/{output_name}/upload_url")
async def processor_get_upload_url(job_id: str, output_name: str, job_private_key: str = Header(...)) -> ProcessorGetJobOutputUploadUrlResponse:
    try:
        job = await fetch_job(job_id, include_private_key=True)
        assert job, f"No job with ID {job_id}"
        if job.jobPrivateKey != job_private_key:
            raise ValueError(f"Invalid job private key for job {job_id}")

        signed_upload_url = await get_upload_url(job=job, output_name=output_name)
        return ProcessorGetJobOutputUploadUrlResponse(uploadUrl=signed_upload_url, success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

class ProcessorGetJobOutputUploadUrlForAdditionalFileResponse(BaseModel):
    uploadUrl: str
    downloadUrl: str
    success: bool

@router.get("/jobs/{job_id}/additional_uploads/sha1/{sha1}/upload_url")
async def processor_get_additional_upload_url(job_id: str, sha1: str, job_private_key: str = Header(...)) -> ProcessorGetJobOutputUploadUrlForAdditionalFileResponse:
    try:
        job = await fetch_job(job_id, include_private_key=True)
        assert job, f"No job with ID {job_id}"
        if job.jobPrivateKey != job_private_key:
            raise ValueError(f"Invalid job private key for job {job_id}")

        signed_upload_url, download_url = await get_additional_upload_url(job=job, sha1=sha1)
        return ProcessorGetJobOutputUploadUrlForAdditionalFileResponse(uploadUrl=signed_upload_url, downloadUrl=download_url, success=True)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e
