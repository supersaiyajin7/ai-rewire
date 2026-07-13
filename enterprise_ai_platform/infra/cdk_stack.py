"""The core CDK stack definition for Enterprise AI Platform infrastructure"""
from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    RemovalPolicy
)
from constructs import Construct

class AiPlatformInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define our enterprise asynchronous jobs state table
        self.jobs_table = dynamodb.Table(
            self, "PlatformJobsTable",
            table_name="platform_jobs",
            partition_key=dynamodb.Attribute(
                name="job_id", 
                type=dynamodb.AttributeType.STRING
            ),
            # PAY_PER_REQUEST means on-demand scaling, classic for enterprise AI workloads
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            # For LocalStack testing, ensure the table destroys itself cleanly when we tear down
            removal_policy=RemovalPolicy.DESTROY
        )
