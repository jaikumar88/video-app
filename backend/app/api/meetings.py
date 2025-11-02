"""
Meeting API endpoints for video conferencing functionality.
"""

import secrets
import string
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, validator, EmailStr
from sqlalchemy import select, update, func

from app.core.database import get_db
from app.core.config import get_settings
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.api.auth import get_current_user, UserResponse
from app.models.user import User
from app.models.meeting import (
    Meeting,
    MeetingParticipant,
    MeetingInvitation,
    MeetingStatus,
    ParticipantRole,
    ParticipantStatus,
)

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


# Pydantic models for request/response
class MeetingSettings(BaseModel):
    waiting_room_enabled: bool = True
    require_password: bool = False
    allow_join_before_host: bool = False
    recording_enabled: bool = False
    auto_recording: bool = False
    chat_enabled: bool = True
    screen_sharing_enabled: bool = True
    max_participants: int = 100


class CreateMeetingRequest(BaseModel):
    title: str
    description: Optional[str] = None
    scheduled_start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    timezone: str = "UTC"
    settings: Optional[MeetingSettings] = None

    @validator("title")
    def validate_title(cls, v):
        if len(v.strip()) < 3:
            raise ValueError("Meeting title must be at least 3 characters long")
        return v.strip()

    @validator("settings")
    def validate_meeting_settings(cls, v):
        if v and hasattr(v, "max_participants"):
            if v.max_participants < 2:
                raise ValueError("Meeting must allow at least 2 participants")
            if v.max_participants > 1000:
                raise ValueError("Meeting cannot have more than 1000 participants")
        return v


class UpdateMeetingRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    settings: Optional[MeetingSettings] = None


class JoinMeetingRequest(BaseModel):
    display_name: Optional[str] = None
    video_enabled: bool = True
    audio_enabled: bool = True
    passcode: Optional[str] = None


class JoinGuestRequest(BaseModel):
    meeting_id: str
    name: str
    email: EmailStr
    video_enabled: bool = True
    audio_enabled: bool = True
    passcode: Optional[str] = None

    @validator("name")
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters long")
        return v.strip()

    @validator("meeting_id")
    def validate_meeting_id(cls, v):
        if not v or v.strip() == "" or v.strip().lower() == "undefined":
            raise ValueError("Valid meeting ID is required")
        return v.strip()


class JoinGuestLegacyRequest(BaseModel):
    """Legacy request model for URL-based meeting ID"""
    name: str
    email: EmailStr
    video_enabled: bool = True
    audio_enabled: bool = True
    passcode: Optional[str] = None

    @validator("name")
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters long")
        return v.strip()


class ParticipantResponse(BaseModel):
    user_id: Optional[str]
    display_name: str
    role: str
    status: str
    join_time: Optional[datetime]
    video_enabled: bool
    audio_enabled: bool
    screen_sharing: bool


class MeetingResponse(BaseModel):
    id: str
    meeting_id: str
    title: str
    description: Optional[str]
    host_user_id: str
    scheduled_start_time: Optional[datetime]
    scheduled_end_time: Optional[datetime]
    actual_start_time: Optional[datetime]
    actual_end_time: Optional[datetime]
    timezone: str
    status: str
    current_participant_count: int
    max_participants: int
    join_url: str
    passcode: Optional[str]
    settings: Dict[str, Any]
    participants: List[ParticipantResponse] = []
    created_at: datetime


class MeetingListResponse(BaseModel):
    meetings: List[MeetingResponse]
    pagination: Dict[str, Any]


class JoinMeetingResponse(BaseModel):
    participant_id: str
    meeting_token: str
    webrtc_config: Dict[str, Any]
    websocket_url: str


# Invitation models
class InviteParticipantRequest(BaseModel):
    email: EmailStr
    role: Optional[str] = "participant"  # participant, moderator
    frontend_url: Optional[str] = None


class InviteParticipantsRequest(BaseModel):
    emails: List[EmailStr]
    role: Optional[str] = "participant"
    message: Optional[str] = None
    frontend_url: Optional[str] = None


class InvitationResponse(BaseModel):
    id: str
    meeting_id: str
    email: str
    invitation_token: str
    sent_at: Optional[datetime]
    accepted_at: Optional[datetime]
    expires_at: datetime
    created_at: datetime


class InvitationListResponse(BaseModel):
    invitations: List[InvitationResponse]
    total: int


def generate_meeting_id() -> str:
    """Generate a unique meeting ID."""
    return "".join(secrets.choice(string.digits) for _ in range(11))


def generate_passcode() -> str:
    """Generate a meeting passcode."""
    return "".join(secrets.choice(string.digits) for _ in range(6))


