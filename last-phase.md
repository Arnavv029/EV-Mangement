since we are building an ev slot management system project in which i have to make last some minimal changes that is its landing page is correct and fine but in its home page i have to make some chnages that is filter the nearby station on the based on rating and shorest distance from us and do one more thing that is you provide dummy data please edit it the location of that station and get the nearby location to my location and also add some more nearby by station near me and make the owner of this station as same owner that you provid the dummy owner and add minimal amount like 10 rupee and 5  rupee in each station sation details page is fine last thing is that please interigate the razopay in my project we can select payment mode it will delect according to it the pop up is open for
for interigation i have plan according to it please implement the payment method 

Phase 1 — Razorpay account and configuration





Create a Razorpay account and enable Test Mode.



From Dashboard → API Keys, copy Key ID and Key Secret.



(Recommended) Dashboard → Webhooks → add endpoint (after deploy) and copy Webhook Secret.

Backend config — add to [backend/ev_backend/settings.py](backend/ev_backend/settings.py) (read from environment, never commit secrets):

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")

Add razorpay to [backend/requirements.txt](backend/requirements.txt):

razorpay>=1.4.0

Create backend/.env.example with the three variables (gitignored .env for local use).



Phase 2 — Data model for pending payments

Add a small model in [backend/core/models.py](backend/core/models.py), e.g. PaymentAttempt:







Field



Purpose





user



FK to CustomUser





razorpay_order_id



From orders.create





amount_paise



Integer (Razorpay uses paise)





status



created / paid / failed / expired





razorpay_payment_id



Set after successful payment





booking



Nullable FK — set after verify creates Booking





payload_json



JSON: slot id, personal + vehicle fields (draft booking data)





created_at



Audit

Why: You must not create a Booking until payment is verified, but you still need to remember slot + form data between create-order and verify.

Migration: 0006_payment_attempt.py (or next number after existing migrations).



Phase 3 — Backend payment service and APIs

New module [backend/core/utils/razorpay_client.py](backend/core/utils/razorpay_client.py):





Initialize razorpay.Client(auth=(KEY_ID, KEY_SECRET)).



create_order(amount_paise, receipt, notes) → calls client.order.create.



verify_payment_signature(order_id, payment_id, signature) → client.utility.verify_payment_signature({...}).



(Phase 2) refund_payment(payment_id, amount_paise) → client.payment.refund.

New views [backend/core/views/payment_views.py](backend/core/views/payment_views.py):

POST /api/payments/razorpay/create-order/ (authenticated)

Body: same booking fields you already send today (slot, full_name, phone, email, vehicle, computed amount_paid).

Steps:





Validate slot exists, is_available, not is_full (same rules as [BookingCreateSerializer.validate_slot](backend/core/serializers.py)).



Compute amount in paise (int(amount * 100)), minimum ₹5 if you keep current MINIMUM_AMOUNT.



Create Razorpay order with receipt like hev-{user_id}-{timestamp} and notes { slot_id, user_id }.



Save PaymentAttempt with status=created and draft payload.



Return:

{
  "key_id": "rzp_test_...",
  "order_id": "order_...",
  "amount": 12000,
  "currency": "INR",
  "attempt_id": 42,
  "prefill": { "name": "...", "email": "...", "contact": "..." }
}

Register routes in [backend/core/urls.py](backend/core/urls.py).

POST /api/payments/razorpay/verify/ (authenticated)

Body: razorpay_order_id, razorpay_payment_id, razorpay_signature, attempt_id (optional cross-check).

Steps:





Load PaymentAttempt for this user; ensure status == created.



Verify signature with Razorpay utility — reject on failure (payment_failed).



Inside transaction.atomic():





select_for_update() on TimeSlot; if full → mark attempt failed, return 409 (document that manual refund may be needed if payment already captured — webhook helps).



Create Booking with payment_status='paid', payment_method='razorpay', transaction_id=razorpay_payment_id.



Increment booked_count, generate QR via existing [generate_qr_code](backend/core/utils/qr_generator.py).



Set attempt status=paid, link booking.



Return same shape as today: { message, booking } so confirmation/history keep working.

POST /api/payments/razorpay/webhook/ (no JWT; CSRF exempt)

Handle at least:





payment.captured — idempotent: if attempt still created, run same confirm logic as verify (covers user closing tab after pay).



payment.failed — set attempt failed.

Verify webhook using X-Razorpay-Signature + RAZORPAY_WEBHOOK_SECRET.

