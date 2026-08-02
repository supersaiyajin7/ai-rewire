# Tool Design & MCP Integration

**Domain Weight:** Significant portion of Domain 2 on the Claude Certified Architect Exam
**Estimated Study Time:** ~3 hours | 4 Notebooks

---

## Overview

The quality of your tools is determined **not by their implementation, but by how clearly you communicate their purpose to the model**. This is the central lesson of Domain 2.

When a customer writes "I need to update my shipping address" and your agent calls `lookup_order` instead of `get_customer`, the problem isn't the model — it's your tool descriptions.

This document covers the five core skills:
1. **Writing tool descriptions that differentiate** — the primary selection signal for the model
2. **Structuring error responses for intelligent recovery** — giving the agent actionable failure information
3. **Distributing tools across agents** — scoped access prevents misuse
4. **Configuring MCP servers** — project vs user level, resources, community vs custom
5. **Selecting the right built-in tools** — Grep, Glob, Read, Write, Edit used incrementally

---

## 1. Tool Descriptions Are the Selection Mechanism

### How Tool Selection Actually Works

When Claude decides which tool to call:
1. Receives a list of available tools (name, description, input schema)
2. Reads the user's request
3. Reads the tool descriptions
4. **Selects the tool whose description best matches the intent**

The description is **not documentation for humans** — it is the **primary selection signal for the model**.

### Restaurant Menu Analogy

If every dish is listed as "food — tastes good," you order randomly.

But if one entry says:
> "Wood-fired margherita pizza — thin crust, San Marzano tomatoes, fresh mozzarella, basil. Best for: a quick, classic Italian meal"

And another says:
> "Slow-braised lamb shank — 8-hour cook, red wine reduction, root vegetables. Best for: a hearty, warming dinner"

You know exactly what you're getting. **Your tool descriptions should be this specific.**

---

## 2. What Makes a Good Tool Description

A good tool description answers **five questions**:

| # | Question | Purpose |
|---|----------|---------|
| 1 | **What does this tool do?** | One sentence, specific and unambiguous |
| 2 | **What are the expected inputs?** | Format, types, constraints |
| 3 | **What does it return?** | Structure and content of the response |
| 4 | **When should you use it?** | Positive examples and use cases |
| 5 | **When should you NOT use it?** | Boundary with similar tools |

---

## 3. Before/After: Tool Description Transformation

### The Problem: Overlapping Descriptions

```python
# BEFORE (BAD) - Minimal, overlapping descriptions
get_customer: "Retrieves customer information"
lookup_order: "Looks up order information"
```

**Why this fails:** "Customer information" and "order information" overlap heavily — an order contains customer data, and a customer record references orders. The model is essentially flipping a coin.

### The Solution: Detailed, Differentiated Descriptions

```python
# AFTER (GOOD) - Explicit boundaries and use cases

get_customer = """
Retrieves a customer's profile by email or customer ID.
Returns: name, email, shipping address, account status, loyalty tier.
Use for: address changes, account questions, loyalty inquiries.
Do NOT use for: order-specific questions (use lookup_order instead).
"""

lookup_order = """
Retrieves order details by order ID or tracking number.
Returns: items, quantities, prices, shipping status, delivery date.
Use for: order status, delivery tracking, item-specific questions.
Do NOT use for: customer profile updates (use get_customer instead).
"""
```

**Result:** "Update my shipping address" → maps to `get_customer` (explicitly mentions address changes). "Where is my package?" → maps to `lookup_order` (explicitly mentions delivery tracking).

---

## 4. Renaming and Splitting Overlapping Tools

### Problem: Functionally Identical Tools

```python
analyze_content: "Analyzes content and returns insights"
analyze_document: "Analyzes a document and returns insights"
```

These are **functionally identical from the model's perspective**.

### Fix Step 1: Rename to Differentiate

Change `analyze_content` → `extract_web_results` with a web-specific description. Names alone now tell the model which context each tool serves.

### Fix Step 2: Split Generic Tools into Purpose-Specific Ones

