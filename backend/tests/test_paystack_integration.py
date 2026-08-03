from decimal import Decimal

from app.paystack import PAID_MEMBERSHIP_PRICES


def test_membership_prices_are_server_controlled():
    assert PAID_MEMBERSHIP_PRICES["Premium Farmer — R99/month"] == Decimal("99.00")
    assert PAID_MEMBERSHIP_PRICES["Premium Buyer — R199/month"] == Decimal("199.00")


def test_paystack_routes_are_registered():
    from app.main import app
    paths = {getattr(route, "path", None) for route in app.routes}
    assert "/api/payments/paystack/initialize" in paths
    assert "/api/payments/paystack/verify/{reference}" in paths
    assert "/api/payments/paystack/status/{reference}" in paths
    assert "/api/payments/paystack/webhook" in paths
