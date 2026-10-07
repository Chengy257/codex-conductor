# Codex Conductor v3 Runtime Rebaseline Plan

Status: working architecture plan  
Date: 2026-10-07  
Target: `Chengy257/codex-conductor`  
Branch: `docs/v3-runtime-rebaseline-20261007`

## 1. Rebaseline decision

Codex Conductor v3 is not a larger skill package.

It is a Codex-native orchestration product composed of:

1. a portable Codex plugin for installation, commands, hooks, small model-visible skills, and optional MCP tool exposure;
2. a local deterministic controller/runtime that owns durable task state, model routing, worker dispatch, validation bookkeeping, quota continuity, and recovery;
3. Codex itself as the execution substrate, primarily through the official `openai-codex` Python SDK backed by persistent `codex app-server` threads, with `codex exec` retained only as a bounded compatibility/emergency path.

The strong root model remains responsible for semantic work: architecture, ambiguity resolution, task decomposition, routing decisions, change control, review, and final acceptance. Cheap workers perform bounded exploration and implementation.

The v3 design must not depend on the root model voluntarily remembering to spawn workers. Delegation and continuation become controller actions.

## 2. Relationship to glm-conductor

`glm-conductor` is a design reference only. ZCode-specific Native Workflow, Scheduled Task, plugin hooks, and workflow execution APIs are not portable to Codex and must not be copied as implementation assumptions.

The transferable principles are:

- strong-model reasoning is spent on planning and acceptance;
- bounded implementation is delegated to a cheaper model;
- model choice is explicit and fails closed instead of silently inheriting the root model;
- task state persists across session/process restarts;
- validation and final acceptance are bound to the actual repository state;
- automatic quota continuation is opt-in, bounded, observable, and safe;
- the conductor does not model facts already owned reliably by the host.

For Codex, the host/runtime boundary is different. Codex app-server owns thread/turn execution and native session state; Codex Conductor owns cross-turn task semantics and orchestration state that Codex does not yet guarantee.

## 3. Product shape

### 3.1 Plugin layer

Recommended layout:

```
codex-conductor/
├─ .codex-plugin/
│  └─ plugin.json
├─ skills/
│  └─ conductor/
│     └─ SKILL.md
├─ hooks/
│  ├─ hooks.json
│  ├─ session_start.py
│  ├─ subagent_start.py
│  ├─ subagent_stop.py
│  ├─ stop.py
│  └─ session_end.py
├─ runtime/
│  └─ codex_conductor/
├─ cli/
├─ profiles/
├─ docs/
└─ tests/
```

The plugin is the installable shell. It should not contain the orchestration logic in prose.

### 3.2 Runtime/controller layer

The runtime is a local Python package and CLI, initially invoked as:

```
codex-conductor ...
```

It owns:

- task creation and durable state;
- repository binding;
- root/worker model policy;
- task contracts and work-unit graph;
- app-server process lifecycle;
- Codex thread IDs and turn IDs;
- worker dispatch;
- worker result normalization;
- deterministic repository checks;
- change freshness;
- quota observation and waiting;
- scheduled wake/resume;
- retry budgets;
- final handoff to the root/reviewer;
- diagnostics and recovery.

It must remain smaller than a general-purpose workflow engine.

## 4. Codex-native execution substrate

### 4.1 Primary: official Codex Python SDK over persistent app-server

Use the published `openai-codex` Python SDK as the primary controller adapter. Stable SDK releases pin a matching Codex CLI runtime and already expose persistent threads, turn execution/streaming, sandbox presets, Goal operations, model listing, and thread resume.

Do not hand-roll the full JSON-RPC client. Keep a narrow protocol adapter only for capabilities not yet present on the public high-level SDK surface.

The controller should:

1. start or attach to one managed app-server process;
2. initialize the protocol;
3. create a root thread with the selected strong model;
4. persist the returned `thread.id`;
5. start turns through `turn/start`;
6. consume lifecycle/usage/error events;
7. use `thread/resume` when reconnecting after controller or app-server restart.

