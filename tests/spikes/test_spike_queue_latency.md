# Spike S2: Queue Latency

## Objective
Giữ latency class interactive ổn định dưới tải.

## Pass Criteria
- p95 interactive < 500ms ở 20 concurrent
- p95 interactive < 800ms với 100 batch backlog
- admission reason codes đúng format

## Fail Branch
Tách worker pools cứng, reserved concurrency; nếu cần thì đổi backend/sharding.
