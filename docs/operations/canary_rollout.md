# Canary Rollout

## Goal
Safely roll out new runtime behavior with measurable rollback criteria.

## Step Plan
1. Roll out to 5% traffic for 15 minutes.
2. If healthy, increase to 20% for 30 minutes.
3. If healthy, increase to 50% for 30 minutes.
4. If healthy, move to 100%.

## Required Metrics Window
- Request error rate
- P95 latency
- Provider error rate
- Sandbox denied rate

## Quantitative Rollback Triggers
- error_rate > 0.05
- p95_latency_ms > 1200
- provider_error_rate > 0.03
- sandbox_denied_rate > 0.10

## Rollback Protocol
1. Stop canary expansion immediately.
2. Trigger runtime kill switch for new task intake if needed.
3. Shift traffic back to previous stable version.
4. Capture incident timeline and metric snapshots.
