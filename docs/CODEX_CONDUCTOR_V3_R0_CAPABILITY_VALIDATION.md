# Codex Conductor v3 — R0 Capability Validation

Status: working validation record  
Date: 2026-10-07  
Baseline upstream stable release: Codex CLI 0.160.1 (2026-10-05)  
Target branch: docs/v3-runtime-rebaseline-20261007

## 1. Purpose

R0 validates the Codex host assumptions required by the v3 runtime rebaseline before implementation begins.

This document distinguishes:

- **UPSTREAM VERIFIED** — confirmed in current OpenAI documentation and/or current `openai/codex` protocol/schema.
- **COMMUNITY CORROBORATED** — implemented successfully by an external Codex project, but still requires our own smoke validation.
- **LOCAL SMOKE REQUIRED** — must be tested against real Codex installations/accounts on the Tier-1 Windows CLI and Linux CLI host profiles before release qualification; architecture freeze and host qualification are tracked separately.
- **NOT A CORE DEPENDENCY** — useful capability, but v3 correctness must not depend on it.

## 2. Current baseline

Current stable upstream Codex release at review time is 0.160.1. The v3 implementation should target the current stable line, not alpha builds, and record `codex --version` in every live R0 smoke record.

Do not hard-code protocol behavior from an alpha build.

## 3. Capability matrix

| Capability | R0 status | v3 decision |
|---|---|---|
| Start persistent app-server thread | UPSTREAM VERIFIED | primary root runtime |
| Select model at `thread/start` | UPSTREAM VERIFIED | use exact task-bound root/worker model |
| Disable provider model fallback | UPSTREAM VERIFIED | required; fail closed |
| Observe actual model returned by start/resume | UPSTREAM VERIFIED | required model-binding check |
| Change model through thread settings/resume | UPSTREAM VERIFIED | controller must prohibit unapproved drift |
| Resume thread by persisted thread id | UPSTREAM VERIFIED | primary restart/quota recovery primitive |
| Model catalog via `model/list` | UPSTREAM VERIFIED | discovery only, not entitlement proof |
| Account rate-limit read | UPSTREAM VERIFIED | quota controller input |
| Backend `ordinaryUsageAllowed` | UPSTREAM VERIFIED | authoritative ordinary-usage gate when non-null |
| Reset timestamps (`resetsAt`) | UPSTREAM VERIFIED | scheduling hint, not proof of availability |
| Rate-limit update notifications | UPSTREAM VERIFIED | live quota observation |
| Native Codex Goal persisted in thread | UPSTREAM VERIFIED | use for root objective where useful |
| Noninteractive Goal get/set/clear | UPSTREAM VERIFIED | may be used by controller |
| Goal `usageLimited` state | UPSTREAM VERIFIED | map to conductor quota state |
| Native automatic cross-window quota resume | NOT AVAILABLE AS RELIABLE HOST GUARANTEE | local supervisor required |
| Lifecycle hooks | UPSTREAM VERIFIED | instrumentation / guard support only |
| Native multi-agent/subagents | UPSTREAM VERIFIED | optional optimization, not core delegation guarantee |
| Custom subagent default model | UPSTREAM VERIFIED | optional native mode only |
| Plugin distribution to Codex CLI | UPSTREAM VERIFIED | plugin is installation/integration shell |
| Plugin hooks always trusted/enabled | FALSE | runtime must not depend on hooks |
| Official `openai-codex` Python SDK | UPSTREAM VERIFIED | primary controller adapter; stable SDK pins matching runtime |
| Persistent app-server community orchestration | COMMUNITY CORROBORATED | useful R2 reference |
| Quota auto-resume via app-server/CLI | COMMUNITY CORROBORATED | useful R5 reference |
| Windows Task Scheduler wake | COMMUNITY CORROBORATED | Tier-1 Windows backend; local smoke required |
| Linux systemd --user wake | COMMUNITY CORROBORATED | Tier-1 Linux backend; local smoke required |

## 4. SDK and app-server findings

### 4.0 Official Python SDK

Current upstream ships a stable `openai-codex` Python SDK (Python >=3.10). Stable SDK releases track the corresponding stable Codex CLI and install an exact matching `openai-codex-cli-bin` runtime.

The SDK already provides thread start/resume, turn execution/streaming, sandbox presets, Goal operations, model listing, authentication reuse, and a typed app-server client.

**R0 decision:** v3 should use the official SDK as the primary controller transport instead of implementing a full JSON-RPC client. Keep only a narrow compatibility/protocol layer for required operations not exposed on the public high-level surface. Pin a tested SDK/runtime release per Conductor release and report any mismatch with the user's global Codex CLI in `doctor`.

