"""
Authentication API endpoints.
Handles user registration, login, email/phone verification.
"""

from datetime import datetime
from typing import Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, validator
import re

from app.core.database import get_db
from app.core.config import get_settings
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.services.sms_service import SMSService

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)
settings = get_settings()


# Pydantic models for request/response
class UserRegistrationRequest(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: str

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v

    @validator("phone_number")
    def validate_phone_number(cls, v):
        if v and not re.match(r"^\+?1?\d{9,15}$", v):
            raise ValueError("Invalid phone number format")
        return v

    def __init__(self, **data):
        super().__init__(**data)
        if not self.email and not self.phone_number:
            raise ValueError("Either email or phone number must be provided")


class LoginRequest(BaseModel):
    email_or_phone: str
    password: str


class VerificationRequest(BaseModel):
    verification_code: str


class ResendVerificationRequest(BaseModel):
    email_or_phone: str


class UserResponse(BaseModel):
    id: str
    email: Optional[str]
    phone_number: Optional[str]
    first_name: str
    last_name: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    email_verified: bool
    phone_verified: bool
    is_verified: bool
    is_superuser: bool
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UserRegistrationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user with email or phone number."""
    logger.info("📝 Registration request received")
    logger.info(
        f"Data: first_name={user_data.first_name}, "
        f"last_name={user_data.last_name}"
    )
    logger.info(f"Email: {user_data.email}, Phone: {user_data.phone_number}")
    
    auth_service = AuthService(db)

    # Check if user already exists
    existing_user = await auth_service.get_user_by_email_or_phone(
        user_data.email, user_data.phone_number
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or phone number already exists",
        )

    # Create user
    user = await auth_service.create_user(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email,
        phone_number=user_data.phone_number,
        password=user_data.password,
    )

    # Send verification
    if user.email:
        logger.info(f"👤 User registered with email: {user.email}")
        logger.info("📧 Adding email verification task to background queue")
        logger.info(f"🔑 Verification token: {user.email_verification_token}")
        
        email_service = EmailService()
        background_tasks.add_task(
            email_service.send_verification_email,
            user.email,
            user.email_verification_token,
        )
        logger.info("✅ Email verification task queued successfully")

    if user.phone_number:
        sms_service = SMSService()
        background_tasks.add_task(
            sms_service.send_verification_sms,
            user.phone_number,
            user.phone_verification_code,
        )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        phone_number=user.phone_number,
        first_name=user.first_name,
        last_name=user.last_name,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        email_verified=user.email_verified,
        phone_verified=user.phone_verified,
        is_verified=user.is_verified,
        is_superuser=user.is_superuser,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login_user(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return access tokens."""
    auth_service = AuthService(db)

    # Authenticate user
    user = await auth_service.authenticate_user(
        login_data.email_or_phone, login_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # Note: Removed verification requirement for login
    # Users can login but may have limited functionality until verified

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is deactivated"
        )

    # Create tokens
    access_token = await auth_service.create_access_token(user.id)
    refresh_token = await auth_service.create_refresh_token(user.id)

    # Update last login
    await auth_service.update_last_login(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            phone_number=user.phone_number,
            first_name=user.first_name,
            last_name=user.last_name,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            email_verified=user.email_verified,
            phone_verified=user.phone_verified,
            is_verified=user.is_verified,
            is_superuser=user.is_superuser,
            is_active=user.is_active,
            created_at=user.created_at,
        )
    )


@router.post("/verify-email")
async def verify_email(
    verification_data: VerificationRequest, db: AsyncSession = Depends(get_db)
):
    """Verify user's email address."""
    auth_service = AuthService(db)

    success = await auth_service.verify_email(verification_data.verification_code)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )

    return {"message": "Email verified successfully"}


@router.post("/verify-phone")
async def verify_phone(
    verification_data: VerificationRequest, db: AsyncSession = Depends(get_db)
):
    """Verify user's phone number."""
    auth_service = AuthService(db)

    success = await auth_service.verify_phone(verification_data.verification_code)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )

    return {"message": "Phone number verified successfully"}


