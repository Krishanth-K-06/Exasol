from app.control import PolicyEngine, SQLValidator


def test_validator_blocks_unbounded_delete():
    result = SQLValidator().validate("DELETE FROM orders", {"orders"})
    assert not result.allowed


def test_validator_allows_scoped_sandbox_update():
    result = SQLValidator().validate("UPDATE orders SET customer_id = customer_id WHERE customer_id IS NOT NULL", {"orders"})
    assert result.allowed


def test_high_risk_requires_approval():
    result = PolicyEngine().authorize(risk_level="HIGH", sandbox_passed=True)
    assert not result.allowed
