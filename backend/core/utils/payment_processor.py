"""
Payment Processor — Simulated Payment Gateway
==============================================
In a production app this would call Razorpay / Stripe / PayU.
Here we simulate the gateway: validate inputs, generate a TXN ID,
always succeed (you can add failure scenarios for testing).

Refund Policy:
  Cancel 30+ min before slot start  →  100 % refund
  Cancel  0–30 min before slot start →   70 % refund
  Cancel  0–30 min after slot start  →   50 % refund
  Cancel 30+ min after slot start    →    0 % refund (no refund)
"""

import random
import string
from datetime import datetime

from django.utils import timezone


# ─────────────────────────────────────────────────────────────────────────────
# GENERATE A FAKE TRANSACTION ID
# ─────────────────────────────────────────────────────────────────────────────
def _generate_txn_id(prefix='TXN'):
    digits = ''.join(random.choices(string.digits, k=12))
    return f"{prefix}{digits}"


# ─────────────────────────────────────────────────────────────────────────────
# SIMULATE PAYMENT
# Returns: (success: bool, transaction_id: str | None, error: str | None)
# ─────────────────────────────────────────────────────────────────────────────
def simulate_payment(payment_method, amount, payment_details):
    """
    Simulate calling a payment gateway.

    payment_method  : 'upi' | 'debit_card' | 'net_banking'
    amount          : Decimal or float  (₹ amount)
    payment_details : dict with method-specific keys

    Returns (True, 'TXN123456789012', None)  on success
    Returns (False, None, 'Error message')   on failure
    """

    # amount can be 0 / None when the station hasn't set a price yet — that's fine,
    # we still validate the payment method details; only reject explicit negatives.
    if amount is not None and float(amount) < 0:
        return False, None, 'Invalid payment amount.'

    # ── UPI ──────────────────────────────────────────────────────────────────
    if payment_method == 'upi':
        upi_id = payment_details.get('upi_id', '')
        if not upi_id or '@' not in upi_id:
            return False, None, 'Invalid UPI ID format.'
        txn_id = _generate_txn_id('UPI')

    # ── Debit / Credit Card ───────────────────────────────────────────────────
    elif payment_method == 'debit_card':
        card_number = payment_details.get('card_number', '').replace(' ', '')
        card_expiry = payment_details.get('card_expiry', '')
        card_cvv    = payment_details.get('card_cvv', '')

        if not card_number or len(card_number) != 16 or not card_number.isdigit():
            return False, None, 'Invalid card number. Must be 16 digits.'
        if not card_expiry or len(card_expiry) != 5:
            return False, None, 'Invalid card expiry. Use MM/YY format.'
        if not card_cvv or len(card_cvv) != 3 or not card_cvv.isdigit():
            return False, None, 'Invalid CVV. Must be 3 digits.'

        # Check expiry date
        try:
            month, year = card_expiry.split('/')
            exp_year  = int('20' + year)
            exp_month = int(month)
            now = datetime.now()
            if exp_year < now.year or (exp_year == now.year and exp_month < now.month):
                return False, None, 'Card has expired.'
        except Exception:
            return False, None, 'Invalid expiry date format.'

        txn_id = _generate_txn_id('CRD')

    # ── Net Banking ───────────────────────────────────────────────────────────
    elif payment_method == 'net_banking':
        bank_name = payment_details.get('bank_name', '')
        if not bank_name:
            return False, None, 'Please select a bank for net banking.'
        txn_id = _generate_txn_id('NB')

    else:
        return False, None, f'Unsupported payment method: {payment_method}'

    # All validations passed — payment "processed"
    return True, txn_id, None


# ─────────────────────────────────────────────────────────────────────────────
# CALCULATE REFUND PERCENTAGE
# ─────────────────────────────────────────────────────────────────────────────
def calculate_refund_percentage(slot_date, slot_start_time, cancel_time=None):
    """
    Determine how much refund the user gets based on WHEN they cancel.

    Slot example: 12:00 – 13:00 on 2026-05-15

    cancel_time vs slot_start (12:00):
      Before 11:30  → diff > 30 min  → 100 % refund
      11:30–12:00   → 0–30 min before → 70 % refund
      12:00–12:30   → 0–30 min after  → 50 % refund
      After 12:30   → > 30 min after  →  0 % refund
    """
    if cancel_time is None:
        cancel_time = timezone.now()

    # Build timezone-aware slot_start datetime
    naive_start = datetime.combine(slot_date, slot_start_time)
    try:
        slot_start = timezone.make_aware(naive_start, timezone.get_current_timezone())
    except Exception:
        slot_start = naive_start.replace(tzinfo=timezone.utc)

    # Positive = still in the future (before slot start)
    # Negative = slot has already started (after slot start)
    diff_minutes = (slot_start - cancel_time).total_seconds() / 60

    if diff_minutes > 30:
        return 100        # More than 30 min before  → full refund
    elif diff_minutes > 0:
        return 70         # 0–30 min before           → 70 % refund
    elif diff_minutes >= -30:
        return 50         # First 30 min of session   → 50 % refund
    else:
        return 0          # More than 30 min in       → no refund


# ─────────────────────────────────────────────────────────────────────────────
# HUMAN-READABLE REFUND REASON
# ─────────────────────────────────────────────────────────────────────────────
def refund_reason(percentage):
    reasons = {
        100: 'Cancelled 30+ minutes before slot — full refund.',
        70:  'Cancelled within 30 minutes before slot — 70% refund.',
        50:  'Cancelled within first 30 minutes of session — 50% refund.',
        0:   'Cancelled after 30 minutes into session — no refund.',
    }
    return reasons.get(percentage, 'Refund calculated.')