The authoritative managed runtime should not silently follow an arbitrary global CLI upgrade.

### 4.1 Thread model selection

### 4.1 Thread model selection

Current app-server protocol exposes a `model` field on `thread/start`.

It also exposes:

```
allowProviderModelFallback
```

The conductor must set this to false / leave the false default and must never opt into provider substitution for a managed task.

`thread/start` returns the effective:

- model;
- model provider;
- reasoning effort;
- permissions/sandbox metadata;
- thread id.

Therefore model selection can be checked mechanically instead of inferred from prompts.

### 4.2 Resume semantics

Current `thread/resume` explicitly recommends resume by `threadId` whenever possible.

It supports model/provider/config overrides, which means resume itself is capable of changing execution identity.

**v3 implication:** Conductor must pass/verify the pinned binding on resume and reject any effective model mismatch. Resume is not permission to select a new model.

### 4.3 Thread settings can change model

`thread/settings/update` exposes a model override for subsequent turns.

Therefore an attached UI/client can potentially change a managed thread's model unless Conductor detects the change.

Required v3 behavior:

- subscribe to `thread/settings/updated`;
- compare effective model/effort/provider with the task binding;
- mark a mismatch as `model_drift`;
- stop automatic progression;
- restore the binding only through controller-owned recovery logic, or require explicit user intervention.

### 4.4 Model reroute telemetry

App-server emits `model/rerouted` notifications containing `fromModel`, `toModel`, thread id, turn id, and reason.

This is important because a platform-managed reroute can violate the project's model-role contract even when the controller requested the correct model.

Default v3 policy:

> a managed task must never silently accept a turn executed under a different effective model.

A rerouted worker result is non-conforming evidence. Record it and stop/replan rather than silently treating it as a valid pinned-worker result.

## 5. Model binding policy — R0 decision

### 5.1 Configuration is flexible; a running task is not

The project must support model evolution.

Examples of valid root choices today include:

- `gpt-6.1-sol`;
- `gpt-6-astra`.

A typical worker choice is:

- `gpt-6-luna`.

Future models must be selectable without changing runtime architecture.

However, these are **selection-time choices**, not turn-time choices.

### 5.2 Two-stage model resolution

Configuration may use named preferences/profiles:

```toml
[model_profiles.strong]
preferred = ["gpt-6.1-sol", "gpt-6-astra"]
reasoning_effort = "high"

[model_profiles.worker]
preferred = ["gpt-6-luna"]
reasoning_effort = "high"
```

At task creation the controller resolves profiles to exact model ids.

The durable task stores exact bindings, not symbolic aliases:

```json
{
  "model_binding": {
    "generation": 1,
    "root": {
      "model": "gpt-6.1-sol",
      "reasoning_effort": "high",
      "provider": "..."
    },
    "worker": {
      "model": "gpt-6-luna",
      "reasoning_effort": "high",
      "provider": "..."
    }
  }
}
```

### 5.3 Binding invariants

After task activation:

- the root model binding is immutable to the model itself;
- the worker model binding is immutable to the model itself;
- root prompts cannot select a cheaper/different worker model;
- workers cannot spawn themselves under another model;
- auto-resume cannot re-resolve aliases to a newer model;
- configuration updates affect **new tasks only**;
- a newly released model does not migrate active tasks automatically.

Every start/resume/worker launch verifies the effective model against the stored exact binding.

### 5.4 Entitlement preflight

OpenAI documents that `model/list` is a catalog and not an entitlement check.

Therefore:

1. resolve a candidate from `model/list`;
2. start a tiny task/thread with that exact model;
3. require a successfully completed inference turn;
4. store the verified exact model/provider binding.

No provider fallback is allowed.

### 5.5 Explicit model migration

The model itself must never be given a tool that changes the task binding.

If a pinned model becomes unavailable during a long-running task:

```
status -> waiting_user
reason -> model_unavailable
```

A future controlled CLI action may support:

```
codex-conductor task rebind-model <task> --root-model ... --worker-model ...
```

but only when:

- no turn/worker is active;
- the user explicitly requests it;
- binding generation increments;
- stale validation/review is invalidated;
- the migration is journaled.

For the first v3 release, it is acceptable to omit rebind entirely and require a new task. Silent or agent-directed migration is forbidden.

## 6. Native Goals findings

Goals are stable and thread-scoped.

Current app-server exposes:

- `thread/goal/set`;
- `thread/goal/get`;
- `thread/goal/clear`;
- `thread/goal/updated`.

Goal status includes:

