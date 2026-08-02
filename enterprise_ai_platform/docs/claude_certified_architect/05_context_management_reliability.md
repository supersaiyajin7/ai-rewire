# Context Management & Reliability

**Pod:** 5 of 6  
**Domain Weight:** 15% of exam  
**Estimated Time:** ~2 hours  
**Notebooks:** 4  
**Status:** Live

---

## Overview

Handle context window limits, escalation criteria, crash recovery, and information provenance. This domain covers the techniques for building reliable, production-grade agent systems that gracefully handle constraints and failures.

---

## 1. Context Window Management

### The Constraint

Claude models have a finite context window (200K tokens for Sonnet 4). Every message, tool result, and thinking block consumes tokens. Unbounded conversations will eventually hit the limit.

### Token Budget Allocation

```python
# Typical token budget for a production agent
CONTEXT_BUDGET = {
    "system_prompt": 8000,       # 4% - Instructions, tool descriptions
    "few_shot_examples": 15000,  # 7.5% - 5-8 examples
    "conversation_history": 50000, # 25% - Recent turns
    "tool_results": 80000,       # 40% - Tool outputs (often largest)
    "thinking_blocks": 20000,    # 10% - Extended thinking
    "response_buffer": 20000,    # 10% - Model response
    "safety_margin": 7000,       # 3.5% - Buffer
    "total": 200000
}
```

### Context Window Strategies

#### Strategy 1: Sliding Window (Conversation Truncation)

```python
def manage_context(messages: List[dict], max_tokens: int = 150000) -> List[dict]:
    """Keep system prompt + recent history within budget."""
    
    # Always preserve system prompt
    system_messages = [m for m in messages if m.get("role") == "system"]
    conversation = [m for m in messages if m.get("role") != "system"]
    
    # Estimate tokens (rough: 4 chars ≈ 1 token)
    def estimate_tokens(msgs):
        return sum(len(str(m.get("content", ""))) // 4 for m in msgs)
    
    # Trim from oldest until under budget
    while estimate_tokens(system_messages + conversation) > max_tokens and len(conversation) > 2:
        # Remove oldest user/assistant pair (keep tool results with their calls)
        conversation = conversation[2:]  # Remove oldest exchange
    
    return system_messages + conversation
```

#### Strategy 2: Summarization

```python
async def summarize_old_context(messages: List[dict], keep_recent: int = 10) -> List[dict]:
    """Summarize old conversation, keep recent turns verbatim."""
    
    if len(messages) <= keep_recent + 1:  # +1 for system
        return messages
    
    system = messages[0]
    old_messages = messages[1:-keep_recent]
    recent = messages[-keep_recent:]
    
    # Generate summary
    summary_prompt = f"""
    Summarize the following conversation for context preservation.
    Focus on: key decisions, facts discovered, tasks completed, current state.
    
    Conversation:
    {format_messages(old_messages)}
    
    Output a concise summary (max 2000 tokens).
    """
    
    summary = await call_model(summary_prompt)
    
    return [
        system,
        {"role": "user", "content": f"[Previous context summary]: {summary}"},
        *recent
    ]
```

#### Strategy 3: Selective Tool Result Retention

```python
def filter_tool_results(messages: List[dict], max_tool_results: int = 20) -> List[dict]:
    """Keep only the most recent/relevant tool results."""
    
    tool_results = [m for m in messages if is_tool_result(m)]
    other_messages = [m for m in messages if not is_tool_result(m)]
    
    if len(tool_results) > max_tool_results:
        # Keep: recent results + results referenced in recent conversation
        referenced_ids = extract_referenced_tool_ids(recent_messages)
        keep = [tr for tr in tool_results if tr["tool_use_id"] in referenced_ids]
        keep += tool_results[-(max_tool_results - len(keep)):]
        tool_results = keep
    
    return other_messages + tool_results
```

### Context Monitoring

