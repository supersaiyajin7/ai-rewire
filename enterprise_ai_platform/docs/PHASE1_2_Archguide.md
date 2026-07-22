The Ultimate, Plain-English Guide to Our Async Document EngineHow to use this document:This is your total, end-to-end reference manual. It is written using zero jargon traps, plain-English analogies, line-by-line breakdowns, and explicit explanations of why every single piece of tech was chosen. If you come back to this project months from now, reading this document will instantly bring you back up to speed for any code review or system design interview.Table of ContentsThe Big Picture: What Problem Are We Solving?The Real-World Analogy: The High-End RestaurantMeet the Cast: Every Technology Explained Like You're 10The Journey of a File: Step-by-Step System FlowDeep-Dive Code Breakdown (Line-by-Line)5.1 The Blueprint: AWS CDK Stack (infra/cdk_stack.py)5.2 The Front Desk: API Ingestion (app/api/v1_jobs.py)5.3 The Invisible Worker: Event Processor (worker.py)Why Did We Build It This Way? (System Design Trade-offs)System Design Interview Q&A (Rookie to Pro Answers)Debugging & Inspection Survival Guide1. The Big Picture: What Problem Are We Solving?Imagine you are building an AI system that takes uploaded documents—like a 500-page medical manual or a 10MB PDF book—and parses them, extracts text, and feeds them into a Machine Learning model.If a user uploads a huge 10MB PDF over the web, processing that PDF (reading pages, scanning text, extracting structure) takes time—sometimes 10 seconds, sometimes 2 minutes.The Naive (Bad) Approach: Synchronous ProcessingIn a standard web app, when a user clicks "Upload":The web browser sends the file to the server.The server receives the file.The server sits there and parses the entire file while the user's browser spins.After 2 minutes, the server finishes and sends back "Done!".Why this fails miserably in production:Timeouts: Web browsers and API gateways usually kill connections if they don't get a response within 30 seconds.Server Freezing: While your server is busy reading that 500-page document, it cannot handle requests from any other users.Crashes (Out Of Memory): If 10 users upload large files at the exact same second, your server loads 10 huge files into RAM simultaneously and crashes hard.The Production-Grade Approach: Asynchronous Event-Driven ArchitectureInstead of making the user wait, we decouple (separate) receiving the file from processing the file:The user uploads the file.The web server saves the file safely in storage, creates a "ticket" (Job ID), puts a message in a line, and immediately returns a response to the user within 100 milliseconds: "Got it! Here is your ticket ID. Check back later."In the background, independent worker programs take tickets from the line, open the file from storage, process it at their own pace, and save the results.2. The Real-World Analogy: The High-End RestaurantTo keep this locked in your mind forever, think of our software as a busy restaurant:[ Customer ] ──► (1. Place Order) ──► [ Waiter ] ──► (2. Put Ingredients in Fridge) ──► [ S3 Storage ]
                                         │
                                         ├──► (3. Write Ticket on Board) ───────► [ DynamoDB Table ]
                                         │
                                         └──► (4. Hang Ticket on Order Rail) ───► [ SQS Queue ]
                                                 │
                                                 ▼
[ Chef (Worker) ] ◄── (5. Take Ticket) ──────────┘
       │
       ├──► (6. Update Ticket to "Cooking") ──────────────────────────────────► [ DynamoDB Table ]
       ├──► (7. Grab Ingredients from Fridge) ────────────────────────────────► [ S3 Storage ]
       └──► (8. Finish Dish & Mark "Done") ───────────────────────────────────► [ DynamoDB Table ]
