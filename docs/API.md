# 📋 API Reference

This document provides comprehensive API documentation for the WorldClass Video Calling Platform.

## 🔐 Authentication

All protected endpoints require a Bearer token in the Authorization header.

```http
Authorization: Bearer <access_token>
```

### Base URL

- **Local Development**: `http://localhost:8000/api/v1`
- **Production**: `https://api.yourdomain.com/api/v1`

---

## 🔑 Authentication Endpoints

### Register User

Register a new user with email or phone number.

**Endpoint:** `POST /auth/register`

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone_number": "+1234567890",
  "password": "SecurePassword123",
  "confirm_password": "SecurePassword123"
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "phone_number": "+1234567890",
  "first_name": "John",
  "last_name": "Doe",
  "display_name": "John Doe",
  "avatar_url": null,
  "email_verified": false,
  "phone_verified": false,
  "is_verified": false,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Validation Rules:**
- Password: Minimum 8 characters, must contain uppercase, lowercase, and digit
- Either `email` or `phone_number` must be provided
- Phone number: E.164 format recommended

---

### Login User

Authenticate user and receive access tokens.

**Endpoint:** `POST /auth/login`

**Request Body:**
```json
{
  "email_or_phone": "john.doe@example.com",
  "password": "SecurePassword123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `401 Unauthorized`: Account not verified
- `401 Unauthorized`: Account deactivated

---

### Verify Email

Verify user's email address with verification token.

**Endpoint:** `POST /auth/verify-email`

**Request Body:**
```json
{
  "verification_code": "abc123def456ghi789"
}
```

**Response:** `200 OK`
```json
{
  "message": "Email verified successfully"
}
```

---

### Verify Phone

Verify user's phone number with SMS verification code.

**Endpoint:** `POST /auth/verify-phone`

**Request Body:**
```json
{
  "verification_code": "123456"
}
```

**Response:** `200 OK`
```json
{
  "message": "Phone number verified successfully"
}
```

---

### Get Current User

Get authenticated user's information.

**Endpoint:** `GET /auth/me`
**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "phone_number": "+1234567890",
  "first_name": "John",
  "last_name": "Doe",
  "display_name": "John Doe",
  "avatar_url": "https://example.com/avatars/john.jpg",
  "email_verified": true,
  "phone_verified": true,
  "is_verified": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### Refresh Token

Refresh access token using refresh token.

**Endpoint:** `POST /auth/refresh`
**Authentication:** Required (Refresh Token)

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### Logout

Logout user and revoke all active sessions.

**Endpoint:** `POST /auth/logout`
**Authentication:** Required

**Response:** `200 OK`
```json
{
  "message": "Logged out successfully"
}
```

---

## 👥 User Management Endpoints

### Get User Profile

Get user profile information.

**Endpoint:** `GET /users/profile`
**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "phone_number": "+1234567890",
  "first_name": "John",
  "last_name": "Doe",
  "display_name": "John Doe",
  "avatar_url": "https://example.com/avatars/john.jpg",
  "email_verified": true,
  "phone_verified": true,
  "is_verified": true,
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-16T08:30:00Z",
  "timezone": "UTC",
  "preferred_language": "en",
  "meeting_settings": {
    "default_video_enabled": true,
    "default_audio_enabled": true,
    "auto_join_audio": true
  }
}
```

---

### Update User Profile

Update user profile information.