The app-server is the preferred basis for long-running sessions and quota recovery.

### 4.2 Runtime-version policy

The managed runtime should pin one tested `openai-codex` SDK release and its matching runtime rather than silently following whatever global Codex binary happens to be installed. `doctor` records SDK/runtime/global-CLI versions and reports mismatches.

An explicit compatibility mode may point `CodexConfig.codex_bin` at a system Codex binary, but it is not the default correctness path.

Python baseline: follow the SDK requirement (currently Python >=3.10); select the project-wide concrete Python version during R1 packaging.

### 4.3 Secondary: `codex exec`

Use `codex exec` for:

- short bounded workers;
- disposable explorer tasks;
- compatibility fallback when an app-server operation cannot be expressed reliably;
- emergency recovery paths.

Do not make `codex exec` the authoritative long-lived task store.

### 4.4 Native Codex subagents

Native subagents remain available as an optimization, but v3 must not rely on them for the core guarantee that implementation uses the task-selected worker model.

Reasons:

- root-triggered spawning remains partly model-driven;
- resumed roots may not reliably recover historical child agent state across versions;
- multi-agent behavior can consume quota unexpectedly;
- nested agent trees are harder to bound than explicit controller dispatch.

Therefore the default v3 worker is an independently launched Codex worker thread/process explicitly pinned to the task's exact worker-model binding. Native subagents can later be enabled for bounded parallel read-only work after runtime validation.

## 5. Model topology and task-frozen model binding

The architecture is role-based rather than permanently tied to one model generation.

Typical current choices are:

```
Root / Director
  selectable strong model, e.g. gpt-6.1-sol or gpt-6-astra
  selected reasoning effort
  architecture + plan + routing + review + acceptance

Explorer
  selectable economical task model, typically gpt-6-luna
  read-only repository investigation

Worker
  selectable economical task model, typically gpt-6-luna
  bounded implementation + focused verification

Optional Reviewer
  defaults to the task's root binding or another explicitly configured strong-review binding
  only for high-assurance tasks
```

### 5.1 Model profiles are defaults, not active-task identities

User/global configuration may define future-proof profiles such as `strong` and `worker` with preferred model lists. This lets new model generations replace today's defaults without redesigning the runtime.

At task creation, profiles are resolved to exact model IDs and reasoning efforts. The exact resolved values are persisted in task state.

### 5.2 Task binding invariant

Once a task becomes active, its model binding is frozen:

- root model/effort/provider are fixed;
- worker model/effort/provider are fixed;
- configuration changes affect new tasks only;
- auto-resume uses the stored exact binding and never re-resolves a symbolic profile;
- the root model may not choose a different worker model during execution;
- a worker may not select or spawn itself under another model.

Every root/worker `thread/start` and `thread/resume` must use and verify the stored binding.

App-server's `allowProviderModelFallback` must remain false. Missing/unavailable model access is a launch or resume blocker, never a reason to inherit/fallback silently.

### 5.3 Drift and reroute detection

App-server permits model changes through thread settings and resume overrides, and can emit `model/rerouted` for platform-managed rerouting.

The controller must therefore:

- observe the effective model returned by start/resume;
- observe `thread/settings/updated`;
- observe `model/rerouted`;
- reject task progression when the effective model no longer matches the binding.

A non-matching worker result is not valid acceptance evidence.

### 5.4 Explicit migration only

If a pinned model is retired or becomes unavailable, the task transitions to `waiting_user`.

No model-facing tool may mutate the binding.

A future user-only `task rebind-model` operation may be added, but it must run only with no active turn/worker, increment a binding generation, journal the decision, and invalidate stale validation/review. Initial v3 may simply require a new task.

## 6. Managed routing model

The managed v3 guarantee is stronger than the old skill routing: repository-writing implementation goes through the task-bound worker model. The strong root plans/reviews and remains read-only for managed write tasks.

Retain the route names for compatibility, but constrain their meaning:

