from app.infrastructure.canary.policy import CanaryPolicyEvaluator


def test_canary_policy_proceeds_when_metrics_within_thresholds():
    evaluator = CanaryPolicyEvaluator()
    decision = evaluator.evaluate(
        {
            "error_rate": 0.01,
            "p95_latency_ms": 700,
            "provider_error_rate": 0.01,
            "sandbox_denied_rate": 0.02,
        }
    )

    assert decision.action == "proceed"
    assert decision.reason == "WITHIN_SLO"


def test_canary_policy_rolls_back_on_error_rate_breach():
    evaluator = CanaryPolicyEvaluator()
    decision = evaluator.evaluate(
        {
            "error_rate": 0.08,
            "p95_latency_ms": 800,
            "provider_error_rate": 0.01,
            "sandbox_denied_rate": 0.03,
        }
    )

    assert decision.action == "rollback"
    assert decision.reason == "ERROR_RATE_EXCEEDED"


def test_canary_policy_rolls_back_on_latency_breach():
    evaluator = CanaryPolicyEvaluator()
    decision = evaluator.evaluate(
        {
            "error_rate": 0.02,
            "p95_latency_ms": 1400,
            "provider_error_rate": 0.01,
            "sandbox_denied_rate": 0.03,
        }
    )

    assert decision.action == "rollback"
    assert decision.reason == "LATENCY_P95_EXCEEDED"


def test_canary_policy_rolls_back_on_provider_error_breach():
    evaluator = CanaryPolicyEvaluator()
    decision = evaluator.evaluate(
        {
            "error_rate": 0.02,
            "p95_latency_ms": 900,
            "provider_error_rate": 0.05,
            "sandbox_denied_rate": 0.03,
        }
    )

    assert decision.action == "rollback"
    assert decision.reason == "PROVIDER_ERROR_RATE_EXCEEDED"


def test_canary_policy_rolls_back_on_sandbox_denied_breach():
    evaluator = CanaryPolicyEvaluator()
    decision = evaluator.evaluate(
        {
            "error_rate": 0.02,
            "p95_latency_ms": 900,
            "provider_error_rate": 0.02,
            "sandbox_denied_rate": 0.2,
        }
    )

    assert decision.action == "rollback"
    assert decision.reason == "SANDBOX_DENIED_RATE_EXCEEDED"
