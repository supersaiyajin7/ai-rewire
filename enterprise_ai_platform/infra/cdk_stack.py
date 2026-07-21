import os
from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_sqs as sqs,  # 🔥 Import SQS construct
    RemovalPolicy
)
from constructs import Construct

class AiPlatformInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Pull the target configurations from environment variables
        target_table_name = os.getenv("DYNAMODB_TABLE_NAME", "platform_jobs")
        target_queue_name = os.getenv("AWS_SQS_QUEUE_NAME", "platform-job-queue")

        # 2. Define our enterprise asynchronous jobs state table
        self.jobs_table = dynamodb.Table(
            self, "PlatformJobsTable",
            table_name=target_table_name,
            partition_key=dynamodb.Attribute(
                name="job_id", 
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # 3. 🔥 Define our Phase 1 SQS Ingestion Queue
        self.jobs_queue = sqs.Queue(
            self, "PlatformJobsQueue",
            queue_name=target_queue_name,
            removal_policy=RemovalPolicy.DESTROY
        )