The Customer (Web User / Client): Comes in and orders a complex meal (uploads a PDF).The Waiter (FastAPI Web Server): Takes the order. Does the waiter stand by your table for 45 minutes watching the food cook? No! The waiter puts the ingredients in the walk-in fridge (S3 Bucket), writes down your order on the status board (DynamoDB Table), hangs a ticket on the kitchen rail (SQS Queue), hands you a buzzer (Job ID), and says "We'll buzz you when it's ready!"The Walk-in Fridge (Amazon S3): Holds big, heavy physical items (raw PDF binary files).The Order Tracking Board (Amazon DynamoDB): A big whiteboard that lists every order status (PENDING, PROCESSING, COMPLETED).The Kitchen Order Rail (Amazon SQS): A paper-ticket holder line. Orders wait here in exact sequence until a chef is free.The Line Chef (Background Worker Process): An independent worker standing in the kitchen. When a new ticket appears on the rail, the chef grabs it, changes the status on the board to PROCESSING, grabs the ingredients out of the fridge, cooks the food, updates the board to COMPLETED, and throws away the paper ticket.3. Meet the Cast: Every Technology Explained Like You're 10Here is every single tool we used in Phase 1 and Phase 2, what it is, and why we need it:1. Docker & Docker ComposeWhat it is: A tool that packages code and its environment into isolated virtual "boxes" called containers.Why we use it: Instead of installing Python, AWS tools, database drivers, and local servers directly onto your Mac/Windows laptop (which leads to "it works on my machine" bugs), Docker runs everything inside identical containers. docker-compose.yml is the master conductor that starts up our API, our Worker, and our local cloud with one single command.2. LocalStackWhat it is: A mock, offline clone of Amazon Web Services (AWS) that runs inside Docker on your computer.Why we use it: Real AWS costs money, requires internet access, and needs API credentials. LocalStack lets us use real AWS Python code locally without spending a single cent or touching the internet.3. AWS CDK (Cloud Development Kit in Python)What it is: Infrastructure as Code (IaC). It allows you to define cloud resources (databases, queues, storage buckets) using pure Python code instead of clicking around in an AWS Web Console.Why we use it: You never want to create databases by hand in production. With CDK, your infrastructure is version-controlled in Git right next to your application code.4. FastAPIWhat it is: A modern, blazing-fast Python web framework for building HTTP API endpoints.Why we use it: It handles incoming web traffic, parses file uploads, auto-generates documentation (/docs), and handles asynchronous background tasks effortlessly.5. python-multipartWhat it is: A Python helper library that allows FastAPI to parse multipart/form-data requests.Why we use it: Standard web APIs send plain text or JSON. When sending raw binary files (like PDFs, images, or audio), browsers wrap them in "multipart" streams. Without python-multipart, FastAPI throws a RuntimeError because it doesn't know how to slice up the raw incoming file stream.6. Amazon S3 (Simple Storage Service)What it is: A massive, virtual file cabinet in the cloud designed to store unlimited files (objects) safely.Why we use it: Databases like PostgreSQL or DynamoDB are meant for short text rows, not multi-megabyte PDF files. Storing files in a database makes it slow and bloated. S3 stores big files cheaply and efficiently.7. Amazon DynamoDBWhat it is: A super-fast NoSQL key-value database.Why we use it: It gives us single-digit millisecond read/write speeds. We use it as our central "State Board" to keep track of every job's lifecycle (job_id, status, s3_key, timestamps).8. Amazon SQS (Simple Queue Service)What it is: A message queue (a waiting line for software messages).Why we use it: It acts as a safety buffer between the API and the Workers. If 1,000 users upload files simultaneously, SQS holds all 1,000 job notifications safely in line without losing a single one. Workers process them one by one at their own pace.4. The Journey of a File: Step-by-Step System FlowHere is the exact lifecycle of an upload from start to finish:[ CLIENT ]             [ FASTAPI API ]            [ AMAZON S3 ]          [ DYNAMODB ]          [ AMAZON SQS ]         [ WORKER ]
    │                         │                         │                     │                      │                    │
    ├─── 1. POST /upload ────►│                         │                     │                      │                    │
    │    (File Payload)       ├─── 2. Stream File ─────►│                     │                      │                    │
    │                         │    to raw/{job_id}      │                     │                      │                    │
    │                         ├─── 3. PutItem (status: "PENDING") ───────────►│                      │                    │
    │                         ├─── 4. SendMessage({"job_id", "s3_key"}) ────────────────────────────►│                    │
    │◄── 5. HTTP 202 ─────────┤                                               │                      │                    │
    │    {"job_id": "xyz"}    │                                               │                      │                    │
    │                         │                                               │                      ├── 6. Receive ─────►│
    │                         │                                               │                      │   Message          │
    │                         │                                               │◄── 7. UpdateItem ─────────────────────────┤
    │                         │                                               │    (PROCESSING)      │                    │
    │                         │                         │◄────────────────────┼───────────────────────────────────────────┤
    │                         │                         │ 8. Stream PDF Bytes │                                           │
    │                         │                         │────────────────────►│                                           │
    │                         │                                               │◄── 9. UpdateItem ─────────────────────────┤
    │                         │                                               │    (COMPLETED)       │                    │
    │                         │                                               │                      ├── 10. Delete ─────┤
    │                         │                                               │                      │   Message          │