```python
class ContextMonitor:
    def __init__(self, warning_threshold: float = 0.7, critical_threshold: float = 0.9):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
    
    def check(self, messages: List[dict]) -> ContextStatus:
        used = estimate_tokens(messages)
        total = 200000  # Model limit
        ratio = used / total
        
        if ratio >= self.critical_threshold:
            return ContextStatus.CRITICAL
        elif ratio >= self.warning_threshold:
            return ContextStatus.WARNING
        return ContextStatus.OK
    
    def get_recommendation(self, status: ContextStatus) -> str:
        if status == ContextStatus.CRITICAL:
            return "IMMEDIATE: Truncate history, summarize, or escalate"
        elif status == ContextStatus.WARNING:
            return "Prepare summarization, avoid large tool results"
        return "Normal operation"
```

---

## 2. Escalation Criteria and Patterns

### When to Escalate

| Trigger | Escalation Type | Example |
|---------|----------------|---------|
| **Context critical** | Summarize + continue | 90% context used |
| **Repeated failures** | Human handoff | 3+ validation retries failed |
| **Permission denied** | Human handoff | Refund >$500 needs manager |
| **Policy ambiguity** | Human handoff | "Is this refund warranted?" unclear |
| **Safety concern** | Immediate stop | User requests harmful action |
| **User explicitly requests** | Human handoff | "Talk to a human" |

### Escalation Decision Framework

```python
class EscalationEngine:
    def __init__(self):
        self.rules = [
            EscalationRule(
                name="context_exhaustion",
                condition=lambda ctx: ctx.status == ContextStatus.CRITICAL,
                action=EscalationAction.SUMMARIZE_AND_CONTINUE
            ),
            EscalationRule(
                name="repeated_tool_failures",
                condition=lambda ctx: ctx.consecutive_failures >= 3,
                action=EscalationAction.HUMAN_HANDOFF
            ),
            EscalationRule(
                name="permission_denied",
                condition=lambda ctx: ctx.last_error_category == "permission",
                action=EscalationAction.HUMAN_HANDOFF
            ),
            EscalationRule(
                name="policy_ambiguity",
                condition=lambda ctx: ctx.model_confidence < 0.6 and ctx.is_policy_decision,
                action=EscalationAction.HUMAN_HANDOFF
            ),
            EscalationRule(
                name="user_request",
                condition=lambda ctx: "human" in ctx.last_user_message.lower() 
                                     or "representative" in ctx.last_user_message.lower(),
                action=EscalationAction.HUMAN_HANDOFF
            ),
        ]
    
    def evaluate(self, context: AgentContext) -> EscalationDecision:
        for rule in self.rules:
            if rule.condition(context):
                return EscalationDecision(
                    should_escalate=True,
                    reason=rule.name,
                    action=rule.action,
                    context_snapshot=capture_context(context)
                )
        return EscalationDecision(should_escalate=False)
```

### Structured Handoff Protocol (from Pod 1)

```python
def create_handoff_package(context: AgentContext, reason: str) -> HandoffPackage:
    return HandoffPackage(
        customer=context.customer_info,
        root_cause=context.root_cause_analysis,
        actions_taken=[
            ActionRecord(
                tool=call.tool_name,
                args=call.args,
                result=call.result,
                timestamp=call.timestamp
            )
            for call in context.tool_calls
        ],
        recommended_next_steps=context.recommended_actions,
        escalation_reason=reason,
        context_summary=summarize_context(context),
        timestamp=datetime.utcnow().isoformat()
    )
```

---

## 3. Crash Recovery and Checkpointing

### Failure Modes

| Failure Type | Recovery Strategy |
|--------------|-------------------|
| **Model API error** | Retry with exponential backoff |
| **Tool execution error** | Validation-retry loop, then escalate |
| **Network partition** | Checkpoint state, resume on reconnect |
| **Process crash** | Restore from last checkpoint |
| **Context corruption** | Full session restart with injected summary |

### Checkpointing System