| Delegability | Assurance | Route | Implementation | Independent review |
|---|---|---|---|---|
| low | standard | solo | root analysis/non-writing work; write requires explicit user opt-in | no |
| high | standard | delegate | bound worker model | no |
| low | high | audit | root analysis + independent review; write requires explicit user opt-in | yes |
| high | high | full | bound worker model | yes |

Any managed repository-writing implementation defaults to `delegate`; ambiguity is resolved by further root planning/exploration or user input, not by silently letting the root implement.

The controller, not the skill, should enforce the selected route.

The root may still revise a route when new evidence appears, but the revision must be written into task state before execution changes.

## 7. Task contract

A delegated unit must contain at least:

```yaml
id:
objective:
repository:
depends_on:
ownership:
interfaces:
constraints:
verification:
```

The runtime should validate:

- graph validity;
- dependency cycles;
- missing references;
- invalid/ambiguous ownership patterns;
- unsafe concurrent write overlaps.

The first v3 release should default to one active write worker per repository. Parallelism is permitted for read-only exploration. Parallel write support can be added only after ownership conflict handling is proven.

## 8. Durable task state

Store runtime state outside normal source files, preferably under:

```
<repo>/.codex-conductor/
```

and add it to local Git exclusion.

Minimal state:

```json
{
  "task_id": "...",
  "goal": "...",
  "repository": "...",
  "route": "...",
  "status": "...",
  "root_thread_id": "...",
  "active_worker": null,
  "model_binding": {
    "generation": 1,
    "root": {"model": "gpt-6.1-sol", "reasoning_effort": "high", "provider": "..."},
    "worker": {"model": "gpt-6-luna", "reasoning_effort": "high", "provider": "..."}
  },
  "phase": "...",
  "validation": {},
  "review": {},
  "quota": {},
  "continuity": {}
}
```

Recommended statuses:

- active
- waiting_quota
- waiting_user
- blocked
- validating
- reviewing
- completed
- cancelled
- failed

Do not mirror every Codex turn event into durable task state. Persist only facts required for orchestration and recovery.

## 9. Root/worker protocol

The root produces a structured implementation contract. The controller validates and dispatches it.

Worker return contract:

```json
{
  "status": "complete|partial|blocked",
  "changed_files": [],
  "verification": [],
  "risks": [],
  "replan_required": false,
  "summary": "..."
}
```

Worker claims are never sufficient for acceptance.

After the worker finishes, the controller collects the real repository diff and verification evidence and presents them to the root.

Root outcome:

- ACCEPT
- CORRECT
- REPLAN
- WAIT_USER

## 10. Repository safety and freshness

Port the useful deterministic ideas, but reimplement them for Codex.

### 10.1 Writer guard

Default invariant:

> At most one active Codex Conductor write execution per repository.

The guard must be process-safe and survive controller crashes. It must never expire merely because time passed. Recovery requires inspection and explicit force release or proof that the owning task is terminal.

### 10.2 Ownership guard

Before acceptance:

```
actual changed paths ⊆ declared task ownership
```

Violations block completion.

### 10.3 Change freshness

Compute a deterministic `change_id` from:

- base revision;
- relevant changed paths;
- file contents/state.

Validation and review records bind to `change_id`.

Any subsequent relevant repository modification invalidates stale validation/review.

## 11. Codex hooks

Hooks are supporting instrumentation, not the primary scheduler.

Use plugin-bundled hooks for:

- `SessionStart`: load task identity/recovery context;
- `SubagentStart` / `SubagentStop`: observe native subagent use when enabled;
- `Stop`: refuse/flag premature task completion when controller invariants fail;
- `SessionEnd`: checkpoint metadata;
- optionally `PostToolUse`: lightweight diagnostics only.

Do not implement orchestration loops inside hooks.

Hooks must degrade visibly if untrusted or unavailable; the controller remains authoritative.

## 12. Skills

Keep one small conductor skill for user/model-facing semantics:

- explain root responsibilities;
- describe the route modes;
- tell the root how to emit a task contract;
- explain acceptance outcomes.

