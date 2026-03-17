# ADR-002: Queue SLA and Priority

## Status
Accepted

## Context
Queue admission cần định lượng để giữ latency interactive ổn định khi có batch backlog.

## Decision
- Giữ priority classes: `interactive`, `standard`, `batch`.
- Dùng admission/backpressure theo threshold hiện có trong constants.
- Giữ SLO mục tiêu interactive p95 < 500ms cho workload spike chuẩn.

## Evidence
- Spike script: `scripts/spikes/queue_load_sim.py`.
- Artifact: `docs/adr/evidence/s2_queue_latency_2026-03-17.json`.
- Relevant tests: `tests/perf/test_interactive_queue_latency.py`, `tests/perf/test_backpressure_admission.py`.

## Acceptance Result (2026-03-17)
- `interactive_p95_ms = 0.002` (artifact S2) => PASS (< 500ms).
- Admission reason format and overload rejection paths validated in perf/chaos tests => PASS.