- active;
- paused;
- blocked;
- usageLimited;
- budgetLimited;
- complete.

This changes the earlier v3 assumption that Goal controls were effectively TUI-only.

### R0 decision

Use native Goal as the root thread's optional persistent objective starting in R2/R3 rather than deferring it to R6.

However:

- Conductor task state remains authoritative for cross-process orchestration;
- Conductor controls the model binding;
- Conductor controls repository locks and acceptance evidence;
- Conductor controls quota wake scheduling;
- Goal state is not a replacement for Conductor task state.

## 7. Quota and continuity findings

### 7.1 Structured rate-limit access

Current app-server exposes:

```
account/rateLimits/read
```

and an `account/rateLimits/updated` notification.

The response includes:

- bucket snapshots;
- reset timestamps;
- `ordinaryUsageAllowed`;
- reset-credit/spend-control information when supplied.

The upstream schema explicitly states that clients must not infer recovery from percentages/reset times when `ordinaryUsageAllowed` is unavailable/authoritative.

### R0 decision

The scheduler uses `resetsAt` only to choose the next wake/check time.

Actual resume admission requires a fresh quota read and, when present, `ordinaryUsageAllowed == true`.

### 7.2 Native auto-resume gap

As of this R0 review, open upstream feature requests still ask Codex to auto-resume sessions/Goals after quota reset.

Therefore cross-window unattended continuation remains a Conductor responsibility.

### 7.3 Community evidence

Two community directions corroborate the proposed implementation:

- app-server orchestrators persist provider thread ids and resume persistent Codex sessions;
- `codex-auto-resume` style supervisors persist jobs, read app-server rate limits, resume the same thread, and include Windows Task Scheduler/systemd/launchd integration.

These are implementation references, not dependencies.

## 8. Plugin and hooks findings

Codex plugins can package:

- skills;
- MCP;
- lifecycle hooks.

Local marketplace plugins are supported in Codex CLI as well as the desktop client.

Lifecycle hooks are useful for:

- SessionStart recovery context;
- Stop completion guard;
- Subagent telemetry;
- SessionEnd checkpoint hints.

But plugin hooks:

- require trust;
- can be disabled;
- are not suitable as the authoritative scheduler;
- should not be required for the runtime to recover safely.

### R0 decision

The plugin is an integration shell.

The local controller/runtime remains independently callable and authoritative.

## 9. Native multi-agent findings

Codex multi-agent is stable in current Codex configuration, with native collaboration tools and configurable default subagent model.

This is valuable for optional read-only exploration and future optimizations.

However native multi-agent remains root/model-directed rather than a fixed deterministic graph, and API multi-agent uses the same request model for root and descendants.

### R0 decision

Do not base v3's strong-root / cheap-worker invariant on hosted/native multi-agent.

Use explicit independently launched/persistent worker threads for the v3 core path.

Native subagents remain optional.

## 10. R0 upstream architecture conclusions

The following v3 mainline assumptions are now supported strongly enough to retain:

1. **Plugin + local controller** is the correct product form.
2. **app-server persistent threads** should be the primary Codex runtime.
3. **explicit task-bound worker threads** are preferable to prompt-only delegation.
4. **exact root and worker model bindings** can be enforced mechanically.
5. **native Goals** can help root continuation but do not replace controller state.
6. **structured quota state** is available.
7. **automatic cross-window wake** still requires an external/local scheduler.
8. **hooks are supporting controls, not the runtime.**
9. **the official Codex Python SDK** should be the controller's primary host adapter.
10. **managed delegate/full root threads should be read-only and have native subagent spawning disabled where the host permits it; bound workers own repository writes.**

## 11. Required mainline corrections

Update `CODEX_CONDUCTOR_V3_RUNTIME_REBASELINE_PLAN.md` to:

- remove hard-coded root identity as GPT-5.6 Sol;
- define configurable root/worker model profiles;
- freeze exact model bindings per task;
- prohibit model-directed model switching;
- require `allowProviderModelFallback = false`;
- verify the effective model on every start/resume;
- detect `thread/settings/updated` model drift;
- detect `model/rerouted`;
- move noninteractive Goal integration earlier because app-server exposes Goal control now;
- retain external quota scheduler as an R5 requirement.

## 12. Remaining local smoke gates

These cannot be closed by repository/document inspection alone.

Run against both Tier-1 target environments before release qualification: Windows Codex CLI and Linux Codex CLI. R0 architecture may freeze before both hosts are physically available, but host validation remains open until each Tier-1 matrix passes. The detailed executable contract is in `CODEX_CONDUCTOR_V3_R0_SMOKE_HARNESS_SPEC.md`:

