---
rule_type: meta
applies_to:
  - "~/.claude/rules/*.md"
  - "project/.claude/rules/*.md"
triggers:
  - event: "rule_create"
    description: "When creating a new rule file"
  - event: "rule_update"
    description: "When modifying an existing rule file"
---

# Rule File Format Standard

The format standard to follow when writing rule files.

---

## 🔴 Required Actions (Action Required)

> **MUST DO**: Follow the format below when creating/modifying rule files.

### When Creating a Rule File (on-create)

| Check | Action |
|-------|--------|
| File type classification | Choose from workflow / reference / meta |
| Write Frontmatter | Define rule_type, applies_to, triggers |
| Check linked skills | If related skills/agents exist, write Linked Skills table |

### When Modifying a Rule File (on-update)

| Check | Action |
|-------|--------|
| Format validation | Run `/rule-validator` to verify format compliance |

---

## Linked Skills

<!-- @linked-skills -->

| Skill | Trigger Condition | Execution Mode | Description |
|-------|-------------------|:--------------:|-------------|
| `/rule-validator` | When creating/modifying rule files | confirm | Format validation and conversion |

<!-- @/linked-skills -->

---

## 1. Rule File Types (rule_type)

| Type | Description | Frontmatter Required | Linked Skills Table |
|------|-------------|:--------------------:|:-------------------:|
| **workflow** | Defines behavior/procedures (has execution order) | ✅ Required | ✅ Required |
| **reference** | Reference information (conventions, guides) | ⚠️ Recommended | ⚠️ Optional |
| **meta** | Rules about rules | ✅ Required | ✅ Required |

### Characteristics by Type

```
workflow:  "Do it this way" → Requires behavior triggers
reference: "Refer to this" → Provides information
meta:      "Write rules this way" → Meta rules
```

---

## 2. Frontmatter Structure

### Required Fields

```yaml
---
rule_type: workflow | reference | meta
applies_to:
  - "Target pattern or situation"
triggers:
  - event: "event_name"
    description: "description"
---
```

### Field Descriptions

| Field | Required | Description |
|-------|:--------:|-------------|
| `rule_type` | ✅ | Rule type (workflow/reference/meta) |
| `applies_to` | ✅ | Target scope (file patterns, situation descriptions) |
| `triggers` | ⚠️ | Trigger events (required only for workflow/meta) |

### Trigger Event Examples

| Event | Description |
|-------|-------------|
| `plan_execute` | When executing a plan file |
| `plan_created` | When plan file creation is complete |
| `code_commit` | Before code commit |
| `file_create` | When creating a file |
| `file_modify` | When modifying a file |
| `server_start` | When server start is requested |
| `test_write` | When writing tests |
| `doc_write` | When writing documentation |
| `code_review` | When reviewing code |

---

## 3. Required Actions Section

Must be included for workflow/meta types:

```markdown
## 🔴 Required Actions (Action Required)

> **MUST DO**: You must perform the following actions whenever this rule applies.

### {Situation} ({event name})

| Check | Condition | Action |
|-------|-----------|--------|
| {What to check} | {condition} | {action to perform} |
```

### Writing Guidelines

- Use `🔴` emoji for visual emphasis
- Use `> **MUST DO**` blockquote to indicate mandatory nature
- Structure with tables for clear action directives

---

## 4. Linked Skills Table

When integration with skills/agents is needed:

```markdown
## Linked Skills

<!-- @linked-skills -->

| Skill | Trigger Condition | Execution Mode | Description |
|-------|-------------------|:--------------:|-------------|
| `/skill-name` | condition | auto/confirm/ask | description |
| `agent-name` | condition | auto/confirm/ask | description |

<!-- @/linked-skills -->
```

### Execution Modes

| Mode | Description |
|------|-------------|
| `auto` | Execute automatically when conditions are met |
| `confirm` | Ask the user whether to execute when conditions are met (include recommended message) |
| `ask` | Ask the user whether it is needed |

### Marker Tags

```markdown
<!-- @linked-skills -->
...table...
<!-- @/linked-skills -->
```

- `/rule-validator` recognizes these markers for validation
- Extracts skill integration info in a parseable structure

---

## 5. Document Structure

### workflow Type

```markdown
---
(Frontmatter)
---

# Rule Title

Description...

---

## 🔴 Required Actions (Action Required)
(required)

---

## Linked Skills
(required)

---

## Detailed Content
...

---

*Related files/docs*: ...
*Last modified*: YYYY-MM-DD
```

### reference Type

```markdown
---
(Frontmatter - optional)
---

# Rule Title

Description...

---

## Content Sections
...

---

## Linked Skills
(optional - add if a validation agent exists)

---

*Related files/docs*: ...
```

---

## 6. Examples

### workflow Example (environment-setup.md)

```yaml
---
rule_type: workflow
applies_to:
  - "Server start/stop"
  - "Development environment setup"
triggers:
  - event: "server_start"
    description: "When server start is requested"
---
```

### reference Example (naming-conventions.md)

```yaml
---
rule_type: reference
applies_to:
  - "*.kt file creation"
  - "Class/method naming"
---
```

---

## 7. Validation Checklist

Verify when writing/modifying rule files:

- [ ] Frontmatter included (required for workflow/meta)
- [ ] rule_type specified
- [ ] applies_to specified
- [ ] triggers specified (workflow/meta)
- [ ] Required Actions section included (workflow/meta)
- [ ] Linked Skills table included (when skill integration exists)
- [ ] `<!-- @linked-skills -->` markers used

---

*This rule is referenced when writing any rule file.*
*Last modified: 2026-02-05*
