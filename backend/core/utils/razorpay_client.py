"""
Razorpay Client Utility
========================
Thin wrapper around the razorpay Python SDK.

Usage:
    from core.utils.razorpay_client import create_order, verify_payment_signature, refund_payment

All functions raise exceptions on failure — callers should catch them.
"""

import razorpay
from django.conf import settings


def _client():
    """Return an initialised Razorpay client using keys from settings."""
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_order(amount_paise: int, receipt: str, notes: dict = None) -> dict:
    """
    Create a Razorpay order.

    Args:
        amount_paise: Amount in smallest currency unit (paise). ₹120 = 12000 paise.
        receipt:      Unique receipt ID, e.g. "hev-42-1715000000".
        notes:        Optional dict of metadata (visible in Razorpay dashboard).

    Returns:
        Razorpay order dict with keys: id, amount, currency, receipt, status, ...
    """
    data = {
        'amount':   amount_paise,
        'currency': 'INR',
        'receipt':  receipt[:40],   # Razorpay caps receipt at 40 chars
        'notes':    notes or {},
    }
    return _client().order.create(data=data)


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """
    Verify the HMAC-SHA256 signature from Razorpay's payment response.

    Call this BEFORE creating a Booking. Returns True if valid, raises on failure.
    """
    params = {
        'razorpay_order_id':   order_id,
        'razorpay_payment_id': payment_id,
        'razorpay_signature':  signature,
    }
    # Raises razorpay.errors.SignatureVerificationError if invalid
    _client().utility.verify_payment_signature(params)
    return True


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """
    Verify the X-Razorpay-Signature header on incoming webhook events.
    Uses RAZORPAY_WEBHOOK_SECRET from settings.
    """
    _client().utility.verify_webhook_signature(
        body.decode('utf-8'),
        signature,
        settings.RAZORPAY_WEBHOOK_SECRET,
    )
    return True


def refund_payment(payment_id: str, amount_paise: int) -> dict:
    """
    Initiate a (partial) refund for a captured payment.

    Args:
        payment_id:   Razorpay payment ID (pay_...).
        amount_paise: Amount to refund in paise.

    Returns:
        Razorpay refund dict.
    """
    return _client().payment.refund(payment_id, {'amount': amount_paise})
