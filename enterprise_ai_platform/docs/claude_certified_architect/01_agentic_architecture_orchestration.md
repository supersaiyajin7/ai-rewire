# Agentic Architecture & Orchestration

**Domain Weight:** 27% of the Claude Certified Architect Exam (largest domain)
**Estimated Study Time:** ~3 hours | 5 Notebooks

---

## Overview

Agentic architecture represents a fundamental shift from traditional deterministic programming to systems where **the model itself drives the control flow**. Instead of writing explicit if/else branches to decide which action to take, the model decides what to do, when to do it, and when it is done.

This document provides a comprehensive reference for building production-grade agentic systems, covering the seven core concepts tested in the largest exam domain.

---

## 1. The Agentic Loop Lifecycle

### Core Concept

The agentic loop is the fundamental execution pattern for all agents. Think of an agent like a chef in a kitchen:
- Reads the recipe (system prompt + messages)
- Checks what ingredients are available (tools)
- Starts cooking (executes tool calls)
- **Critically**: Decides when the dish is done — no external controller says "stop after exactly 5 steps"

### The Loop Algorithm

```python
while True:
    # 1. Send conversation (system prompt + messages) to the model
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=tools,
        messages=messages
    )

    # 2. Check stop_reason - THE MODEL DECIDES WHAT HAPPENS NEXT
    if response.stop_reason == "end_turn":
        # Model has decided it is done
        print(response.content[0].text)
        break

    if response.stop_reason == "tool_use":
        # Model wants to call a tool
        tool_block = next(b for b in response.content if b.type == "tool_use")
        result = execute_tool(tool_block.name, tool_block.input)

        # 3. Append assistant response AND tool result to history
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": [{
            "type": "tool_result",
            "tool_use_id": tool_block.id,
            "content": result
        }]})
```

### Execution Trace Example

**Turn 1:** User asks "What is the status of order ORD-1234?"
- Model responds with `stop_reason: "tool_use"`
- Calls `lookup_order(order_id="ORD-1234")`
- Tool executes, returns `{"status": "shipped", "tracking": "TRK-5678"}`
- Result appended to conversation

**Turn 2:** Model sees tool result
- Responds with `stop_reason: "end_turn"`
- Says: "Your order ORD-1234 has been shipped! The tracking number is TRK-5678."
- Loop exits

**Key Insight:** The model itself decided it needed one tool call and then decided it was done. We never told it "call exactly one tool" or "stop after 2 turns."

---

## 2. Critical Anti-Patterns to Avoid

### Anti-Pattern 1: Parsing Natural Language for Loop Termination ❌

```python
# NEVER DO THIS
if "I'm done" in response.text:
    break
if "task complete" in response.text.lower():
    break
```

**Why this fails:** Natural language is ambiguous. The model might say:
- "I'm done checking the database" (meaning: finished one step)
- "I'm done" (meaning: task is complete)

Using `stop_reason` removes all ambiguity — it's a deterministic signal from the API.

### Anti-Pattern 2: Arbitrary Iteration Caps as Primary Stopping Mechanism ❌

```python
# NEVER DO THIS AS PRIMARY CONTROL FLOW
for i in range(5):
    call_model()
```

**Correct approach:** Let the model drive termination through `stop_reason == "end_turn"`. Use iteration limits **only as a safety net** — a guard rail, not a steering wheel.

```python
# GOOD: Safety net only
MAX_ITERATIONS = 20  # Prevents infinite loops
iteration = 0

while True:
    if iteration >= MAX_ITERATIONS:
        logger.warning("Max iterations reached, forcing termination")
        break
    
    response = client.messages.create(...)
    
    if response.stop_reason == "end_turn":
        break
    elif response.stop_reason == "tool_use":
        # handle tool call
        pass
    
    iteration += 1
```

---

## 3. Multi-Agent Coordinator Patterns (Hub-and-Spoke)

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    COORDINATOR (Hub)                    │
│  • Task Decomposition                                   │
│  • Delegation                                           │
│  • Result Aggregation                                   │
└──────────────────┬──────────────────────┬───────────────┘
                   │                      │
        ┌──────────┴──────────┐  ┌───────┴────────┐
        ▼                     ▼  ▼                ▼
   ┌─────────┐           ┌─────────┐        ┌─────────┐
   │Subagent │           │Subagent │  ...   │Subagent │
   │   A     │           │   B     │        │   N     │
   │Isolated │           │Isolated │        │Isolated │
   │Context  │           │Context  │        │Context  │
   └─────────┘           └─────────┘        └─────────┘
