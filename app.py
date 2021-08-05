#!/usr/bin/env python3

from aws_cdk import core as cdk
from aws_cdk import core

from helloworld.pipeline_stack import PipelineStack

app = core.App()
PipelineStack(app, 'HelloWorldLambdaContainerPipeline', env={
    'region': 'eu-west-1'
})

app.synth()
