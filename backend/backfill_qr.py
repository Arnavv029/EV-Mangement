"""
Backfill QR codes for all existing bookings that are missing them.
Run with: python manage.py runscript backfill_qr
  (or)   python backfill_qr.py  (from backend/ with DJANGO_SETTINGS_MODULE set)
"""

import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ev_backend.settings')
django.setup()

from core.models import Booking
from core.utils.qr_generator import generate_qr_code

missing = Booking.objects.filter(qr_code='') | Booking.objects.filter(qr_code__isnull=True)
total = missing.count()
print(f'Bookings missing QR code: {total}')

fixed = 0
errors = 0
for b in missing:
    try:
        b.qr_code = generate_qr_code(b)
        b.save(update_fields=['qr_code'])
        fixed += 1
        print(f'  [OK] {b.booking_id} — {b.full_name}')
    except Exception as e:
        errors += 1
        print(f'  [ERR] {b.booking_id}: {e}')

all_qr = Booking.objects.exclude(qr_code='').exclude(qr_code__isnull=True).count()
print(f'\nDone! Fixed={fixed} Errors={errors}')
print(f'Total bookings with QR now: {all_qr}')
