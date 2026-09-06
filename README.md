# Codex Conductor

A lightweight personal Codex skill for a director–worker workflow:

**GPT-6 Astra or GPT-5.6 Sol decides, plans, and accepts. GPT-5.6 Luna handles bounded engineering labor.**

The project deliberately relies on Codex's native skills, custom agents, spawn controls, reasoning-effort overrides, sandboxing, and verification capabilities instead of building a separate orchestration framework.

## Topology

```text
             GPT-6 Astra / GPT-5.6 Sol
              architecture + planning
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
  luna_explorer   luna_executor   luna_tester
   read-only        write           verify
    medium        adaptive         medium
          └────────────┼────────────┘
                       ↓
             root review + acceptance
          ACCEPT / CORRECT / REPLAN
```

The three Luna roles are **optional tools, not a fixed pipeline**.

- `luna_explorer`: offload repository reading, search, call-path tracing, dependency/config mapping, and test discovery.
- `luna_executor`: implement bounded changes.
- `luna_tester`: run targeted verification, reproduce failures, and gather exact evidence.
- Root Astra/Sol: keeps architecture, sequencing, change control, evidence interpretation, and final acceptance.

There is intentionally no separate reviewer, planner, researcher fleet, task database, or mandatory parallel scheduler.

## Reasoning policy

All Luna roles default to `medium`. The root should adjust effort per bounded task when the active Codex spawn surface supports overrides.

| Effort | Typical use |
| --- | --- |
| `medium` | Default exploration, targeted testing, clear local implementation, mechanical work |
| `high` | Difficult exploration, multi-file behavior, focused debugging, compatibility work, complex failure reproduction |
| `max` | Rare: genuinely difficult bounded implementation/diagnosis or a sound task that already failed at `high` |

`low` is optional for explicitly speed/cost-first mechanical work.

Do not use higher reasoning effort to compensate for an ambiguous task. Split or replan instead.

## Repository layout

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
└── codex-agents/
    ├── luna_explorer.toml
    ├── luna_executor.toml
    └── luna_tester.toml
```

## Install

Personal Codex skills are loaded from `$HOME/.agents/skills`; personal custom agents are loaded from `~/.codex/agents/`.

```bash
mkdir -p "$HOME/.agents/skills" "$HOME/.codex/agents"

git clone https://github.com/Chengy257/codex-conductor.git \
  "$HOME/.agents/skills/codex-conductor"

cp "$HOME/.agents/skills/codex-conductor/codex-agents/"*.toml \
  "$HOME/.codex/agents/"
```

Restart Codex after installation.

## Upgrade from the old `sol-conductor`

The GitHub repository was renamed from `sol-conductor` to `codex-conductor`, and the skill invocation changed from `$sol-conductor` to `$codex-conductor`.

If you previously installed the old version:

```bash
rm -rf "$HOME/.agents/skills/codex-conductor"
mv "$HOME/.agents/skills/sol-conductor" \
   "$HOME/.agents/skills/codex-conductor"

git -C "$HOME/.agents/skills/codex-conductor" remote set-url origin \
  https://github.com/Chengy257/codex-conductor.git

git -C "$HOME/.agents/skills/codex-conductor" pull
cp "$HOME/.agents/skills/codex-conductor/codex-agents/"*.toml \
  "$HOME/.codex/agents/"
```

Restart Codex afterward. The old `luna_executor.toml` is simply replaced by the updated version; `luna_explorer.toml` and `luna_tester.toml` are added.

## Choose the root model

Use whichever strong root fits the task and your quota/cost preference:

```bash
codex --model gpt-5.6-sol
```

or:

```bash
codex --model gpt-6-astra
```

Practical personal-use guidance:

- **GPT-5.6 Sol**: strong everyday supervisor for most development work.
- **GPT-6 Astra**: use when architecture, long-horizon coherence, difficult repository reasoning, or changing requirements justify the higher root-model cost.

The skill never switches the root model automatically.

## Use

Implicit invocation remains disabled during testing. Invoke explicitly:

```text
$codex-conductor

Complete this task. Keep the current Astra/Sol session responsible for architecture, planning, sequencing and acceptance. Offload substantial repository exploration, bounded implementation, and mechanical verification to the appropriate Luna roles when useful. Choose Luna reasoning effort proportionally and verify decision-critical evidence before continuing.
```

Expected behavior is adaptive, not pipeline-driven. A simple change may use only `luna_executor`. A large unfamiliar repository may use `luna_explorer` first. A costly or noisy test phase may use `luna_tester`. The root may also do small inspections or checks directly when spawning an agent costs more than the work itself.

## Context discipline

Prefer fresh Luna agents for new bounded work. When supported, inherit minimal parent history (`fork_turns = none` or only the few turns needed) and provide necessary context explicitly in the delegated task.

This keeps Astra/Sol focused on high-value reasoning while Luna absorbs lower-cost repository reading, implementation iteration, and test/log processing.

## Optional personal Codex defaults

You do not need a project-scoped `.codex` folder. If useful, merge settings like these into your existing `~/.codex/config.toml` rather than overwriting it:

```toml
[agents]
enabled = true
default_subagent_model = "gpt-5.6-luna"
default_subagent_reasoning_effort = "medium"
max_concurrent_threads_per_session = 2
```

Codex Conductor defaults conceptually to serial delegation; parallelize only genuinely independent bounded tasks.

## Community reference

The design borrows useful ideas from [donvito/codex-astra-luna-orchestrator](https://github.com/donvito/codex-astra-luna-orchestrator), especially Luna-based explorer/tester roles, Astra-root delegation, native Codex agent configuration, and reasoning-effort tuning.

Codex Conductor intentionally remains smaller:

- Astra **or** Sol root;
- only three narrow Luna engineering roles;
- no dedicated root-model reviewer;
- roles are invoked only when useful, not as a mandatory chain;
- serial by default;
- adaptive Luna effort;
- no required project-level `.codex`, `AGENTS.md`, installer, or orchestration runtime.

## Testing focus

Watch for these failure modes:

- root spends too much context on repository exploration that Luna could map;
- root over-implements instead of delegating coherent bounded work;
- tester is spawned redundantly when executor evidence is already sufficient;
- Luna effort is over-provisioned;
- root accepts summaries without spot-checking decision-critical evidence;
- roles start acting like autonomous planners instead of bounded workers.

Refine the skill only when repeated real-task behavior justifies another rule.

## References

- OpenAI latest model guidance: https://developers.openai.com/api/docs/guides/latest-model
- OpenAI Codex skills: https://developers.openai.com/codex/skills
- OpenAI Codex subagents: https://developers.openai.com/codex/subagents
- GPT-6 Astra: https://developers.openai.com/api/docs/models/gpt-6-astra
- GPT-5.6 Sol: https://developers.openai.com/api/docs/models/gpt-5.6-sol
- GPT-5.6 Luna: https://developers.openai.com/api/docs/models/gpt-5.6-luna
