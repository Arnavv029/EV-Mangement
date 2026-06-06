"""
When a user may submit a station review for a booking.
"""

from __future__ import annotations

from datetime import datetime

from django.utils import timezone


def booking_can_receive_review(booking) -> bool:
    """
    True if the user is allowed to POST a review for this booking.

    Rules:
    - No review yet for this booking.
    - Not pending / rejected / cancelled.
    - If status is completed → allowed (owner marked session finished).
    - If status is confirmed → allowed only after the booked slot end time
      (so users can rate without the owner clicking "complete").
    """
    # Local import avoids circular imports at app load
    from core.models import Review

    if Review.objects.filter(booking_id=booking.pk).exists():
        return False

    st = booking.status
    if st in ("pending", "rejected", "cancelled"):
        return False
    if st == "completed":
        return True
    if st == "confirmed":
        slot = booking.slot
        if slot is None:
            return False
        end_dt = timezone.make_aware(datetime.combine(slot.date, slot.end_time))
        return timezone.now() >= end_dt
    return False
