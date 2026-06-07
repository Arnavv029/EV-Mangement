"""
Real UPI Payment — QR Code + Deep Link Generator
==================================================
Generates a real UPI payment QR code pointing to the merchant's UPI ID.
Users scan this with GPay / PhonePe / Paytm and pay real money.

HOW IT WORKS:
  1. Backend builds a UPI Deep Link URL:
       upi://pay?pa=9302117033@ybl&pn=HapticEV&am=120.00&cu=INR&tn=Booking+HEV-001
  2. This URL is encoded into a QR code image (using the qrcode library)
  3. Frontend shows the QR → user scans → real payment happens in their UPI app
  4. UPI app shows a 12-digit UTR (Unique Transaction Reference)
  5. User enters UTR in our form → we store it as transaction_id
  6. Owner can verify UTR in their bank/UPI app statement

UTR FORMAT:
  UTR (Unique Transaction Reference) = 12-digit number assigned by NPCI
  Example: 312526571641
  Location in apps:
    GPay    → Tap transaction → "UPI transaction ID"
    PhonePe → Transaction history → "Transaction ID"
    Paytm   → History → "Order ID"
    BHIM    → History → "Transaction Ref No"
"""

import io
import base64
import re
import qrcode
from urllib.parse import quote

# ── Merchant configuration ────────────────────────────────────────────────────
MERCHANT_UPI_ID   = '9302117033@ybl'
MERCHANT_NAME     = 'HapticEV'
MINIMUM_AMOUNT    = 5.0       # ₹5 minimum charge
CURRENCY          = 'INR'


# ─────────────────────────────────────────────────────────────────────────────
# BUILD UPI DEEP LINK
# ─────────────────────────────────────────────────────────────────────────────
def build_upi_url(amount, transaction_note='HapticEV Booking'):
    """
    Build a standard UPI Intent URL.

    Works with: GPay, PhonePe, Paytm, BHIM, Amazon Pay, any UPI app.

    Format: upi://pay?pa=VPA&pn=NAME&am=AMOUNT&cu=INR&tn=NOTE
      pa = payee address (UPI ID)
      pn = payee name
      am = amount (2 decimal places)
      cu = currency
      tn = transaction note (shown in payment history)
    """
    amt = max(float(amount or 0), MINIMUM_AMOUNT)
    note_encoded = quote(transaction_note, safe='')

    return (
        f"upi://pay"
        f"?pa={MERCHANT_UPI_ID}"
        f"&pn={quote(MERCHANT_NAME)}"
        f"&am={amt:.2f}"
        f"&cu={CURRENCY}"
        f"&tn={note_encoded}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# GENERATE UPI QR CODE IMAGE (base64 PNG)
# ─────────────────────────────────────────────────────────────────────────────
def generate_upi_qr(amount, transaction_note='HapticEV Booking'):
    """
    Returns a base64-encoded PNG of the UPI payment QR code.
    Frontend uses it as: <img src="data:image/png;base64,..."/>

    The QR encodes the full UPI deep link URL.
    Any UPI-compatible app can scan it and initiate payment.
    """
    upi_url = build_upi_url(amount, transaction_note)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
        box_size=10,
        border=4,
    )
    qr.add_data(upi_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color='#1F2933', back_color='white')

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode('utf-8'), upi_url


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATE UTR NUMBER
# ─────────────────────────────────────────────────────────────────────────────
def validate_utr(utr_number):
    """
    Validate a UTR (Unique Transaction Reference) number.

    Rules:
    - Must be 12 digits (IMPS/UPI standard)
    - Some banks issue alphanumeric UTRs (allow those too)
    - Must be at least 10 characters

    Returns: (is_valid: bool, error_message: str | None)
    """
    if not utr_number:
        return False, 'UTR number is required to confirm your payment.'

    utr = utr_number.strip().upper()

    if len(utr) < 10:
        return False, 'UTR number must be at least 10 characters (check your payment app).'

    if len(utr) > 22:
        return False, 'UTR number seems too long. Please re-check.'

    # Must be alphanumeric only
    if not re.match(r'^[A-Z0-9]+$', utr):
        return False, 'UTR number can only contain letters and numbers.'

    return True, None
