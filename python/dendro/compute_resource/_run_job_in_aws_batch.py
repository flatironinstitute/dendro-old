from typing import List

from ..common.dendro_types import DendroJobRequiredResources


# You must first setup the AWS credentials
# You can do this in multiple ways like using the aws configure command
# or by setting environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, etc.).

class JobDefinitionException(Exception):
    pass

def _run_job_in_aws_batch(
    *,
    job_id: str,
    job_private_key: str,
    app_name: str,
    container: str, # for verifying consistent with job definition
    command: str,
    required_resources: DendroJobRequiredResources
):
    import boto3

    client = boto3.client(
        'batch'
    )

    stack_id = 'DendroBatchStack'
    aws_batch_job_definition = f'{app_name}-dendro-jd'
    if required_resources.numGpus > 0:
        aws_batch_job_queue = f'{stack_id}-job-queue-gpu'
    else:
        aws_batch_job_queue = f'{stack_id}-job-queue-cpu'
    job_def_resp = client.describe_job_definitions(jobDefinitionName=aws_batch_job_definition)
    job_defs = job_def_resp['jobDefinitions']
    if len(job_defs) == 0:
        raise JobDefinitionException(f'Job definition not found: {aws_batch_job_definition}')
    job_def = job_defs[0]
    job_def_container = job_def['containerProperties']['image']
    if job_def_container != container:
        raise JobDefinitionException(f'Job definition container does not match: {job_def_container} != {container}')
    # job_def_command = job_def['containerProperties']['command']
    # if not _command_matches(job_def_command, command):
    #     warn(f'Warning: Job definition command does not match: {job_def_command} != {command}')
    #     # raise JobDefinitionException(f'Job definition command does not match: {job_def_command} != {command}')

    job_name = f'dendro-job-{job_id}'

    env_vars = {
        'JOB_ID': job_id,
        'JOB_PRIVATE_KEY': job_private_key,
        'APP_EXECUTABLE': command,
        'DENDRO_JOB_WORKING_DIR': f'/tmp/dendro-jobs/{job_id}',
        'DENDRO_JOB_CLEANUP_DIR': f'/tmp/dendro-jobs/{job_id}'
    }

    if required_resources.timeSec is not None:
        env_vars['JOB_TIMEOUT_SEC'] = str(int(required_resources.timeSec))

    # Not doing this any more -- instead we are setting a custom backend for kachery uploads
    # from ._start_job import _get_kachery_cloud_credentials # avoid circular import
    # kachery_cloud_client_id, kachery_cloud_private_key = _get_kachery_cloud_credentials()
    # if kachery_cloud_client_id is not None:
    #     env_vars['KACHERY_CLOUD_CLIENT_ID'] = kachery_cloud_client_id
    #     if not kachery_cloud_private_key:
    #         raise KeyError('kachery_cloud_private key is not set even though kachery_cloud_client_id is set')
    #     env_vars['KACHERY_CLOUD_PRIVATE_KEY'] = kachery_cloud_private_key

    resource_requirements_aws = [
        {
            'type': 'VCPU',
            'value': str(required_resources.numCpus)
        },
        {
            'type': 'MEMORY',
            # Luiz: "we should define the max RAM always to be just slightly lower than the ram available,
            # e.g. 63000 instead of 65536 in a ~64 Gb ram instance. This is because the actual ram available
            # in the machine is usually slightly less than the number announced, and the Compute Environment
            # will get stuck trying to find an instance with enough ram and never finding one..."
            'value': str(int(required_resources.memoryGb * 1024 * 0.9))
        }
    ]
    if required_resources.numGpus > 0:
        resource_requirements_aws.append({
            'type': 'GPU',
            'value': str(required_resources.numGpus)
        })
        env_vars['NVIDIA_DRIVER_CAPABILITIES'] = 'all'
        env_vars['NVIDIA_REQUIRE_CUDA'] = 'cuda>=11.0'

    response = client.submit_job(
        jobName=job_name,
        jobQueue=aws_batch_job_queue,
        jobDefinition=aws_batch_job_definition,
        containerOverrides={
            'environment': [
                {
                    'name': k,
                    'value': v
                }
                for k, v in env_vars.items()
            ],
            'resourceRequirements': resource_requirements_aws
        },
        timeout={
            # Add a buffer because dendro will be the one to actually terminate the job and do the cleanup
            # based on the required_resources.timeSec parameter that the job also has access to.
            # We assume that the startup and cleanup operations take less than the buffer time.
            'attemptDurationSeconds': int(required_resources.timeSec + 60 * 10)
        }
    )

    batch_job_id = response['jobId']
    print(f'AWS Batch job submitted: {job_id} {batch_job_id}')

def _command_matches(cmd1: List[str], cmd2: str) -> bool:
    return ' '.join(cmd1) == cmd2
