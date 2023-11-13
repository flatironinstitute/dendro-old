from constructs import Construct
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_batch as batch,
    aws_efs as efs
)


class AwsBatchStack(Stack):
    """
    References:
    - https://aws.amazon.com/blogs/hpc/introducing-support-for-per-job-amazon-efs-volumes-in-aws-batch/
    - https://docs.aws.amazon.com/batch/latest/userguide/efs-volumes.html
    - https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-optimized_AMI.html
    """

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
            file_system = efs.FileSystem(
                scope=self,
                id=f"{stack_id}-EfsFileSystem",
                file_system_name=f"{stack_id}-EfsFileSystem",
                vpc=vpc,
                performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
                lifecycle_policy=efs.LifecyclePolicy.AFTER_7_DAYS,
                out_of_infrequent_access_policy=efs.OutOfInfrequentAccessPolicy.AFTER_1_ACCESS,
                throughput_mode=efs.ThroughputMode.BURSTING,
                enable_automatic_backups=False,
                allow_anonymous_access=True,
                removal_policy=RemovalPolicy.DESTROY,
            )
            # fs_access_point = file_system.add_access_point("AccessPoint",
            #     path="/export",
            #     create_acl=efs.Acl(owner_uid="1001", owner_gid="1001", permissions="750"),
            #     posix_user=efs.PosixUser(uid="1001", gid="1001")
            # )

            # # It might be better to create the EFS volume for each job definition
            # efs_volume = batch.EfsVolume(
            #     container_path="containerPath",
            #     file_system=file_system,
            #     name=f"{stack_id}-EfsFileSystemVolume",
            #     # the properties below are optional
            #     access_point_id="accessPointId",
            #     enable_transit_encryption=False,
            #     readonly=False,
            #     root_directory="rootDirectory",
            #     transit_encryption_port=123,
            #     use_job_role=False
            # )

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
