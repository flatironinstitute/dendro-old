import time
from typing import Union, List, Any
from pydantic import BaseModel
from ...core.protocaas_types import ComputeResourceSpecProcessor, ProtocaasJobInputFile, ProtocaasJobOutputFile, ProtocaasJob, ProtocaasJobInputParameter
from ...clients.db import fetch_project, fetch_file, delete_file, fetch_project_jobs, delete_job, insert_job
from ...core._get_project_role import _project_is_editable
from ...core._create_random_id import _create_random_id
from ...clients.pubsub import publish_pubsub_message
from .._remove_detached_files_and_jobs import _remove_detached_files_and_jobs
from ...core.settings import get_settings

class CreateJobRequestInputFile(BaseModel):
    name: str
    fileName: str

class CreateJobRequestOutputFile(BaseModel):
    name: str
    fileName: str

class CreateJobRequestInputParameter(BaseModel):
    name: str
    value: Union[Any, None]

async def create_job(
    project_id: str,
    processor_name: str,
    input_files_from_request: List[CreateJobRequestInputFile],
    output_files_from_request: List[CreateJobRequestOutputFile],
    input_parameters: List[CreateJobRequestInputParameter],
    processor_spec: ComputeResourceSpecProcessor,
    batch_id: Union[str, None],
    user_id: str,
    dandi_api_key: Union[str, None] = None
):
    project = await fetch_project(project_id)
    
    if not _project_is_editable(project, user_id):
        raise Exception('User does not have permission to create jobs')
    
    compute_resource_id = project.computeResourceId
    if not compute_resource_id:
        compute_resource_id = get_settings().DEFAULT_COMPUTE_RESOURCE_ID
        if compute_resource_id is None:
            raise Exception('Project does not have a compute resource ID, and no default VITE_DEFAULT_COMPUTE_RESOURCE_ID is set in the environment.')
    
    input_files: List[ProtocaasJobInputFile] = [] # {name, fileId, fileName}
    for input_file in input_files_from_request:
        file = await fetch_file(project_id, input_file.fileName)
        if file is None:
            raise Exception(f"Project input file does not exist: {input_file.fileName}")
        input_files.append(
            ProtocaasJobInputFile(
                name=input_file.name,
                fileId=file.fileId,
                fileName=file.fileName
            )
        )
    
    job_id = _create_random_id(8)
    job_private_key = _create_random_id(32)

    def filter_output_file_name(file_name):
        # replace ${job-id} with the actual job ID
        return file_name.replace('${job-id}', job_id)
    
    output_files: List[ProtocaasJobOutputFile] = []
    for output_file in output_files_from_request:
        output_files.append(
            ProtocaasJobOutputFile(
                name=output_file.name,
                fileName=filter_output_file_name(output_file.fileName)
            )
        )
    
    something_was_deleted = False
    
    # delete any existing output files
    for output_file in output_files:
        existing_file = await fetch_file(project_id, output_file.fileName)
        if existing_file is not None:
            await delete_file(project_id, output_file.fileName)
            something_was_deleted = True
    
    # delete any jobs that are expected to produce the output files
    # because maybe the output files haven't been created yet, but we still want to delete/cancel them
    all_jobs = await fetch_project_jobs(project_id, include_private_keys=False)
    
    output_file_names = [x.fileName for x in output_files]
    for job in all_jobs:
        should_delete = False
        for output_file in job.outputFiles:
            if output_file.fileName in output_file_names:
                should_delete = True
        if should_delete:
            await delete_job(job.jobId)
            something_was_deleted = True
    
    if something_was_deleted:
        await _remove_detached_files_and_jobs(project_id)
    
    input_parameters2: List[ProtocaasJobInputParameter] = []
    for input_parameter in input_parameters:
        pp = next((x for x in processor_spec.parameters if x.name == input_parameter.name), None)
        if not pp:
            raise Exception(f"Processor parameter not found: {input_parameter.name}")
        input_parameters2.append(
            ProtocaasJobInputParameter(
                name=input_parameter.name,
                value=input_parameter.value,
                secret=pp.secret
            )
        )

    output_bucket_base_url = get_settings().OUTPUT_BUCKET_BASE_URL
    job = ProtocaasJob(
        jobId=job_id,
        jobPrivateKey=job_private_key,
        projectId=project_id,
        userId=user_id,
        processorName=processor_name,
        inputFiles=input_files,
        inputFileIds=[x.fileId for x in input_files],
        inputParameters=input_parameters2,
        outputFiles=output_files,
        timestampCreated=time.time(),
        computeResourceId=compute_resource_id,
        status='pending',
        processorSpec=processor_spec,
        batchId=batch_id,
        dandiApiKey=dandi_api_key,
        consoleOutputUrl=f"{output_bucket_base_url}/protocaas-outputs/{job_id}/_console_output"
    )
    
    await insert_job(job)

    await publish_pubsub_message(
        channel=job.computeResourceId,
        message={
            'type': 'newPendingJob',
            'projectId': project_id,
            'computeResourceId': compute_resource_id,
            'jobId': job_id
        }
    )

    return job_id