```python
import json
import pickle
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import hashlib

@dataclass
class AgentCheckpoint:
    session_id: str
    timestamp: str
    messages: List[dict]
    tool_calls: List[ToolCallRecord]
    context_hash: str
    version: int = 1

class CheckpointManager:
    def __init__(self, storage_path: str = "./checkpoints"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
    
    def save(self, checkpoint: AgentCheckpoint) -> str:
        """Save checkpoint with atomic write."""
        filename = f"{checkpoint.session_id}_v{checkpoint.version}.json"
        temp_path = self.storage_path / f".{filename}.tmp"
        final_path = self.storage_path / filename
        
        with open(temp_path, 'w') as f:
            json.dump(asdict(checkpoint), f)
        
        temp_path.rename(final_path)  # Atomic on POSIX
        return str(final_path)
    
    def load_latest(self, session_id: str) -> Optional[AgentCheckpoint]:
        """Load most recent valid checkpoint."""
        checkpoints = sorted(
            self.storage_path.glob(f"{session_id}_v*.json"),
            key=lambda p: int(p.stem.split('_v')[-1]),
            reverse=True
        )
        
        for cp_path in checkpoints:
            try:
                with open(cp_path) as f:
                    data = json.load(f)
                # Verify integrity
                if self._verify_checkpoint(data):
                    return AgentCheckpoint(**data)
            except (json.JSONDecodeError, KeyError):
                continue  # Try older checkpoint
        
        return None
    
    def _verify_checkpoint(self, data: dict) -> bool:
        """Verify checkpoint integrity."""
        required = ["session_id", "timestamp", "messages", "context_hash"]
        return all(k in data for k in required)

# Usage in agent loop
checkpoint_mgr = CheckpointManager()
CHECKPOINT_INTERVAL = 5  # Every 5 tool calls

tool_call_count = 0
while True:
    response = await call_model(messages)
    
    if response.stop_reason == "tool_use":
        result = await execute_tool(...)
        messages.append(...)
        tool_call_count += 1
        
        # Periodic checkpoint
        if tool_call_count % CHECKPOINT_INTERVAL == 0:
            checkpoint = AgentCheckpoint(
                session_id=session_id,
                timestamp=datetime.utcnow().isoformat(),
                messages=messages,
                tool_calls=tool_call_history,
                context_hash=hash_context(messages)
            )
            checkpoint_mgr.save(checkpoint)
```

### Recovery Procedures

```python
async def recover_session(session_id: str, recovery_mode: str = "auto") -> AgentState:
    """Recover from checkpoint with specified strategy."""
    
    checkpoint = checkpoint_mgr.load_latest(session_id)
    if not checkpoint:
        raise RecoveryError("No valid checkpoint found")
    
    if recovery_mode == "full":
        # Restore exact state
        return AgentState(
            messages=checkpoint.messages,
            tool_calls=checkpoint.tool_calls,
            resume_from=checkpoint.timestamp
        )
    
    elif recovery_mode == "summarized":
        # Restore with summary injection
        summary = await generate_summary(checkpoint.messages)
        return AgentState(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"[Recovered session summary]: {summary}"}
            ],
            tool_calls=[],
            resume_from=checkpoint.timestamp
        )
    
    elif recovery_mode == "fresh":
        # New session with minimal context
        summary = await generate_summary(checkpoint.messages)
        return AgentState(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Previous session summary: {summary}. Continue from here."}
            ],
            tool_calls=[],
            resume_from=None
        )
```

---

## 4. Information Provenance and Audit Trails

### Why Provenance Matters

- **Debugging**: Trace why agent made a decision
- **Compliance**: Audit trail for regulated industries
- **Reproducibility**: Re-run with same inputs
- **Trust**: Human operators can verify agent reasoning

### Provenance Data Model

