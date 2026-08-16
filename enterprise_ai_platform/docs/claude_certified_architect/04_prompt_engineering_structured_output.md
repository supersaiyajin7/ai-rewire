# Prompt Engineering & Structured Output

**Pod:** 4 of 6  
**Domain Weight:** 20% of exam  
**Estimated Time:** ~3 hours  
**Notebooks:** 4  
**Status:** Live

---

## Overview

Apply explicit criteria, few-shot prompting, tool_use schemas, validation-retry loops, and the Batch API. This domain covers the techniques for getting reliable, structured, and verifiable outputs from Claude.

---

## 1. Explicit Criteria and Evaluation Rubrics

### The Problem with Implicit Expectations

Vague prompts lead to inconsistent outputs:
> "Write a good code review."

Better — explicit criteria:
> "Review this PR against these criteria:
> 1. **Correctness**: No logic bugs, edge cases handled
> 2. **Security**: No injection vulnerabilities, secrets exposed
> 3. **Performance**: No N+1 queries, appropriate algorithms
> 4. **Style**: Matches project conventions, clear naming
> 5. **Tests**: New code has tests, existing tests pass
>
> For each criterion, rate: PASS / MINOR_ISSUE / MAJOR_ISSUE / BLOCKER
> Provide specific file:line references for any non-PASS rating."

### Rubric Template

```markdown
## Evaluation Rubric: {{task_name}}

| Criterion | Weight | PASS | MINOR_ISSUE | MAJOR_ISSUE | BLOCKER |
|-----------|--------|------|-------------|-------------|---------|
| Correctness | 30% | Logic sound, edge cases covered | Minor logic gap | Logic error in non-critical path | Critical logic failure |
| Security | 25% | No vulnerabilities | Info disclosure risk | Exploitable in specific context | Remote code execution |
| Performance | 15% | Optimal for constraints | 2x slower than optimal | 10x slower, impacts UX | Unacceptable latency |
| Maintainability | 15% | Clean, documented, tested | Minor style issues | Hard to understand/modify | Unmaintainable |
| Completeness | 15% | All requirements met | Missing nice-to-have | Missing core requirement | Fundamental gap |

**Overall Decision**: PASS / REVISE / REJECT
```

### Using Rubrics in Prompts

```python
prompt = f"""
Review the following code against the rubric below.
Return your evaluation as a JSON object matching the schema.

RUBRIC:
{rubric}

CODE:
{code}

OUTPUT SCHEMA:
{{
  "evaluations": [
    {{"criterion": "string", "rating": "PASS|MINOR_ISSUE|MAJOR_ISSUE|BLOCKER", "evidence": "string", "line_refs": ["string"]}}
  ],
  "overall": "PASS|REVISE|REJECT",
  "summary": "string"
}}
"""
```

---

## 2. Few-Shot Prompting

### Principles

1. **Diversity** — Examples should cover different styles, edge cases, failure modes
2. **Relevance** — Examples must match the target task domain
3. **Quality** — Only include high-quality examples (no "bad" examples unless explicitly contrasted)
4. **Consistency** — Same format, same level of detail across examples
5. **Quantity** — 3-8 examples typically optimal; more can confuse

### Few-Shot Structure

```python
FEW_SHOT_EXAMPLES = [
    {
        "input": "User wants to refund order ORD-123 for $45. Item arrived damaged.",
        "output": {
            "action": "process_refund",
            "amount": 45,
            "reason": "damaged_item",
            "requires_approval": False
        }
    },
    {
        "input": "Customer requests $800 refund for order ORD-456. Past 90-day window.",
        "output": {
            "action": "deny_refund",
            "reason": "return_window_expired",
            "policy": "90-day return policy",
            "escalation_path": "manager_approval"
        }
    },
    {
        "input": "User says 'cancel my subscription' but has annual plan with 6 months left.",
        "output": {
            "action": "escalate_to_human",
            "reason": "complex_billing",
            "details": "Annual plan cancellation requires proration calculation"
        }
    }
]

# Format for prompt
few_shot_prompt = "\n\n".join([
    f"Example {i+1}:\nInput: {ex['input']}\nOutput: {json.dumps(ex['output'], indent=2)}"
    for i, ex in enumerate(FEW_SHOT_EXAMPLES)
])

prompt = f"""Classify the customer request and determine the action.

{few_shot_prompt}

Now classify:
Input: {user_request}
Output:"""
```

### Chain-of-Thought Few-Shot

