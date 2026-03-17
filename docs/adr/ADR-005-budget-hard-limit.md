# ADR-005: Budget Hard Limit

## Status
Accepted (blocking)

## Context
Cảnh báo cost không đủ, cần hard-cutoff trước provider call.

## Decision
- Quota hierarchy: task -> user -> org.
- Hard-fail khi vượt quota trước khi gọi LLM provider.
- Có kill switch runtime.

## Acceptance Criteria
- Runaway scenario bị chặn trước provider call.
- Budget reason codes chuẩn hóa trong logs/API.

## Rollback
- Freeze generation path và chuyển về static-skill mode.
