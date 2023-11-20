from typing import Any, List, Union
import os
from pydantic import BaseModel
from .Project import Project
from ..common.dendro_types import CreateJobRequest, CreateJobResponse, CreateJobRequestInputFile, CreateJobRequestOutputFile, CreateJobRequestInputParameter, ComputeResourceSpecProcessor, DendroJob
from ..common._api_request import _client_post_api_request


class SubmitJobInputFile(BaseModel):
    name: str
    file_name: str

class SubmitJobOutputFile(BaseModel):
    name: str
    file_name: str

class SubmitJobParameter(BaseModel):
    name: str
    value: Any

def submit_job(*,
    project: Project,
    processor_name: str,
    input_files: List[SubmitJobInputFile],
    output_files: List[SubmitJobOutputFile],
    parameters: List[SubmitJobParameter],
    batch_id: Union[str, None] = None,
    rerun_policy: str = 'never' # always | never | if_failed
):
    """Submit a job to the Dendro compute service.

    Args:
        project (Project): The project to submit the job to.
        processor_name (str): The name of the processor to use.
        input_files (List[SubmitJobInputFile]): The input files for the job.
        output_files (List[SubmitJobOutputFile]): The output files for the job.
        parameters (List[SubmitJobParameter]): The input parameters for the job.
        batch_id (Union[str, None], optional): The batch ID to use. Defaults to None.
        rerun_policy (str, optional): The rerun policy to use. One of: 'always', 'never', 'if_failed'. Defaults to 'never'.

    Returns:
        str: The job ID.
    """
    if rerun_policy not in ['always', 'never', 'if_failed']:
        raise ValueError(f'Invalid rerun policy: {rerun_policy}')
    compute_resource = project._compute_resource
    if not compute_resource:
        raise KeyError(f'No compute resource found for project {project._name} ({project._project_id})')
    processor_spec = None
    if compute_resource.spec is None:
        raise KeyError(f'No spec found for compute resource {compute_resource.name} for project {project._name} ({project._project_id})')
    for app in compute_resource.spec.apps:
        for processor in app.processors:
            if processor.name == processor_name:
                processor_spec = processor
                break
        if processor_spec:
            break
    if not processor_spec:
        raise KeyError(f'No processor with name {processor_name} found in compute resource {compute_resource.name} for project {project._name} ({project._project_id})')
    default_parameters = _create_default_parameters(processor_spec, parameters)
    parameters = parameters + default_parameters
    _check_consistency_with_processor_spec(
        processor_spec=processor_spec,
        processor_name=processor_name,
        input_files=input_files,
        output_files=output_files,
        parameters=parameters
    )
    request_input_files = [
        CreateJobRequestInputFile(
            name=x.name,
            fileName=x.file_name
        )
        for x in input_files
    ]
    request_output_files = [
        CreateJobRequestOutputFile(
            name=x.name,
            fileName=x.file_name
        )
        for x in output_files
    ]
    request_parameters = [
        CreateJobRequestInputParameter(
            name=x.name,
            value=x.value
        )
        for x in parameters
    ]
    matching_job = None
    for job in project._jobs:
        if _job_matches(
            job=job,
            processor_name=processor_name,
            input_files=input_files,
            output_files=output_files,
            parameters=parameters
        ):
            matching_job = job
            break
    if matching_job:
        rerun = True
        if rerun_policy == 'never':
            rerun = False
        elif rerun_policy == 'if_failed':
            if matching_job.status == 'failed':
                rerun = True
            else:
                rerun = False
        elif rerun_policy == 'always':
            rerun = True
        else:
            raise ValueError(f'Invalid rerun policy: {rerun_policy}')
        if not rerun:
            print(f'Skipping job submission because a matching job was found: {matching_job.jobId}')
            return matching_job.jobId
    req = CreateJobRequest(
        projectId=project._project_id,
        processorName=processor_name,
        inputFiles=request_input_files,
        outputFiles=request_output_files,
        inputParameters=request_parameters,
        processorSpec=processor_spec,
        batchId=batch_id,
        dandiApiKey=os.environ.get('DANDI_API_KEY', None)
    )

    dendro_api_key = os.environ.get('DENDRO_API_KEY', None)
    if not dendro_api_key:
        raise ValueError('DENDRO_API_KEY environment variable is not set')

    url_path = '/api/client/jobs'
    resp = _client_post_api_request(
        url_path=url_path,
        data=_model_dump(req),
        dendro_api_key=dendro_api_key
    )
    resp = CreateJobResponse(**resp)
    print(f'Submitted job: {resp.jobId}')
    return resp.jobId

