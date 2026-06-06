"""
Seed Mechanics Data — Emergency Section
========================================
Run: python manage.py seed_mechanics

Creates 12 realistic EV mechanics with GPS coordinates spread across
a city (Bhopal, MP as example). These show on the Emergency → Mechanics
map on the user's home page.
"""

from django.core.management.base import BaseCommand
from core.models import Mechanic


MECHANICS = [
    {
        "name": "Rajesh Kumar",
        "phone": "+91 98765 43210",
        "specialization": "battery",
        "location_text": "MP Nagar, Bhopal",
        "latitude": 23.2330,
        "longitude": 77.4340,
        "experience_years": 7,
        "is_available": True,
        "rating": 4.8,
        "review_count": 34,
    },
    {
        "name": "Suresh EV Care",
        "phone": "+91 87654 32109",
        "specialization": "charger",
        "location_text": "Hoshangabad Road, Bhopal",
        "latitude": 23.2150,
        "longitude": 77.4520,
        "experience_years": 5,
        "is_available": True,
        "rating": 4.6,
        "review_count": 21,
    },
    {
        "name": "Anil Singh Mechanics",
        "phone": "+91 76543 21098",
        "specialization": "general",
        "location_text": "Kolar Road, Bhopal",
        "latitude": 23.1890,
        "longitude": 77.4700,
        "experience_years": 10,
        "is_available": True,
        "rating": 4.9,
        "review_count": 58,
    },
    {
        "name": "Vikram Battery Solutions",
        "phone": "+91 65432 10987",
        "specialization": "battery",
        "location_text": "Arera Colony, Bhopal",
        "latitude": 23.2050,
        "longitude": 77.4200,
        "experience_years": 4,
        "is_available": False,
        "rating": 4.2,
        "review_count": 15,
    },
    {
        "name": "Pradeep EV Workshop",
        "phone": "+91 54321 09876",
        "specialization": "motor",
        "location_text": "TT Nagar, Bhopal",
        "latitude": 23.2420,
        "longitude": 77.4100,
        "experience_years": 8,
        "is_available": True,
        "rating": 4.7,
        "review_count": 42,
    },
    {
        "name": "Manoj Charger Experts",
        "phone": "+91 99887 76655",
        "specialization": "charger",
        "location_text": "Karond, Bhopal",
        "latitude": 23.2780,
        "longitude": 77.4010,
        "experience_years": 3,
        "is_available": True,
        "rating": 4.4,
        "review_count": 18,
    },
    {
        "name": "Ram EV Service",
        "phone": "+91 91234 56789",
        "specialization": "general",
        "location_text": "Shivaji Nagar, Bhopal",
        "latitude": 23.2600,
        "longitude": 77.4500,
        "experience_years": 6,
        "is_available": True,
        "rating": 4.5,
        "review_count": 27,
    },
    {
        "name": "Deepak Tyre & EV",
        "phone": "+91 80123 45678",
        "specialization": "tyre",
        "location_text": "Govindpura, Bhopal",
        "latitude": 23.2700,
        "longitude": 77.4600,
        "experience_years": 9,
        "is_available": False,
        "rating": 4.3,
        "review_count": 31,
    },
    {
        "name": "Sanjay Motor Tech",
        "phone": "+91 70987 65432",
        "specialization": "motor",
        "location_text": "Bhopal Junction Area",
        "latitude": 23.2630,
        "longitude": 77.4120,
        "experience_years": 12,
        "is_available": True,
        "rating": 4.9,
        "review_count": 67,
    },
    {
        "name": "Amit Quick Fix EV",
        "phone": "+91 60876 54321",
        "specialization": "general",
        "location_text": "Misrod, Bhopal",
        "latitude": 23.1750,
        "longitude": 77.4900,
        "experience_years": 2,
        "is_available": True,
        "rating": 4.1,
        "review_count": 9,
    },
    {
        "name": "Hari Battery & Charger",
        "phone": "+91 88776 65544",
        "specialization": "battery",
        "location_text": "Berasia Road, Bhopal",
        "latitude": 23.3100,
        "longitude": 77.4300,
        "experience_years": 6,
        "is_available": True,
        "rating": 4.6,
        "review_count": 23,
    },
    {
        "name": "Vinod EV Emergency",
        "phone": "+91 77665 54433",
        "specialization": "charger",
        "location_text": "Bairagarh, Bhopal",
        "latitude": 23.2900,
        "longitude": 77.3800,
        "experience_years": 5,
        "is_available": True,
        "rating": 4.5,
        "review_count": 19,
    },
]


class Command(BaseCommand):
    help = "Seeds 12 demo mechanics for the Emergency section"

    def handle(self, *args, **kwargs):
        created = 0
        skipped = 0
        for data in MECHANICS:
            obj, was_created = Mechanic.objects.get_or_create(
                name=data["name"],
                defaults=data,
            )
            if was_created:
                created += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Mechanics seeded: {created} created, {skipped} already existed."
            )
        )