```

### Three Coordinator Responsibilities

| Responsibility | Description |
|----------------|-------------|
| **Task Decomposition** | Breaking the overall task into subtasks suitable for each specialist |
| **Delegation** | Assigning each subtask to the right subagent with the right context |
| **Result Aggregation** | Combining results from all subagents into a coherent final output |

### Critical Principle: Subagents Have Isolated Context

**Subagents do NOT inherit the coordinator's conversation history.** Each subagent starts with a fresh context window containing only the specific instructions and data the coordinator passes to it.

**Why this matters:** If the coordinator has been handling 20 different customers, passing that entire conversation to a subagent that only needs to check one refund policy would:
1. Waste context window space
2. Potentially confuse the subagent with irrelevant information

Isolated context = focused, high-quality results.

### Implementation Pattern

```python
# Coordinator dispatches to a research subagent
research_result = await run_subagent(
    system_prompt="You are a research specialist.",
    prompt=f"Research the return policy for category: {category}",
    tools=["search_knowledge_base", "lookup_policy"]
    # Note: NO conversation history from coordinator is passed
)

# Coordinator dispatches to an analysis subagent
analysis_result = await run_subagent(
    system_prompt="You are a policy analyst.",
    prompt=f"Policy: {research_result}\nComplaint: {complaint}\nIs a refund warranted?",
    tools=["calculate_refund"]
)
```

### The Risk of Over-Decomposition ⚠️

**Anti-pattern:** Making subagents hyper-specialized (one agent for email validation, one for phone formatting, one for zip codes).

**Problems:**
- Each subagent invocation = full API call + context construction + response parsing
- Significant overhead and latency

**Exam Guidance:** Decompose into **meaningful, coherent subtasks** — not the smallest possible units.

**Better:** A "customer data validation agent" handling all input validation > five separate single-field validators.

---

## 4. Subagent Invocation and the Task Tool

### Task Tool Requirements

For an agent to spawn subagents, its `allowedTools` configuration **must include "Task"**. Without this, the agent cannot create child agents.

### AgentDefinition Configuration

```python
from claude_agent_sdk import AgentDefinition

research_agent = AgentDefinition(
    model="claude-sonnet-4-20250514",
    system_prompt="You are a research specialist. Search for and summarize information.",
    tools=["web_search", "read_document"],
    max_tokens=4096
)
```

### Explicit Context Passing

When the coordinator invokes the Task tool, it **must pass all necessary context explicitly in the prompt**. The subagent will not magically know what the coordinator knows.

```python
task_result = coordinator.invoke_tool("Task", {
    "agent": research_agent,
    "prompt": f"""Research the following customer issue:
    Customer ID: {customer_id}
    Order ID: {order_id}
    Complaint: {complaint_text}
    Find the relevant return policy and precedent cases."""
})
```

### fork_session for Divergent Exploration

The `fork_session` mechanism creates a branch point — the forked session gets a copy of the current context but can diverge without affecting the original.

**Analogy:** Like a save point in a video game. You save progress, try a risky strategy, and if it doesn't work, you go back to the save point.

**Agent Use Case:** Fork the session, let the forked agent explore one approach (refactoring), while the original continues with a different approach (adding a patch). Then compare results.

---

## 5. Multi-Step Workflows and Compliance

### The Compliance Challenge

In high-stakes scenarios (financial operations, healthcare), certain steps are **mandatory** — not optional guidelines.

**Example:** A financial agent that can transfer funds, process refunds, modify account settings. Before ANY financial action, the agent MUST verify customer identity. This is a regulatory requirement.

### Two Approaches

| Approach | Description | Reliability |
|----------|-------------|-------------|
| **Prompt-based guidance** | "Always verify identity before financial transactions" | Probabilistic — model might skip if customer sounds frustrated, conversation is long, request seems straightforward |
| **Programmatic enforcement** | Hooks/prerequisite gates in code make it impossible to execute financial tools without prior verification | Deterministic — 100% enforcement |

### Programmatic Enforcement Example

```python
class IdentityGate:
    def __init__(self):
        self.verified = False

    def verify_identity(self, customer_id, verification_code):
        if check_verification(customer_id, verification_code):
            self.verified = True
            return "Identity verified successfully."
        return "Verification failed."

    def process_refund(self, order_id, amount):
        if not self.verified:
            return "ERROR: Identity must be verified first."
        return execute_refund(order_id, amount)