If `analyze_document` does three different things:
- Extracting data points
- Summarizing content
- Fact-checking

**Split into three tools:**

| Tool | Description |
|------|-------------|
| `extract_data_points` | "Extracts structured data (names, dates, amounts) from a document" |
| `summarize_content` | "Generates a concise summary of a document's main arguments" |
| `verify_claim_against_source` | "Checks whether a specific claim is supported by the source document" |

Each tool now has a **single, clear purpose**. The model selects the right one because there is no ambiguity.

---

## 5. The System Prompt Keyword Trap

### Subtle Failure Mode

Your system prompt says:
> "When the user mentions analysis, always analyze the content thoroughly before responding."

The word **"analyze"** in the system prompt creates an unintended association with any tool containing "analyze" in its name or description. The model sees the keyword match and preferentially selects `analyze_content` even when `lookup_order` would be more appropriate.

### The Fix

Review system prompts for **keyword-sensitive instructions** that might override well-written tool descriptions.

| Instead of... | Use... |
|---------------|--------|
| "Analyze the customer's situation" | "Retrieve the customer's profile" |
| "Process the refund request" | "Check refund eligibility and process if warranted" |
| "Search for relevant information" | "Look up the order details using the order ID" |

**Use task-oriented language** ("retrieve the customer's profile") rather than generic verbs that match tool names ("analyze the customer's situation").

---

## 6. Structured Error Responses

### The Problem: Unactionable Errors

Agent calls `process_refund` and gets back:
```
"Operation failed"
```

**What should the agent do?** Retry? Tell the customer it can't help? Escalate to a human? The agent has no idea — like a doctor receiving a lab report that just says "abnormal."

---

## 7. The MCP isError Flag

The Model Context Protocol provides an `isError` flag that explicitly tells the model a tool call failed. When your MCP server returns a response with `isError: true`, the model knows this is not a normal result — it's a failure that needs handling.

**But the flag alone is not enough.** The model also needs to know **what kind** of failure occurred, because different failures require different responses.

---

## 8. Four Error Categories (Comprehensive Taxonomy)

| Category | Description | Retryable? | Example |
|----------|-------------|------------|---------|
| **1. Transient** | Service temporarily unavailable | ✅ Yes | Database timeout, rate limit, network blip |
| **2. Validation** | Input was malformed | ❌ No (with same input) | Invalid email format, missing required field, order ID pattern mismatch |
| **3. Business** | Request violated business rule | ❌ No | Refund denied (return window expired), already refunded |
| **4. Permission** | Agent lacks authorization | ❌ No (needs escalation) | Refund >$500 requires manager approval, restricted account |

---

## 9. Structured Error Response Format

```json
{
  "isError": true,
  "content": "Refund denied: return window expired (90 days)",
  "metadata": {
    "errorCategory": "business",
    "isRetryable": false,
    "errorCode": "RETURN_WINDOW_EXPIRED",
    "customerMessage": "Unfortunately, this order is past the 90-day return window and is no longer eligible for a refund."
  }
}
```

### What the Agent Now Knows

| Field | Purpose |
|-------|---------|
| `errorCategory: "business"` | Policy issue, not technical glitch |
| `isRetryable: false` | Do NOT attempt the same refund again |
| `customerMessage` | Pre-written, customer-friendly explanation to relay |
| `errorCode` | Machine-readable code for programmatic handling |

**Compare to:** `"Operation failed"` — structured response gives the agent everything it needs to make a good decision.

---

## 10. Why Retryable vs Non-Retryable Matters

| Failure | Category | isRetryable | Agent Action |
|---------|----------|-------------|--------------|
| Database timeout | Transient | ✅ `true` | Wait briefly, retry |
| Refund denied by policy | Business | ❌ `false` | Do NOT retry — explain policy to customer |

**Without this distinction:**
- Agent might retry business failure 3x → wastes tokens, same result
- Agent might give up on transient failure that would succeed on retry

---

## 11. Local Error Recovery in Subagents

