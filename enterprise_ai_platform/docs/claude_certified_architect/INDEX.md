# Claude Certified Architect Prep — Master Index

**Complete reference for all 6 pods / 5 exam domains**

---

## Quick Navigation

| # | Document | Domain | Exam Weight | Est. Time | Notebooks |
|---|----------|--------|-------------|-----------|-----------|
| 0 | [Course Overview](./00_course_overview.md) | — | — | — | — |
| 1 | [Agentic Architecture & Orchestration](./01_agentic_architecture_orchestration.md) | Domain 1 | **27%** | ~3h | 5 |
| 2 | [Tool Design & MCP Integration](./02_tool_design_mcp_integration.md) | Domain 2 | ~18% | ~3h | 4 |
| 3 | [Claude Code Configuration & Workflows](./03_claude_code_workflows.md) | Domain 3 | ~15% | ~3h | 4 |
| 4 | [Prompt Engineering & Structured Output](./04_prompt_engineering_structured_output.md) | Domain 4 | **20%** | ~3h | 4 |
| 5 | [Context Management & Reliability](./05_context_management_reliability.md) | Domain 5 | **15%** | ~2h | 4 |
| 6 | [Certification Practice Exam](./06_certification_practice_exam.md) | Practice | — | ~2h | 1 |

**Total:** ~16 hours | 22 notebooks | 60-question practice exam

---

## Domain Weight Summary

```
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 27% — Agentic Architecture
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 20% — Prompt Engineering
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 18% — Tool Design & MCP
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 15% — Context Management
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 15% — Claude Code Workflows
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  5% — Other / Integration
```

**Priority Order for Study:** 1 → 4 → 2 → 5 → 3 → 6

---

## Cross-Domain Concept Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AGENTIC ARCHITECTURE (Pod 1)                     │
│  Agentic Loop • Multi-Agent Coordination • Task Tool • Hooks       │
│  Compliance • Decomposition • Session Management                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  TOOL DESIGN  │    │  PROMPT ENG   │    │ CONTEXT MGMT  │
│   (Pod 2)     │    │   (Pod 4)     │    │   (Pod 5)     │
│ Descriptions  │    │ Few-shot      │    │ Window limits │
│ Errors        │    │ Schemas       │    │ Escalation    │
│ Distribution  │    │ Validation    │    │ Recovery      │
│ MCP Config    │    │ Batch API     │    │ Provenance    │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             ▼
                    ┌─────────────────┐
                    │ CLAUDE CODE     │
                    │ WORKFLOWS       │
                    │   (Pod 3)       │
                    │ Config hierarchy│
                    │ Custom commands │
                    │ CI/CD patterns  │
                    │ Team alignment  │
                    └─────────────────┘