```

### Exam Principle

> **Use programmatic enforcement for deterministic compliance requirements.** Identity verification before financial operations must never be left to prompt-based guidance alone.

**Save prompt-based guidance for softer requirements:**
- "Maintain a professional tone"
- "Ask clarifying questions when the request is ambiguous"

---

## 6. Structured Handoff Protocols

When an agent escalates to a human representative, it should not just say "transferring you now." A proper handoff includes:

### Required Handoff Components

1. **Customer details:** Name, account ID, contact preferences, tier
2. **Root cause analysis:** What the agent determined the issue to be
3. **Actions already taken:** What tools were called, what results were returned
4. **Recommended next steps:** What the agent thinks the human should do

### Handoff Data Structure

```python
handoff = {
    "customer": {
        "id": "C-789",
        "name": "Alice Smith",
        "tier": "premium"
    },
    "root_cause": "Duplicate charge on order ORD-456 due to payment gateway timeout",
    "actions_taken": [
        {"tool": "lookup_order", "result": "Order found, payment processed twice"},
        {"tool": "check_refund_eligibility", "result": "Eligible for full refund"}
    ],
    "recommendation": "Process refund of $149.99 for duplicate charge"
}
```

**Benefit:** Human representative gets a complete picture and can act immediately rather than asking the customer to repeat everything.

---

## 7. Agent SDK Hooks — Guaranteed Compliance

Hooks are functions that execute automatically at specific points in the agent's lifecycle. Two most important types for compliance:

### PostToolUse Hooks

Fire **after** a tool has been called and returned a result. Can inspect and transform the result before the model sees it.

**Classic Use Case:** Data normalization

```python
from datetime import datetime, timezone

def normalize_timestamps(tool_name, tool_result):
    """PostToolUse hook: convert Unix timestamps to ISO 8601."""
    if "timestamp" in tool_result:
        unix_ts = tool_result["timestamp"]
        dt = datetime.fromtimestamp(unix_ts, tz=timezone.utc)
        tool_result["timestamp"] = dt.isoformat()
    return tool_result
```

**Trace Example:**
- Tool returns: `{"order_id": "ORD-1234", "timestamp": 1710000000}`
- After hook: `{"order_id": "ORD-1234", "timestamp": "2024-03-09T16:00:00+00:00"}`
- Model never parses raw Unix timestamps — always gets clean, human-readable dates

### PreToolUse Hooks (Tool Call Interception)

Fire **before** a tool is executed and can **block the call entirely**. This is where you enforce hard business rules.

```python
def enforce_refund_policy(tool_name, tool_input):
    """PreToolUse hook: block refunds over $500."""
    if tool_name == "process_refund":
        amount = tool_input.get("amount", 0)
        if amount > 500:
            return {
                "blocked": True,
                "reason": f"Refund of ${amount} exceeds $500 limit. Manager approval required."
            }
    return {"blocked": False}
```

### Why Hooks Over Prompts?

| Aspect | Prompts | Hooks |
|--------|---------|-------|
| **Enforcement** | Probabilistic | Deterministic (100%) |
| **Bypass Risk** | Model might ignore under pressure | Impossible to bypass |
| **Audit Trail** | Implicit | Explicit, logged |
| **Use Case** | Best-effort guidance | Guaranteed compliance |

> **Key Exam Insight:** Hooks are for **guaranteed compliance**; prompts are for **best-effort guidance**.

---

## 8. Task Decomposition Strategies

### Fixed Sequential Pipelines (Prompt Chaining)

Each step is predetermined. Output of step 1 → step 2 → step 3.

```
Step 1: Extract key entities from document
    ↓ (entities)
Step 2: Research each entity in knowledge base
    ↓ (research results)
Step 3: Write summary incorporating research
    ↓ (final summary)
```

**Characteristics:**
- Predictable, debuggable, easy to monitor
- Known steps and order
- Works well for well-understood, rarely-changing workflows

**Example:** Loan application processing (verify identity → check credit → calculate terms → generate offer)

### Dynamic Adaptive Decomposition

The model decides what to do next based on what it has learned. No predetermined pipeline.

```
Step 1: Map codebase structure → discovers 47 files, 8 modules
Step 2: (Agent decides) Focus on 3 most relevant modules
Step 3: (Agent decides) Analyze file A → finds suspicious pattern
Step 4: (Agent decides) Check if same pattern in file B → confirms bug
Step 5: (Agent decides) Generate and verify a fix
```

### Per-File Analysis + Cross-File Integration Pass

A powerful pattern for code analysis:

1. **Phase 1 (Per-File):** Agent analyzes each relevant file independently, extracting key patterns and issues
2. **Phase 2 (Integration):** Separate pass looking across all per-file results to find cross-cutting concerns, dependencies, systemic patterns

**Why this works:** Prevents agent from getting lost in details while ensuring nothing is missed.

### When to Use Each Strategy

| Use Fixed Pipelines When... | Use Dynamic Decomposition When... |
|----------------------------|-----------------------------------|
| Workflow is well-defined | Task is exploratory |
| Steps known in advance | Number of steps is unknown |
| Reliability > flexibility | Agent needs to adapt based on discoveries |
| Example: Loan processing | Example: Debugging complex software, open-ended research |

---

## 9. Session Management and Recovery

### Resuming Sessions with `--resume`

The `--resume` flag with a session name continues an agent session exactly where it left off — retaining full conversation history, tool results, and context.

```bash
# Start a session with a name
claude --session "refactoring-auth-module"

