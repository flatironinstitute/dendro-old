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
    ecs_volumes_policy_id,
    batch_jobs_access_role_id,
    vpc_id,
    security_group_id,
    launch_template_id,
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
        ecs_volumes_policy = iam.Policy(
            scope=self,
            id=ecs_volumes_policy_id,
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "ec2:DescribeVolumes",
                        "ec2:AttachVolume"
                    ],
                    resources=["*"],
                    effect=iam.Effect.ALLOW
                )
            ]
        )
        ecs_instance_role.attach_inline_policy(ecs_volumes_policy)

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

        # VPC
        vpc = ec2.Vpc(
            scope=self,
            id=vpc_id,
            max_azs=3,  # Default is all AZs in the region
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
            ],
        )

        # Security Group
        security_group = ec2.SecurityGroup(
            scope=self,
            id=security_group_id,
            vpc=vpc,
            description="Security group for Dendro Batch Stack",
            allow_all_outbound=True,
        )
        # Add inbound rules to the security group as required
        # For example, to allow SSH access (not recommended for production)
        # security_group.add_ingress_rule(
        #     peer=ec2.Peer.any_ipv4(),
        #     connection=ec2.Port.tcp(22),
        #     description="Allow SSH access from anywhere"
        # )

        # Define the block device
        block_device_2T = ec2.BlockDevice(
            device_name="/dev/xvda",
            volume=ec2.BlockDeviceVolume.ebs(
                volume_size=2000,
                delete_on_termination=True
            )
        )

        # Launch templates
        multipart_user_data = ec2.MultipartUserData()
        commands_user_data = ec2.UserData.for_linux()
        script = """#!/bin/bash

# Define the tag for searching the EBS volume
VOLUME_TAG_KEY="dendrotag"
VOLUME_TAG_VALUE="pipeline001"
DEVICE="/dev/sdf"
MOUNT_POINT="/dendro-tmp"

# Fetch the volume ID of the first available EBS volume with the specified tag
VOLUME_ID=$(aws ec2 describe-volumes --filters "Name=tag-key,Values=$VOLUME_TAG_KEY" --query "Volumes[0].VolumeId" --output text)

# Check if a volume ID was found
if [ "$VOLUME_ID" != "None" ]; then
    echo "Found EBS volume with ID: $VOLUME_ID"

    # Get instance ID
    TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
    INSTANCE_ID=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)

    # Attach the EBS volume to this instance
    aws ec2 attach-volume --volume-id $VOLUME_ID --instance-id $INSTANCE_ID --device $DEVICE

    # Wait for the EBS volume to be attached
    while [ ! -e $DEVICE ]; do
        echo "Waiting for EBS volume to attach..."
        sleep 10
    done

    # Create a mount point
    mkdir -p $MOUNT_POINT

    # Check if the EBS volume already has a filesystem
    FS_TYPE=$(file -s $DEVICE | cut -d , -f 1 | awk '{print $2}')
    if [ "$FS_TYPE" == "data" ]; then
        # Format the EBS volume
        echo "No filesystem detected on $DEVICE. Formatting..."
        mkfs -t ext4 $DEVICE
    else
        echo "Filesystem already exists on $DEVICE"
    fi

    # Mount the EBS volume
    mount $DEVICE $MOUNT_POINT

    # Uncomment the following line if you want to ensure it mounts on reboot
    # echo "$DEVICE $MOUNT_POINT ext4 defaults,nofail 0 2" >> /etc/fstab
else
    echo "No available EBS volume found with the specified tag"
fi
        """
        commands_user_data.add_commands(script)
        multipart_user_data.add_user_data_part(commands_user_data, ec2.MultipartBody.SHELL_SCRIPT, True)

        launch_template_gpu = ec2.LaunchTemplate(
            scope=self,
            id=launch_template_id + "-gpu",
            launch_template_name=launch_template_id + "-gpu",
            block_devices=[block_device_2T],
            # instance_type=ec2.InstanceType("g4dn.2xlarge"),
            machine_image=ec2.MachineImage.generic_linux(
                ami_map=ami_map_gpu
            ),
            ebs_optimized=True,
            user_data=multipart_user_data
        )
        Tags.of(launch_template_gpu).add("AWSBatchService", "batch")

        launch_template_cpu = ec2.LaunchTemplate(
            scope=self,
            id=launch_template_id + "-cpu",
            launch_template_name=launch_template_id + "-cpu",
            block_devices=[block_device_2T],
            machine_image=ec2.MachineImage.generic_linux(
                ami_map=ami_map_cpu
            ),
            ebs_optimized=True,
            user_data=multipart_user_data
        )
        Tags.of(launch_template_cpu).add("AWSBatchService", "batch")

        # # Create an EFS filesystem
        # if create_efs:
        #     file_system = efs.FileSystem(
        #         scope=self,
        #         id=efs_file_system_id,
        #         file_system_name=f"{stack_id}-EfsFileSystem",
        #         vpc=vpc,
        #         security_group=security_group,
        #         performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
        #         lifecycle_policy=efs.LifecyclePolicy.AFTER_7_DAYS,
        #         out_of_infrequent_access_policy=efs.OutOfInfrequentAccessPolicy.AFTER_1_ACCESS,
        #         throughput_mode=efs.ThroughputMode.BURSTING,
        #         enable_automatic_backups=False,
        #         allow_anonymous_access=True,
        #         removal_policy=RemovalPolicy.DESTROY,
        #     )
        #     Tags.of(file_system).add("DendroName", f"{stack_id}-EfsFileSystem")

        #     # fs_access_point = file_system.add_access_point("AccessPoint",
        #     #     path="/export",
        #     #     create_acl=efs.Acl(owner_uid="1001", owner_gid="1001", permissions="750"),
        #     #     posix_user=efs.PosixUser(uid="1001", gid="1001")
        #     # )

        # Compute environment for GPU
        ecs_machine_image_gpu = batch.EcsMachineImage(
            image=ec2.MachineImage.generic_linux(ami_map=ami_map_gpu),
            image_type=batch.EcsMachineImageType.ECS_AL2_NVIDIA
        )
        compute_env_gpu = batch.ManagedEc2EcsComputeEnvironment(
            scope=self,
            id=compute_env_gpu_id,
            vpc=vpc,
            instance_types=[
                ec2.InstanceType("g4dn.xlarge"), # 4 vCPUs, 16 GiB
                ec2.InstanceType("g4dn.2xlarge"), # 8 vCPUs, 32 GiB
                ec2.InstanceType("g4dn.4xlarge"), # 16 vCPUs, 64 GiB
            ],
            images=[ecs_machine_image_gpu],
            maxv_cpus=64,
            minv_cpus=0,
            security_groups=[security_group],
            service_role=batch_service_role, # type: ignore because Role implements IRole
            instance_role=ecs_instance_role, # type: ignore because Role implements IRole
            launch_template=launch_template_gpu,
        )
        Tags.of(compute_env_gpu).add("DendroName", f"{stack_id}-compute-env")

        # Compute environment for CPU
        ecs_machine_image_cpu = batch.EcsMachineImage(
            image=ec2.MachineImage.generic_linux(ami_map=ami_map_cpu),
            image_type=batch.EcsMachineImageType.ECS_AL2
        )
        compute_env_cpu = batch.ManagedEc2EcsComputeEnvironment(
            scope=self,
            id=compute_env_cpu_id,
            vpc=vpc,
            instance_types=[
                ec2.InstanceType("optimal")
            ],
            images=[ecs_machine_image_cpu],
            maxv_cpus=128,
            minv_cpus=0,
            security_groups=[security_group],
            service_role=batch_service_role, # type: ignore because Role implements IRole
            instance_role=ecs_instance_role, # type: ignore because Role implements IRole
            launch_template=launch_template_cpu,
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

# generated using ../devel/create_ami_map.py
# not able to get image ID for some regions due to invalid security token.
# used this command: aws ssm get-parameter --name /aws/service/ecs/optimized-ami/amazon-linux-2/gpu/recommended --region us-east-1 --output json
ami_map_gpu = {
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

ami_map_cpu = {
    "ap-south-1": "ami-0ac26d07e5b3dee2c",
    "ap-southeast-1": "ami-04c2b121d2518d721",
    "ap-southeast-2": "ami-0a6407061c6f43c25",
    "ap-northeast-1": "ami-0a50b50d3f0255ea3",
    "ap-northeast-2": "ami-03c5f630f6d2dd64b",
    "ca-central-1": "ami-0f573ab699762ead1",
    "eu-west-1": "ami-08452023a2c1a3bac",
    "eu-west-2": "ami-0f3246ed2fef95399",
    "eu-west-3": "ami-06dc37dc7de5f33d0",
    "eu-north-1": "ami-00dc593afd34193fc",
    "eu-central-1": "ami-04fc217f16fc2aceb",
    "sa-east-1": "ami-00c6fb0d796b16790",
    "us-east-1": "ami-014ff0fa8ac643097",
    "us-east-2": "ami-01fb8a683bddd95be",
    "us-west-1": "ami-0389998efa11239f6",
    "us-west-2": "ami-026b024d2182d335f"
}