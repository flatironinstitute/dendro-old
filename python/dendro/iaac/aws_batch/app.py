#!/usr/bin/env python3

import aws_cdk as cdk

from aws_batch.aws_batch_stack import AwsBatchStack


app = cdk.App()

aws_batch_stack = AwsBatchStack(
    scope=app,
    stack_id="DendroBatchStack",
    create_efs=True,
)

app.synth()
