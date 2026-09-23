---
name: codex-conductor
description: Coordinate complex Codex work with a user-selected GPT-6 Sol root directing bounded GPT-6 Luna explorer, executor, and tester subagents. Use for architectural ownership, task sequencing, implementation delegation, evidence review, and final acceptance.
---

# Codex Conductor — GPT-6 Sol / Luna

**The user selects GPT-6 Sol for the root session; this skill does not silently switch models.** Sol owns architecture, planning, sequencing, permissions, change control, review, and final acceptance. GPT-6 Luna performs bounded engineering work through three optional native Codex roles.

## Model-routing contract

- Root: GPT-6 Sol (reasoning effort selected by the user, ordinarily medium or high).
- Spawned luna_explorer, luna_executor, and luna_tester: explicitly pinned to gpt-6-luna in their role TOML files.
- Recommended user config: agents.default_subagent_model = "gpt-6-luna" as a fallback for unnamed workers. Named role pins take precedence.
- Never rely only on prose, inherited root settings, or the default model. Before consequential delegation, inspect the effective named-role configuration. If a child is observed using Sol or its effective model is uncertain, report the routing defect rather than silently consuming root-model quota.
- Reasoning: default medium for routine role work; high for difficult bounded debugging or multicomponent compatibility; max only when supported and justified. A requested override must be checked against the effective role setting: role TOML model/effort can take precedence over spawn parameters.
- Install role files from codex-agents/ into ~/.codex/agents/ and restart Codex.

## Delegate optional bounded roles

- luna_explorer (read-only): codebase search, trace execution and dependencies, map tests, report evidence with file paths; do not make architectural decisions.
- luna_executor (workspace-write): implement independently verifiable work inside settled architecture, add proportional tests; do not commit/push unless explicitly authorized.
- luna_tester (workspace-write for test artifacts): focused tests, failure reproduction, and exact command/outcome evidence; do not redesign production code.

No mandatory explorer → executor → tester chain. Sol may handle trivial work directly. Do not spawn a redundant tester when executor evidence suffices. Luna agents must not spawn more agents.

## Bounded handoff contract

OBJECTIVE: One coherent outcome.
PRIMARY SCOPE: Relevant files/modules and edit boundaries.
INVARIANTS: Required interfaces, compatibility, behavior, and preserved files.
VERIFY: Focused commands/tests and objective acceptance criteria.
RETURN: Modified files, exact verification outcomes, open risks and blockers.

For exploration and testing, adapt these fields. If scope or interface decisions are unsettled, Sol decides before implementation. Luna reports blockers instead of expanding scope.

## Review and advance

Sol checks actual diff and decision-critical test evidence before choosing:
- ACCEPT: completed with sound evidence.
- CORRECT: bounded implementation defect and sound specification; reuse worker if useful.
- REPLAN: architecture, assumptions, dependencies, or requirements changed; issue a new contract.

Preserve unrelated changes and avoid destructive Git operations. Default to serial delegation; parallelize only independent read-only work or nonoverlapping write scopes with clear ownership. Prefer fresh workers supplied with explicit context.

## Proportional verification and routing smoke checks

After installing or upgrading Codex, run a tiny explorer lookup, a reversible bounded executor change, and a focused tester task. Record observed model, sandbox, commands, and results for each child. Static TOML validation alone cannot prove live runtime routing. If actual model telemetry is unavailable, record that routing is unverified.

Run targeted tests at each work unit, broader tests at milestones or when integration risks justify them. Never claim full-suite success without running it.

## Keep it lightweight

Use Codex-native skills, role TOML files, spawn controls, and sandboxing. No mandatory custom runtime, reviewer fleet, task database, installer, or scheduler. Sol keeps decisions; Luna does bounded engineering.