```python
@dataclass
class ProvenanceRecord:
    # What happened
    event_type: Literal["tool_call", "model_response", "decision", "escalation"]
    timestamp: str
    session_id: str
    
    # Inputs that led to this
    inputs: dict
    
    # Outputs produced
    outputs: dict
    
    # Model reasoning (if available)
    reasoning: Optional[str] = None
    
    # Confidence/uncertainty
    confidence: Optional[float] = None
    
    # Source references
    sources: List[str] = field(default_factory=list)
    
    # Hash for integrity
    content_hash: str = ""

class ProvenanceTracker:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.records: List[ProvenanceRecord] = []
    
    def record_tool_call(self, tool_name: str, args: dict, result: dict, 
                         reasoning: str = None, confidence: float = None):
        record = ProvenanceRecord(
            event_type="tool_call",
            timestamp=datetime.utcnow().isoformat(),
            session_id=self.session_id,
            inputs={"tool": tool_name, "args": args},
            outputs={"result": result},
            reasoning=reasoning,
            confidence=confidence,
            sources=[f"tool:{tool_name}"]
        )
        record.content_hash = self._hash_record(record)
        self.records.append(record)
    
    def record_model_decision(self, prompt: str, response: str, 
                              tool_calls: List[dict] = None):
        record = ProvenanceRecord(
            event_type="model_response",
            timestamp=datetime.utcnow().isoformat(),
            session_id=self.session_id,
            inputs={"prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()[:16]},
            outputs={"response_hash": hashlib.sha256(response.encode()).hexdigest()[:16],
                     "tool_calls": tool_calls or []},
            sources=["model:claude"]
        )
        record.content_hash = self._hash_record(record)
        self.records.append(record)
    
    def export_audit_trail(self, format: str = "json") -> str:
        """Export complete audit trail."""
        if format == "json":
            return json.dumps([asdict(r) for r in self.records], indent=2)
        elif format == "csv":
            return self._to_csv()
        elif format == "markdown":
            return self._to_markdown()
```

### Provenance in Tool Results

```python
# Enrich tool results with provenance metadata
def enrich_with_provenance(result: dict, tool_name: str, args: dict) -> dict:
    return {
        **result,
        "_provenance": {
            "tool": tool_name,
            "args": args,
            "timestamp": datetime.utcnow().isoformat(),
            "source": f"tool:{tool_name}",
            "retrieval_method": "api_call"  # or "cache", "database", etc.
        }
    }

# Example enriched result
{
    "order_id": "ORD-1234",
    "status": "shipped",
    "tracking": "TRK-5678",
    "_provenance": {
        "tool": "lookup_order",
        "args": {"order_id": "ORD-1234"},
        "timestamp": "2024-01-15T10:30:00Z",
        "source": "tool:lookup_order",
        "retrieval_method": "database_query"
    }
}
```

---

## 5. Reliability Patterns

### Circuit Breaker for External Dependencies

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
            else:
                raise CircuitOpenError("Circuit breaker open")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
    
    def on_success(self):
        self.failures = 0
        self.state = "closed"
    
    def on_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "open"
```

### Idempotency for Safe Retries

```python
def idempotent_tool_call(tool_name: str, args: dict, idempotency_key: str):
    """Ensure tool calls are idempotent using key."""
    
    # Check if already executed
    existing = idempotency_store.get(idempotency_key)
    if existing:
        return existing  # Return cached result
    
    # Execute and store
    result = execute_tool(tool_name, args)
    idempotency_store.set(idempotency_key, result, ttl=86400)
    return result

