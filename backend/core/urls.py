"""
Core App URL Configuration
============================
This file maps every URL pattern to its view function.

Complete API Route Table:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
METHOD  ENDPOINT                            WHO CAN USE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST    /api/auth/register/                 Anyone (public)
POST    /api/auth/login/                    Anyone (public)
GET     /api/auth/me/                       Logged-in users

GET     /api/stations/                      Users (with ?lat=&lng=)
GET     /api/stations/{id}/                 Users
GET     /api/stations/{id}/slots/           Users (with ?date=)

POST    /api/bookings/                      Users (create booking + QR)
GET     /api/bookings/                      Users (their booking history)
GET     /api/bookings/{id}/                 Users (single booking + QR)

GET     /api/owner/stations/                Owners
POST    /api/owner/stations/                Owners
POST    /api/owner/slots/                   Owners
GET     /api/owner/bookings/                Owners
GET     /api/owner/bookings/{id}/           Owners
PATCH   /api/owner/bookings/{id}/status/    Owners
POST    /api/owner/verify-qr/              Owners
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from django.urls import path
from core.views import auth_views, station_views, booking_views, owner_views, review_views, emergency_views, payment_views, subscription_views

urlpatterns = [

    # ── AUTHENTICATION ────────────────────────────────────────────────────────
    path('auth/register/', auth_views.register_view,    name='register'),
    path('auth/login/',    auth_views.login_view,       name='login'),
    path('auth/me/',       auth_views.me_view,          name='me'),

    # ── STATIONS (User side — read only) ──────────────────────────────────────
    path('stations/',              station_views.station_list_view,    name='station-list'),
    path('stations/<int:pk>/',     station_views.station_detail_view,  name='station-detail'),
    path('stations/<int:pk>/reviews/', review_views.station_reviews_list_view, name='station-reviews'),
    path('stations/<int:pk>/slots/', station_views.station_slots_view, name='station-slots'),

    # ── BOOKINGS (User side) ──────────────────────────────────────────────────
    path('bookings/',                            booking_views.create_booking_view,  name='booking-create'),
    path('bookings/history/',                    booking_views.user_bookings_view,   name='booking-list'),
    path('bookings/<int:pk>/',                   booking_views.booking_detail_view,  name='booking-detail'),
    path('bookings/<int:pk>/refund-preview/',    booking_views.refund_preview_view,  name='booking-refund-preview'),
    path('bookings/<int:pk>/cancel/',            booking_views.cancel_booking_view,  name='booking-cancel'),
    path('bookings/<int:pk>/review/',            review_views.create_booking_review_view, name='booking-review'),

    # ── OWNER ENDPOINTS ───────────────────────────────────────────────────────
    path('owner/stations/',                         owner_views.owner_station_view,               name='owner-stations'),
    path('owner/stations/<int:pk>/',                owner_views.owner_station_detail_view,        name='owner-station-detail'),
    path('owner/slots/',                            owner_views.owner_create_slots_view,          name='owner-create-slots'),
    path('owner/bookings/',                         owner_views.owner_bookings_view,              name='owner-bookings'),
    path('owner/bookings/<int:pk>/',                owner_views.owner_booking_detail_view,        name='owner-booking-detail'),
    path('owner/bookings/<int:pk>/status/',         owner_views.owner_update_booking_status_view, name='owner-booking-status'),
    path('owner/verify-qr/',                        owner_views.owner_verify_qr_view,            name='owner-verify-qr'),

    # ── EMERGENCY ENDPOINTS ───────────────────────────────────────────────────
    path('emergency/mechanics/',  emergency_views.emergency_mechanics_view,  name='emergency-mechanics'),
    path('emergency/stations/',   emergency_views.emergency_stations_view,   name='emergency-stations'),

    # ── RAZORPAY PAYMENT ──────────────────────────────────────────────────────
    path('payments/razorpay/create-order/', payment_views.razorpay_create_order_view, name='razorpay-create-order'),
    path('payments/razorpay/verify/',       payment_views.razorpay_verify_view,        name='razorpay-verify'),
    path('payments/razorpay/webhook/',      payment_views.razorpay_webhook_view,       name='razorpay-webhook'),

    # ── OWNER SUBSCRIPTION & PRICING ──────────────────────────────────────────
    path('owner/subscription/',          subscription_views.owner_subscription_view,          name='owner-subscription'),
    path('owner/subscription/purchase/', subscription_views.owner_subscription_purchase_view, name='owner-subscription-purchase'),
    path('owner/subscription/purchase/verify/', subscription_views.owner_subscription_verify_view, name='owner-subscription-purchase-verify'),
    path('owner/subscription/revenue/',  subscription_views.owner_subscription_revenue_view,  name='owner-subscription-revenue'),
]
