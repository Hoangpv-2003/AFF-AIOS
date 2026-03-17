# ADR-006: Tracing Boundary

## Status
Accepted

## Context
Cần tách rõ boundary giữa request/infra tracing và prompt-level tracing nhưng vẫn giữ correlation chain end-to-end.

## Decision
- Request-level spans: middleware tại API layer (root trace/span theo request).
- Agent step spans/events: phát từ base agent lifecycle.
- Prompt-level spans/events: wrapper riêng, liên kết qua parent span.
- Correlation: thống nhất `trace_id` xuyên API -> agent -> prompt, truy vấn được qua traces endpoint.

## Evidence
- Tracing modules: `app/infrastructure/observability/tracing.py`, `app/infrastructure/observability/prompt_trace.py`.
- Middleware + propagation: `app/main.py`.
- End-to-end test: `tests/integration/test_trace_correlation_chain.py`.
- Agent contract stability artifact: `docs/adr/evidence/s3_agent_contract_2026-03-17.json`.

## Acceptance Result (2026-03-17)
- Trace chain includes HTTP root span + agent spans + prompt spans with parent correlation => PASS.
- Trace query endpoint returns linked events by trace id => PASS.
