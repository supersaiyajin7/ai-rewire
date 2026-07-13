FROM python:3.11-slim

# Install system dependencies needed for AWS operations
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CDK and the LocalStack CDK wrapper globally INSIDE the container
RUN npm install -g aws-cdk aws-cdk-local

# 🔥 STAFF ENGINEER FIX: Lock down the container OS environment globally.
# This prevents any sub-shell or nested process from losing credentials.
ENV AWS_DEFAULT_REGION=us-east-1
ENV AWS_ACCESS_KEY_ID=mock_key
ENV AWS_SECRET_ACCESS_KEY=mock_secret
ENV CDK_DEFAULT_ACCOUNT=000000000000
ENV CDK_DEFAULT_REGION=us-east-1
ENV JSII_SILENCE_WARNING_DEPRECATED_NODE_VERSION=1

WORKDIR /workspace

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code and infrastructure scripts
COPY . .

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]