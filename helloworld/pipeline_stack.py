from os import path
import yaml

from aws_cdk import (
    core as cdk,
    aws_ecr as ecr,
    aws_codebuild as codebuild,
    aws_codedeploy as codedeploy,
    aws_codepipeline as codepipeline,
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

        # Pipeline
        github_source_artifact = codepipeline.Artifact()

        pipeline = codepipeline.Pipeline(self, "HelloWorldPipeline",
            pipeline_name="HelloWorldLambdaContainerPipeline",
            synth=codepipeline.ShellStep("Synth",
                commands=["npm ci", "npm run build", "npx cdk synth"]
                )
        )

        source_action = codepipeline_actions.GitHubSourceAction(
            action_name="GitHub_Source",
            owner="stuartgraham",
            repo="HelloWorldCDKPipeline",
            oauth_token=cdk.SecretValue.secrets_manager("github-token"),
            output=github_source_artifact,
            branch="lambdacontainer"
        )
        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action]
        )

        # Buildspec
        this_dir = path.dirname(__file__)
        with open(path.join(this_dir, "buildspec.yaml")) as f:
            buildspec = yaml.load(f, Loader=yaml.FullLoader)

        # Codebuild
        codebuild_project = codebuild.PipelineProject(self, "HelloWorldBuildProject", 
            build_spec=codebuild.BuildSpec.from_object(buildspec),
            environment=codebuild.BuildEnvironment(build_image=codebuild.LinuxBuildImage.STANDARD_5_0,
                privileged=True),        
            environment_variables= {
            "AWS_ACCOUNT_ID": {"value": self.account},
            "REPO_NAME": {"value": f"{self.account}.dkr.ecr.{self.region}.amazonaws.com/{ecr_repo.repository_name}"}
            }            
            )

        codebuild_project.role.add_managed_policy(
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryPowerUser"))

        build_action = codepipeline_actions.CodeBuildAction(
            action_name="CodeBuild",
            project=codebuild_project,
            input=github_source_artifact,
            outputs=[codepipeline.Artifact()],
            execute_batch_build=True
        )

        pipeline.add_stage(
            stage_name="Build",
            actions=[build_action]
        )


        hello_world_app = HelloWorldStage(self, 'HelloWorldApp', ecr_repo=ecr_repo, env={
            'region': 'eu-west-1'
        })
        
        pipeline.add_application_stage(hello_world_app)