In multi-agent systems, **where** recovery happens matters:

### Transient Errors → Handle Locally in Subagent
- Database call times out
- Subagent retries once or twice before propagating
- Coordinator should not be bothered with every network hiccup

### Business/Permission Errors → Propagate to Coordinator
Include:
- What was attempted
- What failed and why
- Any partial results obtained before failure

This gives the coordinator context for higher-level decisions (different approach, escalate to human).

---

## 12. Access Failures vs Valid Empty Results

**Critical distinction the exam tests:**

| Scenario | Classification | Agent Should... |
|----------|----------------|-----------------|
| Search for orders → zero results | **Valid empty result** (NOT an error) | Inform customer: "No orders found" |
| Query couldn't execute (permission/outage) | **Access failure** (IS an error) | Retry or escalate: "System unavailable" |

The agent must distinguish: "I checked and there are none" vs "I couldn't check because the system is down."

---

## 13. Tool Distribution Across Agents

### The Problem: Too Many Tools on One Agent

Giving a single agent 18 tools:
- Customer lookup, order search, refund processing, inventory checking
- Shipping tracking, email sending, ticket creation, knowledge base search
- Sentiment analysis, language translation, calendar scheduling, report generation
- Data export, user authentication, payment processing, discount application
- Feedback collection, escalation routing

**Result:** Agent struggles. Not because it can't understand tools, but because **decision space is too large**. With 18 options, every tool call requires evaluating 18 descriptions. Probability of misselection increases with every tool.

### Empirical Guideline

> **4–5 tools per agent** gives reliable selection. Beyond that, accuracy degrades.

---

## 14. Scoped Tool Access Pattern

### Solution: Scope Tools by Agent Role

In a multi-agent customer support system:

| Agent | Tools (3-4 each) | Role |
|-------|------------------|------|
| **Triage Agent** | `get_customer`, `classify_intent`, `route_to_specialist` | Initial routing |
| **Order Specialist** | `lookup_order`, `track_shipment`, `process_return`, `escalate_to_human` | Order-related issues |
| **Billing Specialist** | `get_invoice`, `process_refund`, `apply_credit`, `escalate_to_human` | Billing/refund issues |

**Benefits:**
- Each agent has focused toolset matching its role
- Triage agent never sees `process_refund` → cannot accidentally call it
- Billing specialist never sees `track_shipment` → not distracted by shipping options

---

## 15. Replacing Generic Tools with Constrained Alternatives

Sometimes you can't reduce total tools, but you can make each more constrained.

### Example: Generic vs Constrained

| Generic Tool | Constrained Alternative |
|--------------|------------------------|
| `fetch_url` — hits any URL on internet | `load_document` — only accepts URLs matching your document repository pattern |

**Why constrained wins:**
- Tool itself enforces boundaries
- Model cannot wander outside intended scope even if it tries
- Safety AND reliability win

---

## 16. tool_choice Configuration (Fine-Grained Control)

The Claude API provides three `tool_choice` options:

| Option | Behavior | Use Case |
|--------|----------|----------|
| `"auto"` (default) | Model decides whether to call a tool, and which one | Standard agent interactions |
| `"any"` | Model MUST call a tool (cannot return conversational text) | Guarantee agent takes action rather than chatting |
| `{"type": "tool", "name": "tool_name"}` | Model MUST call the specified tool | Enforce ordering (e.g., metadata extraction first) |

### Forced Selection Example: Document Processing Pipeline

```python
# Turn 1: FORCE metadata extraction
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    tools=tools,
    tool_choice={"type": "tool", "name": "extract_metadata"},
    messages=messages
)

# Process the metadata result...
messages.append({"role": "assistant", "content": response.content})
messages.append({"role": "user", "content": [{"type": "tool_result", ...}]})

# Turn 2+: Let model choose freely
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    tools=tools,
    tool_choice={"type": "auto"},
    messages=messages
)
```

**Pattern:** First call forces `extract_metadata`. Once complete, subsequent calls use `"auto"` so model selects appropriate enrichment tool based on extracted metadata.

