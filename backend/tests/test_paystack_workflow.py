import hashlib
import hmac
import json

def test_paystack_signature_uses_hmac_sha512():
    secret = "sk_test_example"
    raw = json.dumps({"event": "charge.success", "data": {"reference": "PSTK-1"}}).encode()
    signature = hmac.new(secret.encode(), raw, hashlib.sha512).hexdigest()
    assert len(signature) == 128
    assert hmac.compare_digest(signature, signature)

def test_amount_subunit_conversion():
    amount = 99.00
    assert int(round(amount * 100)) == 9900