def get_base_url_from_request(request: Request) -> str:
    """Get the base URL from the request to construct proper meeting links."""
    # Get the scheme (http/https)
    scheme = request.url.scheme
    
    # Get the host (includes port if not standard)
    host = request.headers.get("host", str(request.url.netloc))
    
    # For ngrok, we want to use https and the ngrok domain
    if "ngrok" in host or "localhost" in host:
        # If it's an ngrok URL, use https
        if "ngrok" in host:
            scheme = "https"
    
    return f"{scheme}://{host}"


@router.post("/", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    meeting_data: CreateMeetingRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Create a new meeting."""

    # Generate unique meeting ID
    meeting_id = generate_meeting_id()
    while True:
        stmt = select(Meeting).where(Meeting.meeting_id == meeting_id)
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            break
        meeting_id = generate_meeting_id()

    # Generate passcode if required
    passcode = None
    if meeting_data.settings and meeting_data.settings.require_password:
        passcode = generate_passcode()

    # Create meeting
    meeting = Meeting(
        meeting_id=meeting_id,
        title=meeting_data.title,
        description=meeting_data.description,
        host_user_id=current_user.id,
        scheduled_start_time=meeting_data.scheduled_start_time,
        scheduled_end_time=meeting_data.scheduled_end_time,
        timezone=meeting_data.timezone,
        passcode=passcode,
    )

    # Apply settings
    if meeting_data.settings:
        meeting.waiting_room_enabled = meeting_data.settings.waiting_room_enabled
        meeting.require_password = meeting_data.settings.require_password
        meeting.allow_join_before_host = meeting_data.settings.allow_join_before_host
        meeting.recording_enabled = meeting_data.settings.recording_enabled
        meeting.auto_recording = meeting_data.settings.auto_recording
        meeting.chat_enabled = meeting_data.settings.chat_enabled
        meeting.screen_sharing_enabled = meeting_data.settings.screen_sharing_enabled
        meeting.max_participants = meeting_data.settings.max_participants

    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)

    # Create host participant entry
    host_participant = MeetingParticipant(
        meeting_id=meeting.id,
        user_id=current_user.id,
        display_name=current_user.display_name or current_user.full_name,
        email=current_user.email,
        role=ParticipantRole.HOST,
        status=ParticipantStatus.INVITED,
    )

    db.add(host_participant)
    await db.commit()

    # Get the base URL from the request
    base_url = get_base_url_from_request(request)

    return MeetingResponse(
        id=str(meeting.id),
        meeting_id=meeting.meeting_id,
        title=meeting.title,
        description=meeting.description,
        host_user_id=str(meeting.host_user_id),
        scheduled_start_time=meeting.scheduled_start_time,
        scheduled_end_time=meeting.scheduled_end_time,
        actual_start_time=meeting.actual_start_time,
        actual_end_time=meeting.actual_end_time,
        timezone=meeting.timezone,
        status=meeting.status.value,
        current_participant_count=meeting.current_participant_count,
        max_participants=meeting.max_participants,
        join_url=f"{base_url}/meeting/{meeting.meeting_id}",
        passcode=meeting.passcode,
        settings={
            "waiting_room_enabled": meeting.waiting_room_enabled,
            "require_password": meeting.require_password,
            "allow_join_before_host": meeting.allow_join_before_host,
            "recording_enabled": meeting.recording_enabled,
            "auto_recording": meeting.auto_recording,
            "chat_enabled": meeting.chat_enabled,
            "screen_sharing_enabled": meeting.screen_sharing_enabled,
            "max_participants": meeting.max_participants,
        },
        participants=[],
        created_at=meeting.created_at,
    )


@router.get("/", response_model=MeetingListResponse)
async def list_meetings(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List user's meetings with pagination and filtering."""

    # Build query
    stmt = select(Meeting).where(Meeting.host_user_id == current_user.id)

    # Apply filters
    if status_filter:
        try:
            status_enum = MeetingStatus(status_filter)
            stmt = stmt.where(Meeting.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter: {status_filter}",
            )

    if start_date:
        stmt = stmt.where(Meeting.scheduled_start_time >= start_date)

    if end_date:
        stmt = stmt.where(Meeting.scheduled_start_time <= end_date)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit).order_by(Meeting.created_at.desc())

    # Execute query
    result = await db.execute(stmt)
    meetings = result.scalars().all()

    # Convert to response format
    meeting_responses = []
    for meeting in meetings:
        meeting_responses.append(
            MeetingResponse(
                id=str(meeting.id),
                meeting_id=meeting.meeting_id,
                title=meeting.title,
                description=meeting.description,
                host_user_id=str(meeting.host_user_id),
                scheduled_start_time=meeting.scheduled_start_time,
                scheduled_end_time=meeting.scheduled_end_time,
                actual_start_time=meeting.actual_start_time,
                actual_end_time=meeting.actual_end_time,
                timezone=meeting.timezone,
                status=meeting.status.value,
                current_participant_count=meeting.current_participant_count,
                max_participants=meeting.max_participants,
                join_url=f"https://yourdomain.com/meeting/{meeting.meeting_id}",
                passcode=meeting.passcode,
                settings={
                    "waiting_room_enabled": meeting.waiting_room_enabled,
                    "recording_enabled": meeting.recording_enabled,
                    "chat_enabled": meeting.chat_enabled,
                    "screen_sharing_enabled": meeting.screen_sharing_enabled,
                    "max_participants": meeting.max_participants,
                },
                participants=[],
                created_at=meeting.created_at,
            )
        )

    # Pagination info
    total_pages = (total + limit - 1) // limit
    pagination = {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }

    return MeetingListResponse(meetings=meeting_responses, pagination=pagination)


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get meeting details."""

    # Find meeting
    stmt = select(Meeting).where(Meeting.meeting_id == meeting_id)
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found"
        )

    # Check if user has access (host or participant)
    participant_stmt = select(MeetingParticipant).where(
        MeetingParticipant.meeting_id == meeting.id,
        MeetingParticipant.user_id == current_user.id,
    )
    participant_result = await db.execute(participant_stmt)
    participant = participant_result.scalar_one_or_none()

    if not participant and meeting.host_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this meeting",
        )

    # Get participants
    participants_stmt = select(MeetingParticipant).where(
        MeetingParticipant.meeting_id == meeting.id
    )
    participants_result = await db.execute(participants_stmt)
    participants = participants_result.scalars().all()

    participant_responses = []
    for p in participants:
        participant_responses.append(
            ParticipantResponse(
                user_id=str(p.user_id) if p.user_id else None,
                display_name=p.display_name,
                role=p.role.value,
                status=p.status.value,
                join_time=p.join_time,
                video_enabled=p.video_enabled,
                audio_enabled=p.audio_enabled,
                screen_sharing=p.screen_sharing,
            )
        )

    return MeetingResponse(
        id=str(meeting.id),
        meeting_id=meeting.meeting_id,
        title=meeting.title,
        description=meeting.description,
        host_user_id=str(meeting.host_user_id),
        scheduled_start_time=meeting.scheduled_start_time,
        scheduled_end_time=meeting.scheduled_end_time,
        actual_start_time=meeting.actual_start_time,
        actual_end_time=meeting.actual_end_time,
        timezone=meeting.timezone,
        status=meeting.status.value,
        current_participant_count=meeting.current_participant_count,
        max_participants=meeting.max_participants,
        join_url=f"https://yourdomain.com/meeting/{meeting.meeting_id}",
        passcode=meeting.passcode,
        settings={
            "waiting_room_enabled": meeting.waiting_room_enabled,
            "recording_enabled": meeting.recording_enabled,
            "chat_enabled": meeting.chat_enabled,
            "screen_sharing_enabled": meeting.screen_sharing_enabled,
            "max_participants": meeting.max_participants,
        },
        participants=participant_responses,
        created_at=meeting.created_at,
    )


@router.post("/{meeting_id}/join/", response_model=JoinMeetingResponse)
async def join_meeting(
    meeting_id: str,
    join_data: JoinMeetingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Join a meeting as a participant."""

    # Find meeting
    stmt = select(Meeting).where(Meeting.meeting_id == meeting_id)
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found"
        )

    # Check meeting status
    if meeting.status == MeetingStatus.ENDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Meeting has ended"
        )

    if meeting.status == MeetingStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Meeting has been cancelled"
        )

    # Check passcode if required
    if meeting.require_password and join_data.passcode != meeting.passcode:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid meeting passcode"
        )

    # Check participant limit
    if meeting.current_participant_count >= meeting.max_participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting has reached maximum participant limit",
        )

    # Check if user is already a participant
    participant_stmt = select(MeetingParticipant).where(
        MeetingParticipant.meeting_id == meeting.id,
        MeetingParticipant.user_id == current_user.id,
    )
    participant_result = await db.execute(participant_stmt)
    participant = participant_result.scalar_one_or_none()

    if not participant:
        # Create new participant
        participant = MeetingParticipant(
            meeting_id=meeting.id,
            user_id=current_user.id,
            display_name=join_data.display_name
            or current_user.display_name
            or current_user.full_name,
            email=current_user.email,
            role=(
                ParticipantRole.HOST
                if meeting.host_user_id == current_user.id
                else ParticipantRole.PARTICIPANT
            ),
            status=ParticipantStatus.JOINED,
            video_enabled=join_data.video_enabled,
            audio_enabled=join_data.audio_enabled,
            join_time=datetime.utcnow(),
        )
        db.add(participant)
    else:
        # Update existing participant
        participant.status = ParticipantStatus.JOINED
        participant.video_enabled = join_data.video_enabled
        participant.audio_enabled = join_data.audio_enabled
        participant.join_time = datetime.utcnow()

    # Update meeting status if first participant
    if meeting.status == MeetingStatus.SCHEDULED:
        meeting.status = MeetingStatus.ACTIVE
        meeting.actual_start_time = datetime.utcnow()

    # Update participant count
    await db.execute(
        update(Meeting)
        .where(Meeting.id == meeting.id)
        .values(current_participant_count=Meeting.current_participant_count + 1)
    )

    await db.commit()
    await db.refresh(participant)
    await db.refresh(meeting)

    # WebRTC configuration
    webrtc_config = {
        "iceServers": [
            {"urls": "stun:stun.l.google.com:19302"},
            {
                "urls": settings.TURN_SERVER_URL,
                "username": settings.TURN_USERNAME,
                "credential": settings.TURN_PASSWORD,
            },
        ]
    }

    # Generate meeting token (this would be a proper JWT token)
    meeting_token = f"meeting_token_{participant.id}"

    return JoinMeetingResponse(
        participant_id=str(participant.id),
        meeting_token=meeting_token,
        webrtc_config=webrtc_config,
        websocket_url=f"wss://yourdomain.com/ws/meetings/{meeting_id}",
    )