---

## 17. MCP Server Configuration

### Two Configuration Levels

| Level | File | Scope | Use For |
|-------|------|-------|---------|
| **Project-level** | `.mcp.json` | Committed to version control, shared by team | Shared team tooling: Jira, GitHub, internal knowledge base |
| **User-level** | `~/.claude.json` | Personal, not committed, not shared | Personal/experimental: local DB explorer, note-taking, prototypes |

### Project-Level `.mcp.json` Example

```json
{
  "mcpServers": {
    "jira": {
      "command": "npx",
      "args": ["@anthropic/jira-mcp-server"],
      "env": {
        "JIRA_URL": "https://yourcompany.atlassian.net",
        "JIRA_TOKEN": "${JIRA_TOKEN}"
      }
    },
    "github": {
      "command": "npx",
      "args": ["@anthropic/github-mcp-server"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

**Key:** `${JIRA_TOKEN}` and `${GITHUB_TOKEN}` syntax — MCP supports environment variable expansion. Actual token values come from each developer's local environment, **not the committed file**. This manages credentials without secrets in the repository.

### User-Level `~/.claude.json` Example

```json
{
  "mcpServers": {
    "my-notes": {
      "command": "node",
      "args": ["/Users/me/tools/notes-server/index.js"]
    }
  }
}
```

---

## 18. Tool Discovery at Connection Time

When Claude connects to MCP servers, it discovers **all available tools from all configured servers simultaneously**.

- **No priority ordering** — every tool from every server is in a flat list
- **Tool names must be unique** across servers
- **Descriptions must clearly differentiate** tools from different servers

---

## 19. MCP Resources (Read-Only Data Sources)

MCP is not just tools — it also supports **resources**: read-only data sources the agent can browse without making tool calls. Think of it as a content catalog.

### Example Resources from Issue Tracker MCP Server

| Resource | Purpose |
|----------|---------|
| All open issues with summaries | Agent knows what issues exist without calling "list issues" |
| Documentation hierarchy | Agent knows docs structure without exploratory calls |
| Database schemas | Agent knows table structures without querying |

**Without resources:** Agent makes exploratory calls ("List all issues," "Show me docs structure," "What tables exist?")

**With resources:** Agent already knows what's available → makes targeted, efficient tool calls.

---

## 20. Community vs Custom MCP Servers

| Use Community Servers For... | Build Custom Servers For... |
|------------------------------|----------------------------|
| Standard integrations (Jira, GitHub, Slack, databases) | Team-specific workflows (proprietary API, internal deployment pipeline, custom data format) |
| Well-tested, community-maintained | No community server covers your needs |
| Common use cases | Tighter integration with internal systems needed |

---

## 21. Making MCP Tools Beat Built-in Tools

### The Problem

Claude has built-in tools like **Grep** for searching file contents. You have an MCP tool that searches a code index (faster, more semantic, better results). But the agent might still prefer Grep because:
- It knows Grep well
- Your MCP tool description is vague

### The Fix: Explicit Comparison in Description

```python
search_code_index = """
Searches the pre-built code index for semantic matches.
Faster than Grep for large codebases (returns in <100ms vs seconds).
Supports natural language queries like 'authentication middleware'.
Use this INSTEAD of Grep when searching for concepts rather than exact strings.
"""
```

Now the model has a **clear reason to prefer the MCP tool** over the built-in one.

---

## 22. Built-in Tools: Grep, Glob, Read, Write, Edit

Claude Code provides five built-in tools for codebase work. Each has a specific purpose.

### Tool Selection Guide

| Tool | Purpose | Use For |
|------|---------|---------|
| **Grep** | Search file **contents** | Find callers of a function, error messages, import statements |
| **Glob** | Search file **names/paths** | Find test files, config files, files in specific directory |
| **Read** | Load complete file contents | When you need to see everything |
| **Write** | Replace complete file contents | When replacing entire file |
| **Edit** | Surgical changes via unique anchor | Targeted modifications (more efficient than Read+Write) |

### Decision Tree: Which Tool?

```
Need to find files containing specific text?          → Grep
Need to find files matching a naming pattern?         → Glob
Need to see entire file contents?                     → Read
Need to replace entire file?                          → Write
Need to change a few lines in a file?                 → Edit (if anchor unique) → Read+Write (if not unique)
```

### Edit Constraint

**Edit requires the old text to be UNIQUE within the file.** If text appears multiple times, Edit fails.

### Fallback Pattern

```python
# Try Edit first (more efficient)
try:
    edit_tool(old_text, new_text)