```

---

## Unified Anti-Patterns Checklist

### Agentic Architecture (Pod 1) — 6 Patterns
- [ ] Natural language loop termination → Use `stop_reason`
- [ ] Arbitrary iteration caps as primary control → Safety net only
- [ ] Full history to subagents → Isolated context only
- [ ] Over-decomposition → Meaningful subtasks
- [ ] Prompt-based hard compliance → Hooks/gates
- [ ] Resume stale without updates → Inject file changes

### Tool Design (Pod 2) — 8 Patterns
- [ ] Vague descriptions → 5-question framework
- [ ] Overlapping names → Rename/split
- [ ] Uniform errors → 4 categories + retry guidance
- [ ] Retrying non-retryable → Business errors fail always
- [ ] >5 tools/agent → Scope by role
- [ ] Generic > constrained → `fetch_url` vs `load_document`
- [ ] Secrets in `.mcp.json` → `${ENV_VAR}` expansion
- [ ] Read all files upfront → Grep → Read → Trace

### Prompt Engineering (Pod 4) — 5 Patterns
- [ ] Implicit criteria → Explicit weighted rubrics
- [ ] Poor few-shot (too few, low quality, inconsistent) → 3-8 diverse examples
- [ ] Loose schemas → Strict validation with constraints
- [ ] No validation-retry → Validator + correction loop
- [ ] Synchronous for bulk → Batch API (50% cost)

### Context Management (Pod 5) — 5 Patterns
- [ ] No context monitoring → Thresholds at 70%/90%
- [ ] Ad-hoc escalation → Structured rules + handoff protocol
- [ ] No checkpointing → Periodic atomic checkpoints
- [ ] No provenance → Audit trail on every tool call
- [ ] No reliability patterns → Circuit breaker, idempotency, health checks

### Claude Code Workflows (Pod 3) — 5 Patterns
- [ ] Secrets in committed config → `${ENV_VAR}` in local only
- [ ] Global `allow: ["Bash(*)"]` → Least privilege permissions
- [ ] Untested custom commands → Test before sharing
- [ ] Serial for independent work → Parallel/pipeline execution
- [ ] No team config sharing → Shared config repo with inheritance

---

## Quick Reference Cards

### Agentic Loop (Pod 1)
```python
while True:
    response = client.messages.create(model, tools, messages)
    if response.stop_reason == "end_turn": break
    if response.stop_reason == "tool_use": execute_and_append()
```

### Tool Description Template (Pod 2)
```
tool_name: """
One-sentence what it does.
Returns: structure
Use for: positive cases
Do NOT use for: boundary with similar tools
"""
```

### Error Response (Pod 2)
```json
{
  "isError": true,
  "content": "Human message",
  "metadata": {
    "errorCategory": "transient|validation|business|permission",
    "isRetryable": true|false,
    "errorCode": "CODE",
    "customerMessage": "User-friendly explanation"
  }
}
```

### Few-Shot Checklist (Pod 4)
- [ ] 3-8 examples
- [ ] Diverse (normal, edge, complex)
- [ ] Consistent format
- [ ] High quality only
- [ ] Domain-relevant

### Schema Checklist (Pod 4)
- [ ] `additionalProperties: false`
- [ ] Enums for categorical
- [ ] Patterns for IDs
- [ ] Min/max for numbers
- [ ] Required array explicit
- [ ] Examples included

### Context Thresholds (Pod 5)
| Status | % | Action |
|--------|---|--------|
| OK | <70% | Normal |
| WARNING | 70-90% | Prepare summarization |
| CRITICAL | >90% | Immediate action |

### Escalation Triggers (Pod 5)
1. Context >90%
2. 3+ consecutive failures
3. Permission denied
4. Policy ambiguity (confidence <0.6)
5. User requests human
6. Safety violation

### Config Hierarchy (Pod 3)
```
CLI flags (highest)
→ .claude/settings.json (project, committed)
→ .claude/settings.local.json (project, gitignored)
→ ~/.claude/settings.json (user, global)
→ Defaults (lowest)
```

### Command Frontmatter (Pod 3)
```yaml
---
name: command-name
description: One-line
arguments:
  - name: arg
    description: What it does
    required: true/false
    default: "value"