@router.get("/{meeting_id}/participants", response_model=List[ParticipantResponse])
async def get_meeting_participants(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of participants in a meeting."""
    
    # Find meeting
    stmt = select(Meeting).where(Meeting.meeting_id == meeting_id)
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found"
        )

    # Get participants
    participants_stmt = (
        select(MeetingParticipant, User)
        .join(User, MeetingParticipant.user_id == User.id)
        .where(MeetingParticipant.meeting_id == meeting.id)
    )
    participants_result = await db.execute(participants_stmt)
    participants = participants_result.all()

    # Build response matching ParticipantResponse model
    participant_list = []
    for participant, user in participants:
        participant_list.append(
            ParticipantResponse(
                user_id=str(participant.user_id) if participant.user_id else None,
                display_name=participant.display_name or f"{user.first_name} {user.last_name}",
                role=participant.role.value if participant.role else "participant",
                status=participant.status.value if participant.status else "joined",
                join_time=participant.join_time,
                video_enabled=participant.video_enabled if participant.video_enabled is not None else True,
                audio_enabled=participant.audio_enabled if participant.audio_enabled is not None else True,
                screen_sharing=participant.screen_sharing if participant.screen_sharing is not None else False,
            )
        )

    return participant_list


@router.post("/join-guest", response_model=JoinMeetingResponse)
async def join_meeting_as_guest(
    guest_data: JoinGuestRequest,
    db: AsyncSession = Depends(get_db),
):
    """Join a meeting as a guest without authentication."""

    # Get meeting_id from request body
    meeting_id = guest_data.meeting_id

    # Find meeting
    stmt = select(Meeting).where(Meeting.meeting_id == meeting_id)
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found"
        )

    # Check meeting status
    if meeting.status == MeetingStatus.ENDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Meeting has ended"
        )

    if meeting.status == MeetingStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Meeting has been cancelled"
        )

    # Check passcode if required
    if meeting.require_password and guest_data.passcode != meeting.passcode:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid meeting passcode"
        )

    # Check participant limit
    if meeting.current_participant_count >= meeting.max_participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting has reached maximum participant limit",
        )

    # Create guest participant - no user_id for guests
    participant = MeetingParticipant(
        meeting_id=meeting.id,
        user_id=None,  # Guest participants don't have user accounts
        display_name=guest_data.name,
        email=guest_data.email,
        role=ParticipantRole.PARTICIPANT,  # Guests are always participants
        status=ParticipantStatus.JOINED,
        video_enabled=guest_data.video_enabled,
        audio_enabled=guest_data.audio_enabled,
        join_time=datetime.utcnow(),
    )
    db.add(participant)

    # Update meeting status if first participant
    if meeting.status == MeetingStatus.SCHEDULED:
        meeting.status = MeetingStatus.ACTIVE
        meeting.actual_start_time = datetime.utcnow()

    # Update participant count
    await db.execute(
        update(Meeting)
        .where(Meeting.id == meeting.id)
        .values(current_participant_count=Meeting.current_participant_count + 1)
    )

    await db.commit()
    await db.refresh(participant)

    # WebRTC configuration
    webrtc_config = {
        "iceServers": [
            {"urls": "stun:stun.l.google.com:19302"},
            {
                "urls": settings.TURN_SERVER_URL,
                "username": settings.TURN_USERNAME,
                "credential": settings.TURN_PASSWORD,
            },
        ]
    }

    # Generate meeting token for guest
    meeting_token = f"guest_token_{participant.id}"

    return JoinMeetingResponse(
        participant_id=str(participant.id),
        meeting_token=meeting_token,
        webrtc_config=webrtc_config,
        websocket_url=f"wss://yourdomain.com/ws/meetings/{meeting_id}",
    )


@router.post("/{meeting_id}/join-guest", response_model=JoinMeetingResponse)
async def join_meeting_as_guest_legacy(
    meeting_id: str,
    guest_data: JoinGuestLegacyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Join a meeting as a guest without authentication (legacy URL format)."""
    
    # Validate meeting ID from URL
    if not meeting_id or meeting_id.strip() == "" or meeting_id.strip().lower() == "undefined":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Valid meeting ID is required"
        )

    # Find meeting
    stmt = select(Meeting).where(Meeting.meeting_id == meeting_id)
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found"
        )

    # Check meeting status
    if meeting.status == MeetingStatus.ENDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Meeting has ended"
        )

    if meeting.status == MeetingStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Meeting has been cancelled"
        )

    # Check passcode if required
    if meeting.require_password and guest_data.passcode != meeting.passcode:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid meeting passcode"
        )

    # Check participant limit
    if meeting.current_participant_count >= meeting.max_participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting has reached maximum participant limit",
        )

    # Create guest participant - no user_id for guests
    participant = MeetingParticipant(
        meeting_id=meeting.id,
        user_id=None,  # Guest participants don't have user accounts
        display_name=guest_data.name,
        email=guest_data.email,
        role=ParticipantRole.PARTICIPANT,  # Guests are always participants
        status=ParticipantStatus.JOINED,
        video_enabled=guest_data.video_enabled,
        audio_enabled=guest_data.audio_enabled,
        join_time=datetime.utcnow(),
    )
    db.add(participant)

    # Update meeting status if first participant
    if meeting.status == MeetingStatus.SCHEDULED:
        meeting.status = MeetingStatus.ACTIVE
        meeting.actual_start_time = datetime.utcnow()

    # Update participant count
    await db.execute(
        update(Meeting)
        .where(Meeting.id == meeting.id)
        .values(current_participant_count=Meeting.current_participant_count + 1)
    )

    await db.commit()
    await db.refresh(participant)

    # WebRTC configuration
    webrtc_config = {
        "iceServers": [
            {"urls": "stun:stun.l.google.com:19302"},
            {
                "urls": settings.TURN_SERVER_URL,
                "username": settings.TURN_USERNAME,
                "credential": settings.TURN_PASSWORD,
            },
        ]
    }

    # Generate meeting token for guest
    meeting_token = f"guest_token_{participant.id}"

    return JoinMeetingResponse(
        participant_id=str(participant.id),
        meeting_token=meeting_token,
        webrtc_config=webrtc_config,
        websocket_url=f"wss://yourdomain.com/ws/meetings/{meeting_id}",
    )