The skill must not pretend to enforce model routing, worker launch, quota resume, or repository locks.

Target: approximately 30–60 lines, not a runtime specification.

## 13. Quota-aware execution

This is a first-class v3 capability.

### 13.1 Inputs

The runtime should consume structured Codex/app-server usage information when available, including:

- rate-limit bucket;
- used/remaining percentage;
- `resetsAt`;
- ordinary usage allowed;
- rate-limit reached type;
- credits/spend-control status.

Do not infer recovery only from elapsed time or percentages when the backend provides an explicit availability flag.

### 13.2 Quota failure classification

Separate:

- usage limit reached;
- workspace/account credit exhaustion;
- transient provider error;
- concurrency/subagent limit;
- network failure;
- permission/approval block.

Only true temporary usage-window exhaustion enters `waiting_quota`.

### 13.3 Automatic wake design

Automatic continuation must be opt-in per task.

When a task hits a temporary usage limit:

1. checkpoint controller task state;
2. record Codex root thread ID and the interrupted phase;
3. capture the server-provided reset timestamp when available;
4. transition to `waiting_quota`;
5. release resources that should not remain live while waiting;
6. create a local wake record;
7. sleep without model calls;
8. at/after the reset time, query account/rate-limit state again;
9. only resume when ordinary usage is confirmed available;
10. reconnect/start app-server if needed;
11. `thread/resume` the persisted root thread;
12. start a continuation turn carrying a compact controller checkpoint;
13. revalidate repository state and permissions before writes;
14. continue until task completion, user input, a non-quota blocker, or the configured resume budget is exhausted.

### 13.4 Wake scheduler

Do not depend on the Codex process remaining alive.

Implement a small local supervisor/scheduler.

Cross-platform target:

- Windows: Task Scheduler backend;
- Linux: systemd user timer or durable supervisor;
- macOS: launchd;
- portable fallback: foreground `codex-conductor supervise`.

The runtime should expose a common scheduler adapter rather than embedding OS-specific behavior in task logic.

### 13.5 Bounded continuity

State:

```json
{
  "mode": "manual|auto",
  "max_resumes": 3,
  "resume_count": 0,
  "wake_at": null,
  "scheduler_ref": null
}
```

Rules:

- auto resume must be explicitly enabled;
- each successful quota-window continuation consumes a resume budget unit;
- when the budget is exhausted, transition to `waiting_user`;
- repeated quota errors immediately after wake use bounded backoff and fresh rate-limit checks;
- never spin/busy-wait with model calls.

### 13.6 Resume safety gate

Before every automatic resumed write phase verify:

- repository identity still matches;
- branch/base assumptions remain valid;
- no conflicting external changes invalidate the task contract;
- writer guard is acquirable;
- effective approval/sandbox profile is acceptable;
- worker model is still available;
- usage is actually available.

If any check fails, stop at `waiting_user` or `blocked`.

## 14. Native Goals integration

Codex Goals are useful but are not the v3 scheduler.

R0 confirms that current app-server exposes noninteractive `thread/goal/set`, `thread/goal/get`, and `thread/goal/clear`, with goal states including `active`, `paused`, `blocked`, `usageLimited`, `budgetLimited`, and `complete`.

Therefore native Goal integration moves earlier into the root-session runtime:

- the root thread may use a native Goal as its persistent objective;
- Conductor may read/update Goal state through app-server;
- `usageLimited` can be mapped into the Conductor quota-continuity path;
- Goal state remains thread-local semantic state, not the authoritative cross-process scheduler;
- controller state remains authoritative for model binding, repository guards, quota wake scheduling, validation, and acceptance;
- automatic cross-window resume remains external/local because Codex still does not provide a reliable general host guarantee for unattended quota-window wake.

## 15. SDK-backed controller

Implement a thin Conductor adapter around the official Codex Python SDK, with a narrow typed raw-protocol escape hatch only where required. It must support:

- process start/stop/reconnect;
- initialize handshake;
- thread start/resume;
- turn start;
- event streaming;
- terminal turn state detection;
- rate-limit event extraction;
- thread metadata persistence;
- bounded reconnect;
- cancellation.

