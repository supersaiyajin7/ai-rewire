# Claude Certified Architect Prep — Course Overview

**Course:** Vizuara AI Pods — Claude Certified Architect Prep  
**Difficulty:** Intermediate  
**Total Estimated Time:** ~16 hours  
**Structure:** 6 Pods (all live) | 22 Notebooks | 1 Practice Exam

---

## Course Description

Master the five domains of the Anthropic Claude Certified Architect — Foundations exam with hands-on practice and a full-length practice test.

**Exam Domains Covered:**
1. **Agentic Architecture & Orchestration** (27% — largest domain)
2. **Tool Design & MCP Integration**
3. **Claude Code Configuration & Workflows**
4. **Prompt Engineering & Structured Output** (20%)
5. **Context Management & Reliability** (15%)

---

## Pods in This Course

### Pod 1: Agentic Architecture & Orchestration ⭐ (Largest Domain: 27%)
- **Estimated Time:** ~3 hours
- **Notebooks:** 5
- **Status:** ✅ Live
- **Key Topics:**
  - Agentic loop lifecycle and `stop_reason` control flow
  - Multi-agent coordinator patterns (hub-and-spoke)
  - Subagent invocation via Task tool with isolated context
  - Multi-step workflows and programmatic compliance enforcement
  - Agent SDK hooks (PreToolUse, PostToolUse) for guaranteed compliance
  - Task decomposition: fixed pipelines vs dynamic adaptive
  - Session management: `--resume`, `fork_session`, stale context handling

### Pod 2: Tool Design & MCP Integration
- **Estimated Time:** ~3 hours
- **Notebooks:** 4
- **Status:** ✅ Live
- **Key Topics:**
  - Tool descriptions as primary selection signal (5-question framework)
  - Renaming and splitting overlapping tools
  - System prompt keyword trap avoidance
  - Structured error responses with `isError` flag and 4 error categories
  - Local vs propagated error recovery in multi-agent systems
  - Tool distribution: 4-5 tools per agent, scoped by role
  - `tool_choice` configuration: auto, any, forced selection
  - MCP server config: project-level (`.mcp.json`) vs user-level (`~/.claude.json`)
  - MCP resources for read-only data discovery
  - Community vs custom MCP servers
  - Making MCP tools preferred over built-in tools
  - Built-in tools: Grep, Glob, Read, Write, Edit — incremental codebase exploration

### Pod 3: Claude Code Configuration & Workflows
- **Estimated Time:** ~3 hours
- **Notebooks:** 4
- **Status:** ✅ Live
- **Key Topics:**
  - Layered configuration hierarchy
  - Custom commands and execution strategies
  - CI/CD patterns for team-aligned development
  - Configuration management best practices
  - Workflow automation patterns

### Pod 4: Prompt Engineering & Structured Output
- **Estimated Time:** ~3 hours
- **Notebooks:** 4
- **Status:** ✅ Live
- **Exam Weight:** 20%
- **Key Topics:**
  - Explicit criteria and few-shot prompting
  - Tool use schemas and validation-retry loops
  - Batch API usage
  - Structured output patterns

### Pod 5: Context Management & Reliability
- **Estimated Time:** ~2 hours
- **Notebooks:** 4
- **Status:** ✅ Live
- **Exam Weight:** 15%
- **Key Topics:**
  - Context window limits and optimization
  - Escalation criteria and patterns
  - Crash recovery strategies
  - Information provenance tracking

### Pod 6: Certification Practice Exam
- **Estimated Time:** ~2 hours
- **Notebooks:** 1 (auto-scoring Colab notebook)
- **Status:** ✅ Live
- **Format:** Full-length 60-question practice exam mirroring real test format
- **Features:** Detailed answer explanations, auto-scoring Colab notebook

---

## Course Progress Tracking

```
Overall Progress: 1/6 pods complete (17%)
████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
```

**Free Access:** This entire course is free — all 6 pods, 22 notebooks, and the practice exam. No subscription required. Just log in to start.

---

## Learning Path Structure

Each pod follows the **FPR Technique** (Fundamentals, Practicals, Research):

```
Article (Fundamentals) → Notebooks 1-5 (Practicals) → Certificate
```

| Phase | Component | Purpose |
|-------|-----------|---------|
| **1** | **Article** | Comprehensive explanation with figures, equations, code examples |
| **2** | **Notebooks** | Hands-on Colab notebooks (~5 hours total per pod) |
| **3** | **Certificate** | Download and share achievement |

---

## Domain Weight Distribution

| Domain | Exam Weight | Pod | Status |
|--------|-------------|-----|--------|
| Agentic Architecture & Orchestration | 27% | Pod 1 | ✅ Live |
| Tool Design & MCP Integration | ~18% | Pod 2 | ✅ Live |
| Claude Code Configuration & Workflows | ~15% | Pod 3 | ✅ Live |
| Prompt Engineering & Structured Output | 20% | Pod 4 | ✅ Live |
| Context Management & Reliability | 15% | Pod 5 | ✅ Live |
| **Practice Exam** | N/A | Pod 6 | ✅ Live |

