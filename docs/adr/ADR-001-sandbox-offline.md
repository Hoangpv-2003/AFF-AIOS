# ADR-001: Sandbox Offline Execution

## Status
Accepted (blocking)

## Context
Cần sandbox chạy an toàn trong môi trường offline/air-gapped, không phụ thuộc pull image từ internet.

## Decision
- Dùng local registry + pre-baked images.
- Network policy mặc định deny egress.
- Resource limits bắt buộc: CPU/MEM/TIME.

## Acceptance Criteria
- 100% sandbox runs không có external image pull.
- 0 outbound network calls từ sandbox runtime.
- p95 startup < 4s cho 30 runs.

## Rollback
- Chuyển sang worker prewarmed pool nếu startup latency vượt ngưỡng kéo dài.
