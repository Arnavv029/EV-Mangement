"""
Migration 0003: Payment processing + cancellation/refund system
---------------------------------------------------------------
Changes:
  Booking → payment_status     (CharField with choices)
  Booking → transaction_id     (CharField, nullable)
  Booking → refund_amount      (DecimalField, nullable)
  Booking → refund_percentage  (IntegerField, nullable)
  Booking → cancelled_at       (DateTimeField, nullable)
  Booking → status choices     (add 'cancelled')
  Booking → payment_method     (remove 'pay_at_station', default='upi')
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_station_price_booking_vehicle_payment'),
    ]

    operations = [

        # Payment status field
        migrations.AddField(
            model_name='booking',
            name='payment_status',
            field=models.CharField(
                max_length=30,
                choices=[
                    ('pending_payment',    'Awaiting Payment'),
                    ('paid',               'Payment Successful'),
                    ('refund_initiated',   'Refund Initiated'),
                    ('partially_refunded', 'Partially Refunded'),
                    ('refunded',           'Fully Refunded'),
                    ('payment_failed',     'Payment Failed'),
                ],
                default='pending_payment',
            ),
        ),

        # Transaction ID (simulated gateway reference)
        migrations.AddField(
            model_name='booking',
            name='transaction_id',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),

        # Refund amount in ₹
        migrations.AddField(
            model_name='booking',
            name='refund_amount',
            field=models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True),
        ),

        # Refund percentage (100 / 70 / 50 / 0)
        migrations.AddField(
            model_name='booking',
            name='refund_percentage',
            field=models.IntegerField(blank=True, null=True),
        ),

        # When was the booking cancelled?
        migrations.AddField(
            model_name='booking',
            name='cancelled_at',
            field=models.DateTimeField(blank=True, null=True),
        ),

        # Update payment_method default from 'pay_at_station' → 'upi'
        migrations.AlterField(
            model_name='booking',
            name='payment_method',
            field=models.CharField(
                max_length=30,
                choices=[
                    ('upi',         'UPI'),
                    ('debit_card',  'Debit / Credit Card'),
                    ('net_banking', 'Net Banking'),
                ],
                default='upi',
            ),
        ),
    ]
