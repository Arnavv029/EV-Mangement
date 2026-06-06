"""
Migration 0002: Add pricing, vehicle, and payment fields
---------------------------------------------------------
New fields added:
  Station  → price_per_hour (DecimalField, optional)
  Booking  → vehicle_number, vehicle_type (CharField, optional)
  Booking  → payment_method (CharField with choices, default='pay_at_station')
  Booking  → amount_paid (DecimalField, optional)
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        # Station: price per hour
        migrations.AddField(
            model_name='station',
            name='price_per_hour',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=8, null=True,
                help_text='Rate in ₹ per hour of charging'
            ),
        ),

        # Booking: vehicle details
        migrations.AddField(
            model_name='booking',
            name='vehicle_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='vehicle_type',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),

        # Booking: payment
        migrations.AddField(
            model_name='booking',
            name='payment_method',
            field=models.CharField(
                choices=[
                    ('pay_at_station', 'Pay at Station'),
                    ('upi',            'UPI'),
                    ('debit_card',     'Debit / Credit Card'),
                    ('net_banking',    'Net Banking'),
                ],
                default='pay_at_station',
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name='booking',
            name='amount_paid',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
