"""
Seed Data Management Command
==============================
Run this command to populate the database with demo data for testing.

Usage:
  python manage.py seed_data

Creates demo users, Bhopal-area stations, time slots, and sample reviews
so rating filters work on Home and Emergency pages.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from datetime import date, time, timedelta

from core.models import Station, TimeSlot, Booking, Review

User = get_user_model()

# Bhopal center ~ 23.2599, 77.4126 — spread like emergency mechanics
BHOPAL_STATIONS = [
    {
        'name': 'Green Power Hub',
        'location_text': 'MP Nagar, Bhopal, Madhya Pradesh',
        'latitude': 23.2330,
        'longitude': 77.4340,
        'phone': '9111222333',
        'total_slots': 5,
        'charger_type': 'Fast Charger - 50kW',
        'price_per_hour': Decimal('85.00'),
        'description': 'Open 24/7. Near MP Nagar metro area. Covered parking.',
        'demo_rating': 5,
        'demo_reviews': 28,
    },
    {
        'name': 'EV Charge Point - Arera',
        'location_text': 'Arera Colony, Bhopal, Madhya Pradesh',
        'latitude': 23.2105,
        'longitude': 77.4501,
        'phone': '9222333444',
        'total_slots': 4,
        'charger_type': 'Standard Charger - 22kW',
        'price_per_hour': Decimal('65.00'),
        'description': 'Mall-side parking. 7 AM to 10 PM.',
        'demo_rating': 4,
        'demo_reviews': 15,
    },
    {
        'name': 'HapticEV Fast Charge',
        'location_text': 'Hoshangabad Road, Bhopal, Madhya Pradesh',
        'latitude': 23.2150,
        'longitude': 77.4520,
        'phone': '9333444555',
        'total_slots': 6,
        'charger_type': 'Ultra Fast - 150kW',
        'price_per_hour': Decimal('120.00'),
        'description': 'Premium ultra-fast charging on main road.',
        'demo_rating': 5,
        'demo_reviews': 42,
    },
    {
        'name': 'Kolar Road EV Hub',
        'location_text': 'Kolar Road, Bhopal, Madhya Pradesh',
        'latitude': 23.1890,
        'longitude': 77.4700,
        'phone': '9444555666',
        'total_slots': 4,
        'charger_type': 'Fast Charger - 50kW',
        'price_per_hour': Decimal('75.00'),
        'description': 'Easy highway access from Kolar Road.',
        'demo_rating': 4,
        'demo_reviews': 19,
    },
    {
        'name': 'Karond Green Charge',
        'location_text': 'Karond, Bhopal, Madhya Pradesh',
        'latitude': 23.2680,
        'longitude': 77.3880,
        'phone': '9555666777',
        'total_slots': 3,
        'charger_type': 'Standard Charger - 22kW',
        'price_per_hour': Decimal('60.00'),
        'description': 'Residential area — quiet evenings.',
        'demo_rating': 4,
        'demo_reviews': 11,
    },
    {
        'name': 'TT Nagar Power Station',
        'location_text': 'TT Nagar, Bhopal, Madhya Pradesh',
        'latitude': 23.2410,
        'longitude': 77.4010,
        'phone': '9666777888',
        'total_slots': 5,
        'charger_type': 'Fast Charger - 50kW',
        'price_per_hour': Decimal('80.00'),
        'description': 'Central Bhopal — TT Nagar circle.',
        'demo_rating': 5,
        'demo_reviews': 33,
    },
    {
        'name': 'Shivaji Nagar EV Point',
        'location_text': 'Shivaji Nagar, Bhopal, Madhya Pradesh',
        'latitude': 23.2550,
        'longitude': 77.4180,
        'phone': '9777888999',
        'total_slots': 3,
        'charger_type': 'Standard Charger - 22kW',
        'price_per_hour': Decimal('55.00'),
        'description': 'Budget-friendly charging.',
        'demo_rating': 3,
        'demo_reviews': 8,
    },
    {
        'name': 'Bairagarh Fast Charge',
        'location_text': 'Bairagarh, Bhopal, Madhya Pradesh',
        'latitude': 23.2850,
        'longitude': 77.3650,
        'phone': '9888999000',
        'total_slots': 4,
        'charger_type': 'Ultra Fast - 150kW',
        'price_per_hour': Decimal('110.00'),
        'description': 'West Bhopal fast hub.',
        'demo_rating': 5,
        'demo_reviews': 24,
    },
    {
        'name': 'Misrod Ultra EV',
        'location_text': 'Misrod, Bhopal, Madhya Pradesh',
        'latitude': 23.1750,
        'longitude': 77.4850,
        'phone': '9900111222',
        'total_slots': 5,
        'charger_type': 'Ultra Fast - 150kW',
        'price_per_hour': Decimal('115.00'),
        'description': 'South-east Bhopal corridor.',
        'demo_rating': 4,
        'demo_reviews': 17,
    },
    {
        'name': 'Govindpura Charge Hub',
        'location_text': 'Govindpura, Bhopal, Madhya Pradesh',
        'latitude': 23.2980,
        'longitude': 77.4420,
        'phone': '9011222333',
        'total_slots': 4,
        'charger_type': 'Fast Charger - 50kW',
        'price_per_hour': Decimal('70.00'),
        'description': 'Industrial area charging.',
        'demo_rating': 4,
        'demo_reviews': 14,
    },
    {
        'name': 'Berasia Road EV Station',
        'location_text': 'Berasia Road, Bhopal, Madhya Pradesh',
        'latitude': 23.3050,
        'longitude': 77.4780,
        'phone': '9122333444',
        'total_slots': 3,
        'charger_type': 'Standard Charger - 22kW',
        'price_per_hour': Decimal('58.00'),
        'description': 'North Bhopal access road.',
        'demo_rating': 3,
        'demo_reviews': 6,
    },
    {
        'name': 'New Market EV Hub',
        'location_text': 'New Market, Bhopal, Madhya Pradesh',
        'latitude': 23.2460,
        'longitude': 77.4050,
        'phone': '9233444555',
        'total_slots': 6,
        'charger_type': 'Fast Charger - 50kW',
        'price_per_hour': Decimal('90.00'),
        'description': 'Busy market area — 24/7 security.',
        'demo_rating': 5,
        'demo_reviews': 37,
    },
]

TIME_RANGES = [
    (time(9, 0), time(10, 0)),
    (time(10, 0), time(11, 0)),
    (time(11, 0), time(12, 0)),
    (time(14, 0), time(15, 0)),
    (time(15, 0), time(16, 0)),
    (time(16, 0), time(17, 0)),
    (time(18, 0), time(19, 0)),
]

# Rename / relocate legacy Bangalore seed names if they still exist
LEGACY_BANGALORE_NAMES = [
    'EV Charge Point - Koramangala',
    'Indiranagar Fast Charge',
]


class Command(BaseCommand):
    help = 'Seed demo users, Bhopal EV stations, slots, and sample reviews'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('\n[*] Seeding database...\n'))

        user, owner = self._seed_users()
        stations = self._seed_stations(owner)
        self._seed_slots(stations)
        self._seed_demo_reviews(user, stations)
        self._retire_bangalore_duplicates(stations)

        self.stdout.write(self.style.SUCCESS('''
==================================================
SEED DATA COMPLETE — Bhopal demo area

Demo Accounts (password: password123):
  user1  — EV user
  owner1 — Station owner

Stations: 12 near Bhopal (re-run updates locations & slots)
Rating filters: use 3★+ / 4★+ / Top rated on Home & Emergency

Admin: http://localhost:8000/admin/
==================================================
        '''))

    def _seed_users(self):
        self.stdout.write('Creating demo accounts...')

        user, created = User.objects.get_or_create(
            username='user1',
            defaults={
                'email': 'user1@evapp.com',
                'role': 'user',
                'phone': '9876543210',
                'first_name': 'Ramesh',
                'last_name': 'Kumar',
            },
        )
        if created:
            user.set_password('password123')
            user.save()
            self.stdout.write(self.style.SUCCESS('  [+] Demo User: user1 / password123'))
        else:
            self.stdout.write('  [=] Demo User already exists')

        owner, created = User.objects.get_or_create(
            username='owner1',
            defaults={
                'email': 'owner1@evapp.com',
                'role': 'owner',
                'phone': '9123456789',
                'first_name': 'Suresh',
                'last_name': 'Sharma',
            },
        )
        if created:
            owner.set_password('password123')
            owner.save()
            self.stdout.write(self.style.SUCCESS('  [+] Demo Owner: owner1 / password123'))
        else:
            self.stdout.write('  [=] Demo Owner already exists')

        return user, owner

    def _seed_stations(self, owner):
        self.stdout.write('\nCreating / updating Bhopal demo stations...')
        stations = []

        for data in BHOPAL_STATIONS:
            demo_rating = data.pop('demo_rating', 5)
            demo_reviews = data.pop('demo_reviews', 10)
            station, created = Station.objects.update_or_create(
                name=data['name'],
                defaults={**data, 'owner': owner, 'is_active': True},
            )
            station._demo_rating = demo_rating
            station._demo_reviews = demo_reviews
            stations.append(station)
            tag = '[+]' if created else '[~]'
            self.stdout.write(self.style.SUCCESS(f'  {tag} {station.name} — {station.location_text}'))

        return stations

    def _seed_slots(self, stations):
        self.stdout.write('\nCreating time slots...')
        today = date.today()
        tomorrow = today + timedelta(days=1)
        slot_count = 0

        for station in stations:
            for target_date in [today, tomorrow]:
                for start, end in TIME_RANGES:
                    _, created = TimeSlot.objects.get_or_create(
                        station=station,
                        date=target_date,
                        start_time=start,
                        end_time=end,
                        defaults={'capacity': station.total_slots},
                    )
                    if created:
                        slot_count += 1

        self.stdout.write(self.style.SUCCESS(f'  [+] {slot_count} new time slots'))

    def _seed_demo_reviews(self, user, stations):
        """One completed booking + review per station so avg_rating filters work."""
        self.stdout.write('\nSeeding demo reviews for ratings...')
        today = date.today()
        count = 0

        for station in stations:
            if Review.objects.filter(station=station).exists():
                continue

            slot = (
                TimeSlot.objects.filter(station=station, date__gte=today)
                .order_by('date', 'start_time')
                .first()
            )
            if not slot:
                continue

            rating = getattr(station, '_demo_rating', 5)
            comment = f'Demo review — great charging experience at {station.name}.'

            with transaction.atomic():
                booking = Booking.objects.create(
                    user=user,
                    station=station,
                    slot=slot,
                    full_name=user.get_full_name() or user.username,
                    phone=user.phone or '9876543210',
                    email=user.email,
                    status='completed',
                    payment_method='upi',
                    amount_paid=station.price_per_hour or Decimal('80.00'),
                    payment_status='paid',
                    transaction_id=f'DEMO-{station.id}-{user.id}',
                )
                if slot.booked_count < slot.capacity:
                    slot.booked_count += 1
                    slot.save(update_fields=['booked_count'])

                Review.objects.create(
                    user=user,
                    station=station,
                    booking=booking,
                    rating=rating,
                    comment=comment,
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'  [+] {count} demo reviews created'))

    def _retire_bangalore_duplicates(self, current_stations):
        """Deactivate old Bangalore-named stations not in the new Bhopal list."""
        from django.db.models import Q

        keep_ids = {s.id for s in current_stations}
        legacy = Station.objects.filter(
            Q(location_text__icontains='bangalore') | Q(name__in=LEGACY_BANGALORE_NAMES)
        ).exclude(id__in=keep_ids)
        updated = legacy.update(is_active=False)
        if updated:
            self.stdout.write(
                self.style.WARNING(f'  [~] Deactivated {updated} legacy Bangalore station(s)')
            )
