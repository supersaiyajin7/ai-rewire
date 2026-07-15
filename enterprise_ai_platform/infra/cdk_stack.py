"""The core CDK stack definition for Enterprise AI Platform infrastructure"""
import os
from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    RemovalPolicy
)
from constructs import Construct


class AiPlatformInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 🔄 Pull the target name from environment variables, fallback to local default if empty
        target_table_name = os.getenv("DYNAMODB_TABLE_NAME")

        # Define our enterprise asynchronous jobs state table
        self.jobs_table = dynamodb.Table(
            self, "PlatformJobsTable",
            table_name=target_table_name,  # 🔥 Injected dynamically
            partition_key=dynamodb.Attribute(
                name="job_id", 
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )