# Claude Code Configuration & Workflows

**Pod:** 3 of 6  
**Domain Weight:** ~15% of exam  
**Estimated Time:** ~3 hours  
**Notebooks:** 4  
**Status:** Live

---

## Overview

Master the layered configuration hierarchy, custom commands, execution strategies, and CI/CD patterns that turn Claude Code from a generic assistant into a team-aligned development partner.

This domain covers how to configure, customize, and operationalize Claude Code for production team environments.

---

## 1. Layered Configuration Hierarchy

### Configuration Layers (Priority Order: Highest → Lowest)

| Layer | File/Location | Scope | Use For |
|-------|--------------|-------|---------|
| **1. CLI Flags** | `--flag` at runtime | Per-command | Overrides, one-off changes |
| **2. Project Settings** | `.claude/settings.json` | Project (committed) | Team-shared config, tool permissions |
| **3. Project Local** | `.claude/settings.local.json` | Project (gitignored) | Local overrides, secrets, machine-specific |
| **4. User Settings** | `~/.claude/settings.json` | User (global) | Personal preferences, global tools |
| **5. Defaults** | Built-in | System | Fallback values |

### Settings File Structure

```json
// .claude/settings.json (project-level, committed)
{
  "permissions": {
    "allow": [
      "Bash(git:*)",
      "Bash(npm:*)",
      "Read(**)",
      "Write(**)",
      "Edit(**)",
      "Glob(**)",
      "Grep(**)"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(sudo:*)"
    ],
    "ask": [
      "Bash(*:*)"
    ]
  },
  "model": "claude-sonnet-4-20250514",
  "maxTokens": 8192,
  "hooks": {
    "PreToolUse": [
      {"matcher": "Bash", "command": "echo 'Running: $TOOL_INPUT'"}
    ],
    "PostToolUse": [
      {"matcher": "Edit", "command": "git diff"}
    ]
  },
  "env": {
    "NODE_ENV": "development"
  }
}
```

```json
// .claude/settings.local.json (project-level, gitignored)
{
  "permissions": {
    "allow": [
      "Bash(docker:*)"
    ]
  },
  "env": {
    "DATABASE_URL": "postgresql://localhost:5432/myapp",
    "API_KEY": "${API_KEY}"
  }
}
```

### Configuration Merging Rules

1. **Arrays merge by concatenation** (allow/deny/ask lists)
2. **Objects merge deeply** (hooks, env)
3. **Primitive values override** (model, maxTokens)
4. **CLI flags always win** over file settings

---

## 2. Custom Commands

### Command Definition

Custom commands live in `.claude/commands/` as Markdown files with frontmatter.

**File:** `.claude/commands/feature-review.md`

```markdown
---
name: feature-review
description: Comprehensive feature branch review
arguments:
  - name: branch
    description: Branch to review (default: current)
    required: false
  - name: base
    description: Base branch to compare against
    default: main
---

# Feature Review: {{branch}} vs {{base}}

Please perform a thorough code review of the changes in `{{branch}}` compared to `{{base}}`.

## Review Checklist

### Correctness
- [ ] No logic bugs or off-by-one errors
- [ ] Edge cases handled (empty, null, boundary)
- [ ] Error handling is appropriate and consistent

### Security
- [ ] No SQL injection, XSS, or path traversal vulnerabilities
- [ ] Secrets not hardcoded
- [ ] Input validation on all external data

### Performance
- [ ] No N+1 queries or unnecessary loops
- [ ] Appropriate caching strategy
- [ ] Database indexes for new queries

### Maintainability
- [ ] Clear naming and consistent style
- [ ] Adequate test coverage
- [ ] Documentation updated

## Output Format

Provide your review as:
1. **Summary** (2-3 sentences)
2. **Critical Issues** (must fix before merge)
3. **Suggestions** (nice to have)
4. **Approval** (Approve / Request Changes)
```

### Using Custom Commands

```bash
# Run the command
/feature-review --branch feature/auth-refactor --base main

# Or with current branch
/feature-review
```

### Command Discovery

- Commands auto-discovered from `.claude/commands/**/*.md`
- Subdirectories create namespaces: `.claude/commands/git/rebase.md` → `/git:rebase`
- Tab completion works in Claude Code

---

## 3. Execution Strategies

### Serial vs Parallel Execution

| Strategy | Use Case | Configuration |
|----------|----------|---------------|
| **Serial** | Dependent steps, shared state | Default |
| **Parallel** | Independent tasks, max throughput | `execution: "parallel"` |
| **Pipeline** | Streaming, staged processing | `execution: "pipeline"` |

### Parallel Execution Example

```json
// .claude/settings.json
{
  "execution": {
    "strategy": "parallel",
    "maxConcurrency": 4,
    "queueDepth": 10
  }
}
```

### Subagent Execution Patterns

```python
# Pattern 1: Fire-and-forget parallel subagents
results = await asyncio.gather(*[
    run_subagent(task) for task in tasks
])

# Pattern 2: Pipeline with stages
stage1_results = await asyncio.gather(*[stage1(t) for t in tasks])
stage2_results = await asyncio.gather(*[stage2(r) for r in stage1_results])

# Pattern 3: Map-reduce
partial_results = await asyncio.gather(*[map_fn(item) for item in items])
final_result = reduce_fn(partial_results)
```

### Execution Strategy Selection

| Scenario | Strategy |
|----------|----------|
| Code review multiple files | Parallel (independent) |
| Refactor with dependent changes | Serial |
| Large batch processing | Pipeline (streaming) |
| Exploratory analysis | Parallel (fork_session) |
| CI/CD pipeline stages | Pipeline |

---

## 4. CI/CD Integration Patterns

### GitHub Actions Integration

```yaml
# .github/workflows/claude-code-review.yml
name: Claude Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  claude-review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Setup Claude Code
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
      
      - name: Run Custom Review Command
        run: |
          claude-code /feature-review --branch ${{ github.head_ref }} --base ${{ github.base_ref }}
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      
      - name: Post Review Comment
        uses: actions/github-script@v7
        with:
          script: |
            // Post the review output as PR comment
```

### Pre-commit Hooks

```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: claude-lint
        name: Claude Code Lint
        entry: claude-code /lint
        language: system
        types: [python, javascript, typescript]
        pass_filenames: true

      - id: claude-test
        name: Claude Generate Tests
        entry: claude-code /generate-tests
        language: system
        types: [python]
        stages: [pre-push]
```

### Automated Issue Triage

```yaml
# .github/workflows/triage.yml
name: Issue Triage

on:
  issues:
    types: [opened]

jobs:
  triage:
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@v1
        with:
          prompt: |
            Analyze this GitHub issue and:
            1. Assign appropriate labels
            2. Determine priority (P0-P3)
            3. Suggest assignee based on code ownership
            4. Check for duplicates
            
            Issue: ${{ github.event.issue.title }}
            Body: ${{ github.event.issue.body }}
```

---

## 5. Team Alignment Patterns

### Shared Configuration Repository

```
team-claude-config/
├── settings.json          # Base team settings
├── commands/
│   ├── code-review.md
│   ├── generate-tests.md
│   ├── refactor.md
│   └── security-audit.md
├── hooks/
│   ├── pre-commit.sh
│   └── post-merge.sh
└── templates/
    ├── pr-template.md
    └── issue-template.md
```

**Usage:** Each project includes as git submodule or copies relevant files.

### Configuration Inheritance

```json
// Project .claude/settings.json
{
  "extends": ["team-config:base"],
  "permissions": {
    "allow": ["Bash(project-specific:*)"]
  }
}
```

### Role-Based Configurations

```json
// settings.developer.json
{
  "permissions": {
    "allow": ["Read", "Write", "Edit", "Bash(git:*)", "Bash(npm:*)"]
  }
}

// settings.tech-lead.json
{
  "permissions": {
    "allow": ["*", "Bash(docker:*)", "Bash(kubectl:*)"]
  }
}

// settings.security.json
{
  "permissions": {
    "allow": ["Read", "Grep", "Glob"],
    "deny": ["Write", "Edit", "Bash(*)"]
  }
}
```

---

## 6. Advanced Workflow Patterns

### Multi-Repo Coordination

```python
# Orchestrate changes across multiple repositories
async def coordinated_refactor(repos: list[str], task: str):
    # Create worktrees for each repo
    worktrees = await asyncio.gather(*[
        create_worktree(repo, f"refactor-{task}") for repo in repos
    ])
    
    # Run parallel subagents in each worktree
    results = await asyncio.gather(*[
        run_subagent_in_worktree(wt, task) for wt in worktrees
    ])
    
    # Aggregate results and create PRs
    prs = await asyncio.gather(*[
        create_pr(wt, result) for wt, result in zip(worktrees, results)
    ])
    
    return prs
```

### Progressive Enhancement Workflow

```
1. Analyze (read-only)     → /analyze-codebase
2. Plan (no changes)       → /plan-refactor
3. Prototype (sandbox)     → /prototype-solution
4. Implement (staged)      → /implement --staged
5. Verify (tests + lint)   → /verify
6. Review (team)           → /feature-review
7. Merge (automated)       → /auto-merge
```

### Incident Response Workflow

```markdown
---
name: incident-response
description: Rapid incident analysis and mitigation
arguments:
  - name: service
    required: true
  - name: severity
    required: true
---

# Incident Response: {{service}} (Severity: {{severity}})

## Immediate Actions (0-5 min)
- [ ] Check service health dashboard
- [ ] Review recent deployments
- [ ] Check error rates and latency

## Diagnosis (5-15 min)
- [ ] Analyze logs: `/analyze-logs --service {{service}} --since 1h`
- [ ] Check dependencies: `/check-dependencies --service {{service}}`
- [ ] Identify root cause hypothesis

## Mitigation (15-30 min)
- [ ] If rollback needed: `/rollback --service {{service}}`
- [ ] If config change: `/hotfix-config --service {{service}}`
- [ ] If capacity: `/scale-up --service {{service}}`

## Communication
- [ ] Update incident channel
- [ ] Notify stakeholders
- [ ] Document timeline
```

---

## 7. Configuration Best Practices

### DO ✅

| Practice | Why |
|----------|-----|
| Commit `.claude/settings.json` | Team shares base config |
| Gitignore `.claude/settings.local.json` | Secrets, machine-specific stays local |
| Use `${ENV_VAR}` for secrets | Never commit actual secrets |
| Version custom commands | Track changes, enable collaboration |
| Document command purpose in frontmatter | Discoverability, self-documenting |
| Test commands before sharing | Prevent broken workflows |
| Use namespaces for command organization | Avoid collisions (`git:`, `deploy:`, `test:`) |

### DON'T ❌

| Anti-Pattern | Consequence |
|--------------|-------------|
| Commit secrets in settings | Security breach |
| Override everything in user settings | Team inconsistency |
| Create commands with side effects in read-only | Unexpected mutations |
| Hardcode paths in commands | Breaks on different machines |
| Skip command testing | Broken workflows for team |
| Use global allow `Bash(*)` | Security risk |

---

## 8. Troubleshooting Common Issues

### Command Not Found
```bash
# Check command discovery
claude-code /help  # Lists all available commands

# Verify file location
ls .claude/commands/
ls ~/.claude/commands/
```

### Permission Denied
```bash
# Check effective permissions
claude-code /permissions

# Debug specific tool
claude-code --debug "Bash(ls)"
```

### Configuration Not Loading
```bash
# Verify config hierarchy
claude-code /config:show

# Check for syntax errors
cat .claude/settings.json | jq .
```

### Hook Failures
```json
// Add debugging to hooks
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "echo 'DEBUG: $TOOL_NAME $TOOL_INPUT' >> /tmp/claude-hooks.log"
      }
    ]
  }
}
```

---

## 9. Exam Focus Areas

### Key Concepts to Master

1. **Configuration Hierarchy** — 5 layers, merge rules, precedence
2. **Custom Commands** — Frontmatter, arguments, namespaces, discovery
3. **Execution Strategies** — Serial, parallel, pipeline, when to use each
4. **CI/CD Integration** — GitHub Actions, pre-commit, issue triage
4. **Team Alignment** — Shared configs, role-based, inheritance
5. **Advanced Patterns** — Multi-repo, progressive enhancement, incident response
6. **Security** — Permissions model, allow/deny/ask, least privilege
7. **Troubleshooting** — Debug commands, permission issues, config loading

### Common Exam Questions

| Question Type | Example |
|---------------|---------|
| Config precedence | "User settings has `model: opus`, project has `model: sonnet`, CLI passes `--model haiku`. Which wins?" |
| Command arguments | "How do you make a branch argument optional with default 'main'?" |
| Execution strategy | "You need to analyze 50 independent files. Which execution strategy?" |
| CI/CD pattern | "How do you run a custom command on every PR?" |
| Permission model | "What's the difference between `deny` and `ask`?" |
| Security | "Why shouldn't you use `allow: [\"Bash(*)\"]` in team settings?" |

---

## Quick Reference

### Config Files
```
.claude/
├── settings.json          # Project (committed)
├── settings.local.json    # Project (gitignored)
├── commands/              # Custom commands
│   ├── *.md
│   └── namespace/*.md
└── hooks/                 # Hook scripts (optional)
```

### Command Frontmatter
```yaml
---
name: command-name
description: One-line description
arguments:
  - name: arg-name
    description: What it does
    required: true/false
    default: "value"
---
```

### Permissions Syntax
```json
{
  "permissions": {
    "allow": ["Tool(pattern)", "Tool(*)"],
    "deny": ["Tool(dangerous:*)"],
    "ask": ["Tool(*)"]
  }
}
```

### Execution Strategies
```json
{
  "execution": {
    "strategy": "serial|parallel|pipeline",
    "maxConcurrency": 4,
    "queueDepth": 10
  }
}
```

---

## Related Resources

- **Previous:** [Tool Design & MCP Integration](./02_tool_design_mcp_integration.md)
- **Next:** [Prompt Engineering & Structured Output](./04_prompt_engineering_structured_output.md)
- **Course Overview:** [Claude Certified Architect Prep](./00_course_overview.md)

---

*Source: Vizuara AI Pods — Claude Certified Architect Prep Course, Pod 3: Claude Code Configuration & Workflows (derived from domain description and exam specifications)*