**Endpoint:** `PUT /users/profile`
**Authentication:** Required

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "display_name": "John Smith",
  "timezone": "America/New_York",
  "preferred_language": "en",
  "meeting_settings": {
    "default_video_enabled": true,
    "default_audio_enabled": true,
    "auto_join_audio": false
  }
}
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "first_name": "John",
  "last_name": "Smith",
  "display_name": "John Smith",
  "updated_at": "2024-01-16T10:30:00Z"
}
```

---

## 📅 Meeting Management Endpoints

### Create Meeting

Create a new meeting.

**Endpoint:** `POST /meetings`
**Authentication:** Required

**Request Body:**
```json
{
  "title": "Weekly Team Standup",
  "description": "Weekly team synchronization meeting",
  "scheduled_start_time": "2024-01-20T15:00:00Z",
  "scheduled_end_time": "2024-01-20T16:00:00Z",
  "timezone": "UTC",
  "settings": {
    "waiting_room_enabled": true,
    "require_password": false,
    "allow_join_before_host": false,
    "recording_enabled": true,
    "auto_recording": false,
    "chat_enabled": true,
    "screen_sharing_enabled": true,
    "max_participants": 50
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "meeting-550e8400-e29b-41d4-a716-446655440000",
  "meeting_id": "123-456-789",
  "title": "Weekly Team Standup",
  "description": "Weekly team synchronization meeting",
  "host_user_id": "550e8400-e29b-41d4-a716-446655440000",
  "scheduled_start_time": "2024-01-20T15:00:00Z",
  "scheduled_end_time": "2024-01-20T16:00:00Z",
  "timezone": "UTC",
  "status": "scheduled",
  "join_url": "https://yourdomain.com/meeting/123-456-789",
  "passcode": null,
  "settings": {
    "waiting_room_enabled": true,
    "require_password": false,
    "allow_join_before_host": false,
    "recording_enabled": true,
    "auto_recording": false,
    "chat_enabled": true,
    "screen_sharing_enabled": true,
    "max_participants": 50
  },
  "created_at": "2024-01-16T10:30:00Z"
}
```

---

### Get Meeting

Get meeting details.

**Endpoint:** `GET /meetings/{meeting_id}`
**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": "meeting-550e8400-e29b-41d4-a716-446655440000",
  "meeting_id": "123-456-789",
  "title": "Weekly Team Standup",
  "description": "Weekly team synchronization meeting",
  "host_user_id": "550e8400-e29b-41d4-a716-446655440000",
  "scheduled_start_time": "2024-01-20T15:00:00Z",
  "scheduled_end_time": "2024-01-20T16:00:00Z",
  "actual_start_time": "2024-01-20T15:02:00Z",
  "actual_end_time": null,
  "timezone": "UTC",
  "status": "active",
  "current_participant_count": 12,
  "join_url": "https://yourdomain.com/meeting/123-456-789",
  "settings": {
    "waiting_room_enabled": true,
    "recording_enabled": true,
    "chat_enabled": true,
    "screen_sharing_enabled": true,
    "max_participants": 50
  },
  "participants": [
    {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "display_name": "John Doe",
      "role": "host",
      "status": "joined",
      "join_time": "2024-01-20T15:02:00Z",
      "video_enabled": true,
      "audio_enabled": true
    }
  ]
}
```

---

### List Meetings

List user's meetings with pagination and filtering.

**Endpoint:** `GET /meetings`
**Authentication:** Required

**Query Parameters:**
- `page` (integer, default: 1): Page number
- `limit` (integer, default: 20, max: 100): Items per page
- `status` (string): Filter by status (`scheduled`, `active`, `ended`, `cancelled`)
- `start_date` (ISO date): Filter meetings from this date
- `end_date` (ISO date): Filter meetings until this date

**Example:** `GET /meetings?page=1&limit=10&status=scheduled`

**Response:** `200 OK`
```json
{
  "meetings": [
    {
      "id": "meeting-550e8400-e29b-41d4-a716-446655440000",
      "meeting_id": "123-456-789",
      "title": "Weekly Team Standup",
      "scheduled_start_time": "2024-01-20T15:00:00Z",
      "scheduled_end_time": "2024-01-20T16:00:00Z",
      "status": "scheduled",
      "participant_count": 0,
      "max_participants": 50
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 25,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

---

### Update Meeting

Update meeting details.

**Endpoint:** `PUT /meetings/{meeting_id}`
**Authentication:** Required (Host only)

**Request Body:**
```json
{
  "title": "Updated Meeting Title",
  "description": "Updated description",
  "scheduled_start_time": "2024-01-20T16:00:00Z",
  "settings": {
    "max_participants": 100,
    "recording_enabled": false
  }
}
```

**Response:** `200 OK`
```json
{
  "id": "meeting-550e8400-e29b-41d4-a716-446655440000",
  "title": "Updated Meeting Title",
  "description": "Updated description",
  "scheduled_start_time": "2024-01-20T16:00:00Z",
  "updated_at": "2024-01-16T11:00:00Z"
}
```

---

### Join Meeting

Join a meeting as a participant.

**Endpoint:** `POST /meetings/{meeting_id}/join`
**Authentication:** Required

**Request Body:**
```json
{
  "display_name": "John Doe",
  "video_enabled": true,
  "audio_enabled": true,
  "passcode": "optional_meeting_passcode"
}
```

**Response:** `200 OK`
```json
{
  "participant_id": "participant-550e8400-e29b-41d4-a716-446655440000",
  "meeting_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "webrtc_config": {
    "iceServers": [
      {
        "urls": "stun:stun.l.google.com:19302"
      },
      {
        "urls": "turn:your-turn-server.com:3478",
        "username": "turnuser",
        "credential": "turnpass"
      }
    ]
  },
  "websocket_url": "wss://api.yourdomain.com/ws/meetings/123-456-789"
}
```

---

### Leave Meeting

Leave a meeting.

**Endpoint:** `POST /meetings/{meeting_id}/leave`
**Authentication:** Required

**Response:** `200 OK`
```json
{
  "message": "Left meeting successfully",
  "duration_seconds": 1825
}
```

---

### End Meeting

End a meeting (host only).

**Endpoint:** `POST /meetings/{meeting_id}/end`
**Authentication:** Required (Host only)

**Response:** `200 OK`
```json
{
  "message": "Meeting ended successfully",
  "ended_at": "2024-01-20T16:05:00Z",
  "total_duration_seconds": 3900,
  "total_participants": 15
}
```

---

## 💬 Chat Endpoints

### Send Message

Send a message in a meeting.

**Endpoint:** `POST /meetings/{meeting_id}/messages`
**Authentication:** Required

**Request Body:**
```json
{
  "content": "Hello everyone!",
  "message_type": "text",
  "recipient_user_id": null,
  "is_private": false
}
```

**Response:** `201 Created`
```json
{
  "id": "message-550e8400-e29b-41d4-a716-446655440000",
  "meeting_id": "meeting-550e8400-e29b-41d4-a716-446655440000",
  "sender_user_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "Hello everyone!",
  "message_type": "text",
  "is_private": false,
  "created_at": "2024-01-20T15:30:00Z"
}
```

---

### Get Messages

Get meeting messages with pagination.

**Endpoint:** `GET /meetings/{meeting_id}/messages`
**Authentication:** Required

**Query Parameters:**
- `page` (integer, default: 1): Page number
- `limit` (integer, default: 50, max: 100): Messages per page
- `since` (ISO datetime): Get messages since this timestamp

**Response:** `200 OK`
```json
{
  "messages": [
    {
      "id": "message-550e8400-e29b-41d4-a716-446655440000",
      "sender_user_id": "550e8400-e29b-41d4-a716-446655440000",
      "sender_name": "John Doe",
      "content": "Hello everyone!",
      "message_type": "text",
      "is_private": false,
      "created_at": "2024-01-20T15:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 120,
    "has_next": true
  }
}
```

---

## 🔌 WebSocket Events

### Connection

Connect to meeting WebSocket:

```javascript
const ws = new WebSocket('wss://api.yourdomain.com/ws/meetings/123-456-789?token=jwt_token');
```

### Events

#### Join Meeting
```json
{
  "type": "join_meeting",
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "display_name": "John Doe",
    "video_enabled": true,
    "audio_enabled": true
  }
}
```

#### Leave Meeting
```json
{
  "type": "leave_meeting",
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### WebRTC Signaling
```json
{
  "type": "webrtc_offer",
  "data": {
    "from": "user1",
    "to": "user2",
    "sdp": "v=0\r\no=- 123456 123456 IN IP4...",
    "type": "offer"
  }
}
```

#### Chat Message
```json
{
  "type": "chat_message",
  "data": {
    "message_id": "message-550e8400-e29b-41d4-a716-446655440000",
    "sender_id": "550e8400-e29b-41d4-a716-446655440000",
    "sender_name": "John Doe",
    "content": "Hello everyone!",
    "timestamp": "2024-01-20T15:30:00Z"
  }
}
```

---

## ❌ Error Responses

### Standard Error Format

```json
{
  "detail": "Error message description",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-01-16T10:30:00Z"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created |
| `400` | Bad Request |
| `401` | Unauthorized |
| `403` | Forbidden |
| `404` | Not Found |
| `422` | Validation Error |
| `429` | Rate Limited |
| `500` | Internal Server Error |

### Common Error Codes

| Error Code | Description |
|------------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `AUTHENTICATION_REQUIRED` | Valid authentication required |
| `INSUFFICIENT_PERMISSIONS` | User lacks required permissions |
| `RESOURCE_NOT_FOUND` | Requested resource not found |
| `MEETING_NOT_FOUND` | Meeting not found |
| `MEETING_ENDED` | Meeting has ended |
| `MEETING_FULL` | Meeting has reached participant limit |
| `RATE_LIMIT_EXCEEDED` | Too many requests |

---

## 📊 Rate Limiting

API endpoints are rate-limited to ensure fair usage:

- **Authentication endpoints**: 10 requests per minute
- **Meeting operations**: 60 requests per minute
- **Chat messages**: 100 requests per minute
- **General endpoints**: 1000 requests per hour

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1642348800
```

---

## 🧪 Testing

### Using curl

```bash
# Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Test",
    "last_name": "User", 
    "email": "test@example.com",
    "password": "TestPass123",
    "confirm_password": "TestPass123"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email_or_phone": "test@example.com",
    "password": "TestPass123"
  }'

# Create a meeting
curl -X POST http://localhost:8000/api/v1/meetings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Test Meeting",
    "scheduled_start_time": "2024-01-20T15:00:00Z"
  }'
```

### Postman Collection

A Postman collection is available at `/docs/postman-collection.json` with pre-configured requests for all endpoints.

---

## 📖 Interactive Documentation

When running in development mode, interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide a web interface to test API endpoints directly in your browser.