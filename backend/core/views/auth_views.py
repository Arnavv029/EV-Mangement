"""
Auth Views — Register & Login
==============================
Endpoints:
  POST /api/auth/register/  → Create a new user or owner account
  POST /api/auth/login/     → Login with email + password → returns JWT
  GET  /api/auth/me/        → Get the logged-in user's profile

LOGIN accepts email OR username as the first field for flexibility.
REGISTER accepts email, full_name, phone, password, role.
Username is auto-generated from the email prefix if not provided.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model

from core.serializers import UserProfileSerializer

User = get_user_model()


def _make_username(email):
    """Generate a unique username from email prefix."""
    base = email.split('@')[0].replace('.', '_').replace('+', '_')[:30]
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1
    return username


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


# ─────────────────────────────────────────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    Register a new User or Station Owner.

    Request body (JSON):
    {
        "email": "ramesh@gmail.com",
        "password": "mypassword",
        "role": "user",           ← "user" or "owner"
        "full_name": "Ramesh Kumar",   ← optional, split into first/last
        "phone": "9876543210",         ← optional
        "username": "ramesh123"        ← optional, auto-generated from email if absent
    }

    Response (201 Created):
    {
        "message": "Account created successfully!",
        "user": { ...user details... },
        "tokens": { "access": "...", "refresh": "..." }
    }
    """

    data = request.data
    email = data.get('email', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'user')
    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()
    username = data.get('username', '').strip() or _make_username(email)

    # Basic validation
    if not email or not password:
        return Response(
            {'error': 'Email and password are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if len(password) < 6:
        return Response(
            {'error': 'Password must be at least 6 characters.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'An account with this email already exists.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if User.objects.filter(username=username).exists():
        username = _make_username(email)

    # Split full_name into first/last
    parts = full_name.split(' ', 1)
    first_name = parts[0] if parts else ''
    last_name = parts[1] if len(parts) > 1 else ''

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role=role,
        phone=phone,
        first_name=first_name,
        last_name=last_name,
    )

    return Response({
        'message': 'Account created successfully!',
        'user': UserProfileSerializer(user).data,
        'tokens': _tokens_for_user(user),
    }, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login with email (or username) + password. Returns JWT tokens.

    Request body (JSON):
    {
        "email": "user1@evapp.com",   ← accepts email OR username field
        "password": "password123"
    }

    Response (200 OK):
    {
        "message": "Login successful!",
        "user": { ...user details including role... },
        "tokens": { "access": "...", "refresh": "..." }
    }
    """

    # Accept 'email', 'username', or the generic identifier
    identifier = (
        request.data.get('email') or
        request.data.get('username') or
        ''
    ).strip()
    password = request.data.get('password', '')

    if not identifier or not password:
        return Response(
            {'error': 'Please provide email/username and password.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Try to resolve email → username (Django's authenticate uses username)
    username = identifier
    if '@' in identifier:
        try:
            user_obj = User.objects.get(email=identifier)
            username = user_obj.username
        except User.DoesNotExist:
            pass

    user = authenticate(username=username, password=password)

    if user is None:
        return Response(
            {'error': 'Invalid credentials. Please check your email and password.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'error': 'This account has been deactivated.'},
            status=status.HTTP_403_FORBIDDEN
        )

    return Response({
        'message': 'Login successful!',
        'user': UserProfileSerializer(user).data,
        'tokens': _tokens_for_user(user),
    }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# GET PROFILE
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """Returns the currently logged-in user's profile."""
    return Response(UserProfileSerializer(request.user).data, status=status.HTTP_200_OK)