For complex reasoning, include the thinking process:

```python
COT_EXAMPLES = [
    {
        "input": "Debug why payment failed for order ORD-789",
        "thinking": "First, I need to check the payment status. Then look at the error code. Payment gateway errors (5xx) are retryable. Card declines (402) need customer action. Let me check the order first.",
        "tool_calls": [
            {"tool": "lookup_order", "args": {"order_id": "ORD-789"}},
            {"tool": "get_payment_details", "args": {"payment_id": "PAY-123"}}
        ],
        "output": "Payment failed due to insufficient funds (card decline). Customer needs to update payment method."
    }
]
```

---

## 3. Tool Use Schemas (JSON Schema)

### Schema Design Principles

1. **Strict validation** — Use `additionalProperties: false`
2. **Descriptive names** — Tool names, property names self-documenting
3. **Constraints** — `minLength`, `maxLength`, `pattern`, `enum`, `minimum`, `maximum`
4. **Required fields** — Explicit `required` array
5. **Examples** — Include `examples` in schema for model guidance

### Well-Designed Schema Example

```json
{
  "name": "process_refund",
  "description": "Process a refund for an order. Only use after verifying eligibility.",
  "input_schema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "order_id": {
        "type": "string",
        "pattern": "^ORD-[0-9]{4,}$",
        "description": "Order ID in format ORD-XXXX"
      },
      "amount": {
        "type": "number",
        "minimum": 0.01,
        "maximum": 10000,
        "description": "Refund amount in USD"
      },
      "reason": {
        "type": "string",
        "enum": ["damaged_item", "wrong_item", "not_as_described", "customer_changed_mind", "duplicate_charge", "return_window_expired"],
        "description": "Reason for refund"
      },
      "refund_method": {
        "type": "string",
        "enum": ["original_payment", "store_credit", "bank_transfer"],
        "default": "original_payment",
        "description": "How to issue the refund"
      },
      "requires_approval": {
        "type": "boolean",
        "description": "Whether manager approval is needed (amount > $500)"
      }
    },
    "required": ["order_id", "amount", "reason"],
    "examples": [
      {
        "order_id": "ORD-1234",
        "amount": 49.99,
        "reason": "damaged_item",
        "refund_method": "original_payment",
        "requires_approval": false
      }
    ]
  }
}
```

### Schema Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| `additionalProperties: true` | Model can add unexpected fields | Set `false` |
| No `enum` for categorical | Model invents values | Define explicit enum |
| No `pattern` for IDs | Accepts invalid formats | Add regex pattern |
| Missing `minimum`/`maximum` | Allows unreasonable values | Add bounds |
| No `required` array | Optional fields become ambiguous | Explicit required |

---

## 4. Validation-Retry Loops

### The Pattern

```python
async def validated_tool_call(tool_name: str, args: dict, validator: callable, max_retries: int = 3):
    """Call tool with validation and automatic retry on failure."""
    
    for attempt in range(max_retries):
        result = await call_tool(tool_name, args)
        
        # Validate result
        validation = validator(result)
        
        if validation.is_valid:
            return result
        
        # Build correction prompt
        correction_prompt = f"""
        The previous tool call returned invalid data:
        
        Tool: {tool_name}
        Args: {json.dumps(args)}
        Result: {json.dumps(result)}
        
        Validation Errors:
        {validation.errors}
        
        Please correct the tool call arguments and try again.
        Attempt {attempt + 2} of {max_retries}.
        """
        
        # Get corrected args from model
        corrected = await get_corrected_args(correction_prompt)
        args = corrected
    
    raise ValidationError(f"Failed after {max_retries} attempts")
```

### Validator Functions

```python
from dataclasses import dataclass
from typing import Any, List

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]

def validate_refund_result(result: dict) -> ValidationResult:
    errors = []
    warnings = []
    
    # Required fields
    if "refund_id" not in result:
        errors.append("Missing refund_id")
    
    if "status" not in result:
        errors.append("Missing status")
    elif result["status"] not in ["processed", "pending", "failed"]:
        errors.append(f"Invalid status: {result['status']}")
    
    # Business rules
    if result.get("amount", 0) > 500 and not result.get("approval_id"):
        errors.append("Refunds > $500 require approval_id")
    
    # Data quality
    if result.get("processed_at") and not is_iso8601(result["processed_at"]):
        warnings.append("processed_at should be ISO 8601 format")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )
```

### Retry Strategies

