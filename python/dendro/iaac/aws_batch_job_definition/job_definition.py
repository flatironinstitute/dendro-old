import boto3


def create_job_definition(
    dendro_app_name: str,
    dendro_app_image_uri: str,
    job_definition_name: str,
    job_role_arn: str,
    job_definition_parameters: dict,
    required_memory: int = 2000,
    required_vcpu: int = 2,
    requires_gpu: bool = False,
):
    """
    Create a job definition in AWS Batch.
    References:
    - https://boto3.amazonaws.com/v1/documentation/api/1.26.85/reference/services/batch/client/register_job_definition.html
    - https://docs.aws.amazon.com/batch/latest/userguide/efs-volumes.html#specify-efs-config
    """

    job_definition_name = f"{dendro_app_name}_job_definition"

    # Container Environment variables
    environment_variables = [
        {
            'name': 'string',
            'value': 'string'
        },
    ]

    # Container Resource requirements
    resource_requirements = [
        {
            'type': 'MEMORY',
            'value': str(required_memory),  # Memory in MB
        },
        {
            'type': 'VCPU',
            'value': str(required_vcpu),
        }
    ]
    if requires_gpu:
        resource_requirements.append({
            'type': 'GPU',
            'value': '1',
        })

    # Container Volumes and Mount Points configuration
    volumes = [
        {
            'name': f'{job_definition_name}-EfsVolume',
            'efsVolumeConfiguration': {
                'fileSystemId': 'fs-12345678',
                'rootDirectory': '/path/to/my/data/inside/efs',
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
            'containerPath': 'string',
            'readOnly': False,
            'sourceVolume': f'{job_definition_name}-EfsVolume'
        },
    ]

    # Container properties
    container_properties = {
        "image": dendro_app_image_uri,
        "command": ["python", "main.py"],  # Command to run
        "resourceRequirements": resource_requirements,
        "volumes": volumes,
        "mountPoints": mount_points,
        "environment": environment_variables,
    }

    try:
        client = boto3.client('batch')
        response = client.register_job_definition(
            jobDefinitionName=job_definition_name,
            type='container',
            parameters=job_definition_parameters,
            retryStrategy={"attempts": 1},
            containerProperties=container_properties,
            timeout={"attemptDurationSeconds": 10800},
            jobRoleArn=job_role_arn,
            platformCapabilities=['EC2'],
            tags={'CloudFormationStack': "DendroBatchStack"}
        )
        job_definition_arn = response['jobDefinitionArn']
        return job_definition_arn
    except Exception as e:
        raise Exception(f"Error creating job definition: {e}")