@router.post("/{meeting_id}/leave")
async def leave_meeting(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Leave a meeting."""

    # Find meeting and participant
    stmt = select(Meeting).where(Meeting.meeting_id == meeting_id)
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found"
        )

    participant_stmt = select(MeetingParticipant).where(
        MeetingParticipant.meeting_id == meeting.id,
        MeetingParticipant.user_id == current_user.id,
        MeetingParticipant.status == ParticipantStatus.JOINED,
    )
    participant_result = await db.execute(participant_stmt)
    participant = participant_result.scalar_one_or_none()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not currently in this meeting",
        )

    # Update participant status
    leave_time = datetime.utcnow()
    participant.status = ParticipantStatus.LEFT
    participant.leave_time = leave_time

    if participant.join_time:
        duration = leave_time - participant.join_time
        participant.duration_seconds = int(duration.total_seconds())

    # Update meeting participant count
    await db.execute(
        update(Meeting)
        .where(Meeting.id == meeting.id)
        .values(current_participant_count=Meeting.current_participant_count - 1)
    )

    await db.commit()

    return {
        "message": "Left meeting successfully",
        "duration_seconds": participant.duration_seconds or 0,
    }


@router.post("/{meeting_id}/end")
async def end_meeting(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """End a meeting (host only)."""

    # Find meeting
    stmt = select(Meeting).where(Meeting.meeting_id == meeting_id)
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found"
        )

    # Check if user is the host
    if meeting.host_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can end the meeting",
        )

    # Check if meeting is active
    if meeting.status != MeetingStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting is not currently active",
        )

    # End the meeting
    end_time = datetime.utcnow()
    meeting.status = MeetingStatus.ENDED
    meeting.actual_end_time = end_time

    # Update all joined participants to left status
    await db.execute(
        update(MeetingParticipant)
        .where(
            MeetingParticipant.meeting_id == meeting.id,
            MeetingParticipant.status == ParticipantStatus.JOINED,
        )
        .values(status=ParticipantStatus.LEFT, leave_time=end_time)
    )

    # Reset participant count
    meeting.current_participant_count = 0

    # Get total participants for summary
    total_participants_stmt = select(func.count(MeetingParticipant.id)).where(
        MeetingParticipant.meeting_id == meeting.id
    )
    total_participants_result = await db.execute(total_participants_stmt)
    total_participants = total_participants_result.scalar()

    await db.commit()

    # Calculate total duration
    total_duration = 0
    if meeting.actual_start_time and meeting.actual_end_time:
        duration = meeting.actual_end_time - meeting.actual_start_time
        total_duration = int(duration.total_seconds())

    return {
        "message": "Meeting ended successfully",
        "ended_at": end_time,
        "total_duration_seconds": total_duration,
        "total_participants": total_participants,
    }


# Invitation endpoints
@router.post("/{meeting_id}/invite", response_model=InvitationResponse)
async def invite_participant(
    meeting_id: str,
    invite_data: InviteParticipantRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Invite a participant to a meeting."""
    
    # Find meeting
    stmt = select(Meeting).where(Meeting.meeting_id == meeting_id)
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found"
        )

    # Check if user is host or has permission to invite
    if str(meeting.host_user_id) != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the meeting host can invite participants"
        )

    # Check if already invited
    existing_invite_stmt = select(MeetingInvitation).where(
        MeetingInvitation.meeting_id == meeting.id,
        MeetingInvitation.email == str(invite_data.email)
    )
    existing_invite_result = await db.execute(existing_invite_stmt)
    existing_invite = existing_invite_result.scalar_one_or_none()

    if existing_invite and existing_invite.expires_at > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Participant already invited and invitation is still valid"
        )

    # Generate invitation token
    invitation_token = f"inv_{generate_meeting_id()}"
    expires_at = datetime.utcnow() + timedelta(hours=24)  # 24-hour expiration

    # Create invitation
    invitation = MeetingInvitation(
        meeting_id=meeting.id,
        email=str(invite_data.email),
        invitation_token=invitation_token,
        expires_at=expires_at,
        sent_at=datetime.utcnow(),
    )

    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    # Send email invitation
    email_service = EmailService()
    try:
        meeting_time = meeting.scheduled_start_time.strftime('%Y-%m-%d %H:%M %Z') if meeting.scheduled_start_time else "TBD"
        
        # Use frontend_url from request if provided, otherwise use a default
        if invite_data.frontend_url:
            meeting_url = f"{invite_data.frontend_url}/meeting/{meeting_id}?token={invitation_token}"
        else:
            # Fallback to localhost for development
            meeting_url = f"http://localhost:3000/meeting/{meeting_id}?token={invitation_token}"
        
        await email_service.send_meeting_invitation(
            email=str(invite_data.email),
            meeting_title=meeting.title,
            meeting_url=meeting_url,
            meeting_time=meeting_time
        )
        logger.info(f"Meeting invitation sent to {invite_data.email}")
    except Exception as e:
        logger.error(f"Failed to send meeting invitation email: {e}")
        # Log invitation details for development/testing
        logger.info("="*80)
        logger.info("📧 MEETING INVITATION DETAILS (EMAIL FAILED)")
        logger.info("="*80)
        logger.info(f"To: {invite_data.email}")
        logger.info(f"Meeting: {meeting.title}")
        logger.info(f"Time: {meeting_time}")
        logger.info(f"Join URL: {meeting_url}")
        logger.info(f"Invitation Token: {invitation_token}")
        logger.info("="*80)
        # Don't fail the invitation creation if email fails

    return InvitationResponse(
        id=str(invitation.id),
        meeting_id=meeting_id,
        email=invitation.email,
        invitation_token=invitation.invitation_token,
        sent_at=invitation.sent_at,
        accepted_at=invitation.accepted_at,
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
    )


