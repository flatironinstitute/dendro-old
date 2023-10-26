from constructs import Construct
from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_batch as batch,
)


class AwsBatchStack(Stack):

    def __init__(self, scope: Construct, stack_id: str, **kwargs) -> None:
        super().__init__(scope, stack_id, **kwargs)

        # VPC
        vpc = ec2.Vpc(
            scope=self,
            id=f"{stack_id}-vpc",
            max_azs=3,
        )
            
        # Compute environment
        compute_env = batch.FargateComputeEnvironment(
            scope=self, 
            id=f"{stack_id}-compute-env",
            spot=True,
            maxv_cpus=1,
            vpc=vpc,
        )

        # Job queue
        job_queue = batch.JobQueue(
            scope=self,
            id=f"{stack_id}-job-queue",
            job_queue_name=f"{stack_id}-job-queue",
            priority=1,
            compute_environments=[
                batch.JobQueueComputeEnvironment(
                    compute_environment=compute_env,
                    order=1,
                )
            ],
        )