@router.post("/resend-verification")
async def resend_verification(
    resend_data: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Resend verification code to email or phone."""
    auth_service = AuthService(db)

    user = await auth_service.get_user_by_email_or_phone(
        resend_data.email_or_phone if "@" in resend_data.email_or_phone else None,
        resend_data.email_or_phone if "@" not in resend_data.email_or_phone else None,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Regenerate verification codes
    await auth_service.generate_verification_codes(user)

    # Send verification
    if "@" in resend_data.email_or_phone and user.email:
        email_service = EmailService()
        background_tasks.add_task(
            email_service.send_verification_email,
            user.email,
            user.email_verification_token,
        )
    else:
        sms_service = SMSService()
        background_tasks.add_task(
            sms_service.send_verification_sms,
            user.phone_number,
            user.phone_verification_code,
        )

    return {"message": "Verification code sent successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """Get current user information."""
    auth_service = AuthService(db)

    user = await auth_service.get_current_user(credentials.credentials)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        phone_number=user.phone_number,
        first_name=user.first_name,
        last_name=user.last_name,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        email_verified=user.email_verified,
        phone_verified=user.phone_verified,
        is_verified=user.is_verified,
        is_superuser=user.is_superuser,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    auth_service = AuthService(db)

    tokens = await auth_service.refresh_tokens(credentials.credentials)

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    
    # Get user data from the new access token
    user = await auth_service.get_current_user(tokens["access_token"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            phone_number=user.phone_number,
            first_name=user.first_name,
            last_name=user.last_name,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            email_verified=user.email_verified,
            phone_verified=user.phone_verified,
            is_verified=user.is_verified,
            is_superuser=user.is_superuser,
            is_active=user.is_active,
            created_at=user.created_at,
        )
    )


@router.post("/logout")
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """Logout user and revoke tokens."""
    auth_service = AuthService(db)

    await auth_service.logout_user(credentials.credentials)

    return {"message": "Logged out successfully"}


@router.post("/request-verification")
async def request_verification(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Request new verification codes for the current user."""
    logger.info(f"📧 User {current_user.email} requesting verification resend")
    
    auth_service = AuthService(db)
    
    # Generate new verification codes
    auth_service.generate_verification_codes(current_user)
    await db.commit()
    
    # Send verification emails/SMS
    if current_user.email and not current_user.email_verified:
        email_service = EmailService()
        background_tasks.add_task(
            email_service.send_verification_email,
            current_user.email,
            current_user.email_verification_token,
        )
        logger.info("📧 Email verification resent")
    
    if current_user.phone_number and not current_user.phone_verified:
        sms_service = SMSService()
        background_tasks.add_task(
            sms_service.send_verification_sms,
            current_user.phone_number,
            current_user.phone_verification_code,
        )
        logger.info("📱 SMS verification resent")
    
    return {"message": "Verification codes sent to your registered contact methods"}


@router.get("/dev/verification-info/{email}")
async def get_verification_info_dev(
    email: str,
    db: AsyncSession = Depends(get_db),
):
    """Development endpoint to get verification token for testing."""
    from app.core.config import get_settings
    settings = get_settings()
    
    if settings.ENVIRONMENT != "local":
        raise HTTPException(status_code=404, detail="Not found")
    
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_email_or_phone(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    verification_url = (
        f"http://localhost:3000/verify-email?"
        f"token={user.email_verification_token}"
    )
    
    return {
        "email": email,
        "email_verification_token": user.email_verification_token,
        "email_verified": user.email_verified,
        "verification_url": verification_url,
        "message": "This endpoint is only available in development mode"
    }


@router.post("/dev/test-email")
async def test_email_dev(
    email: str,
    background_tasks: BackgroundTasks,
):
    """Development endpoint to test email sending."""
    from app.core.config import get_settings
    from app.services.email_service import EmailService
    settings = get_settings()
    
    if settings.ENVIRONMENT != "local":
        raise HTTPException(status_code=404, detail="Not found")
    
    email_service = EmailService()
    
    # Send a test email
    background_tasks.add_task(
        email_service.send_verification_email,
        email,
        "test-token-12345"
    )
    
    return {
        "message": f"Test email sent to {email}",
        "smtp_configured": bool(settings.SMTP_SERVER),
        "smtp_server": settings.SMTP_SERVER
    }
