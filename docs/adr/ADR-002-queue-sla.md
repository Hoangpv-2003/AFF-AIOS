# ADR-002: Queue SLA and Priority

## Status
Draft

## Hypothesis
Interactive queue cần p95 < 500ms ở 20 concurrent, dù có batch backlog.

## To Finalize
- Kết quả từ spike `scripts/spikes/queue_load_sim.py`.
- Admission/backpressure thresholds thực tế.
