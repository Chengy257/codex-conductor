# Codex Conductor

Lightweight **GPT-6 Sol director / GPT-6 Luna worker** orchestration through native Codex custom agents and a skill. Sol owns architecture, planning, sequencing, code review, and final acceptance; three optional Luna agents take bounded engineering work. No separate orchestration runtime.

## Topology

    GPT-6 Sol root: architecture / plan / review / ACCEPT-CORRECT-REPLAN
       |                   |                 |
    luna_explorer      luna_executor      luna_tester
    read-only*         workspace-write    focused verification
    GPT-6 Luna         GPT-6 Luna         GPT-6 Luna

*Explorer's read-only sandbox is the intended configuration, not yet verified as an independent child sandbox when the parent is workspace-write. Verify effective sandbox in child session telemetry; do not assume TOML alone enforces isolation.*

The roles are optional tools, not a mandatory pipeline. Sol can do small tasks directly. Delegate when repository exploration, substantial implementation, or mechanical verification would otherwise consume root context.

## Install or upgrade

Personal Codex skills are in `~/.agents/skills`; custom agent TOML files are in `~/.codex/agents`. Clone for a new installation:

```bash
mkdir -p "$HOME/.agents/skills" "$HOME/.codex/agents"
git clone https://github.com/Chengy257/codex-conductor.git "$HOME/.agents/skills/codex-conductor"
cp "$HOME/.agents/skills/codex-conductor/codex-agents/"*.toml "$HOME/.codex/agents/"
```

If already installed:

```bash
git -C "$HOME/.agents/skills/codex-conductor" pull --ff-only
cp "$HOME/.agents/skills/codex-conductor/codex-agents/"*.toml "$HOME/.codex/agents/"
```

Back up any locally customized role TOML before copying. Restart Codex after changes. Do not overwrite an existing global config; merge the optional settings below into `~/.codex/config.toml` if useful:

```toml
model = "gpt-6-sol"
model_reasoning_effort = "medium"

[agents]
enabled = true
default_subagent_model = "gpt-6-luna"
default_subagent_reasoning_effort = "medium"
max_concurrent_threads_per_session = 2
```

Alternatively choose the root from the CLI: `codex --model gpt-6-sol`. The skill never automatically switches the root model. The exact models must be available to the installed Codex version and account.

## Use

Invoke explicitly while validating:

```text
$codex-conductor

Keep this GPT-6 Sol root responsible for architecture, planning, sequencing,
review, and final acceptance. Delegate bounded exploration, implementation,
and targeted testing to GPT-6 Luna as useful. Inspect effective subagent
model routing rather than trusting a prompt or default alone.
```

The root uses ACCEPT / CORRECT / REPLAN after inspecting the actual diff and evidence. Simple changes may use only executor; unfamiliar code can begin with explorer; tester is optional if executor verification already suffices.

## Model precedence and effort

Each named role file explicitly pins `model = "gpt-6-luna"`. Explorer and Tester use medium effort; Executor uses max effort. Global default_subagent_model is a fallback, not a substitute. According to current Codex documentation, explicit settings in a named custom-agent file can take precedence over spawn parameters and global defaults. **Do not promise that per-spawn effort overrides a pinned role file without verifying runtime behavior.** Use a separately named role if another stable effort profile is needed.

| Role | Model | Effort | Sandbox |
| --- | --- | --- | --- |
| Root (selected by user) | GPT-6 Sol | medium or user-selected | user setting |
| luna_explorer | GPT-6 Luna | medium | read-only |
| luna_executor | GPT-6 Luna | max | workspace-write |
| luna_tester | GPT-6 Luna | medium | workspace-write |

Default serial delegation, optional concurrency of two for genuinely independent tasks. Never allow overlapping write workers without explicit ownership.

## Verification and compatibility

Run static checks: `python3 -m unittest discover -s tests -v`. They parse the real TOML and check role pins, documentation, and lightweight design; they do **not** prove runtime model selection.

Run the real Codex smoke-test checklist in `docs/GPT6_UPGRADE_AND_VALIDATION.md` on your installed CLI. A successful deployment requires evidence that the actual spawned role model is GPT-6 Luna. If telemetry is not available, mark runtime routing unverified.

This version targets Codex builds supporting named custom-agent files and agents.default_subagent_model. Retain an older installation until you verify model availability and runtime spawning on your machine.

## References

- [Official Codex subagents](https://developers.openai.com/codex/subagents)
- [Official configuration reference](https://developers.openai.com/codex/config-reference)
- [Official skills](https://developers.openai.com/codex/skills)
- [Community Sol/Astra-Luna orchestration](https://github.com/donvito/codex-astra-luna-orchestrator)

Community Sol/Luna profiles informed model names and testing ideas. Codex Conductor intentionally retains only three optional worker roles rather than copying a reviewer/researcher fleet or mandatory execution pipeline.
