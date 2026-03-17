# ADR-003: Approval RBAC and Escalation

## Status
Accepted (blocking)

## Context
Approval không được là single-point bottleneck, cần timeout/expiry/escalation.

## Decision
- Role matrix: requester/reviewer/admin.
- Approval states: pending/approved/rejected/expired/escalated.
- Có fallback approver khi reviewer chính offline.

## Acceptance Criteria
- Approval timeout rate < 10% ở workload chuẩn.
- Escalation path hoạt động trong integration tests.

## Rollback
- Tạm khóa activation nếu approval service degraded.
