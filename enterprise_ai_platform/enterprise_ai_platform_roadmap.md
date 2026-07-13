# Enterprise AI Platform Architecture & Roadmap
**System Blueprint & Multi-Phase Implementation Guide**

---

## 📋 Architectural Overview
This document outlines the end-to-end production architecture for our containerized Enterprise AI Platform. The architecture transitions a synchronous web request paradigm into an asynchronous, event-driven, horizontally scalable AI processing machine. By leveraging simulated cloud infrastructure locally via LocalStack, we isolate development patterns without relying on active public cloud bills.

### Current Baseline State
* **API Engine:** FastAPI running via Uvicorn on port `8000`.
* **State Persistence:** LocalStack DynamoDB (`platform_jobs` table).
* **Observation Layer:** `dynamodb-admin` UI panel exposing state changes on port `8001`.
* **Data Loop:** Operational ingestion producing `202 Accepted` tasks with unique `job_id` strings and tracking statuses (`pending`).

---

## 🗺️ Master Strategic Roadmap

### Phase 1: Distributed Asynchronous Worker Layer (Current Focus)
**Objective:** Decouple incoming REST traffic from actual system execution to prevent API timeouts and thread starvation during long-running tasks.

* **Infrastructure Additions:**
  * **AWS SQS Queue:** Set up a message broker named `platform-job-queue` inside LocalStack to act as our durable ingestion layer.
  * **Worker Service:** A dedicated, lightweight Python background runtime (`ai_platform_worker`) that continually polls the queue.
* **Execution Flow:**
  1. `POST /v1/jobs` generates a unique UUID `job_id`.
  2. The API drops an architectural ingestion payload message containing the `job_id` and raw text metadata into the SQS queue.
  3. The API immediately responds with `202 Accepted` to the client.
  4. The Worker container picks up the message, updates the DynamoDB table row to `processing`, and initiates down-stream logic.

### Phase 2: Object Ingestion & Storage Virtualization (S3 Grid)
**Objective:** Support high-throughput unstructured file ingestion (PDFs, clinical notes, financial sheets) safely since NoSQL attributes are restricted by size bounds.

* **Infrastructure Additions:**
  * **AWS S3 Storage:** Provision a local mock bucket named `platform-document-ingestion-storage`.
* **Execution Flow:**
  1. The API surfaces a secure multipart form-data endpoint or generates presigned upload URLs.
  2. The raw document payload lands in the S3 bucket.
  3. S3 fires an event notification directly into our SQS queue, or the API passes the exact object key coordinates (`s3://...`) inside the structural SQS message body.
  4. The Worker extracts the document binary stream out of S3 dynamically during the processing sequence.

### Phase 3: AI Intelligence Engine & Core Extraction (AWS Bedrock)
**Objective:** Process the raw payload or extracted document buffers using foundation models via AWS Bedrock APIs for cognitive classification, summarization, or validation.

* **Infrastructure Additions:**
  * **AWS Bedrock / Mock Gateway:** Integration of LangChain, LlamaIndex, or raw Boto3 Amazon Bedrock runtime clients configured to parse target prompts against model families (e.g., Claude 3.5 Sonnet / Haiku).
* **Execution Flow:**
  1. The Worker receives the raw file stream or raw string array metadata.
  2. The text is packed cleanly inside a structured engineering prompt template.
  3. The payload is pushed to the LLM backend wrapper.
  4. The response object is structured, extracted, mapped back to standard attributes, and written to the `metadata` column in the `platform_jobs` table before setting the status to `completed`.

### Phase 4: Production Resilience & Fault Management
**Objective:** Defend the platform cluster from transient data dropouts, network timeouts, and rogue AI parsing failures.

* **Infrastructure Additions:**
  * **Dead-Letter Queue (DLQ):** Route corrupted or repeatedly crashing messages to a tracking queue called `platform-job-dlq` after a specific visibility timeout retry threshold.
  * **Error Propagation:** Trap runtime failures inside the Worker and update the DynamoDB table layout by populating the `error_message` column with full stack traces, marking statuses explicitly as `failed`.

---

## 🛠️ Unified System Configuration (`docker-compose.yml`)
To synchronize the whole ecosystem under a single run command, the target multi-container mesh should follow this declarative structure:

```yaml
version: '3.8'

services:
  localstack:
    container_name: localstack_main
    image: localstack/localstack:latest
    ports:
      - "127.0.0.1:4566:4566"
      - "127.0.0.1:4510-4559:4510-4559"
    environment:
      - AWS_DEFAULT_REGION=us-east-1
      - EDGE_PORT=4566
    volumes:
      - "localstack_data:/var/lib/localstack"
      - "/var/run/docker.sock:/var/run/docker.sock"
    networks:
      - platform_network

  api_platform:
    container_name: ai_platform_app
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      - AWS_ENDPOINT_URL=http://localstack:4566
      - AWS_ENDPOINT_URL_S3=http://localstack:4566
      - AWS_REGION=us-east-1
    depends_on:
      - localstack
    volumes:
      - .:/workspace
    networks:
      - platform_network

  api_worker:
    container_name: ai_platform_worker
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - AWS_ENDPOINT_URL=http://localstack:4566
      - AWS_REGION=us-east-1
    depends_on:
      - localstack
    volumes:
      - .:/workspace
    networks:
      - platform_network

  localstack_gui:
    container_name: localstack_dashboard_ui
    image: aaronshaf/dynamodb-admin:latest
    ports:
      - "127.0.0.1:8001:8001"
    environment:
      - DYNAMO_ENDPOINT=http://localstack:4566
      - AWS_REGION=us-east-1
      - AWS_ACCESS_KEY_ID=mock_id
      - AWS_SECRET_ACCESS_KEY=mock_secret
    depends_on:
      - localstack
    networks:
      - platform_network

networks:
  platform_network:
    name: platform_architecture_net

volumes:
  localstack_data: