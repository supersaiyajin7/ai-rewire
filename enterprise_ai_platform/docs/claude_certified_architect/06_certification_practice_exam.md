# Certification Practice Exam Guide

**Pod:** 6 of 6  
**Estimated Time:** ~2 hours  
**Notebooks:** 1 (auto-scoring Colab notebook)  
**Format:** Full-length 60-question practice exam mirroring real test format

---

## Overview

This is the capstone pod of the Claude Certified Architect Prep course. It provides a **full-length 60-question practice exam** that mirrors the real Anthropic Claude Certified Architect — Foundations exam format, complete with detailed answer explanations and an auto-scoring Colab notebook.

---

## Exam Format

| Aspect | Details |
|--------|---------|
| **Questions** | 60 total |
| **Format** | Mirrors real certification exam |
| **Domains Covered** | All 5 domains (weighted per exam spec) |
| **Answer Explanations** | Detailed for every question |
| **Scoring** | Auto-scoring Colab notebook included |
| **Time Limit** | ~2 hours (self-paced) |

### Domain Distribution (Approximate)

| Domain | Exam Weight | Approx. Questions |
|--------|-------------|-------------------|
| Agentic Architecture & Orchestration | 27% | ~16 |
| Tool Design & MCP Integration | ~18% | ~11 |
| Claude Code Configuration & Workflows | ~15% | ~9 |
| Prompt Engineering & Structured Output | 20% | ~12 |
| Context Management & Reliability | 15% | ~9 |
| **Total** | **100%** | **60** |

---

## What's Included

### 1. Practice Exam Questions (60 Questions)
- Multiple choice and scenario-based questions
- Covers all five exam domains
- Designed to match the difficulty and style of the real exam
- Questions test both theoretical knowledge and practical application

### 2. Detailed Answer Explanations
For each question:
- **Correct answer** with reasoning
- **Why each distractor is incorrect** — critical for understanding anti-patterns
- **Reference to source material** (which pod/article/notebook covers the concept)
- **Exam tips** for similar question types

### 3. Auto-Scoring Colab Notebook
- **Automatic grading** — paste your answers, get instant score
- **Domain-level breakdown** — see exactly which domains need review
- **Question-by-question analysis** — flagged incorrect answers with explanations
- **Readiness assessment** — probability estimate for passing the real exam
- **No manual scoring needed** — runs entirely in Colab

---

## How to Use This Practice Exam

### Recommended Approach

1. **Simulate Real Conditions**
   - Set aside 2 uninterrupted hours
   - No reference materials during the exam
   - Answer all 60 questions

2. **Score Immediately**
   - Run the Colab notebook
   - Review domain-level breakdown

3. **Deep Review (Most Important)**
   - For **every question you got wrong**: read the full explanation
   - For **questions you guessed on**: read the explanation anyway
   - Note which **pod/domain** each weak area maps to

4. **Targeted Remediation**
   - Re-read the specific article sections for weak domains
   - Re-run relevant notebooks
   - Focus on **anti-patterns** — these are heavily tested

5. **Retake (Optional)**
   - After remediation, retake the exam (or a subset)
   - Track improvement

---

## Question Types You'll Encounter

### Type 1: Code Analysis
```python
# Given this agentic loop implementation, what's the bug?
while True:
    response = client.messages.create(...)
    if "done" in response.text:  # Anti-pattern!
        break
```
**Tests:** Anti-pattern recognition (natural language parsing vs `stop_reason`)

### Type 2: Architecture Decision
> "You're building a customer support agent with 15 tools. The agent frequently selects the wrong tool. What's the best fix?"
- A) Add more detailed system prompt
- B) Split into 3 specialized agents with 4-5 tools each (Correct)
- C) Increase model temperature
- D) Add more examples to tool descriptions

**Tests:** Tool distribution principle (4-5 tools per agent)

### Type 3: Error Handling Scenario
> "A tool returns `{'isError': true, 'content': 'Failed'}`. The agent retries 3 times and fails. What's missing from the error response?"
**Tests:** Structured error responses (errorCategory, isRetryable, customerMessage)

### Type 4: Compliance Enforcement
> "A financial agent must verify identity before processing refunds. Which approach guarantees compliance?"
- A) Add "Always verify identity first" to system prompt
- B) Implement PreToolUse hook that blocks refund tools without verification flag (Correct)
- C) Use tool_choice to force verify_identity tool
- D) Add validation in the refund tool implementation

**Tests:** Hooks for guaranteed compliance vs prompts for guidance

### Type 5: Session Management
> "You resume a coding session from yesterday. Several files have been modified. What must you do?"
**Tests:** Stale context handling — inform agent of file changes

### Type 6: MCP Configuration
> "Where should shared team MCP servers (Jira, GitHub) be configured? Where should personal experimental servers go?"
**Tests:** Project-level `.mcp.json` vs user-level `~/.claude.json`

---

## Auto-Scoring Colab Notebook Features

### Input
```python
# Paste your answers as a list
my_answers = ['A', 'B', 'C', 'D', 'A', ...]  # 60 answers
```

### Output
```python
# Comprehensive results
results = {
    "overall_score": "85% (51/60)",
    "pass_probability": "High",
    "domain_breakdown": {
        "Agentic Architecture": "90% (14/16)",
        "Tool Design": "73% (8/11)",
        "Claude Code Workflows": "89% (8/9)",
        "Prompt Engineering": "92% (11/12)",
        "Context Management": "78% (7/9)"
    },
    "incorrect_questions": [
        {"question": 7, "your_answer": "B", "correct": "A", "domain": "Tool Design"},
        {"question": 23, "your_answer": "D", "correct": "C", "domain": "Agentic Architecture"},
        # ...
    ],
    "recommended_review": [
        "Pod 2: Structured error responses (errorCategory, isRetryable)",
        "Pod 1: Hook types (PreToolUse vs PostToolUse)",
        # ...
    ]
}
```

---

## Study Strategy Based on Practice Exam Results

### If You Score ≥ 85% Overall
- **Ready for real exam**
- Light review of incorrect questions only
- Focus on exam-day logistics

### If You Score 70-84%
- **Targeted review needed**
- Identify 1-2 weakest domains
- Re-read those pod articles + re-run notebooks
- Retake practice exam after 1-2 days

### If You Score < 70%
- **Significant gaps exist**
- Full review of all 5 pods recommended
- Focus on anti-patterns checklists
- Complete all notebooks hands-on before retaking

---

## Domain-Specific Review Priorities

### Agentic Architecture (27% — Highest Priority)
| Topic | Review If Weak On... |
|-------|---------------------|
| `stop_reason` control flow | Questions about loop termination |
| Hub-and-spoke coordination | Multi-agent delegation questions |
| Subagent context isolation | Questions about passing history to subagents |
| Hook types (Pre/Post) | Compliance enforcement questions |
| Dynamic vs fixed decomposition | Workflow strategy questions |
| `--resume` vs `fork_session` | Session management scenarios |

### Tool Design (18%)
| Topic | Review If Weak On... |
|-------|---------------------|
| 5-question description framework | Tool selection questions |
| 4 error categories | Error handling scenarios |
| 4-5 tools per agent limit | Architecture/distribution questions |
| `tool_choice` modes | Forced selection questions |
| MCP config levels | Credential/secrets questions |
| Built-in tool selection | Codebase exploration questions |

### Prompt Engineering (20%)
| Topic | Review If Weak On... |
|-------|---------------------|
| Explicit criteria | Evaluation/rubric questions |
| Few-shot patterns | Example formatting questions |
| Tool use schemas | Schema validation questions |
| Validation-retry loops | Self-correction questions |
| Batch API | Cost/throughput optimization questions |

### Context Management (15%)
| Topic | Review If Weak On... |
|-------|---------------------|
| Context window optimization | Token budget questions |
| Escalation criteria | Handoff protocol questions |
| Crash recovery | Checkpoint/restart questions |
| Information provenance | Audit trail questions |

### Claude Code Workflows (15%)
| Topic | Review If Weak On... |
|-------|---------------------|
| Configuration hierarchy | Settings precedence questions |
| Custom commands | Command definition questions |
| Execution strategies | Parallel vs sequential questions |
| CI/CD patterns | Automation pipeline questions |

---

## Anti-Patterns Quick Reference (Exam Day)

### Memorize These 6 Agentic Architecture Anti-Patterns
1. **Natural language loop termination** → Use `stop_reason`
2. **Arbitrary iteration caps as primary control** → Safety net only
3. **Full history to subagents** → Isolated context only
4. **Over-decomposition** → Meaningful subtasks, not atomic
5. **Prompt-based hard compliance** → Hooks/gates for guarantees
6. **Resume stale without updates** → Inject file change summary

### Memorize These 8 Tool Design Anti-Patterns
1. **Vague descriptions** → "Retrieves information" 
2. **Overlapping names** → `analyze_content` / `analyze_document`
3. **Uniform errors** → "Operation failed"
4. **Retrying non-retryable** → Business errors fail every time
5. **Too many tools/agent** → >5 degrades selection
6. **Generic > constrained** → `fetch_url` vs `load_document`
7. **Secrets in .mcp.json** → Use `${ENV_VAR}` expansion
8. **Read all files upfront** → Grep → Read → Trace

---

## Practice Exam Notebook Access

The auto-scoring Colab notebook is available in the course materials. It includes:

1. **Answer key** with explanations (hidden until you run scoring)
2. **Scoring function** — pass your answers list, get full report
3. **Visualization** — domain radar chart, question-level heatmap
4. **Export** — save results as JSON for tracking progress

### Running the Notebook
```bash
# In Colab:
# 1. Upload the notebook
# 2. Run all cells
# 3. Paste your answers in the designated cell
# 4. Run scoring cell
```

---

## Final Exam Day Checklist

### Technical Knowledge
- [ ] Can write a correct agentic loop with `stop_reason` handling
- [ ] Can design hub-and-spoke multi-agent with proper context isolation
- [ ] Can implement PreToolUse/PostToolUse hooks for compliance
- [ ] Can write 5-question tool descriptions with boundaries
- [ ] Can structure error responses with 4 categories + retry guidance
- [ ] Know 4-5 tools per agent rule and scoped distribution
- [ ] Understand `tool_choice`: auto, any, forced
- [ ] Know `.mcp.json` vs `~/.claude.json` and `${ENV_VAR}` secrets
- [ ] Can select correct built-in tool (Grep/Glob/Read/Write/Edit)
- [ ] Know incremental codebase exploration (Grep → Read → Trace)

### Exam Strategy
- [ ] Read every question carefully — watch for "NOT", "EXCEPT", "BEST"
- [ ] Eliminate obviously wrong answers first
- [ ] Anti-pattern questions: identify the violation, then find the answer that fixes it
- [ ] Scenario questions: map to the relevant pod/domain concept
- [ ] Code questions: trace execution mentally, watch for anti-patterns
- [ ] Time management: ~2 minutes per question, flag and return

### Mental Preparation
- [ ] Review anti-patterns checklists the night before
- [ ] Get adequate sleep — this exam tests reasoning, not memorization
- [ ] Trust your preparation — the practice exam is calibrated to the real thing

---

## Related Resources

- **Pod 1:** [Agentic Architecture & Orchestration](./01_agentic_architecture_orchestration.md)
- **Pod 2:** [Tool Design & MCP Integration](./02_tool_design_mcp_integration.md)
- **Pod 3:** [Claude Code Configuration & Workflows](./03_claude_code_workflows.md)
- **Pod 4:** [Prompt Engineering & Structured Output](./04_prompt_engineering_structured_output.md)
- **Pod 5:** [Context Management & Reliability](./05_context_management_reliability.md)
- **Course Overview:** [Claude Certified Architect Prep](./00_course_overview.md)

---

## Practice Exam Metadata

| Field | Value |
|-------|-------|
| **Source** | Vizuara AI Pods — Claude Certified Architect Prep |
| **Curator** | Dr. Rajat Dandekar |
| **Format** | 60 questions, multiple choice + scenario |
| **Scoring** | Auto-scoring Colab notebook |
| **Explanations** | Detailed for all 60 questions |
| **Difficulty** | Matches real certification exam |
| **Last Updated** | 2026-08-03 |

---

*Good luck on your certification journey! The practice exam is your best predictor of readiness. Use it wisely, review deeply, and you'll be well-prepared for the real exam.*

*Source: Vizuara AI Pods — Claude Certified Architect Prep Course, Pod 6: Certification Practice Exam*