@router.post("/{meeting_id}/invite-multiple", response_model=InvitationListResponse)
async def invite_multiple_participants(
    meeting_id: str,
    invite_data: InviteParticipantsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Invite multiple participants to a meeting."""
    
    logger.info(f"🎯 Processing invite-multiple for meeting {meeting_id}")
    logger.info(f"📧 Emails to invite: {invite_data.emails}")
    logger.info(f"🌐 Frontend URL: {invite_data.frontend_url}")
    
    # Find meeting
    stmt = select(Meeting).where(Meeting.meeting_id == meeting_id)
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found"
        )

    # Check if user is host or has permission to invite
    if str(meeting.host_user_id) != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the meeting host can invite participants"
        )

    invitations = []
    
    for email in invite_data.emails:
        # Check if already invited
        existing_invite_stmt = select(MeetingInvitation).where(
            MeetingInvitation.meeting_id == meeting.id,
            MeetingInvitation.email == str(email)
        )
        existing_invite_result = await db.execute(existing_invite_stmt)
        existing_invite = existing_invite_result.scalar_one_or_none()

        if existing_invite and existing_invite.expires_at > datetime.utcnow():
            continue  # Skip already invited and valid invitations

        # Generate invitation token
        invitation_token = f"inv_{generate_meeting_id()}"
        expires_at = datetime.utcnow() + timedelta(hours=24)

        logger.info(f"🎫 Generated token for {email}: {invitation_token}")

        # Create invitation
        invitation = MeetingInvitation(
            meeting_id=meeting.id,
            email=str(email),
            invitation_token=invitation_token,
            expires_at=expires_at,
            sent_at=datetime.utcnow(),
        )

        db.add(invitation)
        invitations.append(invitation)

    await db.commit()
    
    # Refresh all invitations
    for invitation in invitations:
        await db.refresh(invitation)

    # Send bulk email invitations
    email_service = EmailService()
    for invitation in invitations:
        try:
            meeting_time = meeting.scheduled_start_time.strftime('%Y-%m-%d %H:%M %Z') if meeting.scheduled_start_time else "TBD"
            
            # Use frontend_url from request if provided, otherwise use default
            if invite_data.frontend_url:
                meeting_url = f"{invite_data.frontend_url}/meeting/{meeting_id}?token={invitation.invitation_token}"
            else:
                # Fallback to localhost for development
                meeting_url = f"http://localhost:3000/meeting/{meeting_id}?token={invitation.invitation_token}"
            
            await email_service.send_meeting_invitation(
                email=invitation.email,
                meeting_title=meeting.title,
                meeting_url=meeting_url,
                meeting_time=meeting_time
            )
            logger.info(f"Meeting invitation sent to {invitation.email}")
        except Exception as e:
            logger.error(f"Failed to send meeting invitation email to {invitation.email}: {e}")
            # Log invitation details for development/testing
            logger.info("="*80)
            logger.info(f"📧 MEETING INVITATION DETAILS - {invitation.email} (EMAIL FAILED)")
            logger.info("="*80)
            logger.info(f"To: {invitation.email}")
            logger.info(f"Meeting: {meeting.title}")
            logger.info(f"Time: {meeting_time}")
            logger.info(f"Join URL: {meeting_url}")
            logger.info(f"Invitation Token: {invitation.invitation_token}")
            logger.info("="*80)
            # Continue sending to other recipients even if one fails

    invitation_responses = [
        InvitationResponse(
            id=str(invitation.id),
            meeting_id=meeting_id,
            email=invitation.email,
            invitation_token=invitation.invitation_token,
            sent_at=invitation.sent_at,
            accepted_at=invitation.accepted_at,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
        )
        for invitation in invitations
    ]

    logger.info(f"✅ Successfully created {len(invitation_responses)} invitations")
    logger.info(f"📋 Invitation tokens: {[inv.invitation_token for inv in invitation_responses]}")

    return InvitationListResponse(
        invitations=invitation_responses,
        total=len(invitation_responses)
    )


@router.get("/{meeting_id}/invitations", response_model=InvitationListResponse)
async def get_meeting_invitations(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get all invitations for a meeting."""
    
    # Find meeting
    stmt = select(Meeting).where(Meeting.meeting_id == meeting_id)
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found"
        )

    # Check if user is host or has permission to view invitations
    if str(meeting.host_user_id) != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the meeting host can view invitations"
        )

    # Get all invitations for the meeting
    invitations_stmt = select(MeetingInvitation).where(
        MeetingInvitation.meeting_id == meeting.id
    ).order_by(MeetingInvitation.created_at.desc())
    
    invitations_result = await db.execute(invitations_stmt)
    invitations = invitations_result.scalars().all()

    invitation_responses = [
        InvitationResponse(
            id=str(invitation.id),
            meeting_id=meeting_id,
            email=invitation.email,
            invitation_token=invitation.invitation_token,
            sent_at=invitation.sent_at,
            accepted_at=invitation.accepted_at,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
        )
        for invitation in invitations
    ]

    return InvitationListResponse(
        invitations=invitation_responses,
        total=len(invitation_responses)
    )


