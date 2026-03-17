# Canary Metrics Playbook

## Production Metric Sources
1. API gateway/request telemetry for error rate and latency.
2. Agent runtime metrics for provider errors.
3. Sandbox policy metrics for denied executions.
4. Queue and admission metrics for overload signals.

## Window Definitions
1. Short window: 5 minutes for fast rollback signals.
2. Confirm window: 15 minutes before each rollout step increase.
3. Compare against previous stable baseline for same traffic class.

## Decision Protocol
1. If any rollback trigger breaches threshold in short window, rollback immediately.
2. If short window is clean but confirm window degrades trend, hold at current percent.
3. Only proceed when both short and confirm windows are within thresholds.

## CI Simulation vs Production
1. CI simulation validates evaluator logic with mocked metrics.
2. Production decisioning uses live telemetry and on-call approval.
3. CI pass is necessary but never sufficient for production progression.
