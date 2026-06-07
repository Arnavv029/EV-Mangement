"""
Subscription Views — Owner Pricing Plans & Revenue
=====================================================
Endpoints:
  GET   /api/owner/subscription/          → Get current active subscription
  POST  /api/owner/subscription/purchase/ → Purchase a new subscription plan
  GET   /api/owner/subscription/revenue/  → Get commission & revenue details

All endpoints require:
  1. User must be logged in (IsAuthenticated)
  2. User must have role='owner'
"""

import time
import logging
from datetime import date, timedelta

from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Subscription, Booking, PaymentAttempt
from core.serializers import SubscriptionSerializer, SubscriptionPurchaseSerializer
from core.utils.razorpay_client import create_order, verify_payment_signature

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Check if the request user is an owner
# ─────────────────────────────────────────────────────────────────────────────
def is_owner_or_403(request):
    if request.user.role != 'owner':
        return Response(
            {'error': 'Access denied. Only station owners can access this endpoint.'},
            status=status.HTTP_403_FORBIDDEN
        )
    return None


# ─────────────────────────────────────────────────────────────────────────────
# GET CURRENT SUBSCRIPTION
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def owner_subscription_view(request):
    """
    GET /api/owner/subscription/

    Returns the owner's current active subscription, or null if none exists.
    Also returns available plans for reference.
    """
    error = is_owner_or_403(request)
    if error:
        return error

    # Try to get the active subscription
    today = date.today()
    active_sub = (
        Subscription.objects
        .filter(owner=request.user, status='active', end_date__gte=today)
        .order_by('-created_at')
        .first()
    )

    # Also get subscription history
    all_subs = Subscription.objects.filter(owner=request.user).order_by('-created_at')[:10]

    return Response({
        'active_subscription': SubscriptionSerializer(active_sub).data if active_sub else None,
        'subscription_history': SubscriptionSerializer(all_subs, many=True).data,
        'available_plans': [
            {
                'id': 'starter',
                'name': 'Starter Plan',
                'bookings': 500,
                'price': 1000,
                'price_display': '₹1,000',
                'period': 'Monthly',
                'commission_after': '5%',
                'features': [
                    '500 bookings included',
                    'No commission within limit',
                    '5% commission after 500 bookings',
                    'Monthly billing cycle',
                    'Basic dashboard analytics',
                ],
            },
            {
                'id': 'pro',
                'name': 'Pro Plan',
                'bookings': 1200,
                'price': 2000,
                'price_display': '₹2,000',
                'period': 'Monthly',
                'commission_after': '5%',
                'popular': True,
                'features': [
                    '1,200 bookings included',
                    'No commission within limit',
                    '5% commission after 1,200 bookings',
                    'Monthly billing cycle',
                    'Priority support',
                    'Advanced analytics',
                ],
            },
        ],
    })


