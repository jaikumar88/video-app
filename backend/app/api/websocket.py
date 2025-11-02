"""
WebSocket server for WebRTC signaling and real-time communication.
"""

import json
import logging
from typing import Dict, Set, Optional
import asyncio
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User
from app.models.meeting import Meeting, MeetingParticipant
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.debug('[DEBUG] websocket.py logger initialized and set to DEBUG')
logger.setLevel(logging.DEBUG)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for meetings."""

    def __init__(self):
        # meeting_id -> {user_id: websocket}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # user_id -> meeting_id mapping for quick lookup
        self.user_meetings: Dict[str, str] = {}
        # meeting_id -> meeting info cache
        self.meeting_cache: Dict[str, dict] = {}

    async def connect(self, websocket: WebSocket, meeting_id: str, user_id: str):
        """Connect user to a meeting room."""
        await websocket.accept()

        if meeting_id not in self.active_connections:
            self.active_connections[meeting_id] = {}

        self.active_connections[meeting_id][user_id] = websocket
        self.user_meetings[user_id] = meeting_id

        logger.info(f"User {user_id} connected to meeting {meeting_id}")

        # Notify other participants
        await self.broadcast_to_meeting(
            meeting_id,
            {
                "type": "user_joined",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
            exclude_user=user_id,
        )

    def disconnect(self, meeting_id: str, user_id: str):
        """Disconnect user from meeting."""
        if meeting_id in self.active_connections:
            self.active_connections[meeting_id].pop(user_id, None)

            # Clean up empty meeting rooms
            if not self.active_connections[meeting_id]:
                del self.active_connections[meeting_id]
                self.meeting_cache.pop(meeting_id, None)

        self.user_meetings.pop(user_id, None)
        logger.info(f"User {user_id} disconnected from meeting {meeting_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user."""
        meeting_id = self.user_meetings.get(user_id)
        if not meeting_id:
            return False

        websocket = self.active_connections.get(meeting_id, {}).get(user_id)
        if websocket:
            try:
                await websocket.send_text(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"Error sending message to {user_id}: {e}")
                self.disconnect(meeting_id, user_id)

        return False

    async def broadcast_to_meeting(
        self, meeting_id: str, message: dict, exclude_user: Optional[str] = None
    ):
        """Broadcast message to all users in meeting."""
        if meeting_id not in self.active_connections:
            return

        connections = self.active_connections[meeting_id]
        disconnected_users = []

        for user_id, websocket in connections.items():
            if exclude_user and user_id == exclude_user:
                continue

            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to {user_id}: {e}")
                disconnected_users.append(user_id)

        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(meeting_id, user_id)

    def get_meeting_participants(self, meeting_id: str) -> Set[str]:
        """Get list of connected participants in meeting."""
        return set(self.active_connections.get(meeting_id, {}).keys())

    async def handle_webrtc_signaling(
        self, meeting_id: str, from_user: str, to_user: str, signal_data: dict
    ):
        """Handle WebRTC signaling between peers."""
        message = {
            "type": "webrtc_signal",
            "from_user": from_user,
            "signal_data": signal_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.send_personal_message(message, to_user)


# Global connection manager
manager = ConnectionManager()


async def get_websocket_user(token: str, db: AsyncSession) -> User:
    """Authenticate user from WebSocket token."""
    try:
        logger.info(f"[DEBUG] get_websocket_user called with token: {token[:20]}...")
        auth_service = AuthService(db)
        user = await auth_service.get_current_user(token)
        
        logger.info(f"[DEBUG] get_current_user returned: {user}")

        if not user:
            logger.error("[DEBUG] User is None, raising 401")
            raise HTTPException(status_code=401, detail="Invalid token")

        logger.info(f"[DEBUG] User authenticated successfully: {user.id} ({user.email})")
        return user
    except HTTPException as he:
        logger.error(f"[DEBUG] HTTPException in get_websocket_user: {he.status_code} - {he.detail}")
        raise
    except Exception as e:
        logger.error(f"[DEBUG] Unexpected error in get_websocket_user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Authentication error")


async def verify_meeting_access(
    meeting_id: str, user: User, db: AsyncSession
) -> Meeting:
    """Verify user has access to meeting."""
    # The meeting_id parameter is the short meeting code (e.g., "MMXHG4F"), not the UUID
    # Query by meeting_id field, not the id (UUID) field
    result = await db.execute(select(Meeting).where(Meeting.meeting_id == meeting_id))
    meeting = result.scalar_one_or_none()

    if not meeting:
        logger.error(f"[DEBUG] Meeting not found for meeting_id: {meeting_id}")
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Check if user is participant or host
    # Use meeting.id (UUID) to query the participants table
    all_participants_result = await db.execute(
        select(MeetingParticipant).where(
            MeetingParticipant.meeting_id == meeting.id
        )
    )
    all_participants = all_participants_result.scalars().all()
    logger.info(
        f"[DEBUG] All participants for meeting {meeting.id}: "
        f"{[str(p.user_id) for p in all_participants]}"
    )

    logger.info(
        f"[DEBUG] Checking participant for meeting_id={meeting.id}, "
        f"user_id={user.id}"
    )
    participant_result = await db.execute(
        select(MeetingParticipant).where(
            MeetingParticipant.meeting_id == meeting.id,
            MeetingParticipant.user_id == user.id,
        )
    )
    participant = participant_result.scalar_one_or_none()
    logger.info(f"[DEBUG] Participant lookup result: {participant}")

    # Allow access if user is the host OR is a participant
    is_host = (meeting.host_user_id == user.id)
    is_participant = (participant is not None)
    
    logger.info(
        f"[DEBUG] Access check: is_host={is_host}, "
        f"is_participant={is_participant}"
    )
    
    if not (is_host or is_participant):
        logger.error(
            f"[DEBUG] Access denied for user {user.id} "
            f"to meeting {meeting.id}"
        )
        raise HTTPException(status_code=403, detail="Access denied")

    return meeting


@router.websocket("/{meeting_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    meeting_id: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """WebSocket endpoint for meeting participation."""
    
    logger.info(f"[DEBUG] WebSocket connection attempt for meeting {meeting_id}")
    logger.info(f"[DEBUG] Token: {token[:50]}...")

    try:
        # Authenticate user
        logger.info("[DEBUG] Authenticating user...")
        user = await get_websocket_user(token, db)
        logger.info(f"[DEBUG] User authenticated: {user.id} ({user.email})")

        # Verify meeting access
        logger.info("[DEBUG] Verifying meeting access...")
        meeting = await verify_meeting_access(meeting_id, user, db)
        logger.info(f"[DEBUG] Access verified for user {user.id} to meeting {meeting_id}")

        # Connect to meeting
        await manager.connect(websocket, meeting_id, str(user.id))

        # Send initial meeting state
        participants = manager.get_meeting_participants(meeting_id)
        await manager.send_personal_message(
            {
                "type": "meeting_joined",
                "meeting_id": meeting_id,
                "participants": list(participants),
                "meeting_info": {
                    "title": meeting.title,
                    "host_id": str(meeting.host_user_id),
                    "status": meeting.status.value,
                },
            },
            str(user.id),
        )

        # Message handling loop
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                await handle_websocket_message(meeting_id, str(user.id), message, db)
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON format"}, str(user.id)
                )
            except Exception as e:
                logger.error(f"Error handling message from {user.id}: {e}")
                await manager.send_personal_message(
                    {"type": "error", "message": "Message processing failed"},
                    str(user.id),
                )

    except WebSocketDisconnect:
        manager.disconnect(
            meeting_id, str(user.id) if "user" in locals() else "unknown"
        )

        # Notify other participants
        await manager.broadcast_to_meeting(
            meeting_id,
            {
                "type": "user_left",
                "user_id": str(user.id) if "user" in locals() else "unknown",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    except HTTPException as he:
        logger.error(f"[DEBUG] HTTPException in WebSocket: {he.status_code} - {he.detail}")
        await websocket.close(code=1008, reason=he.detail)
        
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}", exc_info=True)
        if "user" in locals():
            manager.disconnect(meeting_id, str(user.id))


async def handle_websocket_message(
    meeting_id: str, user_id: str, message: dict, db: AsyncSession
):
    """Handle incoming WebSocket messages."""

    message_type = message.get("type")

    if message_type == "webrtc_offer":
        # Handle WebRTC offer
        to_user = message.get("to_user")
        if to_user:
            await manager.handle_webrtc_signaling(
                meeting_id,
                user_id,
                to_user,
                {"type": "offer", "sdp": message.get("sdp")},
            )

    elif message_type == "webrtc_answer":
        # Handle WebRTC answer
        to_user = message.get("to_user")
        if to_user:
            await manager.handle_webrtc_signaling(
                meeting_id,
                user_id,
                to_user,
                {"type": "answer", "sdp": message.get("sdp")},
            )

    elif message_type == "webrtc_ice_candidate":
        # Handle ICE candidate
        to_user = message.get("to_user")
        if to_user:
            await manager.handle_webrtc_signaling(
                meeting_id,
                user_id,
                to_user,
                {"type": "ice_candidate", "candidate": message.get("candidate")},
            )

    elif message_type == "chat_message":
        # Handle chat message
        chat_message = {
            "type": "chat_message",
            "from_user": user_id,
            "message": message.get("message", ""),
            "timestamp": datetime.utcnow().isoformat(),
        }
        await manager.broadcast_to_meeting(meeting_id, chat_message)

    elif message_type == "media_state_change":
        # Handle video/audio state changes
        state_message = {
            "type": "participant_media_change",
            "user_id": user_id,
            "video_enabled": message.get("video_enabled"),
            "audio_enabled": message.get("audio_enabled"),
            "screen_sharing": message.get("screen_sharing", False),
            "timestamp": datetime.utcnow().isoformat(),
        }
        await manager.broadcast_to_meeting(
            meeting_id, state_message, exclude_user=user_id
        )

    elif message_type == "ping":
        # Handle ping/keepalive
        await manager.send_personal_message(
            {"type": "pong", "timestamp": datetime.utcnow().isoformat()}, user_id
        )

    else:
        # Unknown message type
        await manager.send_personal_message(
            {"type": "error", "message": f"Unknown message type: {message_type}"},
            user_id,
        )


# Additional utility functions for meeting management


async def notify_meeting_started(meeting_id: str):
    """Notify all participants that meeting has started."""
    await manager.broadcast_to_meeting(
        meeting_id,
        {
            "type": "meeting_started",
            "meeting_id": meeting_id,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


async def notify_meeting_ended(meeting_id: str):
    """Notify all participants that meeting has ended."""
    await manager.broadcast_to_meeting(
        meeting_id,
        {
            "type": "meeting_ended",
            "meeting_id": meeting_id,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    # Disconnect all participants
    if meeting_id in manager.active_connections:
        participants = list(manager.active_connections[meeting_id].keys())
        for user_id in participants:
            manager.disconnect(meeting_id, user_id)


async def get_meeting_participants_info(meeting_id: str) -> dict:
    """Get information about currently connected participants."""
    participants = manager.get_meeting_participants(meeting_id)
    return {
        "meeting_id": meeting_id,
        "participant_count": len(participants),
        "participants": list(participants),
    }
