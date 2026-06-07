"""
Reviews — users rate stations after a completed booking.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Booking, Review, Station
from core.serializers import ReviewListSerializer, BookingDetailSerializer
from core.utils.booking_review import booking_can_receive_review


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_booking_review_view(request, pk):
    """
    POST /api/bookings/{id}/review/
    Body: { "rating": 1-5, "comment": "optional text" }

    Allowed when the session is finished: status completed, or confirmed and
    the booked slot end time has passed. One review per booking.
    """
    try:
        booking = Booking.objects.select_related('slot', 'station').get(pk=pk, user=request.user)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

    if Review.objects.filter(booking=booking).exists():
        return Response(
            {'error': 'You have already submitted a review for this booking.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not booking_can_receive_review(booking):
        return Response(
            {
                'error': (
                    'You can rate this visit after your time slot has ended, or once the station '
                    'marks your session as completed.'
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        rating = int(request.data.get('rating', 0))
    except (TypeError, ValueError):
        rating = 0
    if rating < 1 or rating > 5:
        return Response(
            {'error': 'Rating must be an integer from 1 to 5.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    comment = (request.data.get('comment') or '').strip()

    review = Review.objects.create(
        user=request.user,
        station=booking.station,
        booking=booking,
        rating=rating,
        comment=comment,
    )

    return Response(
        {
            'message': 'Thank you for your feedback!',
            'review': ReviewListSerializer(review).data,
            'booking': BookingDetailSerializer(
                Booking.objects.select_related('slot', 'station', 'station__owner').get(pk=booking.pk),
                context={'request': request},
            ).data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def station_reviews_list_view(request, pk):
    """GET /api/stations/{id}/reviews/ — recent reviews for a station."""
    try:
        station = Station.objects.get(pk=pk, is_active=True)
    except Station.DoesNotExist:
        return Response({'error': 'Station not found.'}, status=status.HTTP_404_NOT_FOUND)

    limit = 30
    raw_lim = request.query_params.get('limit')
    if raw_lim is not None:
        try:
            limit = min(int(raw_lim), 100)
        except (TypeError, ValueError):
            pass
    reviews = (
        Review.objects.filter(station=station)
        .select_related('user')
        .order_by('-created_at')[:limit]
    )
    return Response(
        {
            'station_id': station.id,
            'reviews': ReviewListSerializer(reviews, many=True).data,
        },
        status=status.HTTP_200_OK,
    )