---

## Recommended Study Order

1. **Start with Pod 1** (Agentic Architecture) — largest domain at 27%, foundational concepts
2. **Pod 2** (Tool Design) — critical for reliable tool selection and error handling
3. **Pod 3** (Claude Code Workflows) — practical configuration and team patterns
4. **Pod 4** (Prompt Engineering) — 20% of exam, structured output techniques
5. **Pod 5** (Context Management) — 15% of exam, reliability patterns
6. **Pod 6** (Practice Exam) — full-length 60-question test with auto-scoring

---

## Key Concepts Map

### Agentic Architecture (Pod 1)
```
Agentic Loop → Multi-Agent Coordination → Task Tool → Compliance → Hooks → Decomposition → Session Mgmt
```

### Tool Design (Pod 2)
```
Descriptions → Errors → Distribution → tool_choice → MCP Config → Resources → Built-ins
```

### Cross-Cutting Concerns
- **Deterministic vs Probabilistic:** Hooks/gates for compliance, prompts for guidance
- **Isolation:** Subagent context isolation, scoped tool access
- **Incremental Understanding:** Grep → Read → Trace (not read everything upfront)
- **Structured Data:** Every tool response, error, handoff should be structured

---

## Exam Preparation Strategy

| Phase | Activity | Time Investment |
|-------|----------|-----------------|
| **Foundation** | Read all 5 articles thoroughly | ~5-6 hours |
| **Hands-On** | Complete all 22 notebooks | ~10-12 hours |
| **Practice** | Take full practice exam (Pod 6) | ~2 hours |
| **Review** | Focus on weak areas from practice exam | ~2-3 hours |
| **Total** | | **~19-23 hours** |

---

## Critical Exam Anti-Patterns (Consolidated)

### Agentic Architecture (Pod 1)
- [ ] Parsing natural language for loop termination instead of `stop_reason`
- [ ] Arbitrary iteration caps as primary stopping mechanism
- [ ] Passing coordinator's full conversation history to subagents
- [ ] Over-decomposition into too many tiny subagents
- [ ] Prompt-based guidance for hard compliance requirements
- [ ] Resuming stale sessions without informing about file changes

### Tool Design (Pod 2)
- [ ] Vague tool descriptions ("Retrieves information")
- [ ] Overlapping tool names (`analyze_content` vs `analyze_document`)
- [ ] Uniform error messages ("Operation failed")
- [ ] Retrying non-retryable errors (business rule denials)
- [ ] Too many tools per agent (>5)
- [ ] Generic tools where constrained ones work (`fetch_url` vs `load_document`)
- [ ] Committing secrets in `.mcp.json` (use `${ENV_VAR}`)
- [ ] Reading all files upfront (use Grep first)

---

## File Structure for This Course

```
enterprise_ai_platform/docs/claude_certified_architect/
├── 00_course_overview.md                    # This file
├── 01_agentic_architecture_orchestration.md # Pod 1 - Domain 1 (27%)
├── 02_tool_design_mcp_integration.md        # Pod 2 - Domain 2
├── 03_claude_code_workflows.md              # Pod 3 - Domain 3
├── 04_prompt_engineering_structured_output.md # Pod 4 - Domain 4 (20%)
├── 05_context_management_reliability.md     # Pod 5 - Domain 5 (15%)
└── 06_certification_practice_exam.md        # Pod 6 - Practice Exam
```

---

## How to Use These Materials

### As Context for Coding Agents

These markdown files are designed to be **detailed enough to serve as context** for any coding agent (Claude Code, GitHub Copilot, Cursor, etc.) when building:

- **Agentic systems** — reference Pod 1 for loop patterns, multi-agent coordination, hooks
- **Tool interfaces** — reference Pod 2 for descriptions, error structures, MCP config
- **Claude Code workflows** — reference Pod 3 for configuration, custom commands, CI/CD
- **Prompt engineering** — reference Pod 4 for structured output, validation loops
- **Context management** — reference Pod 5 for window limits, recovery, provenance

### For Exam Preparation

1. Read the detailed markdown for each pod (more comprehensive than articles)
2. Work through the Colab notebooks hands-on
3. Take the practice exam (Pod 6) to identify gaps
4. Review anti-patterns checklists before exam

### For Production System Design

Use these as **architectural reference documents** when:
- Designing multi-agent systems (hub-and-spoke patterns, subagent isolation)
- Building tool interfaces (description templates, error taxonomies)
- Configuring MCP servers (project vs user, resource exposure)
- Implementing compliance (hooks vs prompts, structured handoffs)
- Managing sessions (resume, fork, stale context handling)

---

## Related Resources

- **Official Course:** https://pods.vizuara.ai/courses/claude-certified-architect
- **Vizuara AI Pods:** https://pods.vizuara.ai/
- **Anthropic Certification:** https://www.anthropic.com/certification

---

*Source: Vizuara AI Pods — Claude Certified Architect Prep Course Overview Page*
*Last Updated: 2026-08-03*