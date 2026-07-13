#!/bin/bash
set -e

echo "⏳ Waiting for LocalStack's AWS service endpoints to be fully operational..."
until curl -s http://localstack:4566/_localstack/health | grep -q '"dynamodb":'; do
  echo "...AWS mock cloud mesh initializing, retrying in 2 seconds..."
  sleep 2
done

echo "🚀 Step 1: Deploying Infrastructure via AWS CDK Direct-Injection..."
cdklocal deploy --require-approval never

echo "🔥 Step 2: Launching Enterprise AI Platform API Server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000