Do not expose raw JSON-RPC details to users.

Authoritative managed execution is runtime-first: tasks launched through `codex-conductor run` / equivalent controller entrypoints receive the hard model, sandbox and continuity guarantees. The Codex plugin is a convenience/integration front door; an arbitrary pre-existing Codex session is not silently claimed as managed.

Initial architecture:

```
Codex Plugin / codex-conductor CLI
          |
          v
Local Controller (official Codex Python SDK)
  |       |        |
  |       |        +-- Scheduler / Wake
  |       +----------- State + Guards
  +------------------- App-server Adapter
                           |
                           v
                    Codex app-server
                      |           |
               bound root    bound workers
```

## 16. Worker execution strategy

Phase 1 should favor independent bounded worker launches rather than deep native subagent trees.

Preferred order:

1. app-server worker thread pinned to the task's exact worker-model binding;
2. otherwise `codex exec --model <pinned-worker-model>` bounded worker;
3. native named subagent only as an optional optimization.

This makes model routing observable and deterministic.

## 17. Observability

Provide:

```
codex-conductor status
codex-conductor tasks
codex-conductor inspect <task>
codex-conductor logs <task>
codex-conductor quota
codex-conductor doctor
```

Record:

- selected root/worker models;
- Codex version;
- app-server protocol version/capabilities;
- root/worker thread IDs;
- task transitions;
- quota classification;
- wake scheduling;
- resume outcomes;
- verification outcomes;
- final acceptance.

Do not build a full tracing platform in v3.

## 18. Recovery

Required recovery scenarios:

- controller crash;
- app-server crash;
- terminal closed;
- machine restart;
- quota window crossed while Codex is not running;
- stale writer guard;
- root thread can resume but prior native subagents cannot;
- worker failed after partial repository modification;
- rate-limit payload unavailable;
- approval/sandbox profile changed after resume.

The runtime must be able to reconstruct the task from controller state plus real repository state without relying on a live child-agent tree.

## 19. Security and permissions

The runtime must respect Codex sandbox/approval behavior rather than bypassing it by default.

Auto continuation may resume only within a previously authorized policy envelope.

Do not silently escalate:

- sandbox;
- filesystem scope;
- network permission;
- command approval policy.

A resumed task that requires stronger authority transitions to `waiting_user`.

## 20. Migration from current codex-conductor

Current assets:

- existing skill;
- named Luna TOML roles;
- routing documentation;
- smoke tests.

Migration:

- retain role text as source material;
- shrink SKILL.md substantially;
- keep named role profiles only where native custom agents remain useful;
- remove claims that skill prose guarantees delegation;
- move model selection, state, and validation into runtime code;
- archive old validation document as v2 historical behavior;
- no compatibility requirement for existing v2 orchestration semantics.

This is a deliberate v3 breaking architecture change.

## 21. Implementation phases

### R0 — Capability validation and architecture freeze

Deliver:

- current Codex CLI/app-server capability matrix;
- plugin/hook/custom-agent support matrix;
- exact thread/model/usage/rate-limit protocol observations;
- Windows auto-wake feasibility test;
- final architecture document.

Exit gate: no unverified host assumption remains in the main execution path.

### R1 — Plugin skeleton + runtime foundation

Deliver:

- portable/compatibility plugin manifests;
- CLI package;
- config loading;
- durable task state;
- repository binding;
- event journal;
- doctor/status commands;
- basic hooks.

No multi-agent implementation yet.

### R2 — App-server session runtime

Deliver:

- official Codex Python SDK adapter with version compatibility checks;
- root thread start/resume with exact task-frozen model binding;
- turn lifecycle;
- structured event/error normalization;
- thread persistence;
- native Goal set/get/clear baseline integration;
- Goal state preservation/readback across resume;
- restart/reconnect tests.

Exit gate: a root task survives app-server/controller restart.

### R3 — Deterministic bound-worker delegation

