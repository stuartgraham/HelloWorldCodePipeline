from os import path
import yaml

from aws_cdk import (
    core as cdk,
    aws_ecr as ecr,
    aws_codebuild as codebuild,
    aws_codedeploy as codedeploy,
    aws_codepipeline as codepipeline,
    pipelines as pipelines,
    aws_codepipeline_actions as codepipeline_actions,
    aws_iam as iam
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

        # Pipeline
        pipeline = pipelines.CodePipeline(self, "Pipeline",
            synth = pipelines.ShellStep("Synth",
                input = pipelines.CodePipelineSource.git_hub(
                    "stuartgraham/HelloWorldCDKPipeline",
                    "lambdacontainer",
                    authentication=cdk.SecretValue.secrets_manager("github-token")
                ),
                commands=[
                    "pip install -r requirements.txt", "npm install -g aws-cdk", "cdk synth"
                ]
            )
        )

        pipeline.CodeBuildStep("Synth",
            partial_build_spec=buildspec,
            role=iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryPowerUser"),
            env={
                "AWS_ACCOUNT_ID": {"value": self.account},
                "REPO_NAME": {"value": f"{self.account}.dkr.ecr.{self.region}.amazonaws.com/{ecr_repo.repository_name}"}
            }
        )

        hello_world_app = HelloWorldStage(self, 'HelloWorldApp', ecr_repo=ecr_repo, env={
            'region': 'eu-west-1'
        })
        
        pipeline.add_application_stage(hello_world_app)