---
```

---

## Study Plan (Recommended)

### Week 1: Foundation (Pods 1 + 4)
| Day | Focus | Deliverable |
|-----|-------|-------------|
| 1-2 | Pod 1 Article + Notebooks 1-3 | Agentic loop implementation |
| 3-4 | Pod 1 Notebooks 4-5 + Anti-patterns | Multi-agent with hooks |
| 5-6 | Pod 4 Article + Notebooks 1-2 | Rubric + few-shot + schemas |
| 7 | Pod 4 Notebooks 3-4 | Validation-retry + Batch API |

### Week 2: Tools & Config (Pods 2 + 3)
| Day | Focus | Deliverable |
|-----|-------|-------------|
| 1-2 | Pod 2 Article + Notebooks 1-2 | Tool descriptions + errors |
| 3-4 | Pod 2 Notebooks 3-4 | MCP config + built-in tools |
| 5-6 | Pod 3 Article + Notebooks 1-2 | Config hierarchy + commands |
| 7 | Pod 3 Notebooks 3-4 | CI/CD + team patterns |

### Week 3: Reliability & Practice (Pods 5 + 6)
| Day | Focus | Deliverable |
|-----|-------|-------------|
| 1-2 | Pod 5 Article + Notebooks 1-2 | Context mgmt + escalation |
| 3-4 | Pod 5 Notebooks 3-4 | Recovery + provenance |
| 5 | **Full Practice Exam** (Pod 6) | Score + domain breakdown |
| 6 | Review wrong answers | Targeted re-study |
| 7 | Retake practice / light review | Final confidence |

---

## Using These Docs as Agent Context

### For Building Agentic Systems
```markdown
# Reference these files in your agent prompt:
- 01_agentic_architecture_orchestration.md  (core patterns)
- 02_tool_design_mcp_integration.md         (tool interfaces)
- 05_context_management_reliability.md      (production reliability)
```

### For Tool Development
```markdown
- 02_tool_design_mcp_integration.md (descriptions, errors, MCP)
- 04_prompt_engineering_structured_output.md (schemas, validation)
```

### For Team Claude Code Setup
```markdown
- 03_claude_code_workflows.md (config, commands, CI/CD)
- 00_course_overview.md (domain map)
```

### For Exam Prep
```markdown
- All files in order 00→06
- 06_certification_practice_exam.md for final readiness
```

---

## File Structure

```
enterprise_ai_platform/docs/claude_certified_architect/
├── 00_course_overview.md                      # Course map & study plan
├── 01_agentic_architecture_orchestration.md   # Domain 1 (27%) — LARGEST
├── 02_tool_design_mcp_integration.md          # Domain 2 (~18%)
├── 03_claude_code_workflows.md                # Domain 3 (~15%)
├── 04_prompt_engineering_structured_output.md # Domain 4 (20%)
├── 05_context_management_reliability.md       # Domain 5 (15%)
├── 06_certification_practice_exam.md          # Practice exam guide
└── INDEX.md                                    # This file
```

---

## Source Attribution

All content derived from **Vizuara AI Pods — Claude Certified Architect Prep Course**:

| Pod | Source URL | Curator |
|-----|------------|---------|
| 1 | https://pods.vizuara.ai/courses/claude-certified-architect/agentic-architecture/article | Dr. Rajat Dandekar |
| 2 | https://pods.vizuara.ai/courses/claude-certified-architect/tool-design-mcp/article | Dr. Rajat Dandekar |
| 3 | https://pods.vizuara.ai/courses/claude-certified-architect/claude-code-workflows/article | Dr. Rajat Dandekar |
| 4 | https://pods.vizuara.ai/courses/claude-certified-architect/prompt-engineering-structured-output/article | Dr. Rajat Dandekar |
| 5 | https://pods.vizuara.ai/courses/claude-certified-architect/context-management-reliability/article | Dr. Rajat Dandekar |
| 6 | https://pods.vizuara.ai/courses/claude-certified-architect/certification-practice-exam | Dr. Rajat Dandekar |

**Course Page:** https://pods.vizuara.ai/courses/claude-certified-architect

**Vizuara AI Pods:** https://pods.vizuara.ai/

**Anthropic Certification:** https://www.anthropic.com/certification

---

## Version Info

| Field | Value |
|-------|-------|
| **Created** | 2026-08-03 |
| **Source Version** | Vizuara AI Pods (live pods as of 2026) |
| **Format** | Markdown (agent-ready context) |
| **Coverage** | 5 exam domains + practice exam |
| **Total Content** | ~16 hours of study material |

---

*This index and all referenced documents are designed to serve as comprehensive, detailed context for coding agents (Claude Code, GitHub Copilot, Cursor, etc.) when building agentic AI systems, preparing for the Anthropic Claude Certified Architect exam, or designing production-grade AI workflows.*