### LS-1 — environment

Record:

- `codex --version`;
- OS family/version/architecture;
- execution surface: Windows CLI, Linux CLI, or compatible Linux runtime such as WSL2;
- current authentication surface/account plan;
- available models from `model/list`;
- installed/pinned `openai-codex` SDK and matching runtime version.

### LS-2 — root binding

Start an app-server thread with selected strong root model.

Verify:

- requested model == response model;
- reasoning effort;
- provider;
- no fallback;
- managed native subagent spawning is disabled;
- read-only root policy rejects a controlled write in the disposable smoke repo.

Repeat with another allowed strong model to prove configurability.

### LS-3 — worker binding

Start a worker thread explicitly on the selected task-bound worker model.

Verify:

- response model exactly matches the selected worker binding;
- actual inference succeeds;
- repository command/file tools work under the intended permissions;
- native subagent spawning is disabled for the managed worker;
- bounded workspace write succeeds only in the disposable smoke repo.

### LS-4 — drift detection

Attempt `thread/settings/update` to another model.

Verify the controller detects and blocks the managed task.

### LS-5 — app-server restart

Start root -> persist thread id -> stop app-server -> restart -> `thread/resume`.

Verify:

- same thread resumes;
- pinned model remains/effective model is checked;
- Goal state remains available if configured.

### LS-6 — Goal control

Exercise:

- set active goal;
- get goal;
- pause/block;
- reactivate;
- clear.

Confirm noninteractive app-server behavior on the installed stable build.

### LS-7 — quota read

Call `account/rateLimits/read`.

Record actual fields supplied by the user's plan.

Do not require a real exhaustion event for this smoke.

### LS-8 — scheduler wake

Run the scheduler probe for the active Tier-1 platform.

**Windows CLI**

Create a harmless one-shot user task through Windows Task Scheduler.

**Linux CLI**

Create a harmless one-shot `systemd --user` service/timer. Verify the user manager can invoke Conductor without an interactive Codex shell. If systemd user services are unavailable, exercise the portable `codex-conductor supervise` fallback and report scheduler capability as reduced rather than pretending full unattended wake support.

For either Tier-1 backend verify it can:

- launch `codex-conductor resume <test-task>` or the smoke callback;
- start/reconnect the SDK/app-server runtime;
- locate persisted state;
- exit cleanly;
- remove/disable temporary scheduler artifacts.

### LS-9 — real quota boundary acceptance test

Later, during R5:

- run an explicitly authorized test task until a natural usage-window stop;
- confirm `waiting_quota`;
- confirm reset/wake scheduling;
- close Codex/app-server if desired;
- allow scheduler wake;
- require a fresh quota read;
- resume the same root thread;
- confirm model binding;
- continue without manual prompt.

This is the R5 release gate, not required to start R1 after the rest of R0 is frozen.

## 13. R0 disposition

**Upstream/design review: PASS WITH LOCAL SMOKE REQUIRED.**

No upstream capability gap currently forces abandonment of the proposed v3 architecture.

The most important corrections discovered during R0 are:

1. model binding must be task-frozen because app-server itself permits model changes;
2. Goals are more automatable than assumed and should be integrated earlier;
3. quota state is structured enough for a safe scheduler, but native cross-window auto-resume is still not a reliable host guarantee.

R1 implementation may begin after the R0 architecture and smoke-harness contract are frozen. Tier-1 host validation remains tracked separately: LS-1 through LS-8 must pass on both Windows CLI and Linux CLI before v3 release qualification, or a specific non-core probe must have an explicit documented fallback. LS-9 remains the R5 acceptance gate on at least one real quota boundary and should subsequently be exercised on both Tier-1 scheduler backends.


## 14. Platform correction

R0 originally over-emphasized Windows because the user's connected workstation and scheduler discussion were Windows-based. That is not the product scope.

v3 is CLI/runtime-first. Windows Codex CLI and Linux Codex CLI are equal Tier-1 execution targets. The Codex Desktop/App is an optional plugin bridge only.

Common logic must be identical across both Tier-1 targets:

- model-profile resolution and task-frozen exact bindings;
- SDK/app-server thread/turn lifecycle;
- root read-only / worker write boundaries;
- repository guards and validation freshness;
- Goal integration;
- quota classification and task state;
- role-aware resume.

Platform-specific code is limited primarily to:

- path/user-data conventions;
- process lifecycle details;
- scheduler/wake adapter;
- OS capability diagnostics.

Linux scheduler baseline is `systemd --user`; Windows baseline is Task Scheduler. Neither platform is considered a fallback for the other.