Client Sends Request: User sends a POST request to /v1/jobs/upload containing a binary PDF file.S3 Upload: FastAPI intercepts the file stream and writes it directly to Amazon S3 under the path raw/<job_id>/<filename>.Database Logging: FastAPI writes a new record into DynamoDB:job_id: "e823bb4a-230d-45b8-8e64-4fde5e23736d"status: "PENDING"s3_key: "raw/e823bb4a-230d-45b8-8e64-4fde5e23736d/book.pdf"Queue Notification: FastAPI formats a quick JSON notification {"job_id": "...", "s3_key": "..."} and pushes it into the SQS queue.Instant Acknowledgment: FastAPI immediately returns HTTP 202 Accepted to the user with their job_id. The entire web request is done in milliseconds!Worker Long Polling: The background worker process, which is constantly listening to SQS, receives the message.Status Update (PROCESSING): Worker calls DynamoDB and updates the job state to PROCESSING.S3 Stream Read: Worker uses the s3_key from the message to open a stream from S3 and download the raw bytes of the file.Work Execution: Worker performs parsing, processing, or data extraction on the file bytes.Status Update (COMPLETED) & Cleanup: Worker updates DynamoDB state to COMPLETED and calls sqs.delete_message to remove the ticket from the queue so no other worker tries to process it again.5. Deep-Dive Code Breakdown (Line-by-Line)Let's look at the three critical Python files we created and explain what every block does.5.1 The Blueprint: AWS CDK Stack (infra/cdk_stack.py)This file defines our infrastructure using pure Python code.Pythonimport os
from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_sqs as sqs,
    aws_s3 as s3,
    RemovalPolicy
)
from constructs import Construct

class AiPlatformInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. PULL CONFIGURATION FROM ENVIRONMENT VARIABLES
        # Reads target names or defaults to clean fallback strings
        target_table_name = os.getenv("DYNAMODB_TABLE_NAME", "platform_jobs")
        target_queue_name = os.getenv("AWS_SQS_QUEUE_NAME", "platform-job-queue")
        target_bucket_name = os.getenv("AWS_S3_BUCKET_NAME", "platform-document-ingestion-storage")

        # 2. DEFINE THE DYNAMODB STATE TABLE
        self.jobs_table = dynamodb.Table(
            self, "PlatformJobsTable",
            table_name=target_table_name,
            # Partition Key (Primary Key) uniquely identifies each item in DynamoDB
            partition_key=dynamodb.Attribute(
                name="job_id", 
                type=dynamodb.AttributeType.STRING
            ),
            # PAY_PER_REQUEST means auto-scaling serverless mode (no provisioned capacity limit)
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            # RemovalPolicy.DESTROY means if we tear down the stack, delete the table (great for dev)
            removal_policy=RemovalPolicy.DESTROY
        )

        # 3. DEFINE THE SQS INGESTION QUEUE
        self.jobs_queue = sqs.Queue(
            self, "PlatformJobsQueue",
            queue_name=target_queue_name,
            removal_policy=RemovalPolicy.DESTROY
        )

        # 4. DEFINE THE S3 STORAGE BUCKET
        self.document_bucket = s3.Bucket(
            self, "PlatformDocumentStorageBucket",
            bucket_name=target_bucket_name,
            removal_policy=RemovalPolicy.DESTROY
        )