# Later, resume where you left off
claude --resume "refactoring-auth-module"
```

### Critical Subtlety: Stale Context

If files have changed since the last session, the agent's context may be **stale**. Tool results from the previous session might reference code that no longer exists.

**Exam Requirement:** You MUST inform the resumed session about changes:

```
"Since your last session, these files were modified:
- src/auth/login.py (added 2FA support)
- src/auth/session.py (new file)
Please re-read these files before continuing."
```

### fork_session for Parallel Exploration

When you fork a session, you create a branch — like a git branch for conversations. The forked session starts with a copy of the current context but evolves independently.

```text
Original session: "Fix the bug by refactoring the parser"
Forked session:   "Fix the bug by adding input validation"
```

Both sessions work independently. When they finish, compare results and pick the better approach. The forked session cannot affect the original session's state.

### Resume vs Start Fresh Decision Framework

| Scenario | Action |
|----------|--------|
| Brief interruption, files unchanged, agent mid-task | **Resume** with `--resume` |
| Significant time passed, many files changed, old tool results misleading | **Start fresh with injected summary** |

**Injected Summary Approach:** Start a new session but provide a concise recap:
> "In the previous session, we identified the authentication bug in the token refresh logic. We attempted retry logic but it did not resolve the issue. Please try a different approach."

---

## 10. Putting It All Together: Complete Customer Support Agent

| Concept | Implementation |
|---------|----------------|
| **1. Agentic Loop** | While loop checking `stop_reason` to decide tool calls vs final response |
| **2. Multi-Agent Coordination** | Complex cases delegated to specialist subagents via hub-and-spoke |
| **3. Task Tool** | Subagents spawned with explicit context — no inherited conversation |
| **4. Workflow Enforcement** | Identity verification enforced programmatically before financial ops |
| **5. Hooks** | PostToolUse normalizes data; PreToolUse blocks policy violations |
| **6. Task Decomposition** | Simple queries = direct tool calls; complex cases = dynamic decomposition |
| **7. Session Management** | Long-running cases use `--resume`; parallel investigation uses `fork_session` |

---

## 11. Exam Anti-Patterns Checklist

Memorize these — they are explicitly tested:

- [ ] ❌ Parsing natural language to determine loop termination instead of using `stop_reason`
- [ ] ❌ Using arbitrary iteration caps as the primary stopping mechanism
- [ ] ❌ Passing the coordinator's full conversation history to subagents
- [ ] ❌ Decomposing tasks into too many tiny subagents (over-decomposition)
- [ ] ❌ Using prompt-based guidance for hard compliance requirements
- [ ] ❌ Resuming stale sessions without informing the agent about file changes

---

## 12. Quick Reference Card

### Agentic Loop Control Flow
```python
while True:
    response = client.messages.create(model, tools, messages)
    if response.stop_reason == "end_turn": break
    if response.stop_reason == "tool_use": execute_tool_and_append()
```

### Subagent Isolation Rule
> **Subagents start with ONLY what you pass them. No conversation history inheritance.**

### Hook Types
| Hook | When | Use For |
|------|------|---------|
| `PostToolUse` | After tool returns | Data normalization, enrichment |
| `PreToolUse` | Before tool executes | Policy enforcement, blocking calls |

### Compliance Enforcement
| Requirement Type | Mechanism |
|-----------------|-----------|
| Hard/Regulatory | Programmatic (hooks, gates, IdentityGate class) |
| Soft/Guidance | Prompt-based (tone, clarification requests) |

### Session Decision
| Context Freshness | Strategy |
|------------------|----------|
| Fresh (brief pause, no file changes) | `--resume "session-name"` |
| Stale (time passed, files changed) | New session + injected summary |
| Need parallel approaches | `fork_session` |

---

## Related Resources

- **Next Domain:** [Tool Design & MCP Integration](./02_tool_design_mcp_integration.md) (Domain 2)
- **Course Overview:** [Claude Certified Architect Prep Course Summary](./00_course_overview.md)
- **Practice Exam:** [Certification Practice Exam Guide](./06_certification_practice_exam.md)

---

*Source: Vizuara AI Pods — Claude Certified Architect Prep Course, Pod 1: Agentic Architecture & Orchestration*