"""Application-wide constants used across modules."""

API_V1_PREFIX = "/api/v1"

REQUEST_ID_HEADER = "X-Request-Id"
IDEMPOTENCY_KEY_HEADER = "Idempotency-Key"

QUEUE_CLASSES = ("interactive", "standard", "batch")

SLA_TARGET_MS = {
    "interactive": 500,
    "standard": 1500,
    "batch": 5000,
}

ADMISSION_DEPTH_THRESHOLDS = {
    "interactive": 2000,
    "standard": 1000,
    "batch": 500,
}

ADMISSION_REASON_CODES = {
    "accepted": "ACCEPTED",
    "queue_overloaded": "QUEUE_OVERLOADED",
    "invalid_priority": "INVALID_PRIORITY",
}

TASK_STATES = (
    "RECEIVED",
    "PLANNED",
    "CODED",
    "REVIEWED_PASS",
    "REVIEWED_WARN",
    "WAITING_APPROVAL",
    "APPROVED",
    "ACTIVATED",
    "FAILED",
    "CANCELLED",
)

REASON_CODES = (
    "TIMEOUT",
    "BUDGET_EXCEEDED",
    "SANDBOX_DENIED",
    "VALIDATION_FAILED",
    "PROVIDER_ERROR",
    "QUEUE_OVERLOADED",
    "USER_CANCELLED",
)

DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_RETRY_LIMIT = 2

