from typing import Union, List
import traceback
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Header

from ._authenticate_gui_request import _authenticate_gui_request
from ...services.gui.create_job import create_job, CreateJobRequestInputFile, CreateJobRequestOutputFile, CreateJobRequestInputParameter
from ...core.protocaas_types import ComputeResourceSpecProcessor


router = APIRouter()

# create job
class CreateJobRequest(BaseModel):
    projectId: str
    processorName: str
    inputFiles: List[CreateJobRequestInputFile]
    outputFiles: List[CreateJobRequestOutputFile]
    inputParameters: List[CreateJobRequestInputParameter]
    processorSpec: ComputeResourceSpecProcessor
    batchId: Union[str, None] = None
    dandiApiKey: Union[str, None] = None

class CreateJobResponse(BaseModel):
    jobId: str
    success: bool

class AuthException(Exception):
    pass

@router.post("/jobs")
async def create_job_handler(data: CreateJobRequest, github_access_token: str = Header(...)) -> CreateJobResponse:
    try:
        # authenticate the request
        user_id = await _authenticate_gui_request(github_access_token)
        if not user_id:
            raise AuthException('User is not authenticated')

        # parse the request
        project_id = data.projectId
        processor_name = data.processorName
        input_files_from_request = data.inputFiles
        output_files_from_request = data.outputFiles
        input_parameters = data.inputParameters
        processor_spec = data.processorSpec
        batch_id = data.batchId
        dandi_api_key = data.dandiApiKey

        job_id = await create_job(
            project_id=project_id,
            processor_name=processor_name,
            input_files_from_request=input_files_from_request,
            output_files_from_request=output_files_from_request,
            input_parameters=input_parameters,
            processor_spec=processor_spec,
            batch_id=batch_id,
            user_id=user_id,
            dandi_api_key=dandi_api_key
        )

        return CreateJobResponse(
            jobId=job_id,
            success=True
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
