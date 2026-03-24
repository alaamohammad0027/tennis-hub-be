"""
accounts/views/schema.py
All drf-spectacular decorators, OpenApiExamples, and schema-only serializers
for the accounts app. Import and apply in views — keeps views focused on logic.
"""

from drf_spectacular.utils import (
    OpenApiExample,
    PolymorphicProxySerializer,
    extend_schema,
    extend_schema_view,
)
from rest_framework import serializers

from accounts.serializers import (
    ClubProfileSerializer,
    CoachProfileSerializer,
    FanProfileSerializer,
    FederationProfileSerializer,
    PlayerProfileSerializer,
    RefereeProfileSerializer,
    # register
    FederationRegisterSerializer,
    ClubRegisterSerializer,
    CoachRegisterSerializer,
    RefereeRegisterSerializer,
    PlayerRegisterSerializer,
    FanRegisterSerializer,
    ResendVerificationSerializer,
    VerifyEmailSerializer,
    CompleteProfileSerializer,
    # auth
    LoginSerializer,
    LoginResponseSerializer,
    LogoutSerializer,
    # reset password
)
from accounts.serializers.reset_password import (
    RequestResetPasswordSerializer,
    VerifyResetPasswordSerializer,
    SetNewPasswordSerializer,
)

# ─────────────────────────────────────────────────────────────
# Tags
# ─────────────────────────────────────────────────────────────

_AUTH = "Authentication"
_REG = "Registration"
_PROFILE = "Profile"
_VERIFICATION = "Management"

# ─────────────────────────────────────────────────────────────
# Me — schema-only serializers (oneOf in Swagger)
# These are never used at runtime; they only inform Swagger what
# each user type's GET /me response looks like.
# ─────────────────────────────────────────────────────────────


