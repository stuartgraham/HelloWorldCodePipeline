from aws_cdk import (
    core as cdk,
    aws_lambda as _lambda
)

class HelloWorldStage(cdk.Stage):
    def __init__(self, scope: cdk.Construct, id: str, ecr_repo=None, **kwargs):
        super().__init__(scope, id, **kwargs)
        self.ecr_repo = ecr_repo
        HelloWorldStack(self, "HelloWorld", ecr_repo=self.ecr_repo)


class HelloWorldStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, ecr_repo=None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.ecr_repo = ecr_repo
        _lambda.DockerImageFunction(self, "HelloWorld-AppHandler",
            code=_lambda.DockerImageCode.from_ecr(ecr_repo)
        )
