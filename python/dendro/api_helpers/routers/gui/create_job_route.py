from typing import Union
from fastapi import APIRouter, Header

from ._authenticate_gui_request import _authenticate_gui_request
from ...services.gui.create_job import create_job
from ..common import api_route_wrapper

from ....common.dendro_types import CreateJobRequest, CreateJobResponse


router = APIRouter()

# create job

@router.post("/jobs")
@api_route_wrapper
async def create_job_handler(
    data: CreateJobRequest,
    github_access_token: Union[str, None] = Header(None),
    dendro_api_key: Union[str, None] = Header(None)
) -> CreateJobResponse:
    # authenticate the request
    user_id = await _authenticate_gui_request(
        github_access_token=github_access_token,
        dendro_api_key=dendro_api_key,
        raise_on_not_authenticated=True
    )
    assert user_id

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
