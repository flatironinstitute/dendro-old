from constructs import Construct
from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_batch as batch,
    aws_efs as efs
)


class AwsBatchStack(Stack):

    def __init__(
        self,
        scope: Construct,
        stack_id: str,
        use_efs: bool = False,
        **kwargs
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        # Create IAM Roles
        batch_service_role = iam.Role(
            scope=self,
            id=f"{stack_id}-BatchServiceRole",
            assumed_by=iam.ServicePrincipal("batch.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSBatchServiceRole")
            ]
        )
        ecs_instance_role = iam.Role(
            scope=self,
            id=f"{stack_id}-EcsInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2ContainerServiceforEC2Role"),
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchLogsFullAccess")
            ]
        )
        batch_jobs_access_role = iam.Role(
            scope=self,
            id=f"{stack_id}-BatchJobsAccessRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchLogsFullAccess")
            ]
        )

        # VPC
        vpc = ec2.Vpc(
            scope=self,
            id=f"{stack_id}-vpc",
            max_azs=3,
        )

        # Security group
        security_group = ec2.SecurityGroup(
            scope=self,
            id=f"{stack_id}-security-group",
            vpc=vpc,
            allow_all_outbound=True,
        )

        # Create an EFS filesystem
        create_efs = False
        if create_efs:
            file_system = efs.FileSystem(self, "EfsFileSystem", vpc=vpc)

            # Create an EFS access point
            access_point = file_system.add_access_point("AccessPoint",
                path="/export",
                create_acl=efs.Acl(owner_uid="1001", owner_gid="1001", permissions="750"),
                posix_user=efs.PosixUser(uid="1001", gid="1001")
            )

        # Compute environment
        compute_env_1 = batch.ManagedEc2EcsComputeEnvironment(
            scope=self,
            id=f"{stack_id}-compute-env",
            vpc=vpc,
            instance_types=[
                ec2.InstanceType("g4dn.2xlarge"),
            ],
            maxv_cpus=32,
            minv_cpus=0,
            security_groups=[security_group],
            service_role=batch_service_role,
            instance_role=ecs_instance_role,
        )

        # Job queue
        job_queue = batch.JobQueue(
            scope=self,
            id=f"{stack_id}-job-queue",
            job_queue_name=f"{stack_id}-job-queue",
            priority=1,
            compute_environments=[
                batch.OrderedComputeEnvironment(compute_environment=compute_env_1, order=1)
                # batch.OrderedComputeEnvironment(compute_environment=compute_env_2, order=2)
            ],
        )
