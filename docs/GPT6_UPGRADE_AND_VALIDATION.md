# GPT-6 Sol / Luna upgrade and validation

## Scope
Upgrade existing lightweight Codex Conductor in place. Retain one Sol director and three optional Luna roles. Do not add a separate scheduler, reviewer/researcher fleet, or mandatory role pipeline.

## Configuration contract
- The user selects the GPT-6 Sol root through Codex config or invocation.
- Named roles pin gpt-6-luna: Explorer medium, Executor max, Tester medium. Verify actual effective effort in child session telemetry.
- Optional global default_subagent_model and default_subagent_reasoning_effort are fallback settings.
- Explicit named role TOML settings take precedence over default and spawn values under current Codex documentation.
- Explorer requests read-only and implementation/testing request workspace-write. Actual A/B runtime evidence (2026-09-23): Explorer under workspace-write root ran workspace-write despite read-only role TOML; Explorer under read-only root ran read-only. Therefore do not claim independent Explorer sandbox isolation on this tested Codex build. The no-write instruction is behavioral, not enforced. For strict isolation use a separate `codex --model gpt-6-sol --sandbox read-only` root session. Revalidate after CLI updates. Do not silently fall back to another model.

## Static checks
Run python3 -m unittest discover -s tests -v. Check actual TOML parsing, role/model/sandbox pins, and documentation consistency. Static tests do not prove runtime model selection.

## Runtime smoke checklist (manual on installed Codex)
1. Record codex --version, installed model availability, actual root model, merged user config and installed role profiles.
2. Spawn luna_explorer for a read-only lookup of a known file/symbol; inspect actual child model and sandbox via session telemetry.
3. Spawn luna_executor for a tiny reversible change with one focused test; inspect actual model and resulting diff.
4. Spawn luna_tester for the focused test; inspect actual model, sandbox, and exact result.
5. Have Sol review the diff and evidence, then ACCEPT/CORRECT/REPLAN.
6. Explorer sandbox A/B completed 2026-09-23. Under root workspace-write, child gpt-6-luna/medium had workspace-write; under root read-only, child gpt-6-luna/medium had read-only. Evidence: child rollout IDs `01a0cde0-69bc-7662-a6d1-590c874f0bd9` (A) and `01a0cde3-6dc7-7ce0-98b6-193ba72e8999` (B). This establishes observed parent-correlated sandbox behavior, not a general guarantee about every Codex version. Keep independent sandbox isolation marked UNSUPPORTED/UNVERIFIED for this build; do not fail the overall model-routing check solely on this known limitation. Strict read-only workflows require a read-only root session. Recheck after updates.
7. If available, test an intentionally invalid model on a throwaway profile in an isolated session to confirm that misrouting is detected. Never mutate a live installed role during active work.

Evidence: model per child (or unverified if not observable), effort, sandbox, spawn parameters, commands, pass/fail/not-run results, final Sol decision.

## Rollout
Review upgrade branch, run static tests, and verify runtime spawning on your Codex installation. Back up locally customized role files before copying. Do not automatically rewrite personal ~/.codex/config.toml. Merge into main after checks.
