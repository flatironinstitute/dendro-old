from typing import Union, List
from .... import BaseModel
from fastapi import APIRouter, Header

from ._authenticate_gui_request import _authenticate_gui_request
from ...services.gui.create_job import create_job, CreateJobRequestInputFile, CreateJobRequestOutputFile, CreateJobRequestInputParameter
from ....common.dendro_types import ComputeResourceSpecProcessor
from ..common import api_route_wrapper


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

@router.post("/jobs")
@api_route_wrapper
async def create_job_handler(data: CreateJobRequest, github_access_token: str = Header(...)) -> CreateJobResponse:
    # authenticate the request
    user_id = await _authenticate_gui_request(github_access_token, raise_on_not_authenticated=True)

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