@router.post("/invitation/{invitation_token}/accept")
async def accept_invitation(
    invitation_token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Accept a meeting invitation using the invitation token."""
    
    # Find invitation
    stmt = select(MeetingInvitation).where(
        MeetingInvitation.invitation_token == invitation_token
    )
    result = await db.execute(stmt)
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
        )

    # Check if invitation is expired
    if invitation.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation has expired"
        )

    # Check if invitation is already accepted
    if invitation.accepted_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation already accepted"
        )

    # Get meeting details
    meeting_stmt = select(Meeting).where(Meeting.id == invitation.meeting_id)
    meeting_result = await db.execute(meeting_stmt)
    meeting = meeting_result.scalar_one()

    # Get the base URL from the request
    base_url = get_base_url_from_request(request)

    # Return meeting information - let the frontend handle user auth
    return {
        "message": "Invitation is valid",
        "invitation": {
            "id": str(invitation.id),
            "email": invitation.email,
            "invitation_token": invitation.invitation_token,
            "expires_at": invitation.expires_at,
            "created_at": invitation.created_at
        },
        "meeting": {
            "id": meeting.meeting_id,
            "title": meeting.title,
            "description": meeting.description,
            "scheduled_start_time": meeting.scheduled_start_time,
            "scheduled_end_time": meeting.scheduled_end_time,
            "join_url": f"{base_url}/meeting/{meeting.meeting_id}?token={invitation_token}"
        },
        "instructions": {
            "message": "Please login or register with the email address this invitation was sent to, then join the meeting.",
            "required_email": invitation.email
        }
    }


@router.get("/invitation/{invitation_token}")
async def get_invitation_details(
    invitation_token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get invitation details without requiring authentication."""
    
    # Find invitation
    stmt = select(MeetingInvitation).where(
        MeetingInvitation.invitation_token == invitation_token
    )
    result = await db.execute(stmt)
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
        )

    # Check if invitation is expired
    if invitation.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation has expired"
        )

    # Get meeting details
    meeting_stmt = select(Meeting).where(Meeting.id == invitation.meeting_id)
    meeting_result = await db.execute(meeting_stmt)
    meeting = meeting_result.scalar_one()

    # Get the base URL from the request
    base_url = get_base_url_from_request(request)

    return {
        "invitation": {
            "id": str(invitation.id),
            "email": invitation.email,
            "invitation_token": invitation.invitation_token,
            "expires_at": invitation.expires_at,
            "created_at": invitation.created_at,
            "accepted": invitation.accepted_at is not None,
            "accepted_at": invitation.accepted_at
        },
        "meeting": {
            "id": meeting.meeting_id,
            "title": meeting.title,
            "description": meeting.description,
            "scheduled_start_time": meeting.scheduled_start_time,
            "scheduled_end_time": meeting.scheduled_end_time,
            "status": meeting.status.value,
            "join_url": f"{base_url}/meeting/{meeting.meeting_id}?token={invitation_token}"
        }
    }


@router.post("/invitation/{invitation_token}/confirm")
async def confirm_invitation_acceptance(
    invitation_token: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Confirm and mark an invitation as accepted after user authentication."""
    
    # Find invitation
    stmt = select(MeetingInvitation).where(
        MeetingInvitation.invitation_token == invitation_token
    )
    result = await db.execute(stmt)
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
        )

    # Check if invitation is expired
    if invitation.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation has expired"
        )

    # Check if invitation is already accepted
    if invitation.accepted_at:
        return {
            "message": "Invitation already accepted",
            "accepted_at": invitation.accepted_at,
        }

    # Check if the authenticated user's email matches the invitation
    if current_user.email != invitation.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation was not sent to your email address"
        )

    # Mark invitation as accepted
    invitation.accepted_at = datetime.utcnow()
    await db.commit()

    # Get meeting details
    meeting_stmt = select(Meeting).where(Meeting.id == invitation.meeting_id)
    meeting_result = await db.execute(meeting_stmt)
    meeting = meeting_result.scalar_one()

    return {
        "message": "Invitation accepted successfully",
        "meeting_id": meeting.meeting_id,
        "meeting_title": meeting.title,
        "accepted_at": invitation.accepted_at,
    }
