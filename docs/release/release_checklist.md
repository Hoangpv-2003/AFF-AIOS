# Release Checklist

## Pre-release Validation
1. Confirm CI workflow is green for lint, unit, integration, contract, and security jobs.
2. Run full local regression: `python -m pytest -q`.
3. Verify critical chaos checks pass (reviewer unavailable escalation, queue overload degrade).
4. Verify sandbox outbound policy block test passes.

## Operational Readiness
1. Confirm kill switch command path is documented and tested.
2. Confirm budget hard-cutoff behavior is validated in integration tests.
3. Confirm tracing and reconciliation endpoints respond as expected.
4. Confirm offline sandbox runbook is available to on-call.

## Rollback Readiness
1. Prepare rollback tag for previous stable commit.
2. Confirm ability to enable runtime kill switch immediately.
3. Confirm ability to freeze new task intake and activation path.
4. Confirm incident communication template is ready.

## Sign-off
1. Engineering lead sign-off.
2. On-call sign-off.
3. Product/release manager sign-off.
