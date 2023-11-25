# AWS Batch IaC

In order to run Dendro Apps as AWS Batch jobs, the infrastructure must be provisioned first. This is done in two stages:

1. Before installing any Apps: Provision the base AWS Batch infrastructure using CDK. This includes IAM roles, VPC, Security Group, EFS filesystems, Batch Compute Environments and Batch Job Queues.
2. At every App install: Provision the App-specific infrastructure using Boto3. This includes one EFS Volume one Batch Job Definition.

## Prerequisites

- Python 3.10
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- [AWS CDK Toolkit](https://docs.aws.amazon.com/cdk/latest/guide/cli.html)
- [AWS CDK Python](https://docs.aws.amazon.com/cdk/latest/guide/work-with-cdk-python.html)
- Set up your AWS credentials, either by [configuring the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html) or by [setting environment variables](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html).


## Provision base Batch infrastructure with CDK

AWS CDK is a very convenient tool, it helps automate the provisioning of AWS infrastructure and organizes all created resources in a CloudFormation stack, which can be easily updated or deleted.

Follow these steps if you're running Dendro CDK stack for the first time:
- go to `cloned_dendro_repo_path/iac/aws_batch` directory.
- run `cdk bootstrap` to set up the CDK deployment infrastructure (CKDToolkit) in your AWS account. This only needs to be done once.
- run `cdk synth` to synthesize the CloudFormation template.
- run `cdk deploy` to deploy the stack to your default AWS account/region.
- you will be prompted to confirm the deployment. Review the changes, then type `y` and hit enter.

If deployment is successful, you will be able to see the stacks in the CloudFormation page in AWS console.

![CloudFormation stacks](https://github.com/flatironinstitute/dendro/assets/3679296/87ca6dcd-fe59-4afc-b64f-4fcc24b64f86)

Other useful CDK commands:
- `cdk ls` - list all stacks in the app.
- `cdk diff` - compare deployed stack with current state.
- `cdk destroy` - destroy the stack.
- `cdk docs` - open CDK documentation.

## Provision App-specific infrastructure with Boto3

For every Dendro App installed on a Dendro Compute Resource, an AWS Batch Job Definition must be created. This is done automatically by the Dendro Compute Resource Controller.


## Extra - Simple File Manager for Amazon EFS

ref: https://aws.amazon.com/solutions/implementations/simple-file-manager-for-amazon-efs/