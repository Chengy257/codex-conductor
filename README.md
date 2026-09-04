# Sol Conductor

A lightweight Codex skill for a simple supervisor–executor workflow:

**Sol decides, decomposes, supervises, and verifies. Luna implements bounded work.**

Sol Conductor keeps the primary GPT-5.6 Sol session responsible for architecture, rolling planning, sequencing, change control, and acceptance. Clear implementation units are delegated to a custom GPT-5.6 Luna agent running at `max` reasoning effort.

> Status: experimental. This repository is intentionally small so the workflow can be tested and refined from real Codex tasks.

## Design

The default loop is:

```text
Inspect → Decide → Define → Delegate → Verify → ACCEPT / CORRECT / REPLAN
```

The skill deliberately does **not** add a model router, reviewer agent, task database, automatic parallel scheduler, or Git workflow manager.

## Repository layout

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
└── codex-agents/
    └── luna_executor.toml
```

`agents/openai.yaml` is metadata and invocation policy for the skill. It is **not** the Luna subagent definition.

`codex-agents/luna_executor.toml` is the custom Codex agent that must be installed separately under `~/.codex/agents/`.

## Install

Personal Codex skills are loaded from `$HOME/.agents/skills`, while personal custom agents are loaded from `~/.codex/agents/`.

```bash
mkdir -p "$HOME/.agents/skills" "$HOME/.codex/agents"
git clone https://github.com/Chengy257/sol-conductor.git \
  "$HOME/.agents/skills/sol-conductor"
cp "$HOME/.agents/skills/sol-conductor/codex-agents/luna_executor.toml" \
  "$HOME/.codex/agents/luna_executor.toml"
```

Restart Codex after installation so both the skill and custom agent are discovered.

### Update

```bash
git -C "$HOME/.agents/skills/sol-conductor" pull
cp "$HOME/.agents/skills/sol-conductor/codex-agents/luna_executor.toml" \
  "$HOME/.codex/agents/luna_executor.toml"
```

Restart Codex after updating the custom agent configuration.

## Use

Start or select a GPT-5.6 Sol primary session. In Codex CLI, for example:

```bash
codex --model gpt-5.6-sol
```

The skill disables implicit invocation during the experimental phase. Invoke it explicitly:

```text
$sol-conductor Implement this change. First inspect the repository, decide the architecture and plan, then delegate bounded implementation units to Luna and verify each result before continuing.
```

For a realistic test, use a project with a small but non-trivial feature that requires several related edits and tests. The expected behavior is:

1. Sol inspects and resolves important design decisions.
2. Sol defines one bounded implementation unit.
3. Sol spawns the custom `luna_executor` agent.
4. Luna implements and verifies the unit without redefining architecture.
5. Sol independently checks the real diff and verification evidence.
6. Sol chooses `ACCEPT`, `CORRECT`, or `REPLAN` and continues only as needed.

## What to watch during testing

The first tests should focus on three failure modes:

- **Sol over-implements** instead of delegating coherent implementation work.
- **Units are too broad**, forcing Luna to make architecture decisions.
- **Sol under-reviews**, accepting Luna's report without checking repository reality.

Refine the skill only when a repeated real-task failure justifies an additional rule.

## Model configuration

The included Luna executor uses:

```toml
model = "gpt-5.6-luna"
model_reasoning_effort = "max"
sandbox_mode = "workspace-write"
```

The skill does not change the parent session model. Select GPT-5.6 Sol in Codex yourself.

## Official references

- OpenAI: Build skills — https://learn.chatgpt.com/docs/build-skills
- OpenAI: Subagents — https://learn.chatgpt.com/docs/agent-configuration/subagents
- OpenAI: GPT-5.6 Sol — https://developers.openai.com/api/docs/models/gpt-5.6-sol
- OpenAI: GPT-5.6 Luna — https://developers.openai.com/api/docs/models/gpt-5.6-luna