# ─────────────────────────────────────────────────────────────────────────────
# PURCHASE SUBSCRIPTION
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def owner_subscription_purchase_view(request):
    """
    POST /api/owner/subscription/purchase/

    Body:
      { "plan": "starter" }   or   { "plan": "pro" }

    Creates a Razorpay order for subscription payment and returns order details
    to the frontend. The owner completes payment in the Razorpay checkout,
    then the frontend verifies the payment with /purchase/verify/.
    """
    error = is_owner_or_403(request)
    if error:
        return error

    serializer = SubscriptionPurchaseSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    plan = serializer.validated_data['plan']
    config = Subscription.PLAN_CONFIG[plan]

    amount_paise = int(config['price'] * 100)
    receipt = f"hev-sub-{request.user.id}-{plan}-{int(time.time())}"

    try:
        rz_order = create_order(
            amount_paise=amount_paise,
            receipt=receipt,
            notes={'owner_id': str(request.user.id), 'plan': plan},
        )
    except Exception as e:
        logger.error("Razorpay create_order failed for subscription: %s", e)
        return Response(
            {'error': 'Payment gateway unavailable. Please try again later.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    attempt = PaymentAttempt.objects.create(
        user=request.user,
        razorpay_order_id=rz_order['id'],
        amount_paise=amount_paise,
        status='created',
        payload_json={
            'intent': 'subscription',
            'plan': plan,
            'price': config['price'],
            'bookings': config['bookings'],
        },
    )

    return Response({
        'key_id':   settings.RAZORPAY_KEY_ID,
        'order_id': rz_order['id'],
        'amount':   amount_paise,
        'currency': 'INR',
        'attempt_id': attempt.id,
        'plan': plan,
        'price': config['price'],
        'prefill': {
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
            'contact': request.user.phone or '',
        },
    }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# VERIFY SUBSCRIPTION PAYMENT
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def owner_subscription_verify_view(request):
    """
    POST /api/owner/subscription/purchase/verify/

    Body:
      razorpay_order_id, razorpay_payment_id, razorpay_signature, attempt_id

    Verifies Razorpay payment and creates the subscription record.
    """
    error = is_owner_or_403(request)
    if error:
        return error

    order_id = request.data.get('razorpay_order_id')
    payment_id = request.data.get('razorpay_payment_id')
    signature = request.data.get('razorpay_signature')
    attempt_id = request.data.get('attempt_id')

    if not all([order_id, payment_id, signature, attempt_id]):
        return Response({'error': 'Missing payment verification fields.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        attempt = PaymentAttempt.objects.get(
            id=attempt_id,
            razorpay_order_id=order_id,
            user=request.user,
        )
    except PaymentAttempt.DoesNotExist:
        return Response({'error': 'Payment attempt not found.'}, status=status.HTTP_404_NOT_FOUND)

    if attempt.status != 'created':
        return Response(
            {'error': f'Payment already {attempt.status}. Duplicate verification rejected.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if attempt.payload_json.get('intent') != 'subscription':
        return Response({'error': 'Invalid payment intent.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        verify_payment_signature(order_id, payment_id, signature)
    except Exception as e:
        logger.warning('Razorpay signature verification failed: %s', e)
        attempt.status = 'failed'
        attempt.save(update_fields=['status', 'updated_at'])
        return Response({'error': 'Payment signature verification failed.'}, status=status.HTTP_400_BAD_REQUEST)

    plan = attempt.payload_json.get('plan')
    if plan not in Subscription.PLAN_CONFIG:
        return Response({'error': 'Invalid subscription plan.'}, status=status.HTTP_400_BAD_REQUEST)

    config = Subscription.PLAN_CONFIG[plan]
    today = date.today()
    end_date = today + timedelta(days=30)

    try:
        with transaction.atomic():
            Subscription.objects.filter(owner=request.user, status='active').update(status='expired')

            subscription = Subscription.objects.create(
                owner=request.user,
                plan=plan,
                status='active',
                amount_paid=config['price'],
                bookings_total=config['bookings'],
                bookings_remaining=config['bookings'],
                bookings_used=0,
                transaction_id=payment_id,
                payment_method='razorpay',
                start_date=today,
                end_date=end_date,
            )

            attempt.status = 'paid'
            attempt.razorpay_payment_id = payment_id
            attempt.save(update_fields=['status', 'razorpay_payment_id', 'updated_at'])
    except Exception as e:
        logger.error('Subscription creation failed after payment verify: %s', e)
        return Response({'error': 'Subscription activation failed. Contact support.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'message': f'{plan.title()} plan activated successfully!',
        'subscription': SubscriptionSerializer(subscription).data,
    }, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────────────────────────────────────
# REVENUE & COMMISSION DETAILS
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def owner_subscription_revenue_view(request):
    """
    GET /api/owner/subscription/revenue/

    Returns detailed revenue and commission information:
    - Current subscription usage
    - Commission accrued (over-limit bookings)
    - Total earnings from all completed bookings
    - Breakdown of within-plan vs over-limit bookings
    """
    error = is_owner_or_403(request)
    if error:
        return error

    today = date.today()

    # Current active subscription
    active_sub = (
        Subscription.objects
        .filter(owner=request.user, status='active', end_date__gte=today)
        .order_by('-created_at')
        .first()
    )

    # Total completed bookings for this owner
    completed_bookings = Booking.objects.filter(
        station__owner=request.user,
        status='completed'
    )

    total_completed = completed_bookings.count()
    total_revenue = sum(
        float(b.amount_paid or 0) for b in completed_bookings
    )

    # Commission data
    commission_owed = float(active_sub.commission_owed) if active_sub else 0
    commission_bookings = active_sub.commission_bookings if active_sub else 0

    return Response({
        'subscription': SubscriptionSerializer(active_sub).data if active_sub else None,
        'revenue': {
            'total_completed_bookings': total_completed,
            'total_revenue': round(total_revenue, 2),
            'commission_owed': round(commission_owed, 2),
            'commission_bookings': commission_bookings,
            'commission_rate': '5%',
            'net_revenue': round(total_revenue - commission_owed, 2),
        },
    })
