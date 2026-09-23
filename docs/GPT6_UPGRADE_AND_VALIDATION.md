# GPT-6 Sol / Luna upgrade and validation

## Scope
Upgrade existing lightweight Codex Conductor in place. Retain one Sol director and three optional Luna roles. Do not add a separate scheduler, reviewer/researcher fleet, or mandatory role pipeline.

## Configuration contract
- The user selects the GPT-6 Sol root through Codex config or invocation.
- Named roles pin gpt-6-luna at medium. For high/max, use separately configured profiles and verify runtime precedence.
- Optional global default_subagent_model and default_subagent_reasoning_effort are fallback settings.
- Explicit named role TOML settings take precedence over default and spawn values under current Codex documentation.
- Respect read-only exploration, workspace-write implementation/testing, and approval policy; do not silently fall back to another model.

## Static checks
Run python3 -m unittest discover -s tests -v. Check actual TOML parsing, role/model/sandbox pins, and documentation consistency. Static tests do not prove runtime model selection.

## Runtime smoke checklist (manual on installed Codex)
1. Record codex --version, installed model availability, actual root model, merged user config and installed role profiles.
2. Spawn luna_explorer for a read-only lookup of a known file/symbol; inspect actual child model and sandbox via session telemetry.
3. Spawn luna_executor for a tiny reversible change with one focused test; inspect actual model and resulting diff.
4. Spawn luna_tester for the focused test; inspect actual model, sandbox, and exact result.
5. Have Sol review the diff and evidence, then ACCEPT/CORRECT/REPLAN.
6. If available, test an intentionally invalid model on a throwaway profile in an isolated session to confirm that misrouting is detected. Never mutate a live installed role during active work.

Evidence: model per child (or unverified if not observable), effort, sandbox, spawn parameters, commands, pass/fail/not-run results, final Sol decision.

## Rollout
Review upgrade branch, run static tests, and verify runtime spawning on your Codex installation. Back up locally customized role files before copying. Do not automatically rewrite personal ~/.codex/config.toml. Merge into main after checks.
