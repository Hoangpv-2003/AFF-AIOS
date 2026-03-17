# Rollback Runbook

## Objective
Restore stable service behavior within the target incident response window.

## Immediate Actions
1. Enable runtime kill switch to freeze risky traffic.
2. Disable skill activation endpoints if drift risk is suspected.
3. Freeze coder generation and route to static-skill-only mode.

## Restore Previous Stable
1. Deploy previous stable artifact/tag.
2. Validate health and readiness endpoints.
3. Verify queue admission and budget controls return expected responses.
4. Re-enable traffic gradually (10% -> 50% -> 100%).

## Verification Checklist
1. Error rate returns below baseline threshold.
2. P95 latency returns within SLO.
3. Provider error rate and sandbox denial rate stabilize.
4. No unexpected drift quarantine spikes.
