"""
Django Admin Configuration
============================
The Django Admin panel is available at: http://localhost:8000/admin/

It gives you a GUI to:
  - View all users, stations, slots, and bookings in the database
  - Edit any record directly (very useful for debugging during hackathon!)
  - Manually approve/reject bookings if needed

To use admin panel:
  1. Run: python manage.py createsuperuser
  2. Open: http://localhost:8000/admin/
  3. Login with your superuser credentials

We customize each admin class to show useful columns in the list view.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Station, TimeSlot, Booking, Review, Mechanic, PaymentAttempt


@admin.register(PaymentAttempt)
class PaymentAttemptAdmin(admin.ModelAdmin):
    list_display = ['razorpay_order_id', 'user', 'amount_paise', 'status', 'razorpay_payment_id', 'created_at']
    list_filter  = ['status', 'created_at']
    search_fields = ['razorpay_order_id', 'razorpay_payment_id', 'user__username']
    readonly_fields = ['razorpay_order_id', 'razorpay_payment_id', 'payload_json', 'created_at', 'updated_at']



@admin.register(Mechanic)
class MechanicAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'specialization', 'location_text', 'is_available', 'rating', 'experience_years']
    list_filter = ['specialization', 'is_available']
    search_fields = ['name', 'phone', 'location_text']
    list_editable = ['is_available']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['station', 'user', 'rating', 'booking', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['comment', 'station__name', 'user__username']


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Shows users with their role in the admin list"""

    # Columns shown in the user list
    list_display = ['username', 'email', 'role', 'phone', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active']
    search_fields = ['username', 'email', 'phone']

    # Add 'role' and 'phone' to the edit form
    fieldsets = UserAdmin.fieldsets + (
        ('EV System Fields', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('EV System Fields', {'fields': ('role', 'phone')}),
    )


# ─── Station Admin ─────────────────────────────────────────────────────────
@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'location_text', 'total_slots', 'charger_type', 'is_active', 'created_at']
    list_filter = ['is_active', 'charger_type']
    search_fields = ['name', 'location_text', 'owner__username']
    list_editable = ['is_active']  # Can toggle active status directly from list


# ─── TimeSlot Admin ────────────────────────────────────────────────────────
@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['station', 'date', 'start_time', 'end_time', 'capacity', 'booked_count', 'is_available']
    list_filter = ['date', 'is_available', 'station']
    search_fields = ['station__name']
    date_hierarchy = 'date'  # Adds a date drill-down navigator


# ─── Booking Admin ─────────────────────────────────────────────────────────
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_id_short', 'full_name', 'phone', 'station', 'slot', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'station']
    search_fields = ['full_name', 'email', 'phone', 'booking_id']
    list_editable = ['status']  # Can approve/reject directly from admin list
    readonly_fields = ['booking_id', 'qr_code', 'created_at', 'updated_at']

    def booking_id_short(self, obj):
        """Show only first 8 characters of UUID in list (easier to read)"""
        return str(obj.booking_id)[:8] + '...'
    booking_id_short.short_description = 'Booking ID'