5.2 The Front Desk: API Ingestion (app/api/v1_jobs.py)This endpoint receives the document from the user and orchestrates Phase 2 ingestion.Pythonimport uuid
import json
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, status, HTTPException
import boto3

router = APIRouter()

# Initialize AWS SDK (boto3) clients pointing to LocalStack endpoint
s3_client = boto3.client('s3', endpoint_url="http://localstack:4566")
dynamodb = boto3.resource('dynamodb', endpoint_url="http://localstack:4566")
sqs_client = boto3.client('sqs', endpoint_url="http://localstack:4566")

table = dynamodb.Table("platform_jobs")

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(file: UploadFile = File(...)):
    # 1. Generate a unique job identifier (UUIDv4)
    job_id = str(uuid.uuid4())
    
    # 2. Construct a predictable S3 storage key path
    s3_key = f"raw/{job_id}/{file.filename}"

    try:
        # 3. Stream binary object straight to S3 bucket
        s3_client.upload_fileobj(
            file.file,
            "platform-document-ingestion-storage",
            s3_key
        )

        # 4. Record initial job state metadata in DynamoDB
        table.put_item(
            Item={
                "job_id": job_id,
                "status": "PENDING",
                "filename": file.filename,
                "s3_key": s3_key,
                "created_at": datetime.utcnow().isoformat()
            }
        )

        # 5. Get queue URL and dispatch event payload to SQS
        queue_url = sqs_client.get_queue_url(QueueName="platform-job-queue")["QueueUrl"]
        
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps({
                "job_id": job_id,
                "s3_key": s3_key
            })
        )

        # 6. Return immediate 202 response to client
        return {
            "job_id": job_id,
            "status": "PENDING",
            "message": "Document successfully queued for processing."
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {str(e)}"
        )
5.3 The Invisible Worker: Event Processor (worker.py)This script runs indefinitely in a separate container, consuming tasks off the queue.Pythonimport time
import json
import boto3

# Connect to LocalStack services
s3_client = boto3.client('s3', endpoint_url="http://localstack:4566")
dynamodb = boto3.resource('dynamodb', endpoint_url="http://localstack:4566")
sqs_client = boto3.client('sqs', endpoint_url="http://localstack:4566")

table = dynamodb.Table("platform_jobs")

def update_job_status(job_id: str, new_status: str):
    """Updates the status attribute of a specific job in DynamoDB."""
    table.update_item(
        Key={"job_id": job_id},
        UpdateExpression="SET #s = :status_val, updated_at = :time_val",
        ExpressionAttributeNames={"#s": "status"},  # 'status' is a reserved word in DynamoDB
        ExpressionAttributeValues={
            ":status_val": new_status,
            ":time_val": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    )

def start_worker():
    print("🚀 Worker Active | Polling SQS queue for incoming jobs...")
    
    # Resolve Queue URL
    queue_url = sqs_client.get_queue_url(QueueName="platform-job-queue")["QueueUrl"]

    while True:
        # 1. Long Poll SQS for messages (Wait up to 20s if queue is empty)
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20
        )

        messages = response.get("Messages", [])
        
        if not messages:
            continue  # No messages received, loop back and poll again

        for message in messages:
            # 2. Extract JSON body
            body = json.loads(message["Body"])
            job_id = body["job_id"]
            s3_key = body["s3_key"]

            print(f"📋 Processing job_id: {job_id}")

            # 3. Transition State -> PROCESSING
            update_job_status(job_id, "PROCESSING")

            # 4. Fetch binary object stream from S3 Storage Grid
            s3_object = s3_client.get_object(
                Bucket="platform-document-ingestion-storage",
                Key=s3_key
            )
            file_bytes = s3_object["Body"].read()

            print(f"📄 Retrieved document: {s3_key} ({len(file_bytes)} bytes)")

            # 5. Simulated Workload (In Phase 3, this becomes our LLM Parser Engine)
            time.sleep(2)

            # 6. Transition State -> COMPLETED
            update_job_status(job_id, "COMPLETED")
            print(f"✅ Status updated -> COMPLETED for job_id: {job_id}")

            # 7. Delete message from queue so it is never processed again
            sqs_client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message["ReceiptHandle"]
            )

