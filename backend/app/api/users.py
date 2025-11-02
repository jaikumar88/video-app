"""
Users API endpoints for profile management.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
import json

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter()
security = HTTPBearer()


# Pydantic models
class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    timezone: Optional[str] = None
    preferred_language: Optional[str] = None
    meeting_settings: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, Any]] = None


class UserProfileResponse(BaseModel):
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
    created_at: str
    last_login: Optional[str]
    timezone: str
    preferred_language: str
    meeting_settings: Dict[str, Any]
    notification_settings: Dict[str, Any]


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user."""
    auth_service = AuthService(db)
    user = await auth_service.get_current_user(credentials.credentials)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    return user


@router.get("/me", response_model=UserProfileResponse)
@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get user profile information."""

    # Parse JSON settings
    meeting_settings = {}
    notification_settings = {}

    if current_user.meeting_settings:
        try:
            meeting_settings = json.loads(current_user.meeting_settings)
        except json.JSONDecodeError:
            meeting_settings = {}

    if current_user.notification_settings:
        try:
            notification_settings = json.loads(current_user.notification_settings)
        except json.JSONDecodeError:
            notification_settings = {}

    return UserProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        phone_number=current_user.phone_number,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        email_verified=current_user.email_verified,
        phone_verified=current_user.phone_verified,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at.isoformat(),
        last_login=(
            current_user.last_login.isoformat() if current_user.last_login else None
        ),
        timezone=current_user.timezone,
        preferred_language=current_user.preferred_language,
        meeting_settings=meeting_settings,
        notification_settings=notification_settings,
    )


@router.put("/me", response_model=UserProfileResponse)
@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user profile information."""

    # Update fields if provided
    if profile_data.first_name is not None:
        current_user.first_name = profile_data.first_name.strip()

    if profile_data.last_name is not None:
        current_user.last_name = profile_data.last_name.strip()

    if profile_data.display_name is not None:
        current_user.display_name = profile_data.display_name.strip() or None

    if profile_data.timezone is not None:
        current_user.timezone = profile_data.timezone

    if profile_data.preferred_language is not None:
        current_user.preferred_language = profile_data.preferred_language

    if profile_data.meeting_settings is not None:
        current_user.meeting_settings = json.dumps(profile_data.meeting_settings)

    if profile_data.notification_settings is not None:
        current_user.notification_settings = json.dumps(
            profile_data.notification_settings
        )

    await db.commit()
    await db.refresh(current_user)

    # Return updated profile
    return await get_user_profile(current_user)


@router.post("/profile/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload user avatar image."""

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File must be an image"
        )

    # Validate file size (max 5MB)
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 5MB",
        )

    # TODO: Implement file upload to storage (S3, local, etc.)
    # For now, just return a placeholder URL
    avatar_url = f"https://api.yourdomain.com/uploads/avatars/{current_user.id}.jpg"

    # Update user avatar URL
    current_user.avatar_url = avatar_url
    await db.commit()

    return {"message": "Avatar uploaded successfully", "avatar_url": avatar_url}


@router.delete("/profile/avatar")
async def delete_avatar(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Delete user avatar."""

    if not current_user.avatar_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No avatar found"
        )

    # TODO: Delete file from storage

    # Remove avatar URL from user
    current_user.avatar_url = None
    await db.commit()

    return {"message": "Avatar deleted successfully"}


@router.get("/settings/meeting")
async def get_meeting_settings(current_user: User = Depends(get_current_user)):
    """Get user's meeting settings."""

    if current_user.meeting_settings:
        try:
            return json.loads(current_user.meeting_settings)
        except json.JSONDecodeError:
            pass

    # Default meeting settings
    return {
        "default_video_enabled": current_user.default_video_enabled,
        "default_audio_enabled": current_user.default_audio_enabled,
        "auto_join_audio": True,
        "noise_suppression": True,
        "echo_cancellation": True,
        "high_quality_video": True,
        "bandwidth_optimization": False,
    }


@router.put("/settings/meeting")
async def update_meeting_settings(
    settings: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user's meeting settings."""

    # Update specific settings in user model
    if "default_video_enabled" in settings:
        current_user.default_video_enabled = bool(settings["default_video_enabled"])

    if "default_audio_enabled" in settings:
        current_user.default_audio_enabled = bool(settings["default_audio_enabled"])

    # Store full settings as JSON
    current_user.meeting_settings = json.dumps(settings)

    await db.commit()

    return {"message": "Meeting settings updated successfully"}


@router.get("/settings/notifications")
async def get_notification_settings(current_user: User = Depends(get_current_user)):
    """Get user's notification settings."""

    if current_user.notification_settings:
        try:
            return json.loads(current_user.notification_settings)
        except json.JSONDecodeError:
            pass

    # Default notification settings
    return {
        "email_notifications": True,
        "sms_notifications": False,
        "meeting_reminders": True,
        "meeting_invitations": True,
        "meeting_started": True,
        "meeting_ended": False,
        "chat_messages": False,
        "push_notifications": True,
    }


@router.put("/settings/notifications")
async def update_notification_settings(
    settings: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user's notification settings."""

    current_user.notification_settings = json.dumps(settings)
    await db.commit()

    return {"message": "Notification settings updated successfully"}


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get user dashboard statistics."""

    # TODO: Implement actual statistics queries
    # This would query meetings, participation, etc.

    return {
        "total_meetings_hosted": 0,
        "total_meetings_attended": 0,
        "total_meeting_time_minutes": 0,
        "meetings_this_week": 0,
        "upcoming_meetings": 0,
        "recent_activity": [],
    }
