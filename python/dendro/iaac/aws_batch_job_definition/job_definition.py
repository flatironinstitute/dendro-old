import boto3


def create_job_definition(
    job_definition_name: str,
    job_role_arn: str,
    job_definition_parameters: dict,
    requires_gpu: bool = False,
):
    """Create a job definition in AWS Batch"""

    job_definition_name = f"{user_name}_job_definition"

    container_properties = {
        "image": "amazonlinux",  # specify your container image
        "vcpus": 2,
        "memory": 2000,  # Memory in MB
        "command": ["python", "main.py"],  # Command to run
        "resourceRequirements": [
            {
                "type": "GPU",
                "value": "1"
            }
        ],
    }

    try:
        client = boto3.client('batch')
        response = client.register_job_definition(
            jobDefinitionName=job_definition_name,
            type='container',
            parameters=job_definition_parameters,
            retryStrategy={"attempts": 1},
            containerProperties=job_definition_container_properties,
            timeout={"attemptDurationSeconds": 10800},
            jobRoleArn=job_role_arn,
            volumes=[],
            tags={'CloudFormationStack': stack_name}
        )
        job_definition_arn = response['jobDefinitionArn']
        return job_definition_arn
    except Exception as e:
        raise Exception(f"Error creating job definition: {e}")