| Strategy | When to Use | Implementation |
|----------|-------------|----------------|
| **Same args retry** | Transient failures (network, timeout) | `for i in range(3): try: return call() except TransientError: wait(2**i)` |
| **Model-corrected args** | Validation errors, schema violations | Validation-retry loop above |
| **Alternative approach** | Business rule failures | Try different tool or escalate |
| **Human escalation** | Repeated failures, permission errors | Handoff protocol |

---

## 5. Batch API for High-Throughput Processing

### When to Use Batch API

- Processing 100+ similar requests
- Cost optimization (50% discount vs synchronous)
- Non-real-time requirements (results in 24 hours)
- Evaluation, classification, extraction tasks

### Batch Request Format

```python
# Prepare batch requests
batch_requests = [
    {
        "custom_id": f"review-{i}",
        "params": {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": f"Review this code: {code_snippets[i]}"}
            ],
            "tools": [code_review_tool],
            "tool_choice": {"type": "tool", "name": "code_review"}
        }
    }
    for i, code_snippets in enumerate(code_batches)
]

# Submit batch
batch = client.messages.batches.create(requests=batch_requests)

# Poll for completion
while batch.processing_status != "ended":
    batch = client.messages.batches.retrieve(batch.id)
    time.sleep(60)

# Retrieve results
results = client.messages.batches.results(batch.id)
```

### Batch Processing Patterns

```python
# Pattern 1: Map-reduce with batches
def batch_process(items: List[Any], processor: callable, batch_size: int = 100):
    # Split into batches
    batches = [items[i:i+batch_size] for i in range(0, len(items), batch_size)]
    
    # Submit all batches
    batch_jobs = [submit_batch(batch) for batch in batches]
    
    # Wait for all
    results = [wait_for_batch(job) for job in batch_jobs]
    
    # Combine
    return [item for batch_result in results for item in batch_result]

# Pattern 2: Progressive batching (start small, scale up)
async def adaptive_batch_process(items, processor):
    batch_size = 10  # Start small
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        batch_result = await processor(batch)
        results.extend(batch_result)
        
        # Increase batch size if successful
        if len(batch_result) == len(batch):  # All succeeded
            batch_size = min(batch_size * 2, 1000)
    
    return results
```

### Cost Optimization

| Approach | Cost | Latency | Use Case |
|----------|------|---------|----------|
| Synchronous | 100% | Seconds | Real-time, interactive |
| Batch API | 50% | Hours | Bulk processing, evaluations |
| Prompt caching | Up to 90% | Same | Repeated context (system prompts, few-shots) |

---

## 6. Structured Output Patterns

### JSON Mode

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    messages=[{"role": "user", "content": prompt}],
    # Force JSON output
    tool_choice={"type": "tool", "name": "output_json"},
    tools=[{
        "name": "output_json",
        "description": "Output the result as JSON",
        "input_schema": output_schema
    }]
)

# Extract JSON from tool call
json_output = response.content[0].input
```

### Structured Output with Validation

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional

class CodeReviewOutput(BaseModel):
    evaluations: List[Evaluation]
    overall: Literal["PASS", "REVISE", "REJECT"]
    summary: str = Field(min_length=50, max_length=500)
    
    @validator("evaluations")
    def must_have_evaluations(cls, v):
        if not v:
            raise ValueError("At least one evaluation required")
        return v

# In prompt:
prompt = f"""
Review the code and output JSON matching this schema:
{CodeReviewOutput.schema_json(indent=2)}
"""

# Parse and validate
try:
    review = CodeReviewOutput.parse_raw(json_output)
except ValidationError as e:
    # Retry with error feedback
    pass
```

### Streaming Structured Output

```python
async def stream_structured(prompt: str, schema: dict):
    """Stream and parse structured output incrementally."""
    
    buffer = ""
    async with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
        tool_choice={"type": "tool", "name": "output_json"},
        tools=[{"name": "output_json", "input_schema": schema}]
    ) as stream:
        async for chunk in stream:
            if chunk.type == "content_block_delta":
                if chunk.delta.type == "input_json_delta":
                    buffer += chunk.delta.partial_json
                    # Try parsing incrementally
                    try:
                        yield json.loads(buffer)
                    except json.JSONDecodeError:
                        continue  # Wait for more
```

---

## 7. Prompt Optimization Techniques

### 1. Prompt Caching (Implicit)

