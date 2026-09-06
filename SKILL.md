---
name: sol-conductor
description: Supervise bounded Codex implementation with a strong root model such as GPT-6 Astra or GPT-5.6 Sol while delegating execution to GPT-5.6 Luna. Use when the user explicitly wants the root session to own architecture, planning, sequencing, change control, and acceptance while Luna performs bounded implementation work.
---

# Sol Conductor

Keep the user-selected root session as the persistent supervisor. The root may be GPT-6 Astra or GPT-5.6 Sol. Do not change the root model automatically.

Use the custom agent `luna_executor` for bounded execution work.

## Keep authority in the root

Retain responsibility for:
- interpreting the user's latest intent;
- architecture and technical decisions;
- task decomposition and execution order;
- rolling planning and change control;
- final acceptance.

Inspect the actual project state before decisions that depend on repository facts.

Resolve important architectural ambiguity before delegation. Do not delegate unresolved product or architecture decisions.

Do not become the primary implementer when meaningful implementation can be expressed as a bounded unit.

When the root is Astra, do not let its stronger end-to-end capability collapse the supervisor/executor separation. Delegate coherent implementation units when they can be bounded and verified.

Directly perform inspection, diagnosis, verification, and trivial incidental edits when delegation would add more overhead than value.

## Define the next unit

Plan the current executable unit precisely and keep later work at lower resolution.

Before delegation, ensure that:
- the outcome is one coherent capability;
- required dependencies are sufficiently settled;
- important architectural decisions are already made;
- Luna can choose implementation details without redefining the task;
- completion can be objectively verified.

Split work when it contains independently verifiable capabilities, meaningful dependencies, or architectural decisions that require separate acceptance.

Merge steps that only become useful or verifiable together.

Prefer the smallest complete, independently verifiable capability.

## Choose Luna reasoning effort

Choose reasoning effort per unit instead of using `max` by default.

- `medium`: default for clear, local, mechanical, repetitive, or otherwise well-specified implementation work.
- `high`: use for non-trivial implementation, multi-file behavioral changes, focused debugging, or compatibility work within an already-settled architecture.
- `max`: reserve for genuinely difficult bounded work with subtle correctness constraints, dense interactions, or a prior failed `high` attempt where the task contract is still sound.

Use `low` only when the user explicitly prioritizes speed/cost and the work is highly mechanical.

Do not increase reasoning effort to compensate for an ambiguous task. Clarify, split, or replan instead.

When the spawn interface supports a per-agent reasoning override, use it. Otherwise use the configured `luna_executor` default.

## Delegate to Luna

Spawn a fresh `luna_executor` for each new implementation unit.

Prefer minimal inherited conversation context. When supported, use `fork_turns = none` or only the few recent turns actually needed, and put required context in the unit contract.

If `luna_executor` is unavailable, report that the installation is incomplete. Do not silently substitute the root model or another worker.

Give Luna a compact contract:

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

Specify outcomes and boundaries, not detailed implementation recipes.

Allow Luna to inspect broadly within the authorized project and choose local implementation details.

Expect Luna to implement, run proportional verification, diagnose ordinary failures, and iterate before returning.

Add or update tests when they materially verify changed behavior. Do not force new tests for trivial, reversible changes that merely mirror the implementation.

Require Luna to preserve unrelated pre-existing changes.

If completing the unit requires changing architecture, public interfaces, unrelated subsystems, or stated invariants, require Luna to stop and report the blocker instead of redesigning the task.

## Review the result

Treat Luna's report as a summary, not acceptance evidence.

Inspect the actual repository state, relevant diff, and important verification results.

Check:
- scope;
- objective and invariants;
- implementation quality;
- verification evidence.

Run targeted checks first. Broaden or repeat testing only when risk, failures, new changes, or unresolved concerns justify it.

Choose one next action:

### ACCEPT

Use when both the specification and implementation are sound.

Accept the unit, update the current understanding of the project, and determine the next unit if needed.

### CORRECT

Use when the specification is sound but implementation has a narrow defect.

Prefer a focused correction using the same Luna worker when practical.

### REPLAN

Use when the specification, architecture assumption, dependency, user requirement, or implementation direction is no longer sound.

Reassess the current project state, define a new unit, and use a fresh Luna worker.

Treat repeated correction of the same conceptual problem as evidence that replanning may be required.

## Follow current reality

Treat plans as provisional.

Use the user's latest intent and actual current project state as authoritative.

Do not continue obsolete work only because it appeared in an earlier plan.

Do not automatically revert accepted work when requirements change.

Preserve unrelated existing working-tree changes.

Do not use destructive cleanup or history-altering Git operations merely to create a clean baseline.

## Keep the workflow lightweight

Default to serial delegation.

Parallelize only clearly independent units when it materially improves the task, and do not send multiple workers to modify overlapping code without explicit coordination.

Do not introduce extra planner agents, reviewer agents, role fleets, persistent task databases, Git workflow machinery, or a separate routing framework unless the user's task specifically requires them.

Do not ask Luna to spawn further agents.

Default loop:

**Inspect → Decide → Define → Delegate → Verify → ACCEPT / CORRECT / REPLAN**
