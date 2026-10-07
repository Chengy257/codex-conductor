# Codex Conductor v3 — R0 Smoke Harness Specification

Status: working R0 validation specification  
Date: 2026-10-07

## 1. Purpose

R0 validation must be repeatable after Codex upgrades. Build a small compatibility harness rather than relying on a one-time manual checklist.

Planned surface:

```
codex-conductor doctor
codex-conductor r0-smoke
codex-conductor r0-smoke --probe <LS-id>
codex-conductor r0-smoke --json
codex-conductor r0-smoke --root-model <id> --worker-model <id>
```

R0 may first implement this as `tools/r0_smoke.py`; R1 may absorb stable probes into the production CLI. This tooling is not a second orchestration runtime.

## 2. Isolation and safety

All live probes use a disposable Git repository under `%TEMP%\codex-conductor-r0-<run-id>`.

Never mutate a real project, persistent Codex config, existing user thread, account/workspace settings, reset credits, or permissions beyond the probe.

Model generations are inputs, not hard-coded constants. A binding is accepted only after exact model/effort/provider verification plus one successful minimal inference. Provider fallback is disabled.

## 3. Hard role-boundary probe

The core path must prevent the root from bypassing controller dispatch.

Target policy:

```
delegate/full root:
  native subagent spawning = disabled
  repository = read-only
  worker dispatch = controller only

worker:
  native subagent spawning = disabled
  repository = workspace-write
```

Current Codex exposes agent/multi-agent enablement, but R0 must verify the exact thread-scoped override form on the installed stable build. If it cannot be enforced per thread, use a dedicated managed Codex profile/config rather than falling back silently to prompt-only enforcement.

For explicit `solo/audit`, a separately authorized root execution context may have write access; that route is fixed before execution.

## 4. Required probes

### LS-1 — Environment/protocol

Record Codex version, SDK/runtime version, Windows version/arch, non-secret auth surface, app-server initialize, `model/list`, and required method/notification availability.

Required methods include `thread/start`, `thread/resume`, `thread/settings/update`, `turn/start`, Goal set/get/clear, `account/rateLimits/read`, and `model/list`.

Required notifications include settings updates, turn completion, Goal updates, rate-limit updates, and `model/rerouted`.

### LS-2 — Root binding

Start a disposable root thread with the requested strong model.

Require exact effective model/provider/effort, provider fallback off, native multi-agent disabled, read-only policy active, minimal inference success, and rejection of a controlled write attempt.

An optional alternate root model may be tested to prove configurability.

### LS-3 — Worker binding

Start a disposable worker thread with the requested worker model.

Require exact model/provider/effort, fallback off, native multi-agent disabled, workspace-write active, one bounded file edit, one focused verification command, and changed paths confined to smoke ownership.

### LS-4 — Drift/reroute

On a disposable thread only, change model through `thread/settings/update` when a second accessible model exists and require the detector to flag `MODEL_DRIFT`.

Do not deliberately trigger a platform/safety reroute. Feed a schema-valid `model/rerouted` fixture to the detector and require the turn to become non-conforming.

### LS-5 — App-server restart/resume

```
start managed SDK/app-server runtime
→ create persistent root thread
→ optionally set smoke Goal
→ persist thread id + exact binding
→ stop runtime
→ start fresh matching runtime
→ thread/resume(threadId, pinned binding)
```

Require same thread, exact binding, acceptable permissions, Goal readback, and no silent fallback/reroute.

### LS-6 — Native Goal control

On a dedicated smoke thread: set active objective → get → pause → get → block → get → reactivate → clear → confirm empty.

Do not fake `usageLimited` as a real quota event; use a fixture in R0 and a real event only for R5 acceptance.

### LS-7 — Quota read

Call `account/rateLimits/read` and record only redacted shape/evidence: limit ids, bucket presence, percentages if present, `resetsAt`, and `ordinaryUsageAllowed`.

Do not intentionally exhaust quota or consume reset credits.

### LS-8 — Windows scheduler wake

Create a temporary one-shot user scheduled task whose callback loads persisted smoke state and atomically writes a `wake.json` marker without inference.

Require creation without admin escalation, callback execution, matching state/run identity, successful exit, and cleanup.

Initial guarantee: wake works when the user session is available even if Codex, terminal, and app-server are closed.

After reboot, durable state survives and overdue tasks are recovered by a logon/startup catch-up scan. Do not claim pre-logon execution without separately validating an authorized Windows credential/service configuration.

## 5. Deferred LS-9 — real quota-window acceptance

LS-9 is an R5 release gate, not routine R0:

```
active
→ real usage-window exhaustion
→ waiting_quota
→ persist task/thread/binding/phase
→ schedule from resetsAt
→ wake
→ fresh rate-limit read
→ ordinary usage allowed
→ restart matching runtime
→ resume same root thread with exact binding
→ safety preflight
→ continue
```

Evidence must prove same task id, root thread id, binding generation and exact root/worker models, bounded resume-count increment, no busy model polling, and no permission escalation.

## 6. Results

Statuses: `PASS | FAIL | SKIP | INCOMPLETE`.

Recommended exit codes:

- 0 — all required probes PASS;
- 1 — required FAIL;
- 2 — required INCOMPLETE because of environment/auth/input;
- 3 — harness error.

`--json` records run id, Codex/SDK/runtime versions, platform, requested bindings, per-probe summary/evidence/remediation, and overall status. Secrets and model reasoning are never persisted.

## 7. doctor vs r0-smoke

`doctor` is passive by default: no inference and no settings mutation.

`r0-smoke` is explicit live validation. It may use a small amount of quota but operates only on disposable smoke resources.

## 8. CI split

CI validates deterministic logic only: result schema, binding comparison, drift/reroute handling, quota parser, scheduler command construction, state transitions, redaction, cleanup, and fake app-server transcript replay.

LS-1 through LS-8 are local integration tests. CI success must never be presented as proof of live account/Codex compatibility.

## 9. R0 freeze gate

Freeze R0 when upstream review remains PASS, this harness design is frozen, and LS-1 through LS-8 pass on the target Windows environment (or a non-core item has an explicit fallback).

LS-9 remains the R5 release gate. Then produce one consolidated R1–R5 implementation specification.
