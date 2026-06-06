# EV Station Slot Booking System

A full-stack web application for booking EV charging station slots with QR-based verification.

---

## Project Structure

```
EV-Mangment/
└── backend/                   ← Django REST API (Phase 1 - COMPLETE)
    ├── manage.py
    ├── requirements.txt
    ├── db.sqlite3              ← SQLite database (auto-created after migrate)
    ├── ev_backend/             ← Django project config
    │   ├── settings.py         ← App settings, JWT, CORS, database
    │   └── urls.py             ← Root URL router
    └── core/                  ← Main app
        ├── models.py           ← Database tables (User, Station, TimeSlot, Booking)
        ├── serializers.py      ← Python ↔ JSON conversion
        ├── urls.py             ← All API route definitions
        ├── admin.py            ← Django admin panel config
        ├── views/
        │   ├── auth_views.py   ← Register, Login, Profile
        │   ├── station_views.py← List stations, detail, slots by date
        │   ├── booking_views.py← Create booking (+ QR), history, detail
        │   └── owner_views.py  ← Station mgmt, QR verify, approve/reject
        ├── utils/
        │   ├── qr_generator.py ← Generates QR code as base64 PNG
        │   └── distance.py     ← Haversine formula for GPS distance
        └── management/commands/
            └── seed_data.py    ← Creates demo users, stations & slots
```

---

## Quick Start

```bash
# 1. Go to backend folder
cd backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create database tables
python manage.py migrate

# 4. Load demo data
python manage.py seed_data

# 5. Start the server
python manage.py runserver

# Server runs at: http://localhost:8000/
```

---

## Demo Accounts (after seed_data)

| Role | Username | Password |
|------|----------|----------|
| EV User | `user1` | `password123` |
| Station Owner | `owner1` | `password123` |

---

## Complete API Reference

### Authentication
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register/` | Register new account | No |
| POST | `/api/auth/login/` | Login → get JWT tokens | No |
| GET | `/api/auth/me/` | Get current user profile | Yes |

### Stations (User)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/stations/` | List stations (optional: `?lat=&lng=` for distance sort) | Yes |
| GET | `/api/stations/{id}/` | Station detail | Yes |
| GET | `/api/stations/{id}/slots/` | Slots for a date (`?date=YYYY-MM-DD`) | Yes |

### Bookings (User)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/bookings/` | Create booking (auto-generates QR) | Yes |
| GET | `/api/bookings/history/` | My booking history | Yes |
| GET | `/api/bookings/{id}/` | Single booking + QR code | Yes |

### Owner Management
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET/POST | `/api/owner/stations/` | List / Add stations | Owner only |
| POST | `/api/owner/slots/` | Create time slots (single or bulk) | Owner only |
| GET | `/api/owner/bookings/` | All bookings for my stations | Owner only |
| GET | `/api/owner/bookings/{id}/` | Single booking detail | Owner only |
| PATCH | `/api/owner/bookings/{id}/status/` | Approve or reject booking | Owner only |
| POST | `/api/owner/verify-qr/` | Scan QR → return booking info | Owner only |

---

## How JWT Authentication Works

```
1. User logs in → backend returns:
   { "access": "eyJ...", "refresh": "eyJ..." }

2. Frontend stores tokens in localStorage

3. Every API call includes:
   Header: Authorization: Bearer eyJ...

4. Backend verifies token → identifies user → processes request
```

---

## How QR Code Works

```
1. User creates booking → backend generates UUID (booking_id)
2. Backend encodes booking details into JSON:
   {"booking_id": "abc...", "user_name": "Ramesh", "station": "Green Power Hub", ...}
3. JSON is converted to a QR code image
4. QR image is base64-encoded and stored with the booking
5. Frontend displays: <img src="data:image/png;base64,..." />
6. Owner scans QR → reads JSON → extracts booking_id
7. Owner sends booking_id to /api/owner/verify-qr/
8. Backend returns full booking details → owner approves/rejects
```

---

## Admin Panel

```bash
# Create superuser account
python manage.py createsuperuser

# Open in browser
http://localhost:8000/admin/
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Django 6 + Django REST Framework |
| Authentication | JWT (djangorestframework-simplejwt) |
| Database | SQLite (built-in) |
| QR Generation | Python `qrcode` + `Pillow` |
| CORS | `django-cors-headers` |

---

## Development Phases

- [x] **Phase 1** — Backend (Django REST API) ← **YOU ARE HERE**
- [ ] **Phase 2** — Frontend (React + TailwindCSS)
- [ ] **Phase 3** — Integration (Axios API calls)