Expose in [backend/ev_backend/urls.py](backend/ev_backend/urls.py) or core/urls.py; for local dev use ngrok or similar so Razorpay can reach your machine.



Phase 4 — Refactor existing booking endpoint

Update [create_booking_view](backend/core/views/booking_views.py):





Option A (recommended): Deprecate direct paid booking — return 400 with message “Use Razorpay checkout” if old payload includes utr_number / card fields.



Option B: Keep for local dev only when DEBUG=True and env ALLOW_SIMULATED_PAYMENT=true.

Remove or stop using manual UPI QR endpoint [upi_qr_view](backend/core/views/booking_views.py) once Razorpay handles UPI inside Checkout (optional cleanup).

Update [BookingCreateSerializer](backend/core/serializers.py):





Add razorpay to allowed payment_method choices on the model (migration AlterField on payment_method).



Drop write-only utr_number, card_*, bank_name from serializer when moving to Razorpay-only UI.



Phase 5 — Frontend changes ([booking.html](frotend/public/pages/booking.html))





Add Razorpay script in <head>:

<script src="https://checkout.razorpay.com/v1/checkout.js"></script>





Replace the three payment method panels (UPI / card / netbanking) with:





Order summary (unchanged)



One primary button: Pay securely with Razorpay



New submit flow in page script:

on Pay click:
  1. POST /api/payments/razorpay/create-order/  (booking draft fields)
  2. new Razorpay({ key, order_id, amount, currency, name, prefill, handler })
  3. handler → POST /api/payments/razorpay/verify/ with payment response
  4. on success → sessionStorage + redirect confirmation.html
  5. on dismiss → toast "Payment cancelled"





Expose RAZORPAY_KEY_ID to frontend only via create-order response (key_id) — never send Key Secret to the browser.



Update copy: remove UTR test hint; mention test cards from Razorpay test docs.

No change required to [api.js](frotend/public/js/api.js) beyond using existing apiPost.



Phase 6 — Real refunds on cancellation (recommended follow-up)

In [cancel_booking_view](backend/core/views/booking_views.py), after computing refund amount:





If booking.transaction_id looks like Razorpay payment id (pay_...) and refund > 0:





Call razorpay_client.refund_payment(payment_id, int(refund * 100)).



Store Razorpay refund id in a new optional field refund_transaction_id or append to notes.



On API failure: do not mark payment_status=refunded until success; return error to user.

Partial refunds map cleanly to your existing percentage rules in [payment_processor.py](backend/core/utils/payment_processor.py) (calculate_refund_percentage).



Phase 7 — Testing checklist







Step



Action





1



Set test keys in backend/.env, restart runserver





2



Book a slot → Razorpay test modal opens





3



Pay with test UPI/card → verify → booking + QR on confirmation





4



Try double-booking same slot from two tabs → second verify should 409

5
Cancel booking → (Phase 6) refund appears in Razorpay Dashboard
6

Configure webhook + ngrok → repeat payment; confirm booking still created if verify call fails
Files to add or change (summary)
Area
Files
Config
[backend/ev_backend/settings.py](backend/ev_backend/settings.py), [backend/requirements.txt](backend/requirements.txt), .env.example
Mode
[backend/core/models.py](backend/core/models.py), new migration
Payment logic
backend/core/utils/razorpay_client.py, backend/core/views/payment_views.py
Routes
[backend/core/urls.py](backend/core/urls.py)
Booking
[backend/core/views/booking_views.py](backend/core/views/booking_views.py), [backend/core/serializers.py](backend/core/serializers.py)
Refunds
[backend/core/views/booking_views.py](backend/core/views/booking_views.py) cancel path
[frotend/public/pages/booking.html](frotend/public/pages/booking.html)

Admin
[backend/core/admin.py](backend/core/admin.py) register PaymentAttempt
Security notes
Key Secret and webhook secret only on server.
Always verify razorpay_signature on the server before creating a booking.
Use webhooks for idempotency; store razorpay_payment_id uniquely to avoid double booking.
In production: DEBUG=False, HTTPS, restrict ALLOWED_HOSTS, use live keys only on deployed environment.
Estimated effort
Phase 1–5 (pay + book): ~1–2 days for a working test-mode integration.
Phase 6 (Razorpay refunds): ~half day.
Webhook hardening + edge cases: ~half day.
This plan keeps your existing booking, QR, history, and review flows intact while swapping the payment layer for Razorpay’s verified, production-grade checkout.