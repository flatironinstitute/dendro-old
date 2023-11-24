from typing import Union
import boto3


def get_efs_fs_id(efs_fs_name: str):
    """
    Get the EFS file system ID from its name.
    References:
    - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/efs.html#EFS.Client.describe_file_systems
    """
    try:
        client = boto3.client('efs')
        efs_fs_id = None
        response = client.describe_file_systems()
        for fs in response['FileSystems']:
            if fs.get("Name", "") == efs_fs_name:
                efs_fs_id = fs.get("FileSystemId")
        if efs_fs_id:
            return efs_fs_id
        else:
            raise Exception(f"EFS file system ID not found for name: {efs_fs_name}")
    except Exception as e:
        raise Exception(f"Error getting EFS file system ID: {e}")


def get_role_arn(role_name: str):
    """
    Get the role ARN from its name.
    References:
    - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam/client/list_roles.html#list-roles
    - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam/client/list_role_tags.html#list-role-tags
    """
    try:
        iam_client = boto3.client('iam')
        required_tag_key = "DendroName"
        required_tag_value = role_name
        response = iam_client.list_roles()
        for role in response['Roles']:
            # Get the tags for each role
            role_name = role['RoleName']
            tags = iam_client.list_role_tags(RoleName=role_name)
            # Check if the role has the specific tag
            for tag in tags['Tags']:
                if tag['Key'] == required_tag_key and tag['Value'] == required_tag_value:
                    return role['Arn']
    except Exception as e:
        raise Exception(f"Error getting role ARN: {e}")


def create_job_definition(
    dendro_app_name: str,
    dendro_app_image_uri: str,
    job_role_name: str,
    efs_fs_name: Union[str, None] = None,
    environment_variables: Union[list, None] = None,
    container_command_override: Union[list, None] = None,
    container_required_memory: int = 8192,  # Memory in MiB
    container_required_vcpu: int = 4,    # Number of vCPUs
    container_requires_gpu: bool = False,
):
    """
    Create a job definition in AWS Batch.
    References:
    - https://boto3.amazonaws.com/v1/documentation/api/1.26.85/reference/services/batch/client/register_job_definition.html
    - https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html#task_size
    - https://docs.aws.amazon.com/batch/latest/userguide/efs-volumes.html#specify-efs-config
    - https://aws.amazon.com/blogs/hpc/introducing-support-for-per-job-amazon-efs-volumes-in-aws-batch/
    """

    job_definition_name = f"{dendro_app_name}-dendro-jd"

    # Container Environment variables
    # e.g.: environment_variables = [{'name': 'string', 'value': 'string'}]
    if environment_variables is None:
        environment_variables = []
    else:
        for env_var in environment_variables:
            if not isinstance(env_var, dict):
                raise Exception("Environment variables must be a list of dictionaries.")
            if 'name' not in env_var or 'value' not in env_var:
                raise Exception("Environment variables must be a list of dictionaries with 'name' and 'value' keys. E.g.: [{'name': 'string', 'value': 'string'}]")

    # Container Resource requirements
    resource_requirements = []
    resource_requirements.append({'type': 'MEMORY', 'value': str(container_required_memory)})
    resource_requirements.append({'type': 'VCPU', 'value': str(container_required_vcpu)})
    if container_requires_gpu:
        resource_requirements.append({'type': 'GPU', 'value': '1'})

    # Get EFS file system ID and set container volumes and mount points
    volumes = []
    mount_points = []
    if efs_fs_name:
        efs_fs_id = get_efs_fs_id(efs_fs_name)
        if efs_fs_id:
            # Container Volumes and Mount Points configuration
            volumes = [
                {
                    'name': f'{job_definition_name}-EfsVolume',
                    'efsVolumeConfiguration': {
                        'fileSystemId': efs_fs_id,
                        'rootDirectory': "/",
                        # 'transitEncryption': 'ENABLED'|'DISABLED',
                        # 'transitEncryptionPort': 123,
                        # 'authorizationConfig': {
                        #     'accessPointId': 'string',
                        #     'iam': 'ENABLED'|'DISABLED'
                        # }
                    }
                },
            ]
            mount_points = [
                {
                    'containerPath': '/tmp',
                    'readOnly': False,
                    'sourceVolume': f'{job_definition_name}-EfsVolume'
                },
            ]

    # Get job role ARN
    job_role_arn = get_role_arn(job_role_name)

    # Container Command
    container_command = ["python", "/app/main.py"]
    if container_command_override:
        container_command = container_command_override

    # Container properties
    container_properties = {
        "image": dendro_app_image_uri,
        "command": container_command,
        "resourceRequirements": resource_requirements,
        "volumes": volumes,
        "mountPoints": mount_points,
        "environment": environment_variables,
        "jobRoleArn": job_role_arn,
    }

    try:
        client = boto3.client('batch')
        response = client.register_job_definition(
            jobDefinitionName=job_definition_name,
            type='container',
            retryStrategy={"attempts": 1},
            containerProperties=container_properties,
            timeout={"attemptDurationSeconds": 10800},
            platformCapabilities=['EC2'],
            tags={'CloudFormationStack': "DendroBatchStack"}
        )
        job_definition_arn = response['jobDefinitionArn']
        return job_definition_arn
    except Exception as e:
        raise Exception(f"Error creating job definition: {e}")