def _create_default_parameters(
    processor_spec: ComputeResourceSpecProcessor,
    parameters: List[SubmitJobParameter]
) -> List[SubmitJobParameter]:
    default_parameters = []
    for pp in processor_spec.parameters:
        if not any(x.name == pp.name for x in parameters):
            # need to wait for the model to be updated to include the "required" flag to do this
            # if pp.required:
            #     raise KeyError(f"Required parameter not found: {pp.name}")
            default_parameters.append(SubmitJobParameter(name=pp.name, value=pp.default))
    return default_parameters

def _check_consistency_with_processor_spec(
    processor_spec: ComputeResourceSpecProcessor,
    processor_name: str,
    input_files: List[SubmitJobInputFile],
    output_files: List[SubmitJobOutputFile],
    parameters: List[SubmitJobParameter]
):
    # check that the processor name matches
    if processor_spec.name != processor_name:
        raise KeyError(f'Processor name mismatch: {processor_spec.name} != {processor_name}')
    # check that the input files are consistent with the spec
    for input_file in input_files:
        pp = next((x for x in processor_spec.inputs if x.name == input_file.name), None)
        if not pp:
            raise KeyError(f"Processor input not found: {input_file.name}")
    # check that no input files are missing
    for input in processor_spec.inputs:
        if not any(x.name == input.name for x in input_files):
            raise KeyError(f"Required input not found: {input.name}")
    # check that the output files are consistent with the spec
    for output_file in output_files:
        pp = next((x for x in processor_spec.outputs if x.name == output_file.name), None)
        if not pp:
            raise KeyError(f"Processor output not found: {output_file.name}")
    # check that no output files are missing
    for output in processor_spec.outputs:
        if not any(x.name == output.name for x in output_files):
            raise KeyError(f"Required output not found: {output.name}")
    # check that the input parameters are consistent with the spec
    for input_parameter in parameters:
        pp = next((x for x in processor_spec.parameters if x.name == input_parameter.name), None)
        if not pp:
            raise KeyError(f"Processor parameter not found: {input_parameter.name}")

    # For this we need to wait for the model to be updated to include the "required" flag
    # # check that no required parameters are missing
    # for pp in processor_spec.parameters:
    #     if pp.required:
    #         input_parameter = next((x for x in parameters if x.name == pp.name), None)
    #         if not input_parameter:
    #             raise KeyError(f"Required parameter not found: {pp.name}")

def _model_dump(model, exclude_none=False):
    # handle both pydantic v1 and v2
    if hasattr(model, 'model_dump'):
        return model.model_dump(exclude_none=exclude_none)
    else:
        return model.dict(exclude_none=exclude_none)

def _job_matches(*,
    job: DendroJob,
    processor_name: str,
    input_files: List[SubmitJobInputFile],
    output_files: List[SubmitJobOutputFile],
    parameters: List[SubmitJobParameter]
):
    if job.processorName != processor_name:
        return False

    # input files
    if len(job.inputFiles) != len(input_files):
        return False
    for input_file in input_files:
        x = next((x for x in job.inputFiles if x.name == input_file.name), None)
        if not x:
            return False
        if x.fileName != input_file.file_name:
            return False

    # output files
    if len(job.outputFiles) != len(output_files):
        return False
    for output_file in output_files:
        x = next((x for x in job.outputFiles if x.name == output_file.name), None)
        if not x:
            return False
        if x.fileName != output_file.file_name:
            return False

    # input parameters
    if len(job.inputParameters) != len(parameters):
        return False
    for input_parameter in parameters:
        x = next((x for x in job.inputParameters if x.name == input_parameter.name), None)
        if not x:
            return False
        if x.value != input_parameter.value:
            return False
    return True