Deliver:

- root/worker model-profile resolution and entitlement smoke;
- task-frozen root/worker binding;
- provider fallback disabled;
- model drift/reroute detection;
- economical-model explorer;
- economical-model implementation worker;
- bounded contracts;
- one-writer guard;
- ownership checks;
- real diff collection;
- worker result normalization.

Exit gate: a non-trivial task demonstrably routes implementation to the task's pinned worker model without depending on root voluntary spawning.

### R4 — Validation and acceptance

Deliver:

- change_id;
- validation record;
- stale-evidence detection;
- root ACCEPT/CORRECT/REPLAN loop;
- optional fresh strong-model review for high-assurance route.

Exit gate: task cannot reach completed state from worker claims alone.

### R5 — Quota continuity

Deliver:

- account/rate-limit reader;
- Goal `usageLimited` mapping when a native Goal is active;
- error classifier;
- `waiting_quota`;
- reset-time persistence;
- scheduler abstraction;
- Windows Task Scheduler implementation first;
- automatic app-server restart + thread resume;
- bounded `max_resumes`;
- repository/sandbox/model safety preflight.

Exit gate: real controlled test crosses one quota/reset boundary and automatically resumes the same task/thread without manual user input.

### R6 — Native Codex integration improvements

Evaluate only after R0–R5 are stable:

- deeper use of native Goal lifecycle after the R2/R3 baseline integration;
- native subagents for read-only parallel exploration;
- SubagentStart/Stop telemetry;
- plugin MCP tools for controller inspection/control;
- macOS/Linux scheduler backends;
- optional worktree isolation for multiple independent repositories/tasks.

### R7 — Release hardening

Deliver:

- installation/update path;
- migration guide from v2;
- failure-injection tests;
- restart/recovery matrix;
- Windows-first real-use validation;
- documentation;
- release candidate.

## 22. Explicit non-goals for v3 initial release

Do not build:

- a general distributed workflow engine;
- a web dashboard;
- SQLite unless file-backed state proves inadequate;
- arbitrary nested worker trees;
- autonomous agent-to-agent chat fabric;
- multi-repository distributed transactions;
- full task marketplace;
- hidden sandbox escalation;
- token-saving claims without measurement;
- background busy polling.

## 23. Community projects to study, not copy

Use community implementations as targeted references:

- Astra/Sol + Luna orchestrators for explicit model routing and worker contracts;
- app-server based orchestrators for persistent Codex thread management;
- auto-resume tools for quota reset parsing and session re-entry;
- orchestrated-mode Codex forks for state-machine and role-boundary ideas.

Adopt mechanisms only after they are compatible with current upstream Codex.

## 24. Acceptance criteria for v3

A v3 release is successful when all of the following are demonstrated on real Codex:

1. The task-selected strong root model remains the planning/review authority.
2. A bounded implementation can be forced through the task-selected economical worker model by controller policy.
3. The controller survives process restart.
4. A root thread resumes through app-server using its persisted thread ID.
5. Repository state, not model claims, determines completion evidence.
6. A task hitting a real usage-window limit enters `waiting_quota` without spinning.
7. The local scheduler wakes after the reset window even if Codex was closed.
8. The controller confirms quota availability, resumes the same root task, and continues.
9. Auto-resume is bounded and can stop safely for permissions, repository drift, or user decisions.
10. Skills are optional guidance rather than the enforcement mechanism.

## 25. Recommended immediate next step

Do not implement R1 yet.

First execute R0 as an independent capability-validation round against the currently installed/latest Codex build, especially:

- app-server model selection per thread and exact-model verification;
- task-frozen root/worker binding across thread start/resume;
- model-drift and model-reroute observation;
- thread/resume behavior;
- usage/rate-limit events and `resetsAt`;
- behavior after app-server restart;
- noninteractive Goal control availability;
- Windows scheduler invocation of the controller;
- approval/sandbox persistence after resume.

After R0, freeze the architecture and then write one implementation specification covering R1–R5, rather than splitting into many small specification documents.
