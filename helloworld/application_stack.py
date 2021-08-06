from aws_cdk import (
    core as cdk,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_apigatewayv2 as api_gw,
    aws_apigatewayv2_integrations as api_gw_int
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
        
        # Lambda
        hello_world_lambda = _lambda.DockerImageFunction(self, "HelloWorld-AppHandler",
            code=_lambda.DockerImageCode.from_ecr(repository=ecr_repo, tag="latest")
        )
        hello_world_lambda.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryPowerUser"))

        hello_world_lambda.role.add_to_policy(iam.PolicyStatement(
                resources=["*"],
                actions=["ssm:GetParameters"]
        ))

        # APIGW
        apigw_helloworld = api_gw.HttpApi(self, 'HelloWorld-APIGW-Http')
        ## Lambda Integrations
        hello_world_lambda_int = api_gw_int.LambdaProxyIntegration(
            handler=hello_world_lambda)
        ## Routes
        apigw_helloworld.add_routes(
            path='/',
            methods=[api_gw.HttpMethod.GET],
            integration=hello_world_lambda_int
        )