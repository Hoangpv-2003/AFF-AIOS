# Spike S1: Sandbox Offline

## Objective
Chứng minh sandbox chạy skill mẫu trong môi trường offline, không outbound, không external pull.

## Pass Criteria
- 100% local-image usage
- 0 outbound attempts
- p95 startup < 4s (30 runs)
- pass rate >= 95% (50 runs)

## Fail Branch
Nếu fail, chuyển sang prewarmed workers hoặc siết policy image bundle.
