"""
Owner Views — Station Management & QR Verification
====================================================
Endpoints:
  POST  /api/owner/stations/              → Add a new station
  GET   /api/owner/stations/              → List owner's own stations
  POST  /api/owner/slots/                 → Create time slots for a station
  GET   /api/owner/bookings/              → View all bookings for owner's stations
  GET   /api/owner/bookings/{id}/         → Single booking detail
  PATCH /api/owner/bookings/{id}/status/  → Approve or reject a booking
  POST  /api/owner/verify-qr/             → Scan QR → get booking info

All these endpoints require:
  1. User must be logged in (IsAuthenticated)
  2. User must have role='owner' (checked by is_owner_or_403 helper)
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.db.models import Exists, OuterRef

from core.models import Station, TimeSlot, Booking, Review
from core.serializers import (
    StationSerializer,
    TimeSlotSerializer,
    BookingDetailSerializer,
    BookingStatusUpdateSerializer,
    QRVerifySerializer
)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Check if the request user is an owner
# ─────────────────────────────────────────────────────────────────────────────
def is_owner_or_403(request):
    """
    Returns None if the user is an owner.
    Returns a 403 Response if the user is NOT an owner.

    Usage in views:
        error = is_owner_or_403(request)
        if error: return error
    """
    if request.user.role != 'owner':
        return Response(
            {'error': 'Access denied. Only station owners can access this endpoint.'},
            status=status.HTTP_403_FORBIDDEN
        )
    return None


# ─────────────────────────────────────────────────────────────────────────────
# ADD / LIST STATIONS
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def owner_station_view(request):
    """
    GET  → List all stations belonging to this owner
    POST → Create a new station

    POST Request body:
    {
        "name": "Green Power Hub",
        "location_text": "MG Road, Bangalore, Karnataka",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "phone": "9876543210",
        "total_slots": 5,
        "charger_type": "Fast Charger - 50kW",
        "description": "Open 24/7. Near Metro station."
    }
    """

    error = is_owner_or_403(request)
    if error:
        return error

    if request.method == 'GET':
        stations = Station.objects.filter(owner=request.user)
        serializer = StationSerializer(stations, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = StationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Set owner automatically; always activate the station on creation
            serializer.save(owner=request.user, is_active=True)
            return Response({
                'message': 'Station added successfully!',
                'station': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# UPDATE STATION (price_per_hour, description, etc.)
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def owner_station_detail_view(request, pk):
    """
    GET   → Return single station belonging to this owner
    PATCH → Partially update station fields (e.g. price_per_hour, description)

    URL: PATCH /api/owner/stations/1/
    Body: { "price_per_hour": 120.00 }
    """
    error = is_owner_or_403(request)
    if error:
        return error

    try:
        station = Station.objects.get(pk=pk, owner=request.user)
    except Station.DoesNotExist:
        return Response(
            {'error': 'Station not found or you do not own this station.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = StationSerializer(station, context={'request': request})
        return Response(serializer.data)

    elif request.method == 'PATCH':
        serializer = StationSerializer(station, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Station updated successfully!',
                'station': serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# CREATE TIME SLOTS
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def owner_create_slots_view(request):
    """
    Owner defines time slots for their station.

    The owner can create multiple slots at once using 'bulk' mode,
    or create one slot at a time.

    Single slot request:
    {
        "station": 1,
        "date": "2026-05-06",
        "start_time": "09:00",
        "end_time": "10:00",
        "capacity": 3
    }

    Bulk slot request (multiple times on same date):
    {
        "station": 1,
        "date": "2026-05-06",
        "capacity": 3,
        "time_ranges": [
            {"start_time": "09:00", "end_time": "10:00"},
            {"start_time": "10:00", "end_time": "11:00"},
            {"start_time": "11:00", "end_time": "12:00"},
            {"start_time": "14:00", "end_time": "15:00"},
            {"start_time": "15:00", "end_time": "16:00"}
        ]
    }
    """

    error = is_owner_or_403(request)
    if error:
        return error

    station_id = request.data.get('station')
    date = request.data.get('date')
    capacity = request.data.get('capacity', 1)
    time_ranges = request.data.get('time_ranges')  # Optional: for bulk creation

    # Validate station ownership
    try:
        station = Station.objects.get(pk=station_id, owner=request.user)
    except Station.DoesNotExist:
        return Response(
            {'error': 'Station not found or you do not own this station.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # ── BULK CREATION ─────────────────────────────────────────────────────────
    if time_ranges:
        created_slots = []
        errors = []

        for tr in time_ranges:
            slot_data = {
                'station': station.id,
                'date': date,
                'start_time': tr.get('start_time'),
                'end_time': tr.get('end_time'),
                'capacity': capacity,
            }
            serializer = TimeSlotSerializer(data=slot_data)
            if serializer.is_valid():
                slot = serializer.save()
                created_slots.append(serializer.data)
            else:
                errors.append(serializer.errors)

        return Response({
            'message': f'{len(created_slots)} slot(s) created.',
            'created': created_slots,
            'errors': errors
        }, status=status.HTTP_201_CREATED)

    # ── SINGLE SLOT CREATION ──────────────────────────────────────────────────
    else:
        slot_data = {
            'station': station.id,
            'date': date,
            'start_time': request.data.get('start_time'),
            'end_time': request.data.get('end_time'),
            'capacity': capacity,
        }
        serializer = TimeSlotSerializer(data=slot_data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Time slot created!',
                'slot': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# VIEW ALL BOOKINGS (for owner's stations)
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def owner_bookings_view(request):
    """
    Returns all bookings made for this owner's stations.
    Shown in the Owner Dashboard.

    Optional filter: ?status=pending  (show only pending bookings)

    Response: All bookings with user name, slot time, station name, status.
    """

    error = is_owner_or_403(request)
    if error:
        return error

    # Get all bookings where the station belongs to this owner
    rev_exists = Review.objects.filter(booking_id=OuterRef('pk'))
    bookings = (
        Booking.objects.filter(station__owner=request.user)
        .select_related('user', 'station', 'slot')
        .annotate(has_review=Exists(rev_exists))
        .order_by('-created_at')
    )

    # Optional status filter
    filter_status = request.query_params.get('status')
    if filter_status:
        bookings = bookings.filter(status=filter_status)

    serializer = BookingDetailSerializer(bookings, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# SINGLE BOOKING DETAIL (owner view)
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def owner_booking_detail_view(request, pk):
    """
    Returns full details of a single booking.
    Owner uses this to see who booked, when, and what their status is.

    URL: GET /api/owner/bookings/1/
    """

    error = is_owner_or_403(request)
    if error:
        return error

    try:
        rev_exists = Review.objects.filter(booking_id=OuterRef('pk'))
        booking = (
            Booking.objects.filter(pk=pk, station__owner=request.user)
            .select_related('user', 'station', 'slot')
            .annotate(has_review=Exists(rev_exists))
            .get()
        )
    except Booking.DoesNotExist:
        return Response(
            {'error': 'Booking not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = BookingDetailSerializer(booking, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# APPROVE / REJECT / COMPLETE BOOKING
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def owner_update_booking_status_view(request, pk):
    """
    Owner updates booking status.

    URL: PATCH /api/owner/bookings/{id}/status/

    Body:
      { "status": "confirmed" }  — from pending
      { "status": "rejected" }   — from pending
      { "status": "completed" }  — from confirmed (charging session finished)
    """

    error = is_owner_or_403(request)
    if error:
        return error

    try:
        booking = Booking.objects.get(pk=pk, station__owner=request.user)
    except Booking.DoesNotExist:
        return Response(
            {'error': 'Booking not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = BookingStatusUpdateSerializer(
        booking,
        data=request.data,
        partial=True  # partial=True enables PATCH behavior
    )

    if serializer.is_valid():
        serializer.save()
        new_status = serializer.validated_data['status']

        # If owner REJECTS, free up the slot again
        if new_status == 'rejected' and booking.slot.booked_count > 0:
            booking.slot.booked_count -= 1
            booking.slot.save()

        return Response({
            'message': f'Booking {new_status} successfully!',
            'booking_id': str(booking.booking_id),
            'status': new_status
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# VERIFY QR CODE
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def owner_verify_qr_view(request):
    """
    Owner scans a user's QR code → backend returns booking details.

    This is the QR verification endpoint.

    HOW IT WORKS:
      1. Owner opens QR Scanner page on their device
      2. Camera reads the QR code
      3. QR code contains JSON: { "booking_id": "550e8400-..." }
      4. Frontend extracts the booking_id and sends it here
      5. Backend looks up the booking and returns details
      6. Owner sees: user name, slot time, station — then approves/rejects

    Request body:
    {
        "booking_id": "550e8400-e29b-41d4-a716-446655440000"
    }

    Response (success):
    {
        "valid": true,
        "booking": {
            "id": 1,
            "booking_id": "550e8400-...",
            "full_name": "Ramesh Kumar",
            "phone": "9876543210",
            "email": "ramesh@gmail.com",
            "station": { ... },
            "slot": { ... },
            "status": "pending"
        }
    }
    """

    error = is_owner_or_403(request)
    if error:
        return error

    serializer = QRVerifySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    booking_id = serializer.validated_data['booking_id']

    try:
        # Find the booking using the UUID from the QR code
        booking = Booking.objects.get(
            booking_id=booking_id,
            station__owner=request.user  # Security: only owner's own stations
        )
    except Booking.DoesNotExist:
        return Response({
            'valid': False,
            'error': 'Invalid QR code. Booking not found or does not belong to your station.'
        }, status=status.HTTP_404_NOT_FOUND)

    return Response({
        'valid': True,
        'booking': BookingDetailSerializer(booking, context={'request': request}).data
    }, status=status.HTTP_200_OK)