# Usage: Generate key from tool + args
idempotency_key = hashlib.sha256(
    f"{tool_name}:{json.dumps(args, sort_keys=True)}".encode()
).hexdigest()[:16]
```

### Health Checks and Readiness

```python
class AgentHealthCheck:
    def __init__(self, agent):
        self.agent = agent
    
    async def check_liveness(self) -> HealthStatus:
        """Is the agent process alive?"""
        return HealthStatus(
            healthy=True,
            checks={"process": "alive"}
        )
    
    async def check_readiness(self) -> HealthStatus:
        """Can the agent handle requests?"""
        checks = {}
        
        # Check model API
        try:
            await self.agent.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}]
            )
            checks["model_api"] = "healthy"
        except Exception as e:
            checks["model_api"] = f"unhealthy: {e}"
        
        # Check tool dependencies
        for tool in self.agent.tools:
            if hasattr(tool, "health_check"):
                checks[tool.name] = await tool.health_check()
        
        # Check context window
        context_ratio = self.agent.context_monitor.get_usage_ratio()
        checks["context_window"] = "healthy" if context_ratio < 0.8 else "degraded"
        
        overall = all(v == "healthy" for v in checks.values())
        
        return HealthStatus(
            healthy=overall,
            checks=checks
        )
```

---

## 6. Exam Focus Areas

### Key Concepts to Master

1. **Context Window Management** — Budget allocation, sliding window, summarization, selective retention
2. **Escalation Criteria** — Triggers, decision framework, structured handoff protocol
3. **Crash Recovery** — Checkpointing, recovery modes (full/summarized/fresh), integrity verification
4. **Information Provenance** — Audit trails, provenance metadata, source tracking, export formats
5. **Reliability Patterns** — Circuit breaker, idempotency, health checks, readiness probes

### Common Exam Questions

| Question Type | Example |
|---------------|---------|
| Context management | "Context at 85%. What do you do?" |
| Escalation | "List 5 escalation triggers and their handoff actions" |
| Checkpointing | "Design a checkpoint system with atomic writes and integrity verification" |
| Provenance | "What metadata should every tool result include for auditability?" |
| Recovery modes | "When to use full vs summarized vs fresh recovery?" |
| Circuit breaker | "Implement a circuit breaker for external API calls" |
| Idempotency | "How to make refund processing idempotent?" |

---

## Quick Reference

### Context Thresholds
| Status | Threshold | Action |
|--------|-----------|--------|
| OK | < 70% | Normal |
| WARNING | 70-90% | Prepare summarization |
| CRITICAL | > 90% | Immediate truncation/escalation |

### Escalation Triggers
1. Context critical (>90%)
2. 3+ consecutive failures
3. Permission denied
4. Policy ambiguity (confidence < 0.6)
5. User requests human
6. Safety violation

### Recovery Modes
| Mode | Use When | Context Preserved |
|------|----------|-------------------|
| Full | Recent crash, state critical | Exact messages + tool calls |
| Summarized | Stale checkpoint, files changed | Summary + recent turns |
| Fresh | Major changes, corrupted state | Minimal injected summary |

### Provenance Required Fields
```json
{
  "event_type": "tool_call|model_response|decision|escalation",
  "timestamp": "ISO8601",
  "session_id": "string",
  "inputs": {},
  "outputs": {},
  "reasoning": "string|null",
  "confidence": "float|null",
  "sources": ["string"],
  "content_hash": "string"
}
```

### Reliability Checklist
- [ ] Context monitoring with thresholds
- [ ] Escalation rules with structured handoffs
- [ ] Periodic checkpointing (every N tool calls)
- [ ] Checkpoint integrity verification
- [ ] Provenance tracking on all tool calls
- [ ] Circuit breakers on external dependencies
- [ ] Idempotency keys for mutating operations
- [ ] Health/readiness endpoints

---

## Related Resources

- **Previous:** [Prompt Engineering & Structured Output](./04_prompt_engineering_structured_output.md)
- **Next:** [Certification Practice Exam](./06_certification_practice_exam.md)
- **Course Overview:** [Claude Certified Architect Prep](./00_course_overview.md)
- **Agentic Architecture (foundation):** [Pod 1](./01_agentic_architecture_orchestration.md)

---

*Source: Vizuara AI Pods — Claude Certified Architect Prep Course, Pod 5: Context Management & Reliability (derived from domain description and exam specifications)*