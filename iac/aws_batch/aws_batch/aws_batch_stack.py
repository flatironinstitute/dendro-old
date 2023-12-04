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
import boto3

from .stack_config import (
    stack_id,
    batch_service_role_id,
    ecs_instance_role_id,
    batch_jobs_access_role_id,
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
        # get the default aws region
        boto_client = boto3.client("sts")
        aws_region = boto_client.meta.region_name
        print(f'Using default region: {aws_region}')
        # get the aws account id
        aws_account_id = boto_client.get_caller_identity()["Account"]
        print(f'Using account id: {aws_account_id}')
        super().__init__(
            scope,
            stack_id,
            env={
                "region": aws_region,
                "account": aws_account_id
            },
            **kwargs
        )

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

        # Use the default VPC
        ec2_client = boto3.client("ec2")
        default_vpc_id = ec2_client.describe_vpcs(
            Filters=[
                {
                    "Name": "isDefault",
                    "Values": ["true"]
                }
            ]
        )["Vpcs"][0]["VpcId"]
        print(f'Using default vpc: {default_vpc_id}')
        vpc = ec2.Vpc.from_lookup(
            scope=self,
            id=default_vpc_id,
            is_default=True
        )

        # Use the default Security Group
        default_security_group_id = ec2_client.describe_security_groups(
            Filters=[
                {
                    "Name": "vpc-id",
                    "Values": [default_vpc_id]
                },
                {
                    "Name": "group-name",
                    "Values": ["default"]
                }
            ]
        )["SecurityGroups"][0]["GroupId"]
        print(f'Using default security group: {default_security_group_id}')
        security_group = ec2.SecurityGroup.from_security_group_id(
            scope=self,
            id=default_security_group_id,
            security_group_id=default_security_group_id,
            # allow_all_ipv6_outbound=True,
            allow_all_outbound=True
        )

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

        # generated using ../devel/create_ami_map.py
        # not able to get image ID for some regions due to invalid security token.
        # used this command: aws ssm get-parameter --name /aws/service/ecs/optimized-ami/amazon-linux-2/gpu/recommended --region us-east-1 --output json
        ami_map = {
            "ap-south-1": "ami-0622a76878be0b6c4",
            "ap-southeast-1": "ami-0ab04c2c315eb61e2",
            "ap-southeast-2": "ami-0ebb73c7ce7e9723b",
            "ap-northeast-1": "ami-0cda4bbd18f922fed",
            "ap-northeast-2": "ami-0714add0dc329c54a",
            "ca-central-1": "ami-08fd9fdd5f9d1efec",
            "eu-west-1": "ami-071c88c2c808990ac",
            "eu-west-2": "ami-0f1aefb81f8314ab9",
            "eu-west-3": "ami-0daf0b137875a822c",
            "eu-north-1": "ami-0efece97c680f1431",
            "eu-central-1": "ami-009660d5f3dda658e",
            "sa-east-1": "ami-054639759cfa07cbc",
            "us-east-1": "ami-06cb3eee472508700",
            "us-east-2": "ami-0d625ab7e92ab3a43",
            "us-west-1": "ami-0a40523920cc84619",
            "us-west-2": "ami-00bba07182e3aeb24"
        }

        # Machine image for the GPU compute environment
        machine_image_gpu = ec2.MachineImage.generic_linux(
            ami_map=ami_map
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
                ec2.InstanceType("g4dn.xlarge"), # 4 vCPUs, 16 GiB
                ec2.InstanceType("g4dn.2xlarge"), # 8 vCPUs, 32 GiB
                # ec2.InstanceType("g4dn.4xlarge"), # 16 vCPUs, 64 GiB
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