except NotUniqueError:
    # Fallback: Read + Write
    content = read_tool(file_path)
    # Find specific occurrence using surrounding context
    modified = content.replace(specific_occurrence, new_text)
    write_tool(file_path, modified)
```

---

## 23. Building Codebase Understanding Incrementally

### Wrong Approach ❌

Read every file upfront → floods context window with irrelevant code.

### Right Approach: Incremental Pattern

| Step | Action | Tool | Purpose |
|------|--------|------|---------|
| **1** | Find entry points | **Grep** | Search for function name, error message, concept |
| **2** | Follow imports & trace flows | **Read** | Open files from step 1, trace imports to related modules |
| **3** | Trace function usage across wrappers | **Grep** | Identify all exported names, search for each across codebase |

**Pattern:** Search → Read → Trace → builds understanding efficiently without overwhelming context window.

---

## 24. Quick Reference Card

### Tool Description Template
```markdown
tool_name: """
One-sentence description of what this tool does.
Returns: [structure and content of response]
Use for: [positive examples and use cases]
Do NOT use for: [boundary with similar tools]
"""
```

### Error Response Template
```json
{
  "isError": true,
  "content": "Human-readable error description",
  "metadata": {
    "errorCategory": "transient|validation|business|permission",
    "isRetryable": true|false,
    "errorCode": "MACHINE_READABLE_CODE",
    "customerMessage": "Pre-written customer-friendly explanation"
  }
}
```

### Tool Distribution Rule
> **4–5 tools per agent maximum.** Scope by role. No cross-contamination.

### MCP Configuration
| Config | File | Secrets Handling |
|--------|------|------------------|
| Project (shared) | `.mcp.json` | `${ENV_VAR}` expansion — never commit secrets |
| User (personal) | `~/.claude.json` | Local only, not shared |

### Built-in Tool Selection
| Need | Tool |
|------|------|
| Search content | Grep |
| Search file names | Glob |
| Read entire file | Read |
| Write entire file | Write |
| Targeted edit | Edit (unique anchor) → Read+Write (fallback) |

### Codebase Exploration
> **Grep → Read → Trace** (incremental, not upfront)

---

## 25. Exam Anti-Patterns to Avoid

- [ ] ❌ Vague tool descriptions — "Retrieves information" tells the model nothing
- [ ] ❌ Overlapping tool names — `analyze_content` vs `analyze_document`
- [ ] ❌ Uniform error messages — "Operation failed" with no category or retry guidance
- [ ] ❌ Retrying non-retryable errors — Business rule denials fail every time
- [ ] ❌ Too many tools per agent — Beyond 5, selection degrades
- [ ] ❌ Generic tools where constrained ones would work — `fetch_url` vs `load_document`
- [ ] ❌ Committing secrets in `.mcp.json` — Use `${ENV_VAR}` expansion
- [ ] ❌ Reading all files upfront — Use Grep to find entry points first

---

## Related Resources

- **Previous Domain:** [Agentic Architecture & Orchestration](./01_agentic_architecture_orchestration.md) (Domain 1 - 27%)
- **Next Domain:** [Claude Code Configuration & Workflows](./03_claude_code_workflows.md) (Domain 3)
- **Course Overview:** [Claude Certified Architect Prep Course Summary](./00_course_overview.md)

---

*Source: Vizuara AI Pods — Claude Certified Architect Prep Course, Pod 2: Tool Design & MCP Integration*