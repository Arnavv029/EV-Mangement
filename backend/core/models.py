"""
Models — Database Structure
============================
Think of models as blueprints for your database tables.
Each class = one table. Each field = one column.

Tables we are creating:
  1. CustomUser  → stores users AND owners (role field distinguishes them)
  2. Station     → EV charging stations added by owners
  3. TimeSlot    → Time slots (9–10, 10–11, etc.) for each station on a date
  4. Booking     → A user's booking for a specific slot at a specific station

Relationships:
  Station   → belongs to → CustomUser (owner)
  TimeSlot  → belongs to → Station
  Booking   → belongs to → CustomUser (user) + Station + TimeSlot
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


# ══════════════════════════════════════════════════════════════════════════════
# 1. CUSTOM USER MODEL
# ══════════════════════════════════════════════════════════════════════════════
class CustomUser(AbstractUser):
    """
    We extend Django's built-in User model to add a 'role' field.

    Why extend AbstractUser?
    Django already handles password hashing, login, etc.
    We just add our 'role' field on top of everything Django provides.

    Fields inherited from AbstractUser (free of cost!):
      - username, email, password (hashed automatically)
      - first_name, last_name
      - is_active, is_staff, is_superuser
      - date_joined, last_login
    """

    ROLE_CHOICES = [
        ('user', 'EV Owner / User'),      # Can book slots
        ('owner', 'Station Owner'),        # Can add stations & verify QR
    ]

    # This field determines what the person can do in the system
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user'
    )

    # Phone number of the user (optional but useful for booking contact)
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        # This is what shows up in Django Admin for this user
        return f"{self.username} ({self.role})"

    def is_owner(self):
        """Helper method: returns True if this user is a station owner"""
        return self.role == 'owner'

    def is_ev_user(self):
        """Helper method: returns True if this user is an EV owner"""
        return self.role == 'user'


# ══════════════════════════════════════════════════════════════════════════════
# 2. STATION MODEL
# ══════════════════════════════════════════════════════════════════════════════
class Station(models.Model):
    """
    Represents an EV Charging Station added by a Station Owner.

    Key points:
    - 'owner' is a ForeignKey → means each station belongs to ONE owner,
      but one owner can have MANY stations.
    - latitude/longitude → used to calculate distance from the user's location
    - image → station photo (stored in media/stations/ folder)
    - total_slots → total number of physical charging points at this station
    """

    # Who owns this station?
    # on_delete=CASCADE → if the owner is deleted, their stations are deleted too
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='stations',  # owner.stations.all() gives all stations of an owner
        limit_choices_to={'role': 'owner'}  # Only users with role='owner' can be owners
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    location_text = models.CharField(max_length=500)  # Human-readable address

    # GPS coordinates for distance calculation
    # null=True, blank=True → optional (owner might not provide exact GPS)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Contact details
    phone = models.CharField(max_length=15, blank=True, null=True)

    # Station photo — uploaded to backend/media/stations/
    image = models.ImageField(upload_to='stations/', blank=True, null=True)

    # How many physical charging points does this station have?
    total_slots = models.PositiveIntegerField(default=1)

    # Charging speed info (e.g., "Fast Charger - 50kW")
    charger_type = models.CharField(max_length=100, blank=True, null=True)

    # Price charged per hour of charging (e.g., ₹80.00 per hour)
    price_per_hour = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text='Rate in ₹ per hour of charging'
    )

    # Is this station currently active/visible?
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)  # Set once on creation
    updated_at = models.DateTimeField(auto_now=True)       # Updated on every save

    class Meta:
        ordering = ['-created_at']  # Newest stations shown first

    def __str__(self):
        return f"{self.name} — {self.location_text}"


# ══════════════════════════════════════════════════════════════════════════════
# 3. TIME SLOT MODEL
# ══════════════════════════════════════════════════════════════════════════════
class TimeSlot(models.Model):
    """
    Represents a bookable time window at a station on a specific date.

    Example:
      Station: "Green Power Station"
      Date: 2026-05-06
      Start: 09:00, End: 10:00
      Capacity: 3 (3 cars can charge at 9–10 AM)

    Why separate date and time?
    Because owners define time slots once (e.g., 9–10 AM every day),
    but bookings happen on specific dates.
    We create TimeSlot records per date so we can track
    how many are booked on each specific day.

    Availability logic:
      booked_count < capacity  → GREEN (available)
      booked_count >= capacity → RED  (fully booked)
    """

    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='time_slots'  # station.time_slots.all() gives all slots
    )

    date = models.DateField()           # Which day is this slot for?
    start_time = models.TimeField()     # e.g., 09:00:00
    end_time = models.TimeField()       # e.g., 10:00:00

    # How many cars can book this slot?
    capacity = models.PositiveIntegerField(default=1)

    # How many cars have already booked? (incremented when a booking is confirmed)
    booked_count = models.PositiveIntegerField(default=0)

    # Is this slot available for booking?
    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # A station cannot have two slots with the same time on the same date
        unique_together = ['station', 'date', 'start_time', 'end_time']
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.station.name} | {self.date} | {self.start_time}–{self.end_time}"

    @property
    def is_full(self):
        """Returns True if no more bookings are possible for this slot"""
        return self.booked_count >= self.capacity

    @property
    def available_spots(self):
        """Returns how many spots are still open"""
        return max(0, self.capacity - self.booked_count)


# ══════════════════════════════════════════════════════════════════════════════
# 4. BOOKING MODEL
# ══════════════════════════════════════════════════════════════════════════════
class Booking(models.Model):
    """
    Represents a user's booking for a specific time slot at a station.

    Key design decisions:
    - booking_id is a UUID (universally unique ID) — not a simple integer.
      This is the data encoded in the QR code. It's impossible to guess.
    - qr_code stores the generated QR as a base64 string so the frontend
      can display it directly without needing a separate image file.
    - We store user's details at booking time (full_name, phone, email)
      because users might update their profile later; we want the
      original booking details to stay accurate.

    Status flow:
      'pending'   → Booking created, waiting for owner approval
      'confirmed' → Owner approved (charging allowed)
      'rejected'  → Owner rejected (charging denied)
      'completed' → User finished charging
    """

    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected',  'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # UUID: looks like "550e8400-e29b-41d4-a716-446655440000"
    # This is the unique identifier encoded in the QR code
    booking_id = models.UUIDField(
        default=uuid.uuid4,  # Automatically generate a new UUID on creation
        unique=True,
        editable=False
    )

    # Who made this booking?
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    # Which station?
    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    # Which time slot?
    slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    # ── Personal Details (captured at booking time) ───────────────────────────
    # These are filled in the Booking Form on the frontend
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    email = models.EmailField()

    # ── Booking Status ────────────────────────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # ── Vehicle Details (captured at booking time) ────────────────────────────
    vehicle_number = models.CharField(max_length=20, blank=True, null=True)
    vehicle_type   = models.CharField(max_length=100, blank=True, null=True)

    # ── Payment ───────────────────────────────────────────────────────────────
    PAYMENT_CHOICES = [
        ('upi',        'UPI'),
        ('debit_card', 'Debit / Credit Card'),
        ('net_banking','Net Banking'),
        ('razorpay',   'Razorpay'),
    ]
    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_CHOICES,
        default='upi'
    )
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # ── Payment Status ────────────────────────────────────────────────────────
    PAYMENT_STATUS_CHOICES = [
        ('pending_payment',      'Awaiting Payment'),
        ('paid',                 'Payment Successful'),
        ('refund_initiated',     'Refund Initiated'),
        ('partially_refunded',   'Partially Refunded'),
        ('refunded',             'Fully Refunded'),
        ('payment_failed',       'Payment Failed'),
    ]
    payment_status = models.CharField(
        max_length=30,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending_payment'
    )
    transaction_id   = models.CharField(max_length=100, blank=True, null=True)

    # ── Cancellation & Refund ─────────────────────────────────────────────────
    refund_amount     = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    refund_percentage = models.IntegerField(null=True, blank=True)   # 100 / 70 / 50 / 0
    cancelled_at      = models.DateTimeField(null=True, blank=True)

    # ── QR Code ───────────────────────────────────────────────────────────────
    # Stored as base64 encoded PNG image string.
    # Frontend uses it like: <img src="data:image/png;base64,..." />
    qr_code = models.TextField(blank=True, null=True)

    # When was this booking made?
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # Newest bookings first

    def __str__(self):
        return f"Booking #{str(self.booking_id)[:8]} | {self.full_name} | {self.station.name} | {self.status}"


# ══════════════════════════════════════════════════════════════════════════════
# 5. REVIEW (after completed charging session)
# ══════════════════════════════════════════════════════════════════════════════
class Review(models.Model):
    """
    One review per completed booking. Shown on station cards (average rating)
    and used to filter stations (e.g. minimum 4 stars).
    """

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='reviews_written',
    )
    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='review',
    )
    rating = models.PositiveSmallIntegerField()  # 1–5
    comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rating}★ @ {self.station.name} by {self.user.username}"


# ══════════════════════════════════════════════════════════════════════════════
# 6. MECHANIC MODEL  (Emergency Section)
# ══════════════════════════════════════════════════════════════════════════════
class Mechanic(models.Model):
    """
    Represents an EV mechanic who can help users in emergency situations.
    Used by the Emergency → Mechanics section on the user home page.

    Fields:
    - name          : Mechanic's full name
    - phone         : Contact number (most important field for emergencies)
    - specialization: What they fix (Battery, Charger, General EV, Tyre, etc.)
    - location_text : Human-readable address
    - latitude/longitude: GPS for "nearby mechanics" map
    - experience_years: Years of EV experience
    - is_available  : Whether they are currently accepting calls
    - rating        : Average rating (1-5)
    """

    SPECIALIZATION_CHOICES = [
        ('battery',  'Battery Specialist'),
        ('charger',  'Charger / Wiring'),
        ('general',  'General EV Mechanic'),
        ('tyre',     'Tyre & Suspension'),
        ('motor',    'Motor & Drivetrain'),
    ]

    name             = models.CharField(max_length=200)
    phone            = models.CharField(max_length=15)
    specialization   = models.CharField(max_length=30, choices=SPECIALIZATION_CHOICES, default='general')
    location_text    = models.CharField(max_length=500)
    latitude         = models.FloatField(null=True, blank=True)
    longitude        = models.FloatField(null=True, blank=True)
    experience_years = models.PositiveIntegerField(default=1)
    is_available     = models.BooleanField(default=True)
    rating           = models.DecimalField(max_digits=3, decimal_places=1, default=4.0)
    review_count     = models.PositiveIntegerField(default=0)
    photo            = models.ImageField(upload_to='mechanics/', blank=True, null=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_available', '-rating']

    def __str__(self):
        return f"{self.name} ({self.get_specialization_display()}) — {self.location_text}"


# ══════════════════════════════════════════════════════════════════════════════
# 7. PAYMENT ATTEMPT MODEL  (Razorpay Integration)
# ══════════════════════════════════════════════════════════════════════════════
class PaymentAttempt(models.Model):
    """
    Tracks a Razorpay order before the booking is confirmed.

    Why this exists:
      Razorpay's flow is:
        1. Backend creates Razorpay order → saves PaymentAttempt (status=created)
        2. User pays in Razorpay popup
        3. Backend verifies signature → creates Booking (status=paid)

    We CANNOT create a Booking until payment is verified. But we must remember
    the slot, form data, and amount between steps 1 and 3. That's what this
    model stores.

    Status transitions:
      created → paid      (verify succeeded, Booking created)
      created → failed    (verify failed / payment.failed webhook)
      created → expired   (never verified, cleanup job)
    """

    STATUS_CHOICES = [
        ('created', 'Order Created'),
        ('paid',    'Payment Successful'),
        ('failed',  'Payment Failed'),
        ('expired', 'Expired'),
    ]

    user               = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payment_attempts')
    razorpay_order_id  = models.CharField(max_length=100, unique=True)
    amount_paise       = models.PositiveIntegerField()         # Amount in paise (₹1 = 100 paise)
    status             = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    booking            = models.OneToOneField(
        'Booking', on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_attempt'
    )
    payload_json       = models.JSONField()   # Draft booking data: slot_id, name, phone, email, vehicle, etc.
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Attempt {self.razorpay_order_id} | {self.user.username} | {self.status}"

