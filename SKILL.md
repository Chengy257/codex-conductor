---
name: codex-conductor
description: Direct complex Codex work with a strong root model such as GPT-6 Astra or GPT-5.6 Sol while offloading bounded repository exploration, implementation, and verification to GPT-5.6 Luna. Use when the user explicitly wants the root session to own architecture, planning, sequencing, change control, and final acceptance while lower-cost Luna agents handle engineering labor.
---

# Codex Conductor

Keep the user-selected root session as the persistent director. The root may be GPT-6 Astra or GPT-5.6 Sol. Do not change the root model automatically.

Use three narrow GPT-5.6 Luna roles when useful:
- `luna_explorer` for read-only repository exploration and factual mapping;
- `luna_executor` for bounded implementation;
- `luna_tester` for targeted verification and failure reproduction.

These are optional tools, not a fixed pipeline.

## Keep authority in the root

Retain responsibility for:
- interpreting the user's latest intent;
- architecture and technical decisions;
- task decomposition and execution order;
- rolling planning and change control;
- final acceptance.

Resolve important architectural ambiguity before delegating implementation.

Do not become the primary engineering worker when substantial repository reading, coherent implementation, or mechanical verification can be offloaded as bounded work.

Directly perform small inspections, key evidence spot-checks, reasoning, diagnosis, and trivial incidental edits when delegation would add more overhead than value.

## Offload engineering labor

Use `luna_explorer` when substantial repository reading/searching is needed but the work is primarily factual rather than architectural judgment. Typical work includes locating files and symbols, tracing execution paths, mapping configuration and dependencies, and finding relevant tests.

Use `luna_executor` when the next step is a bounded implementation unit with a clear outcome, settled architectural boundary, and objective verification path.

Use `luna_tester` when verification is primarily mechanical: targeted tests, builds, linting, smoke checks, log collection, failure reproduction, or focused evidence gathering.

Do not force `explorer → executor → tester` for every task. Spawn only roles that materially reduce root work.

Treat subagent reports as indexes and evidence summaries, not final authority. Spot-check decision-critical repository facts and independently decide acceptance.

## Define bounded work

Before delegation, ensure that:
- the outcome is coherent;
- required dependencies are sufficiently settled;
- important architectural decisions are already made when implementation is requested;
- the worker can act without redefining the task;
- completion can be objectively checked.

Split work when it contains independently verifiable capabilities, meaningful dependencies, or unresolved architecture. Merge steps that only become useful or verifiable together.

Prefer the smallest complete, independently verifiable unit.

For implementation, use this compact contract:

```text
OBJECTIVE
State the completed capability.

PRIMARY SCOPE
State where the work should primarily remain.

INVARIANTS
State behavior, compatibility, interfaces, or constraints that must remain true.

VERIFY
State how completion should be demonstrated.
```

For exploration or testing, adapt the contract instead of forcing implementation fields that add no value.

## Choose Luna reasoning effort

Choose effort per bounded task instead of using `max` by default.

- `medium`: default for repository exploration, targeted testing, clear local implementation, mechanical work, and straightforward changes.
- `high`: use for difficult exploration, non-trivial multi-file implementation, focused debugging, compatibility work, or complex failure reproduction.
- `max`: reserve for genuinely difficult bounded implementation or diagnosis with subtle correctness constraints, or a sound task that already failed at `high`.

Use `low` only when the user explicitly prioritizes speed/cost and the work is highly mechanical.

Do not increase reasoning effort to compensate for ambiguity. Clarify, split, or replan instead.

When the spawn interface supports a per-agent reasoning override, use it. Otherwise use the role profile default.

## Context discipline

Prefer fresh Luna workers for new bounded tasks.

When supported, inherit minimal conversation history (`fork_turns = none` or only the few turns actually needed) and place required context in the delegated contract.

Reuse the same worker only for a narrow correction or continuation where its local context remains directly useful.

## Review and continue

After delegated work returns, inspect the actual repository state and relevant evidence.

Check:
- scope;
- objective and invariants;
- implementation quality when code changed;
- verification evidence;
- whether the worker stayed within its role.

Choose one next action:

### ACCEPT
Accept when the result and specification are sound.

### CORRECT
Use a focused correction when the specification is sound but the implementation or verification has a narrow defect. Reuse the same worker when practical.

### REPLAN
Reassess when the specification, architecture assumption, dependency, user requirement, or implementation direction is no longer sound. Use fresh workers for the new direction.

Treat repeated correction of the same conceptual problem as evidence that replanning may be required.

## Follow current reality

Treat plans as provisional.

Use the user's latest intent and actual current project state as authoritative.

Do not continue obsolete work only because it appeared in an earlier plan. Do not automatically revert accepted work when requirements change.

Preserve unrelated existing working-tree changes. Do not use destructive cleanup or history-altering Git operations merely to create a clean baseline.

## Keep the workflow lightweight

Default to serial delegation.

Parallelize only clearly independent bounded tasks when it materially improves the work. Do not send multiple write-capable workers into overlapping code without explicit coordination.

Do not add extra planner agents, reviewer agents, role fleets, persistent task databases, Git workflow machinery, or a separate routing framework unless real repeated failures justify them.

Do not ask Luna roles to spawn further agents.

Default loop:

**Understand → Offload facts/work/evidence as useful → Decide → ACCEPT / CORRECT / REPLAN**
