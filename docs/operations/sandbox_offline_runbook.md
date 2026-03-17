# Sandbox Offline Runbook

## Purpose
Run reviewer sandbox checks in offline mode with deny-by-default network policy.

## Preconditions
- Offline profile is active (`sandbox_offline_mode=true`).
- Required runtime image/tooling is preloaded locally.
- No outbound internet access is required for review pipeline.

## Image Preload and Update Procedure
1. Build or pull approved sandbox image in connected environment.
2. Export image tar artifact and checksum.
3. Transfer artifact to offline environment.
4. Import image and verify checksum before enabling runtime.
5. Record image version, digest, and import timestamp in ops log.

## Offline Execution Checklist
1. Verify policy is deny-by-default for network egress.
2. Start API stack and ensure `/health` and `/ready` are green.
3. Trigger reviewer flow with a safe artifact set.
4. Confirm sandbox result is success and contains no policy violations.
5. Trigger reviewer flow that requests network access.
6. Confirm failure with `NETWORK_EGRESS_DENIED`.

## Incident Troubleshooting
- Symptom: reviewer fails for safe artifacts.
  - Check command/process policy and resource limits.
  - Validate CPU/memory/timeout caps are not overly strict.
- Symptom: network attempts are not blocked.
  - Validate `allow_network=false` in active sandbox policy.
  - Re-run drift/security test to confirm expected denial.
- Symptom: missing artifacts/log output.
  - Verify runner output path permissions.
  - Check runtime stderr for policy violations.

## Rollback
1. Disable dynamic review execution.
2. Route to static-only reviewer checks.
3. Keep activation blocked for unreviewed outputs.
4. Open incident and attach sandbox policy snapshot.
