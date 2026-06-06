"""
Booking Views — For EV Users
==============================
Endpoints:
  POST /api/bookings/                    → Create booking + process payment + generate QR
  GET  /api/bookings/history/            → User's booking history
  GET  /api/bookings/{id}/               → Single booking detail (with QR)
  GET  /api/bookings/{id}/refund-preview/ → Show refund amount before cancelling
  POST /api/bookings/{id}/cancel/        → Cancel booking + initiate refund

PAYMENT FLOW:
  1. Frontend sends booking details + payment details
  2. Backend validates slot availability
  3. Backend processes payment via simulate_payment()
  4. If payment succeeds → create booking, generate QR
  5. If payment fails → return error (slot NOT booked, user can retry)

CANCELLATION + REFUND POLICY:
  Cancel 30+ min before slot start →  100% refund
  Cancel  0-30 min before slot     →   70% refund
  Cancel  0-30 min after slot start →  50% refund
  Cancel 30+ min after slot start  →    0% refund
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils import timezone

from core.models import Booking, TimeSlot, Review
from core.serializers import BookingCreateSerializer, BookingDetailSerializer
from core.utils.qr_generator import generate_qr_code
from core.utils.payment_processor import calculate_refund_percentage, refund_reason
from core.utils.upi_payment import (
    generate_upi_qr,
    build_upi_url,
    validate_utr,
    MERCHANT_UPI_ID,
    MERCHANT_NAME,
    MINIMUM_AMOUNT,
)


# ─────────────────────────────────────────────────────────────────────────────
# UPI QR CODE — generate real payment QR for the frontend
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def upi_qr_view(request):
    """
    Generates a real UPI payment QR code the user scans with GPay/PhonePe/Paytm.

    Query params:
      ?amount=120.00        ← exact amount to charge
      ?note=Booking+HEV-5   ← shown in payment history

    Response:
    {
        "qr_code":      "iVBORw0KGgo...",   ← base64 PNG
        "upi_url":      "upi://pay?pa=9302117033@ybl&...",
        "upi_id":       "9302117033@ybl",
        "merchant":     "HapticEV",
        "amount":       120.00,
        "minimum":      5.0,
        "intent_gpay":  "gpay://upi/pay?...",
        "intent_phone": "phonepe://pay?...",
        "intent_paytm": "paytmmp://pay?...",
    }
    """
    raw_amount = request.query_params.get('amount', '0')
    note       = request.query_params.get('note', 'HapticEV Booking')

    try:
        amount = max(float(raw_amount), MINIMUM_AMOUNT)
    except (ValueError, TypeError):
        amount = MINIMUM_AMOUNT

    qr_b64, upi_url = generate_upi_qr(amount, note)

    return Response({
        'qr_code':      qr_b64,
        'upi_url':      upi_url,
        'upi_id':       MERCHANT_UPI_ID,
        'merchant':     MERCHANT_NAME,
        'amount':       round(amount, 2),
        'minimum':      MINIMUM_AMOUNT,
        # App-specific intent URLs (open UPI app directly)
        'intent_gpay':  upi_url.replace('upi://', 'gpay://'),
        'intent_phone': upi_url.replace('upi://', 'phonepe://'),
        'intent_paytm': upi_url.replace('upi://', 'paytmmp://'),
    })


# ─────────────────────────────────────────────────────────────────────────────
# CREATE BOOKING  (payment → slot lock → QR)
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_booking_view(request):
    """
    Full flow:
      1. Validate input (slot, personal, vehicle, payment details)
      2. Check slot availability
      3. Process payment (simulate gateway)
      4. If payment OK → create booking, increment slot count, generate QR
      5. Return booking + QR
    """
    serializer = BookingCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    vd = serializer.validated_data  # shorthand

    payment_method = vd.get('payment_method')
    amount         = float(vd.get('amount_paid') or 0)

    # ── Step 1: Validate payment proof ────────────────────────────────────
    if payment_method == 'upi':
        # For real UPI: validate the UTR number the user got from their payment app
        utr_number = vd.get('utr_number', '').strip()
        is_valid, utr_error = validate_utr(utr_number)
        if not is_valid:
            return Response({'error': utr_error}, status=status.HTTP_400_BAD_REQUEST)
        txn_id = utr_number.upper()   # UTR itself IS the transaction reference

    elif payment_method == 'debit_card':
        # Simulation — replace with Razorpay for real card processing
        card_num = vd.get('card_number', '').replace(' ', '')
        txn_id   = 'CARD' + card_num[-4:] + str(int(amount * 100))

    elif payment_method == 'net_banking':
        # Simulation — replace with Razorpay for real net banking
        txn_id = 'NB' + vd.get('bank_name', 'BANK')[:4].upper() + str(int(amount * 100))

    else:
        return Response(
            {'error': 'Invalid payment method.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ── Step 2: Lock slot + create booking atomically ─────────────────────
    try:
        with transaction.atomic():
            slot = TimeSlot.objects.select_for_update().get(pk=vd['slot'].pk)

            if slot.is_full:
                # Payment succeeded but slot just got filled — in real life
                # you would trigger a refund here. For simulation, fail gracefully.
                return Response(
                    {'error': 'Slot was just booked by someone else. Please choose another slot. Your payment will be reversed within 2–3 business days.'},
                    status=status.HTTP_409_CONFLICT
                )

            booking = Booking.objects.create(
                user           = request.user,
                station        = slot.station,
                slot           = slot,
                full_name      = vd['full_name'],
                phone          = vd['phone'],
                email          = vd['email'],
                vehicle_number = vd.get('vehicle_number', ''),
                vehicle_type   = vd.get('vehicle_type', ''),
                payment_method = vd.get('payment_method'),
                amount_paid    = amount if amount else None,
                payment_status = 'paid',
                transaction_id = txn_id,
                status         = 'pending',
            )

            slot.booked_count += 1
            slot.save()

            # QR generated ONLY after payment is confirmed
            booking.qr_code = generate_qr_code(booking)
            booking.save()

    except Exception as e:
        return Response(
            {'error': f'Booking failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response({
        'message': 'Payment successful! Booking confirmed. Show the QR code at the station.',
        'booking': BookingDetailSerializer(booking, context={'request': request}).data,
    }, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────────────────────────────────────
# REFUND PREVIEW  (GET — does NOT cancel, just shows what refund would be)
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def refund_preview_view(request, pk):
    """
    Returns the refund amount the user would get if they cancel RIGHT NOW.
    Frontend calls this when the cancel modal opens so user sees before deciding.

    Response:
    {
        "refund_percentage": 70,
        "refund_amount": 56.00,
        "reason": "Cancelled within 30 minutes before slot — 70% refund.",
        "amount_paid": 80.00,
        "can_cancel": true
    }
    """
    try:
        booking = Booking.objects.get(pk=pk, user=request.user)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

    if booking.status in ('cancelled', 'completed', 'rejected'):
        return Response(
            {'error': 'This booking cannot be cancelled.', 'can_cancel': False},
            status=status.HTTP_400_BAD_REQUEST
        )

    pct = calculate_refund_percentage(
        booking.slot.date,
        booking.slot.start_time
    )
    paid   = float(booking.amount_paid or 0)
    refund = round(paid * pct / 100, 2)

    return Response({
        'refund_percentage': pct,
        'refund_amount':     refund,
        'reason':            refund_reason(pct),
        'amount_paid':       paid,
        'can_cancel':        True,
    })


# ─────────────────────────────────────────────────────────────────────────────
# CANCEL BOOKING  (POST — actually cancels and initiates refund)
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_booking_view(request, pk):
    """
    Cancels a booking and calculates the refund.

    Steps:
      1. Validate booking belongs to user + is cancellable
      2. Calculate refund percentage based on current time
      3. Update booking: status='cancelled', refund fields
      4. Free up the slot (decrement booked_count)
      5. Return refund details

    Response:
    {
        "message": "Booking cancelled successfully.",
        "refund_percentage": 70,
        "refund_amount": 56.00,
        "reason": "...",
        "booking": { ...full booking... }
    }
    """
    try:
        booking = Booking.objects.get(pk=pk, user=request.user)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Only pending or confirmed bookings can be cancelled
    if booking.status in ('cancelled', 'completed', 'rejected'):
        return Response(
            {'error': f'Cannot cancel a booking with status "{booking.status}".'},
            status=status.HTTP_400_BAD_REQUEST
        )

    now = timezone.now()

    pct    = calculate_refund_percentage(booking.slot.date, booking.slot.start_time, now)
    paid   = float(booking.amount_paid or 0)
    refund = round(paid * pct / 100, 2)

    # Determine payment_status after cancellation
    if paid == 0:
        new_payment_status = 'refunded'          # Nothing to refund
    elif pct == 0:
        new_payment_status = 'paid'              # No refund — money kept
    elif pct == 100:
        new_payment_status = 'refunded'
    else:
        new_payment_status = 'partially_refunded'

    with transaction.atomic():
        booking.status           = 'cancelled'
        booking.cancelled_at     = now
        booking.refund_percentage = pct
        booking.refund_amount    = refund
        booking.payment_status   = new_payment_status
        booking.save()

        # Free up the slot
        slot = TimeSlot.objects.select_for_update().get(pk=booking.slot.pk)
        if slot.booked_count > 0:
            slot.booked_count -= 1
            slot.save()

    return Response({
        'message':          'Booking cancelled successfully.',
        'refund_percentage': pct,
        'refund_amount':     refund,
        'reason':            refund_reason(pct),
        'booking':           BookingDetailSerializer(booking, context={'request': request}).data,
    }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# USER'S BOOKING HISTORY
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_bookings_view(request):
    rev_exists = Review.objects.filter(booking_id=OuterRef('pk'))
    bookings = (
        Booking.objects.filter(user=request.user)
        .select_related('station', 'slot', 'station__owner')
        .annotate(has_review=Exists(rev_exists))
        .order_by('-created_at')
    )

    filter_status = request.query_params.get('status')
    if filter_status:
        bookings = bookings.filter(status=filter_status)

    serializer = BookingDetailSerializer(bookings, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# SINGLE BOOKING DETAIL
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_detail_view(request, pk):
    rev_exists = Review.objects.filter(booking_id=OuterRef('pk'))
    try:
        booking = (
            Booking.objects.filter(pk=pk, user=request.user)
            .select_related('station', 'slot', 'station__owner')
            .annotate(has_review=Exists(rev_exists))
            .get()
        )
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = BookingDetailSerializer(booking, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)
