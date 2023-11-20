import time
from typing import Union, List, Any
from ....common.dendro_types import ComputeResourceSpecProcessor, DendroJobInputFile, DendroJobOutputFile, DendroJob, DendroJobInputParameter
from ...clients.db import fetch_project, fetch_file, delete_file, fetch_project_jobs, delete_job, insert_job
from ...core._get_project_role import _check_user_can_edit_project
from ...core._create_random_id import _create_random_id
from ...clients.pubsub import publish_pubsub_message
from .._remove_detached_files_and_jobs import _remove_detached_files_and_jobs
from ...core.settings import get_settings
from ....common.dendro_types import CreateJobRequestInputFile, CreateJobRequestOutputFile, CreateJobRequestInputParameter

class CreateJobException(Exception):
    pass

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
    _check_job_is_consistent_with_processor_spec(
        processor_spec=processor_spec,
        processor_name=processor_name,
        input_files_from_request=input_files_from_request,
        output_files_from_request=output_files_from_request,
        input_parameters=input_parameters
    )

    project = await fetch_project(project_id)
    assert project is not None, f"No project with ID {project_id}"

    _check_user_can_edit_project(project, user_id)

    compute_resource_id = project.computeResourceId if project.computeResourceId else get_settings().DEFAULT_COMPUTE_RESOURCE_ID
    if not compute_resource_id:
        raise KeyError('Project does not have a compute resource ID, and no default VITE_DEFAULT_COMPUTE_RESOURCE_ID is set in the environment.')

    input_files: List[DendroJobInputFile] = [] # {name, fileId, fileName}
    for input_file in input_files_from_request:
        file = await fetch_file(project_id, input_file.fileName)
        if file is None:
            raise CreateJobException(f"Project input file does not exist: {input_file.fileName}")
        input_files.append(
            DendroJobInputFile(
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

    output_files: List[DendroJobOutputFile] = []
    for output_file in output_files_from_request:
        output_files.append(
            DendroJobOutputFile(
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

    input_parameters2: List[DendroJobInputParameter] = []
    for input_parameter in input_parameters:
        pp = next((x for x in processor_spec.parameters if x.name == input_parameter.name), None)
        if not pp:
            raise CreateJobException(f"Processor parameter not found: {input_parameter.name}")
        input_parameters2.append(
            DendroJobInputParameter(
                name=input_parameter.name,
                value=input_parameter.value,
                secret=pp.secret
            )
        )

    output_bucket_base_url = get_settings().OUTPUT_BUCKET_BASE_URL
    job = DendroJob(
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
        consoleOutputUrl=f"{output_bucket_base_url}/dendro-outputs/{job_id}/_console_output"
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

def _check_job_is_consistent_with_processor_spec(
    processor_spec: ComputeResourceSpecProcessor,
    processor_name: str,
    input_files_from_request: List[CreateJobRequestInputFile],
    output_files_from_request: List[CreateJobRequestOutputFile],
    input_parameters: List[CreateJobRequestInputParameter]
):
    # check that the processor name matches
    if processor_spec.name != processor_name:
        raise CreateJobException(f"Processor name mismatch: {processor_spec.name} != {processor_name}")

    # check that the input files are consistent with the spec
    for input_file in input_files_from_request:
        if input_file.name.endswith(']'):
            base_name = input_file.name.split('[')[0]
            xx = next((x for x in processor_spec.inputs if x.name == base_name), None)
            if not xx:
                raise CreateJobException(f"Processor input not found: {base_name}")
            if not xx.list:
                raise CreateJobException(f"Processor input is not a list: {base_name}")
        else:
            xx = next((x for x in processor_spec.inputs if x.name == input_file.name), None)
            if not xx:
                raise CreateJobException(f"Processor input not found: {input_file.name}")

    # check that all the required inputs are present
    for input in processor_spec.inputs:
        if not input.list:
            if not any(x.name == input.name for x in input_files_from_request):
                raise CreateJobException(f"Required input not found: {input.name}")

    # check that the output files are consistent with the spec
    for output_file in output_files_from_request:
        xx = next((x for x in processor_spec.outputs if x.name == output_file.name), None)
        if not xx:
            raise CreateJobException(f"Processor output not found: {output_file.name}")

    # check that the required output files are present
    for output in processor_spec.outputs:
        if not any(x.name == output.name for x in output_files_from_request):
            raise CreateJobException(f"Required output not found: {output.name}")

    # check that the input parameters are consistent with the spec
    for input_parameter in input_parameters:
        pp = next((x for x in processor_spec.parameters if x.name == input_parameter.name), None)
        if not pp:
            raise CreateJobException(f"Processor parameter not found: {input_parameter.name}")
        if not _parameter_value_is_consistent_with_type(input_parameter.value, pp.type):
            raise CreateJobException(f"Parameter value is not consistent with type: {input_parameter.name} {input_parameter.value} {pp.type}")

    # check that the parameters that do not have a default are present
    for pp in processor_spec.parameters:
        if pp.default is None and not pp.type.startswith('Optional['):
            input_parameter = next((x for x in input_parameters if x.name == pp.name), None)
            if not input_parameter:
                raise CreateJobException(f"Required parameter not found: {pp.name}")

def _parameter_value_is_consistent_with_type(value: Any, type: str):
    if type == 'str':
        return isinstance(value, str)
    elif type == 'int':
        return isinstance(value, int)
    elif type == 'float':
        return isinstance(value, float) or isinstance(value, int)
    elif type == 'bool':
        return isinstance(value, bool)
    elif type == 'List[str]':
        return isinstance(value, list) and all(isinstance(x, str) for x in value)
    elif type == 'List[int]':
        return isinstance(value, list) and all(isinstance(x, int) for x in value)
    elif type == 'List[float]':
        return isinstance(value, list) and all(isinstance(x, float) or isinstance(x, int) for x in value)
    elif type == 'List[bool]':
        return isinstance(value, list) and all(isinstance(x, bool) for x in value)
    elif type == 'Optional[int]':
        return isinstance(value, int) or value is None
    elif type == 'Optional[float]':
        return isinstance(value, float) or isinstance(value, int) or value is None
    else:
        raise Exception(f"Unknown type in _parameter_value_is_consistent_with_type: {type}")
