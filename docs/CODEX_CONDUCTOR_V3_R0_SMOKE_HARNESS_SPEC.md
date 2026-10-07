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

All live probes use a disposable Git repository under the platform temp directory, for example:

```
Windows: %TEMP%\codex-conductor-r0-<run-id>\
Linux:  $TMPDIR/codex-conductor-r0-<run-id>/  (fallback /tmp)
```

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

Record global Codex version, pinned `openai-codex` SDK version, SDK-managed runtime version, OS family/version/arch, execution surface (Windows CLI / Linux CLI / WSL2-compatible Linux), non-secret auth surface, app-server initialize, `model/list`, plugin discovery, and required method/notification availability.

Required methods include `thread/start`, `thread/resume`, `thread/settings/update`, `turn/start`, Goal set/get/clear, `account/rateLimits/read`, and `model/list`.

Required notifications include settings updates, turn completion, Goal updates, rate-limit updates, and `model/rerouted`.

Plugin packaging check: validate the required `.codex-plugin/plugin.json` layout through the current Codex plugin tooling. Do not add a root-level `plugin.json`; current Codex plugin scaffolding treats `.codex-plugin/plugin.json` as the required manifest. Hook discovery is recorded separately because hooks are not a correctness dependency.

### LS-2 — Root binding

Start a disposable root thread with the requested strong model.

Require exact effective model/provider/effort, provider fallback off, native multi-agent disabled, read-only policy active, minimal inference success, and rejection of a controlled write attempt. Establish/verify the pinned reasoning effort before the first task turn rather than assuming a global config value was honored.

An optional alternate root model may be tested to prove configurability.

### LS-3 — Worker binding

Start a disposable worker thread with the requested worker model.

Require exact model/provider/effort, fallback off, native multi-agent disabled, workspace-write active, one bounded file edit, one focused verification command, and changed paths confined to smoke ownership. Establish/verify the pinned reasoning effort before the first worker task turn.

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

Require same thread, exact model/provider/effort binding after resume, acceptable permissions, Goal readback, and no silent fallback/reroute. Re-apply/verify pinned reasoning effort before continuation if the resume helper does not carry it directly.

### LS-6 — Native Goal control

On a dedicated smoke thread: set active objective → get → pause → get → block → get → reactivate → clear → confirm empty.

Also verify the orchestration discipline used by v3: an active root Goal is paused before an external worker phase so the root cannot autonomously start a competing implementation/review turn.

Do not fake `usageLimited` as a real quota event; use a fixture in R0 and a real event only for R5 acceptance.

### LS-7 — Quota read

Call `account/rateLimits/read` and record only redacted shape/evidence: limit ids, bucket presence, percentages if present, `resetsAt`, and `ordinaryUsageAllowed`.

Do not intentionally exhaust quota or consume reset credits.

### LS-8 — Tier-1 scheduler wake

Run a platform-specific one-shot scheduler probe. The callback loads persisted smoke state and atomically writes a `wake.json` marker without inference.

**Windows CLI**

Use Windows Task Scheduler under the normal user context. Require creation without admin escalation, callback execution, matching state/run identity, successful exit, and cleanup.

Initial Windows guarantee: wake works when the user session is available even if Codex, terminal, and app-server are closed. After reboot, durable state survives and overdue tasks are recovered by a logon/startup catch-up scan. Do not claim pre-logon execution without separately validating an authorized Windows credential/service configuration.

**Linux CLI**

Use a transient/temporary `systemd --user` service + timer when the user systemd manager is available. Require timer creation, callback execution, matching state/run identity, successful exit, and cleanup.

Initial Linux guarantee: wake works without an interactive Codex shell while the user systemd manager is running. For headless hosts, `loginctl enable-linger` may extend this across logout/reboot, but the smoke harness must only detect/report linger state; it must not silently enable it.

If `systemd --user` is unavailable (for example a minimal container or some WSL environments), run the portable foreground `codex-conductor supervise` probe and report `scheduler_mode=foreground_fallback`. This validates continuity logic but does not count as full unattended scheduler PASS.

## 5. Deferred LS-9 — real quota-window acceptance

LS-9 is an R5 release gate, not routine R0:

```
active root/worker/reviewer
→ real usage-window exhaustion
→ waiting_quota
→ persist task + active role/thread/turn/work-unit + model/runtime binding + phase
→ schedule from resetsAt
→ wake
→ fresh rate-limit read
→ ordinary usage allowed
→ restart matching runtime
→ resume the same active role thread with exact binding
→ inspect prior turn state
→ safety preflight
→ continue
```

Evidence must prove same task id, correct resumed role/thread id, binding generation, exact role model, matching SDK/runtime identity, bounded resume-count increment, no blind duplicate write after uncertain worker interruption, no busy model polling, and no permission escalation.

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

Freeze the R0 **architecture/design** when upstream review remains PASS and this dual-platform harness design is frozen.

Track host qualification independently:

- Windows CLI: LS-1 through LS-8;
- Linux CLI: LS-1 through LS-8.

Both Tier-1 host matrices must pass before v3 release qualification (or a non-core item has an explicit documented fallback).

LS-9 remains the R5 release gate. Exercise at least one real quota boundary during R5, then verify wake/resume behavior on both Tier-1 scheduler backends before release.


## 10. Tier-1 platform matrix

The smoke harness is one logical suite with two Tier-1 host profiles, not separate Windows and Linux products.

| Capability | Windows CLI | Linux CLI |
|---|---|---|
| SDK/app-server thread lifecycle | required | required |
| exact root/worker model binding | required | required |
| root read-only / worker write boundary | required | required |
| native subagent bypass disabled | required | required |
| Goal lifecycle | required | required |
| quota read/classification | required | required |
| process restart + thread resume | required | required |
| durable task state | required | required |
| unattended wake backend | Task Scheduler | systemd --user |
| portable fallback | supervise | supervise |
| graphical Codex app required | no | no |

WSL2 is tested as a Linux execution surface. If `systemd --user` is enabled, use the Linux scheduler path; otherwise report the foreground fallback instead of silently crossing into Windows Task Scheduler unless a future explicit WSL bridge is designed.
