from typing import List
from warnings import warn
import os


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
    requires_gpu: bool,
    container: str, # for verifying consistent with job definition
    command: str
):
    import boto3

    aws_access_key_id = os.getenv('BATCH_AWS_ACCESS_KEY_ID', None)
    if aws_access_key_id is None:
        raise KeyError('BATCH_AWS_ACCESS_KEY_ID is not set')
    aws_secret_access_key = os.getenv('BATCH_AWS_SECRET_ACCESS_KEY', None)
    if aws_secret_access_key is None:
        raise KeyError('BATCH_AWS_SECRET_ACCESS_KEY is not set')
    aws_region = os.getenv('BATCH_AWS_REGION', None)
    if aws_region is None:
        raise KeyError('BATCH_AWS_REGION is not set')

    client = boto3.client(
        'batch',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region
    )

    stack_id = 'DendroBatchStack'
    aws_batch_job_definition = f'{app_name}-dendro-jd'
    if requires_gpu:
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
    job_def_command = job_def['containerProperties']['command']
    if not _command_matches(job_def_command, command):
        warn(f'Warning: Job definition command does not match: {job_def_command} != {command}')
        # raise JobDefinitionException(f'Job definition command does not match: {job_def_command} != {command}')

    job_name = f'dendro-job-{job_id}'

    env_vars = {
        'JOB_ID': job_id,
        'JOB_PRIVATE_KEY': job_private_key,
        'APP_EXECUTABLE': command,
        'DENDRO_JOB_WORKING_DIR': f'/dendro-jobs/{job_id}',
        'DENDRO_JOB_CLEANUP_DIR': f'/dendro-jobs/{job_id}'
    }

    # Not doing this any more -- instead we are setting a custom backend for kachery uploads
    # from ._start_job import _get_kachery_cloud_credentials # avoid circular import
    # kachery_cloud_client_id, kachery_cloud_private_key = _get_kachery_cloud_credentials()
    # if kachery_cloud_client_id is not None:
    #     env_vars['KACHERY_CLOUD_CLIENT_ID'] = kachery_cloud_client_id
    #     if not kachery_cloud_private_key:
    #         raise KeyError('kachery_cloud_private key is not set even though kachery_cloud_client_id is set')
    #     env_vars['KACHERY_CLOUD_PRIVATE_KEY'] = kachery_cloud_private_key

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
            'resourceRequirements': [
                {
                    'type': 'VCPU',
                    'value': '4'
                },
                {
                    'type': 'MEMORY',
                    'value': '16384'
                },
                # {
                #     'type': 'GPU',
                #     'value': '1'
                # }
            ]
        }
    )

    batch_job_id = response['jobId']
    print(f'AWS Batch job submitted: {job_id} {batch_job_id}')

def _command_matches(cmd1: List[str], cmd2: str) -> bool:
    return ' '.join(cmd1) == cmd2