if __name__ == "__main__":
    start_worker()
6. Why Did We Build It This Way? (System Design Trade-offs)When explaining this project in an interview, senior engineers want to know why you made specific architectural choices. Use this table as your mental cheat sheet:Architectural ChoiceWhy we did itWhat would happen if we didn'tHTTP 202 AcceptedTells the caller the job was accepted into a queue, not finished.Returning 200 OK tricks clients into thinking processing is complete when it hasn't even started.SQS Long Polling (WaitTimeSeconds=20)Keeps the request open for 20s if the queue is empty, returning instantly when a message arrives.Short polling sends constant requests every millisecond, burning 100% CPU and flooding local network ports.Separate S3 and DynamoDBUses S3 for heavy binaries and DynamoDB for lightweight metadata.Putting raw PDF bytes into DynamoDB hits its 400 KB item limit and incurs high database costs.Deleting SQS Messages After ProcessingEnsures a message is removed only after a worker successfully completes the job.If you delete the message before processing and the worker container crashes, the file is lost forever.IaC via AWS CDKKeeps infrastructure fully codified, versioned, and reproducible across environments.Manual configuration via cloud UI consoles leads to human error and environment mismatches.7. System Design Interview Q&A (Rookie to Pro Answers)Q1: "What happens if 10,000 users upload files at the exact same second?"Answer:"Our architecture scales smoothly under heavy load because it is fully decoupled:API Layer: FastAPI streams incoming files directly to S3 and writes a tiny message to SQS. It doesn't perform heavy computing, so it handles thousands of incoming HTTP requests per second easily.Buffer Layer: SQS acts as a shock absorber. It absorbs all 10,000 messages instantly without dropping any.Worker Layer: Workers process messages off SQS at a controlled rate. If the queue builds up, we can spin up additional worker containers (horizontal auto-scaling) to drain the queue faster without putting extra load on the API."Q2: "What happens if a worker crashes while processing a document?"Answer:"SQS handles worker failures gracefully using a Visibility Timeout.When a worker receives a message, SQS makes that message invisible to other workers for a set period (e.g., 30 seconds).If the worker processes the file successfully, it explicitly calls delete_message.If the worker container crashes midway through, it never calls delete_message. Once the 30-second Visibility Timeout expires, the message automatically becomes visible in the queue again, and a healthy worker picks it up and retries."Q3: "Why did you use SQS instead of Redis or Celery?"Answer:"While Celery with Redis is popular in Python setups, SQS provides managed cloud durability. Redis stores queues in memory by default—if the Redis node crashes, unprocessed messages can be lost. SQS replicates messages across multiple Availability Zones natively, requires zero broker server maintenance, and integrates seamlessly into AWS IAM security and infrastructure."8. Debugging & Inspection Survival GuideIf you ever restart your local environment and want to verify or inspect what is happening inside your local cloud, use these quick commands:1. View DynamoDB Jobs Table in Web BrowserOpen your browser to:👉 http://localhost:8001 (Runs dynamodb-admin UI)You can inspect item rows, view job_id keys, check timestamps, and monitor status state transitions (PENDING -> PROCESSING -> COMPLETED) in real time.2. View Raw S3 Objects via Terminal (AWS CLI)List all files currently saved inside your local S3 bucket:Bashaws --endpoint-url=http://localhost:4566 s3 ls s3://platform-document-ingestion-storage/ --recursive
3. Download / View S3 Object in Web BrowserTo view or download an uploaded PDF file directly, paste the S3 key path into your browser:Plaintexthttp://localhost:4566/platform-document-ingestion-storage/raw/<JOB_ID>/<FILENAME>.pdf
4. Inspect Real-Time Worker LogsTo watch the background worker process messages off SQS:Bashdocker compose logs -f ai_platform_worker
This document contains the complete architectural foundation for Phase 1 and Phase 2. Save this .md file in your repository as docs/PHASE_1_AND_2_ARCHITECTURAL_GUIDE.md for future reference!