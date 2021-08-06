from os import path
import yaml

from aws_cdk import (
    core as cdk,
    aws_ecr as ecr,
    aws_iam as iam,
    pipelines as pipelines
)

from helloworld.application_stack import HelloWorldStage

class PipelineStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ECR
        ecr_repo = ecr.Repository(self, "ECRRepo",
            repository_name="helloworldlambdacontainer"
        )
        ecr_repo.add_lifecycle_rule(max_image_count=10)

        # Buildspec
        this_dir = path.dirname(__file__)
        with open(path.join(this_dir, "buildspec.yaml")) as f:
            buildspec = yaml.load(f, Loader=yaml.FullLoader)

        # Github Source
        git_hub = pipelines.CodePipelineSource.git_hub(
                    "stuartgraham/HelloWorldCDKPipeline",
                    "lambdacontainer",
                    authentication=cdk.SecretValue.secrets_manager("github-token")
                )

        # Pipeline
        pipeline = pipelines.CodePipeline(self, "Pipeline",
            synth = pipelines.ShellStep("Synth",
                input = git_hub,
                commands=[
                    "pip install -r requirements.txt", "npm install -g aws-cdk", "cdk synth"
                ]
            )
        )

        pipelines.CodeBuildStep("Synth",
            input = git_hub,
            partial_build_spec=buildspec,
            commands=[],
            role=iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryPowerUser"),
            env={
                "AWS_ACCOUNT_ID": {"value": self.account},
                "REPO_NAME": {"value": f"{self.account}.dkr.ecr.{self.region}.amazonaws.com/{ecr_repo.repository_name}"}
            }
        )

        hello_world_app = HelloWorldStage(self, 'HelloWorldApp', ecr_repo=ecr_repo)
        
        pipeline.add_application_stage(hello_world_app)
