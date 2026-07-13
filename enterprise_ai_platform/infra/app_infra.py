#!/usr/bin/env python3
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aws_cdk import App, Environment, LegacyStackSynthesizer
from infra.cdk_stack import AiPlatformInfraStack

app = App()

mock_env = Environment(account="000000000000", region="us-east-1")

# Explicitly using LegacyStackSynthesizer to bypass S3 asset staging buckets completely
AiPlatformInfraStack(
    app, 
    "AiPlatformInfraStack", 
    env=mock_env,
    synthesizer=LegacyStackSynthesizer()
)

app.synth()