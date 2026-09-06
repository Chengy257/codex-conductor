# Sol Conductor

A lightweight Codex skill for a simple supervisor–executor workflow:

**A strong root model decides, decomposes, supervises, and verifies. GPT-5.6 Luna implements bounded work.**

The root can be either **GPT-6 Astra** or **GPT-5.6 Sol**. The skill does not switch the parent model for you; use whichever root model fits the task and your quota/cost preference.

> Status: experimental. The repository intentionally stays small and relies on Codex's native skill, custom-agent, spawn, reasoning-effort, and verification capabilities instead of building a separate orchestration framework.

## Design

```text
Astra or Sol root
      ↓
Inspect → Decide → Define bounded unit
      ↓
GPT-5.6 Luna executor
      ↓
Verify → ACCEPT / CORRECT / REPLAN
```

The root owns architecture, rolling planning, sequencing, change control, and final acceptance. Luna owns only the current bounded execution unit.

The skill deliberately does **not** add a fleet of explorer/worker/tester/reviewer roles, a model router, task database, automatic parallel scheduler, or Git workflow manager.

## Why Astra + Sol are both supported

Use **GPT-5.6 Sol** as a strong everyday supervisor when you want lower usage/cost and the task does not need the strongest available root reasoning.

Use **GPT-6 Astra** for the hardest end-to-end work, especially when architecture, long-horizon coherence, complex repository reasoning, or changing requirements matter enough to justify the higher usage cost.

Astra is intentionally not forced as the only root. OpenAI notes that Astra can consume Codex allowance faster than GPT-5.6 Sol, so keeping both available is useful for personal workflows.

## Adaptive Luna reasoning

`luna_executor.toml` uses `medium` as the safe default instead of pinning every task to `max`.

The skill asks the root to choose effort per implementation unit:

| Effort | Use for |
| --- | --- |
| `medium` | Default. Clear local changes, mechanical/repetitive work, straightforward implementation. |
| `high` | Non-trivial implementation, multi-file behavior, focused debugging, compatibility work. |
| `max` | Genuinely difficult bounded work, subtle correctness constraints, or a sound task that already failed at `high`. |

`low` remains available for explicitly cost/latency-first mechanical work. `xhigh` is supported by Luna but is intentionally not part of the default three-band policy; keeping the policy small makes behavior easier to predict.

Increasing effort is **not** a substitute for a better task contract. If a unit is architecturally ambiguous, the root should split or replan it instead.

When the active Codex spawn interface exposes a reasoning-effort override, the root can set it per Luna unit. If that override is unavailable on a particular Codex surface/version, the custom agent's `medium` setting is the fallback.

## Context discipline

A new Luna worker is preferred for each new unit. When supported, the root should use minimal inherited conversation history (`fork_turns = none` or only a few needed turns) and pass the necessary context in the unit contract.

This keeps Luna inexpensive and disposable while the root retains the long-lived project state.

## Repository layout

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
└── codex-agents/
    └── luna_executor.toml
```

`agents/openai.yaml` controls skill metadata and keeps implicit invocation disabled during testing.

`codex-agents/luna_executor.toml` is the single custom executor profile. We intentionally do not duplicate it into medium/high/max role files; Codex's native per-spawn reasoning control is preferred when available.

## Install

Personal Codex skills are loaded from `$HOME/.agents/skills`, while personal custom agents are loaded from `~/.codex/agents/`.

```bash
mkdir -p "$HOME/.agents/skills" "$HOME/.codex/agents"
git clone https://github.com/Chengy257/sol-conductor.git \
  "$HOME/.agents/skills/sol-conductor"
cp "$HOME/.agents/skills/sol-conductor/codex-agents/luna_executor.toml" \
  "$HOME/.codex/agents/luna_executor.toml"
```

Restart Codex after installation.

### Update

```bash
git -C "$HOME/.agents/skills/sol-conductor" pull
cp "$HOME/.agents/skills/sol-conductor/codex-agents/luna_executor.toml" \
  "$HOME/.codex/agents/luna_executor.toml"
```

Restart Codex after updating the agent configuration.

## Choose the root model

Start or select either root model in Codex:

```bash
codex --model gpt-5.6-sol
```

or, when Astra is available to your account:

```bash
codex --model gpt-6-astra
```

Astra currently requires a recent Codex build; OpenAI's rollout guidance specifies Codex CLI 0.153.0 or newer.

The root reasoning effort is your own session-level choice. A practical personal-use baseline is:

- Sol `medium` or `high` for most work;
- Astra `medium` for strong general orchestration, `high` when the task truly benefits from deeper root reasoning;
- `xhigh`/`max` only when the task warrants the extra usage.

## Use

The skill disables implicit invocation during the experimental phase. Invoke it explicitly:

```text
$sol-conductor

Implement this change. Keep the current Astra/Sol session responsible for architecture, planning and acceptance. Delegate bounded implementation units to Luna, choose Luna reasoning effort proportionally, and verify each result before continuing.
```

Expected behavior:

1. The root inspects the real repository state and resolves important design decisions.
2. It defines one bounded implementation unit.
3. It chooses Luna effort (`medium`, `high`, or rarely `max`) based on that unit rather than the whole project.
4. Luna implements and performs proportional verification without redefining architecture.
5. The root independently checks the real diff and important verification evidence.
6. The root chooses `ACCEPT`, `CORRECT`, or `REPLAN`.

## Optional Codex defaults

You do not need a project-scoped `.codex` folder for Sol Conductor. If you want personal defaults, merge settings like these into your existing `~/.codex/config.toml` rather than overwriting it:

```toml
[agents]
enabled = true
default_subagent_model = "gpt-5.6-luna"
default_subagent_reasoning_effort = "medium"
max_concurrent_threads_per_session = 2
```

The skill defaults to serial delegation. Increase concurrency only when units are genuinely independent.

## What we borrowed from codex-astra-luna-orchestrator

The community project [donvito/codex-astra-luna-orchestrator](https://github.com/donvito/codex-astra-luna-orchestrator) is a useful reference for Astra-root/Luna-child configuration, native Codex agent defaults, reasoning-effort tuning, and bounded delegation.

Sol Conductor intentionally stays smaller:

- Astra **or** Sol can be the root;
- one Luna executor instead of explorer/worker/tester/researcher roles;
- the root performs review instead of spawning a dedicated Astra reviewer;
- serial delegation by default;
- adaptive reasoning effort instead of fixed `max`;
- no required project-level `.codex`, `AGENTS.md`, or installer.

## What to watch during testing

Focus on four failure modes:

- **Root over-implements** instead of delegating coherent implementation work.
- **Units are too broad**, forcing Luna to make architecture decisions.
- **Effort is over-provisioned**, especially `max` on straightforward tasks.
- **Root under-reviews**, accepting Luna's report without checking repository reality.

Refine the skill only when repeated real-task behavior justifies an additional rule.

## References

- OpenAI model guidance: https://developers.openai.com/api/docs/guides/latest-model
- GPT-6 Astra: https://developers.openai.com/api/docs/models/gpt-6-astra
- GPT-5.6 Sol: https://developers.openai.com/api/docs/models/gpt-5.6-sol
- GPT-5.6 Luna: https://developers.openai.com/api/docs/models/gpt-5.6-luna
- Community reference: https://github.com/donvito/codex-astra-luna-orchestrator
