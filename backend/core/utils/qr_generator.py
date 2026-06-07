"""
QR Code Generator
==================
This utility generates a QR code for a booking and returns it
as a base64-encoded PNG string.

WHY BASE64?
  Instead of saving the QR as an image file and serving it via URL,
  we encode it as a base64 string. The frontend can use it directly:
    <img src="data:image/png;base64,iVBORw0KGgo..." />
  This avoids dealing with file storage and image URLs.

WHAT DATA GOES IN THE QR?
  The QR encodes a JSON string with:
    - booking_id (UUID) → The unique key for verification
    - user details
    - station details
    - slot time
  When the owner scans it, the app reads this JSON and verifies
  against the database using the booking_id.
"""

import qrcode
import base64
import json
from io import BytesIO


def generate_qr_code(booking):
    """
    Generate a QR code for a booking object.

    Args:
        booking: A Booking model instance

    Returns:
        str: Base64-encoded PNG image string (ready to embed in <img> tag)

    How it works:
      1. Build a dictionary with all booking details
      2. Convert it to a JSON string
      3. Generate a QR code image from that JSON string
      4. Save the image to an in-memory buffer (BytesIO)
      5. Encode the buffer as base64
      6. Return the base64 string
    """

    # ── Step 1: Build the data that will be encoded in the QR ─────────────────
    qr_data = {
        "booking_id": str(booking.booking_id),      # UUID string
        "user_name": booking.full_name,
        "user_email": booking.email,
        "user_phone": booking.phone,
        "station_name": booking.station.name,
        "station_location": booking.station.location_text,
        "slot_date": str(booking.slot.date),
        "slot_start": str(booking.slot.start_time),
        "slot_end": str(booking.slot.end_time),
        "status": booking.status,
    }

    # ── Step 2: Convert dictionary to JSON string ──────────────────────────────
    # json.dumps() converts Python dict → JSON string
    qr_content = json.dumps(qr_data)

    # ── Step 3: Create QR Code image ──────────────────────────────────────────
    qr = qrcode.QRCode(
        version=1,              # QR size (1 = smallest, 40 = largest)
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # 7% error recovery
        box_size=10,            # Size of each square in the QR grid
        border=4,               # White border thickness
    )
    qr.add_data(qr_content)
    qr.make(fit=True)           # Auto-resize to fit all data

    # Create the actual image (black and white)
    img = qr.make_image(fill_color="black", back_color="white")

    # ── Step 4: Save image to memory buffer ───────────────────────────────────
    # BytesIO = an in-memory file. No actual file is written to disk.
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)  # Go back to the start of the buffer

    # ── Step 5: Encode as base64 ───────────────────────────────────────────────
    # base64.b64encode() → converts raw bytes to base64 bytes
    # .decode('utf-8')   → converts base64 bytes to a Python string
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    # ── Step 6: Return base64 string ──────────────────────────────────────────
    # Frontend uses this like:
    #   <img src={`data:image/png;base64,${qr_code}`} />
    return img_base64