class _MeBase(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField(read_only=True)
    phone_number = serializers.CharField()
    user_type = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    email_verified = serializers.BooleanField(read_only=True)
    photo = serializers.ImageField(allow_null=True)
    nationality = serializers.CharField(allow_blank=True)
    date_of_birth = serializers.DateField(allow_null=True)
    bio = serializers.CharField(allow_blank=True)


class FederationMeSerializer(_MeBase):
    profile = FederationProfileSerializer(allow_null=True)


class ClubMeSerializer(_MeBase):
    profile = ClubProfileSerializer(allow_null=True)


class CoachMeSerializer(_MeBase):
    profile = CoachProfileSerializer(allow_null=True)


class RefereeMeSerializer(_MeBase):
    profile = RefereeProfileSerializer(allow_null=True)


class PlayerMeSerializer(_MeBase):
    profile = PlayerProfileSerializer(allow_null=True)


class FanMeSerializer(_MeBase):
    profile = FanProfileSerializer(allow_null=True)


class AdminMeSerializer(_MeBase):
    """Admin users have no profile model."""

    profile = serializers.SerializerMethodField()

    def get_profile(self, obj):
        return None


_MeResponseSerializer = PolymorphicProxySerializer(
    component_name="MeResponse",
    serializers=[
        FederationMeSerializer,
        ClubMeSerializer,
        CoachMeSerializer,
        RefereeMeSerializer,
        PlayerMeSerializer,
        FanMeSerializer,
        AdminMeSerializer,
    ],
    resource_type_field_name="user_type",
)

_USER_EXAMPLE = {
    "id": "uuid",
    "first_name": "",
    "last_name": "",
    "full_name": "",
    "email": "",
    "phone_number": "",
    "user_type": "",
    "is_active": True,
    "email_verified": True,
    "photo": None,
    "nationality": "",
    "date_of_birth": None,
    "bio": "",
}

_me_get_examples = [
    OpenApiExample(
        "Federation",
        response_only=True,
        value={
            **_USER_EXAMPLE,
            "first_name": "Ahmed",
            "last_name": "Al-Rashid",
            "full_name": "Ahmed Al-Rashid",
            "email": "ahmed@federation.com",
            "phone_number": "+966501234567",
            "user_type": "federation",
            "nationality": "SA",
            "date_of_birth": "1975-03-10",
            "bio": "",
            "profile": {
                "id": "uuid",
                "federation_name": "Saudi Tennis Federation",
                "sport": "tennis",
                "country": "SA",
                "founding_year": 1985,
                "registration_number": "STF-001",
                "logo": None,
                "website": "https://saudifederation.com",
                "contact_email": "ahmed@federation.com",
                "contact_phone": "+966501234567",
                "description": "",
                "verification_status": "approved",
                "verified_by": "uuid",
                "verified_at": "2024-01-10T08:00:00Z",
                "rejection_reason": "",
                "is_active": True,
            },
        },
    ),
    OpenApiExample(
        "Club / Academy",
        response_only=True,
        value={
            **_USER_EXAMPLE,
            "first_name": "Sara",
            "last_name": "Al-Mutairi",
            "full_name": "Sara Al-Mutairi",
            "email": "sara@eliteclub.com",
            "phone_number": "+966509876543",
            "user_type": "club",
            "nationality": "SA",
            "date_of_birth": "1988-06-20",
            "bio": "",
            "profile": {
                "id": "uuid",
                "club_name": "Elite Tennis Academy",
                "club_type": "academy",
                "country": "SA",
                "city": "Riyadh",
                "address": "King Fahd Road, Riyadh",
                "founding_year": 2010,
                "registration_number": "ETA-2010",
                "logo": None,
                "website": "https://eliteclub.com",
                "contact_email": "sara@eliteclub.com",
                "contact_phone": "+966509876543",
                "description": "Premier tennis academy",
                "facility_count": 6,
                "verification_status": "approved",
                "verified_by": "uuid",
                "verified_at": "2024-02-15T09:30:00Z",
                "rejection_reason": "",
                "is_active": True,
            },
        },
    ),
    OpenApiExample(
        "Coach",
        response_only=True,
        value={
            **_USER_EXAMPLE,
            "first_name": "John",
            "last_name": "Doe",
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone_number": "+1234567890",
            "user_type": "coach",
            "nationality": "US",
            "date_of_birth": "1985-04-12",
            "bio": "Former ATP player.",
            "profile": {
                "id": "uuid",
                "specialization": "Serve & Volley",
                "coaching_level": "advanced",
                "license_number": "ITF-COACH-4521",
                "certifications": "ITF Level 3",
                "years_experience": 10,
                "verification_status": "approved",
                "verified_by": "uuid",
                "verified_at": "2024-03-01T10:00:00Z",
                "rejection_reason": "",
                "is_active": True,
            },
        },
    ),
    OpenApiExample(
        "Referee",
        response_only=True,
        value={
            **_USER_EXAMPLE,
            "first_name": "Maria",
            "last_name": "Garcia",
            "full_name": "Maria Garcia",
            "email": "maria@referee.com",
            "phone_number": "+34612345678",
            "user_type": "referee",
            "nationality": "ES",
            "date_of_birth": "1990-09-03",
            "bio": "8 years of international refereeing.",
            "profile": {
                "id": "uuid",
                "referee_level": "national",
                "license_number": "ITF-REF-7731",
                "certifications": "ITF White Badge",
                "years_experience": 8,
                "itf_badge": "white",
                "verification_status": "under_review",
                "verified_by": None,
                "verified_at": None,
                "rejection_reason": "",
                "is_active": True,
            },
        },
    ),
    OpenApiExample(
        "Player",
        response_only=True,
        value={
            **_USER_EXAMPLE,
            "first_name": "Carlos",
            "last_name": "Fernandez",
            "full_name": "Carlos Fernandez",
            "email": "carlos@player.com",
            "phone_number": "+5491123456789",
            "user_type": "player",
            "nationality": "AR",
            "date_of_birth": "1998-07-22",
            "bio": "Competitive amateur player.",
            "profile": {
                "id": "uuid",
                "skill_level": "intermediate",
                "ranking": 142,
                "dominant_hand": "right",
                "verification_status": "pending",
                "verified_by": None,
                "verified_at": None,
                "rejection_reason": "",
                "is_active": True,
            },
        },
    ),
    OpenApiExample(
        "Fan",
        response_only=True,
        value={
            **_USER_EXAMPLE,
            "first_name": "Lisa",
            "last_name": "Chen",
            "full_name": "Lisa Chen",
            "email": "lisa@fan.com",
            "phone_number": "",
            "user_type": "fan",
            "nationality": "CN",
            "date_of_birth": None,
            "bio": "Big tennis fan.",
            "profile": {
                "id": "uuid",
                "favorite_club": "uuid",
                "favorite_club_name": "Elite Tennis Academy",
                "verification_status": "approved",
                "is_active": True,
            },
        },
    ),
    OpenApiExample(
        "Admin",
        response_only=True,
        value={
            **_USER_EXAMPLE,
            "first_name": "Platform",
            "last_name": "Admin",
            "full_name": "Platform Admin",
            "email": "admin@tennispass.com",
            "phone_number": "",
            "user_type": "admin",
            "nationality": "",
            "date_of_birth": None,
            "bio": "",
            "profile": None,
        },
    ),
    OpenApiExample(
        "Google user — profile not completed yet",
        response_only=True,
        value={
            "id": "uuid",
            "full_name": "New User",
            "email": "newuser@gmail.com",
            "phone_number": "",
            "user_type": "fan",
            "is_active": True,
            "email_verified": True,
            "photo": None,
            "profile": None,
        },
    ),
]

me_schema = extend_schema_view(
    get=extend_schema(
        tags=[_PROFILE],
        summary="Get my profile",
        description=(
            "Returns the authenticated user's account fields + their typed profile in one response.\n\n"
            "`profile` is `null` for Google OAuth users who haven't completed their profile yet "
            "(redirect them to `POST /complete-profile`)."
        ),
        responses={200: _MeResponseSerializer},
        examples=_me_get_examples,
    ),
    patch=extend_schema(
        tags=[_PROFILE],
        summary="Update my profile",
        description=(
            "Update user account fields and/or profile fields in one call.\n\n"
            "**User fields (all types):** `first_name`, `last_name`, `phone_number`, `photo`, `nationality`, `date_of_birth`, `bio`\n\n"
            "**Profile fields:** type-specific writable fields, all flat at the top level. "
            "Verification fields (`verification_status`, `verified_by`, etc.) are read-only and cannot be changed here.\n\n"
            "All fields are optional — send only what you want to change.\n\n"
            "| Type | Writable profile fields |\n"
            "|---|---|\n"
            "| `federation` | `federation_name`, `sport`, `country`, `founding_year`, `registration_number`, `logo`, `website`, `contact_email`, `contact_phone`, `description` |\n"
            "| `club` | `club_name`, `club_type`, `country`, `city`, `address`, `founding_year`, `registration_number`, `logo`, `website`, `contact_email`, `contact_phone`, `description`, `facility_count` |\n"
            "| `coach` | `specialization`, `coaching_level`, `license_number`, `certifications`, `years_experience` |\n"
            "| `referee` | `referee_level`, `license_number`, `certifications`, `years_experience`, `itf_badge` |\n"
            "| `player` | `skill_level`, `dominant_hand` |\n"
            "| `fan` | `favorite_club` |\n"
            "| `admin` | no profile — only user account fields |\n"
        ),
        examples=[
            OpenApiExample(
                "Coach updates bio and phone",
                request_only=True,
                value={
                    "phone_number": "+1987654321",
                    "bio": "Updated bio.",
                    "years_experience": 12,
                },
            ),
            OpenApiExample(
                "Club updates city",
                request_only=True,
                value={"city": "Jeddah", "facility_count": 8},
            ),
            OpenApiExample(
                "Player updates skill level",
                request_only=True,
                value={"skill_level": "advanced", "dominant_hand": "left"},
            ),
            OpenApiExample(
                "Admin updates name",
                request_only=True,
                value={"first_name": "Super", "last_name": "Admin"},
            ),
        ],
    ),
)

# ─────────────────────────────────────────────────────────────
# Registration
# ─────────────────────────────────────────────────────────────

_reg_response = OpenApiExample(
    "Response",
    response_only=True,
    status_codes=["201"],
    value={
        "email": "user@example.com",
        "message": "Registration successful. Please check your email for the verification code.",
    },
)

federation_register_schema = extend_schema(
    tags=[_REG],
    request=FederationRegisterSerializer,
    summary="Register as Federation",
    description=(
        "Register a Sport Federation account. "
        "An OTP is sent to the provided email. "
        "Use `POST /auth/verify-email` to activate the account."
    ),
    examples=[
        OpenApiExample(
            "Request",
            request_only=True,
            value={
                "email": "admin@federation.com",
                "password": "SecurePass123",
                "password_confirm": "SecurePass123",
                "first_name": "Ahmed",
                "last_name": "Al-Rashid",
                "phone": "+966501234567",
                "nationality": "SA",
                "date_of_birth": "1975-03-10",
                "bio": "",
                "federation_name": "Saudi Tennis Federation",
                "country": "SA",
                "sport": "tennis",
                "founding_year": 1985,
                "registration_number": "STF-001",
                "website": "https://saudifederation.com",
            },
        ),
        _reg_response,
    ],
)

club_register_schema = extend_schema(
    tags=[_REG],
    request=ClubRegisterSerializer,
    summary="Register as Club / Academy",
    description="Register a Club or Academy account. An OTP is sent to the email for verification.",
    examples=[
        OpenApiExample(
            "Request",
            request_only=True,
            value={
                "email": "admin@eliteclub.com",
                "password": "SecurePass123",
                "password_confirm": "SecurePass123",
                "first_name": "Sara",
                "last_name": "Al-Mutairi",
                "phone": "+966509876543",
                "nationality": "SA",
                "date_of_birth": "1988-06-20",
                "bio": "",
                "club_name": "Elite Tennis Academy",
                "club_type": "academy",
                "country": "SA",
                "city": "Riyadh",
                "address": "King Fahd Road, Riyadh",
                "registration_number": "ETA-2010",
                "website": "https://eliteclub.com",
            },
        ),
        _reg_response,
    ],
)

coach_register_schema = extend_schema(
    tags=[_REG],
    request=CoachRegisterSerializer,
    summary="Register as Coach",
    description="Register a Coach account. An OTP is sent to the email for verification.",
    examples=[
        OpenApiExample(
            "Request",
            request_only=True,
            value={
                "email": "john@coach.com",
                "password": "SecurePass123",
                "password_confirm": "SecurePass123",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "nationality": "US",
                "date_of_birth": "1985-04-12",
                "bio": "Former ATP player turned coach.",
                "specialization": "Serve & Volley",
                "coaching_level": "advanced",
                "license_number": "ITF-COACH-4521",
                "years_experience": 10,
            },
        ),
        _reg_response,
    ],
)

referee_register_schema = extend_schema(
    tags=[_REG],
    request=RefereeRegisterSerializer,
    summary="Register as Referee",
    description="Register a Referee account. An OTP is sent to the email for verification.",
    examples=[
        OpenApiExample(
            "Request",
            request_only=True,
            value={
                "email": "maria@referee.com",
                "password": "SecurePass123",
                "password_confirm": "SecurePass123",
                "first_name": "Maria",
                "last_name": "Garcia",
                "phone": "+34612345678",
                "nationality": "ES",
                "date_of_birth": "1990-09-03",
                "bio": "8 years of international refereeing.",
                "referee_level": "national",
                "license_number": "ITF-REF-7731",
                "years_experience": 8,
                "itf_badge": "white",
            },
        ),
        _reg_response,
    ],
)

player_register_schema = extend_schema(
    tags=[_REG],
    request=PlayerRegisterSerializer,
    summary="Register as Player",
    description="Register a Player account. An OTP is sent to the email for verification.",
    examples=[
        OpenApiExample(
            "Request",
            request_only=True,
            value={
                "email": "carlos@player.com",
                "password": "SecurePass123",
                "password_confirm": "SecurePass123",
                "first_name": "Carlos",
                "last_name": "Fernandez",
                "phone": "+5491123456789",
                "nationality": "AR",
                "date_of_birth": "1998-07-22",
                "bio": "Competitive amateur player.",
                "skill_level": "intermediate",
                "dominant_hand": "right",
            },
        ),
        _reg_response,
    ],
)

fan_register_schema = extend_schema(
    tags=[_REG],
    request=FanRegisterSerializer,
    summary="Register as Fan",
    description=(
        "Register a Fan account. " "An OTP is sent to the email for verification."
    ),
    examples=[
        OpenApiExample(
            "Request",
            request_only=True,
            value={
                "email": "lisa@fan.com",
                "password": "SecurePass123",
                "password_confirm": "SecurePass123",
                "first_name": "Lisa",
                "last_name": "Chen",
                "nationality": "CN",
                "bio": "Big tennis fan.",
            },
        ),
        _reg_response,
    ],
)

resend_verification_schema = extend_schema(
    tags=[_AUTH],
    request=ResendVerificationSerializer,
    summary="Resend email verification OTP",
    description=(
        "Resend the email verification OTP. Use this when the original OTP has expired "
        "or was not received. Returns a new JWT token to use with `POST /auth/verify-email`.\n\n"
        "Always returns 200 — even if email not found — to prevent user enumeration."
    ),
    examples=[
        OpenApiExample(
            "Request",
            request_only=True,
            value={"email": "john@coach.com"},
        ),
        OpenApiExample(
            "Response",
            response_only=True,
            status_codes=["200"],
            value={
                "email": "john@coach.com",
                "message": "Verification code resent. Please check your email.",
            },
        ),
    ],
)

verify_email_schema = extend_schema(
    tags=[_AUTH],
    request=VerifyEmailSerializer,
    responses={200: LoginResponseSerializer},
    summary="Verify email with OTP",
    description=(
        "Verify email with the 6-digit OTP sent after registration. "
        "Returns the same response as login on success. "
        "The profile's `verification_status` advances from `pending` → `under_review`."
    ),
    examples=[
        OpenApiExample(
            "Request",
            request_only=True,
            value={"email": "john@coach.com", "otp_code": "483921"},
        ),
        OpenApiExample(
            "Response",
            response_only=True,
            status_codes=["200"],
            value={
                "email": "john@coach.com",
                "full_name": "John Doe",
                "user_type": "coach",
                "tokens": {
                    "access": "<access_token>",
                    "refresh": "<refresh_token>",
                },
            },
        ),
    ],
)

complete_profile_schema = extend_schema(
    tags=[_REG],
    request=CompleteProfileSerializer,
    summary="Complete profile (Google OAuth)",
    description=(
        "For users who signed up via Google OAuth (`is_new_user=true`). "
        "Choose a `user_type` and supply the required fields for that type."
    ),
    examples=[
        OpenApiExample(
            "As Coach",
            request_only=True,
            value={
                "user_type": "coach",
                "specialization": "Baseline",
                "coaching_level": "intermediate",
                "years_experience": 3,
            },
        ),
        OpenApiExample(
            "As Club",
            request_only=True,
            value={
                "user_type": "club",
                "club_name": "Elite Tennis Academy",
                "club_type": "academy",
                "country": "SA",
                "city": "Riyadh",
            },
        ),
        OpenApiExample(
            "As Fan",
            request_only=True,
            value={"user_type": "fan", "nationality": "CN"},
        ),
    ],
)

# ─────────────────────────────────────────────────────────────
# Authentication
# ─────────────────────────────────────────────────────────────

login_schema = extend_schema(
    tags=[_AUTH],
    summary="Login",
    description="Login with email and password. Returns access + refresh tokens.",
    request=LoginSerializer,
    responses={200: LoginResponseSerializer},
)

logout_schema = extend_schema(
    tags=[_AUTH],
    summary="Logout",
    description="Logout and blacklist the refresh token.",
    request=LogoutSerializer,
)

# ─────────────────────────────────────────────────────────────
# Password reset
# ─────────────────────────────────────────────────────────────

request_reset_schema = extend_schema(
    tags=[_AUTH],
    summary="Request password reset",
    description=(
        "Step 1 — Request a password reset OTP by email. "
        "Always returns 200 to prevent email enumeration."
    ),
    request=RequestResetPasswordSerializer,
)

verify_reset_schema = extend_schema(
    tags=[_AUTH],
    summary="Verify password reset OTP",
    description="Step 2 — Verify the OTP. Returns `uidb64` + `reset_token` needed for step 3.",
    request=VerifyResetPasswordSerializer,
)

set_new_password_schema = extend_schema(
    tags=[_AUTH],
    summary="Set new password",
    description="Step 3 — Set the new password using `uidb64` + `reset_token` from step 2.",
    request=SetNewPasswordSerializer,
)

# ─────────────────────────────────────────────────────────────
# Profiles / Verification
# ─────────────────────────────────────────────────────────────

federation_profiles_schema = extend_schema_view(
    list=extend_schema(
        tags=[_VERIFICATION],
        summary="List federation profiles",
        description=(
            "**Admin** sees all federations. **Others** see only their own federation profile."
        ),
    ),
    retrieve=extend_schema(tags=[_VERIFICATION], summary="Federation profile detail"),
    approve=extend_schema(
        tags=[_VERIFICATION],
        summary="Approve a federation profile",
        description="**Admin only.** Sets `verification_status` → `approved`.",
    ),
    reject=extend_schema(
        tags=[_VERIFICATION],
        summary="Reject a federation profile",
        description='**Admin only.** Body: `{"reason": "<explanation>"}`. Sets `verification_status` → `rejected`.',
    ),
)

club_profiles_schema = extend_schema_view(
    list=extend_schema(
        tags=[_VERIFICATION],
        summary="List club profiles",
        description=(
            "**Admin** sees all clubs. "
            "**Federation** sees clubs linked to their federation. "
            "**Others** see only their own club profile."
        ),
    ),
    retrieve=extend_schema(tags=[_VERIFICATION], summary="Club profile detail"),
    approve=extend_schema(
        tags=[_VERIFICATION],
        summary="Approve a club profile",
        description="**Admin or Federation.** Sets `verification_status` → `approved`.",
    ),
    reject=extend_schema(
        tags=[_VERIFICATION],
        summary="Reject a club profile",
        description='**Admin or Federation.** Body: `{"reason": "<explanation>"}`. Sets `verification_status` → `rejected`.',
    ),
)

coach_profiles_schema = extend_schema_view(
    list=extend_schema(
        tags=[_VERIFICATION],
        summary="List coach profiles",
        description=(
            "**Admin** sees all coaches. "
            "**Club** sees coaches affiliated with their club. "
            "**Coach** sees only their own profile."
        ),
    ),
    retrieve=extend_schema(tags=[_VERIFICATION], summary="Coach profile detail"),
    approve=extend_schema(
        tags=[_VERIFICATION],
        summary="Approve a coach profile",
        description="**Admin or affiliated Club.** Sets `verification_status` → `approved`.",
    ),
    reject=extend_schema(
        tags=[_VERIFICATION],
        summary="Reject a coach profile",
        description='**Admin or affiliated Club.** Body: `{"reason": "<explanation>"}`. Sets `verification_status` → `rejected`.',
    ),
)

referee_profiles_schema = extend_schema_view(
    list=extend_schema(
        tags=[_VERIFICATION],
        summary="List referee profiles",
        description=(
            "**Admin** sees all referees. "
            "**Club** sees referees affiliated with their club. "
            "**Federation** sees referees affiliated with their federation. "
            "**Referee** sees only their own profile."
        ),
    ),
    retrieve=extend_schema(tags=[_VERIFICATION], summary="Referee profile detail"),
    approve=extend_schema(
        tags=[_VERIFICATION],
        summary="Approve a referee profile",
        description="**Admin, affiliated Club, or affiliated Federation.** Sets `verification_status` → `approved`.",
    ),
    reject=extend_schema(
        tags=[_VERIFICATION],
        summary="Reject a referee profile",
        description='**Admin, affiliated Club, or affiliated Federation.** Body: `{"reason": "<explanation>"}`. Sets `verification_status` → `rejected`.',
    ),
)

player_profiles_schema = extend_schema_view(
    list=extend_schema(
        tags=[_VERIFICATION],
        summary="List player profiles",
        description=(
            "**Admin** sees all players. "
            "**Club** sees players with an active membership. "
            "**Player** sees only their own profile."
        ),
    ),
    retrieve=extend_schema(tags=[_VERIFICATION], summary="Player profile detail"),
    approve=extend_schema(
        tags=[_VERIFICATION],
        summary="Approve a player profile",
        description="**Admin or Club (with active membership).** Sets `verification_status` → `approved`.",
    ),
    reject=extend_schema(
        tags=[_VERIFICATION],
        summary="Reject a player profile",
        description='**Admin or Club (with active membership).** Body: `{"reason": "<explanation>"}`. Sets `verification_status` → `rejected`.',
    ),
)

fan_profiles_schema = extend_schema_view(
    list=extend_schema(
        tags=[_VERIFICATION],
        summary="List fan profiles",
        description=(
            "**Admin** sees all fans. **Fan** sees only their own profile. "
            "Fans are auto-approved at registration — no verification actions available."
        ),
    ),
    retrieve=extend_schema(tags=[_VERIFICATION], summary="Fan profile detail"),
)
