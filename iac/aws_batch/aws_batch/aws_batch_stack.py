from constructs import Construct
from aws_cdk import (
    Stack,
    RemovalPolicy,
    Tags,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_batch as batch,
    aws_efs as efs
)

from .stack_config import (
    stack_id,
    batch_service_role_id,
    ecs_instance_role_id,
    batch_jobs_access_role_id,
    security_group_id,
    vpc_id,
    efs_file_system_id,
    compute_env_gpu_id,
    compute_env_cpu_id,
    job_queue_gpu_id,
    job_queue_cpu_id
)


class AwsBatchStack(Stack):
    """
    References:
    - https://constructs.dev/packages/@aws-cdk/aws-batch-alpha/v/2.95.1-alpha.0?lang=python
    - https://aws.amazon.com/blogs/hpc/introducing-support-for-per-job-amazon-efs-volumes-in-aws-batch/
    - https://docs.aws.amazon.com/batch/latest/userguide/efs-volumes.html
    - https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-optimized_AMI.html
    - https://docs.aws.amazon.com/efs/latest/ug/accessing-fs-create-security-groups.html
    """

    def __init__(
        self,
        scope: Construct,
        create_efs: bool = False,
        **kwargs
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        # AWS Batch service role
        batch_service_role = iam.Role(
            scope=self,
            id=batch_service_role_id,
            assumed_by=iam.ServicePrincipal("batch.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSBatchServiceRole")
            ]
        )
        Tags.of(batch_service_role).add("DendroName", f"{stack_id}-BatchServiceRole")

        # ECS instance role
        ecs_instance_role = iam.Role(
            scope=self,
            id=ecs_instance_role_id,
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2ContainerServiceforEC2Role"),
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchLogsFullAccess")
            ]
        )
        Tags.of(ecs_instance_role).add("DendroName", f"{stack_id}-EcsInstanceRole")

        # Batch jobs access role
        batch_jobs_access_role = iam.Role(
            scope=self,
            id=batch_jobs_access_role_id,
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchLogsFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEFSCSIDriverPolicy"),
            ]
        )
        Tags.of(batch_jobs_access_role).add("DendroName", f"{stack_id}-BatchJobsAccessRole")

        # Virtual Private Cloud (VPC)
        vpc = ec2.Vpc(
            scope=self,
            id=vpc_id,
            max_azs=3, # Availability Zones
        )
        Tags.of(vpc).add("DendroName", f"{stack_id}-vpc")

        # Security group
        security_group = ec2.SecurityGroup(
            scope=self,
            id=security_group_id,
            vpc=vpc,
            allow_all_ipv6_outbound=True,
            allow_all_outbound=True,
        )
        # Allow inbound traffic from the same security group
        security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.all_traffic(),
            description="Allow inbound traffic from the same security group"
        )
        # Additional inbound rules for EFS access
        security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4('0.0.0.0/0'),
            connection=ec2.Port.tcp(2049),  # NFS port
            description="Allow NFS traffic for EFS access"
        )
        Tags.of(security_group).add("DendroName", f"{stack_id}-security-group")

        # Create an EFS filesystem
        if create_efs:
            file_system = efs.FileSystem(
                scope=self,
                id=efs_file_system_id,
                file_system_name=f"{stack_id}-EfsFileSystem",
                vpc=vpc,
                security_group=security_group,
                performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
                lifecycle_policy=efs.LifecyclePolicy.AFTER_7_DAYS,
                out_of_infrequent_access_policy=efs.OutOfInfrequentAccessPolicy.AFTER_1_ACCESS,
                throughput_mode=efs.ThroughputMode.BURSTING,
                enable_automatic_backups=False,
                allow_anonymous_access=True,
                removal_policy=RemovalPolicy.DESTROY,
            )
            Tags.of(file_system).add("DendroName", f"{stack_id}-EfsFileSystem")

            # fs_access_point = file_system.add_access_point("AccessPoint",
            #     path="/export",
            #     create_acl=efs.Acl(owner_uid="1001", owner_gid="1001", permissions="750"),
            #     posix_user=efs.PosixUser(uid="1001", gid="1001")
            # )

        # Machine image for the GPU compute environment
        machine_image_gpu = ec2.MachineImage.generic_linux(
            ami_map={
                # aws ssm get-parameter --name /aws/service/ecs/optimized-ami/amazon-linux-2/gpu/recommended --region us-east-1 --output json
                "us-east-1": "ami-06cb3eee472508700",
                "us-east-2": "ami-0d625ab7e92ab3a43",
            }
        )
        ecs_machine_image_gpu = batch.EcsMachineImage(
            image=machine_image_gpu,
            image_type=batch.EcsMachineImageType.ECS_AL2_NVIDIA
        )

        # Machine image for the CPU compute environment
        ecs_machine_image_cpu = batch.EcsMachineImage(
            image_type=batch.EcsMachineImageType.ECS_AL2
        )

        # Compute environment for GPU
        compute_env_gpu = batch.ManagedEc2EcsComputeEnvironment(
            scope=self,
            id=compute_env_gpu_id,
            vpc=vpc,
            instance_types=[
                ec2.InstanceType("g4dn.2xlarge"), # 8 vCPUs, 32 GiB
            ],
            images=[ecs_machine_image_gpu],
            maxv_cpus=32,
            minv_cpus=0,
            security_groups=[security_group],
            service_role=batch_service_role, # type: ignore because Role implements IRole
            instance_role=ecs_instance_role, # type: ignore because Role implements IRole
        )
        Tags.of(compute_env_gpu).add("DendroName", f"{stack_id}-compute-env")

        # Compute environment for CPU
        compute_env_cpu = batch.ManagedEc2EcsComputeEnvironment(
            scope=self,
            id=compute_env_cpu_id,
            vpc=vpc,
            instance_types=[
                # tried using t4g.* instance types but there was an error during cdk deploy
                ec2.InstanceType("optimal")
            ],
            images=[ecs_machine_image_cpu],
            maxv_cpus=32,
            minv_cpus=0,
            security_groups=[security_group],
            service_role=batch_service_role, # type: ignore because Role implements IRole
            instance_role=ecs_instance_role, # type: ignore because Role implements IRole
        )
        Tags.of(compute_env_cpu).add("DendroName", f"{stack_id}-compute-env")

        # Job queue for GPU
        job_queue_gpu = batch.JobQueue(
            scope=self,
            id=job_queue_gpu_id,
            job_queue_name=job_queue_gpu_id,
            priority=1,
            compute_environments=[
                batch.OrderedComputeEnvironment(compute_environment=compute_env_gpu, order=1)
            ],
        )
        Tags.of(job_queue_gpu).add("DendroName", f"{stack_id}-job-queue")

        # Job queue for CPU
        job_queue_cpu = batch.JobQueue(
            scope=self,
            id=job_queue_cpu_id,
            job_queue_name=job_queue_cpu_id,
            priority=1,
            compute_environments=[
                batch.OrderedComputeEnvironment(compute_environment=compute_env_cpu, order=1)
            ],
        )
        Tags.of(job_queue_cpu).add("DendroName", f"{stack_id}-job-queue")
