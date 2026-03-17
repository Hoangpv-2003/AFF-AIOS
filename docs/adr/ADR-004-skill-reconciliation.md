# ADR-004: Skill Reconciliation and Quarantine

## Status
Accepted

## Context
Skill drift giữa registry/runtime/git phải bị chặn thực thi tự động để tránh chạy artifact không còn tin cậy.

## Decision
- Drift rule: mismatch runtime/git digest so với registry digest => quarantine.
- Enforcement: skill ở `quarantined` không được execute.
- Recovery: chỉ cho phép recover có kiểm soát từ `quarantined` về `reviewed/approved`.

## Evidence
- Reconciliation implementation: `app/infrastructure/reconciliation/reconcile_service.py`.
- Drift quarantine test: `tests/integration/test_skill_drift_quarantine.py`.
- Runtime evidence baseline: `docs/adr/evidence/s1_sandbox_offline_2026-03-17.json`.

## Acceptance Result (2026-03-17)
- Inject drift => auto quarantine => execute blocked (integration test) => PASS.
- Recovery transitions controlled in registry state machine => PASS.