```python
# System prompt and tools cached automatically
# Reuse same client, same system prompt across calls
client = anthropic.Anthropic()

# First call - caches system prompt + tools
response1 = client.messages.create(
    model="claude-sonnet-4-20250514",
    system=SYSTEM_PROMPT,  # Cached
    tools=TOOLS,           # Cached
    messages=messages1
)

# Subsequent calls - cache hit (up to 90% cost reduction)
response2 = client.messages.create(
    model="claude-sonnet-4-20250514",
    system=SYSTEM_PROMPT,  # Cache hit!
    tools=TOOLS,           # Cache hit!
    messages=messages2
)
```

### 2. Prefill for Constrained Output

```python
# Force output to start with specific format
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    messages=[
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": '{"evaluations": ['}  # Prefill
    ]
)
```

### 3. XML Tags for Structure

```python
prompt = """
<task>
Analyze the following code for security vulnerabilities.
</task>

<code>
{code}
</code>

<output_format>
<vulnerabilities>
  <vulnerability>
    <type>SQL_INJECTION</type>
    <line>42</line>
    <severity>HIGH</severity>
    <description>...</description>
  </vulnerability>
</vulnerabilities>
</output_format>
"""
```

### 4. Step-by-Step Instructions

```python
prompt = """
Follow these steps exactly:

1. First, identify all user inputs in the code
2. For each input, trace its flow to sinks (DB, HTML, shell)
3. Check if each flow has proper validation/sanitization
4. Classify any unprotected flows by vulnerability type
5. Output findings in the specified JSON format

Do not skip steps. Do not combine steps.
"""
```

---

## 8. Exam Focus Areas

### Key Concepts to Master

1. **Explicit Criteria** — Rubrics, weighted scoring, structured evaluation output
2. **Few-Shot Design** — Diversity, relevance, quality, consistency, quantity (3-8)
3. **Tool Schemas** — Strict validation, constraints, enums, patterns, examples
4. **Validation-Retry** — Validator design, retry strategies, correction prompts
5. **Batch API** — When to use, request format, polling, cost optimization
6. **Structured Output** — JSON mode, Pydantic validation, streaming, prefill
7. **Optimization** — Prompt caching, prefill, XML tags, step-by-step

### Common Exam Questions

| Question Type | Example |
|---------------|---------|
| Schema design | "Design a tool schema for processing refunds with validation" |
| Few-shot | "How many examples? What makes a good few-shot set?" |
| Validation-retry | "Tool returns invalid data. Design a retry loop with model correction" |
| Batch API | "When would you use Batch API vs synchronous? Cost difference?" |
| Structured output | "How to enforce JSON output matching a schema?" |
| Prompt caching | "How does prompt caching work? What gets cached?" |
| Rubric design | "Create a rubric for evaluating code reviews with 5 criteria" |

---

## Quick Reference

### Few-Shot Checklist
- [ ] 3-8 examples
- [ ] Diverse cases (normal, edge, complex)
- [ ] Same format throughout
- [ ] High quality only
- [ ] Relevant to target domain

### Schema Checklist
- [ ] `additionalProperties: false`
- [ ] All fields have `type`
- [ ] Enums for categorical fields
- [ ] Patterns for IDs/formats
- [ ] Min/max for numbers
- [ ] Required array explicit
- [ ] Examples included

### Validation-Retry Loop
```python
for attempt in range(max_retries):
    result = call_tool(args)
    validation = validate(result)
    if validation.valid: return result
    args = model_correct(args, validation.errors)
raise FailedError
```

### Batch API Decision
| Factor | Batch | Sync |
|--------|-------|------|
| Volume | 100+ | <100 |
| Latency tolerance | Hours | Seconds |
| Cost sensitivity | High | Low |
| Interactivity | No | Yes |

### Output Enforcement
```python
# JSON mode via tool
tool_choice = {"type": "tool", "name": "output_json"}
tools = [{"name": "output_json", "input_schema": schema}]

# Or prefill
messages.append({"role": "assistant", "content": '{"key":'})

# Or Pydantic validation post-hoc
Model.parse_raw(output)
```

---

## Related Resources

- **Previous:** [Claude Code Configuration & Workflows](./03_claude_code_workflows.md)
- **Next:** [Context Management & Reliability](./05_context_management_reliability.md)
- **Course Overview:** [Claude Certified Architect Prep](./00_course_overview.md)

---

*Source: Vizuara AI Pods — Claude Certified Architect Prep Course, Pod 4: Prompt Engineering & Structured Output (derived from domain description and exam specifications)*