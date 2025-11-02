# Testing Two Participants Locally

## Method 1: Host + Guest (Recommended)

### Setup
- Frontend: http://localhost:3000/video-app-frontend
- Backend: http://localhost:8000

### Steps

#### Browser 1 (Chrome) - Host
1. Navigate to `http://localhost:3000/video-app-frontend`
2. Login with:
   - Email: `admin@videoapp.com`
   - Password: `admin123`
3. Click **"Start Meeting"**
4. Note the **Meeting ID** displayed (e.g., "58458873903")
5. Allow camera/microphone access when prompted

#### Browser 2 (Edge/Firefox) - Guest
1. Navigate to `http://localhost:3000/video-app-frontend`
2. Click **"Join as Guest"** button on homepage
3. Enter the Meeting ID from Browser 1
4. Enter your name (e.g., "Test Guest")
5. Click **"Join Meeting"**
6. Allow camera/microphone access when prompted

### Expected Results
✅ Both participants should see each other's video
✅ Both can hear each other's audio
✅ Participant count shows "2"
✅ Both names are visible in participant list
✅ Video controls work for both participants

---

## Method 2: Two Authenticated Users

### Create Second User
```bash
# In backend directory
cd backend
python -c "
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.services.auth_service import AuthService

async def create_user():
    async with AsyncSessionLocal() as db:
        auth = AuthService()
        user = await auth.register_user(
            db,
            email='user2@videoapp.com',
            password='user123',
            first_name='Test',
            last_name='User'
        )
        print(f'Created user: {user.email}')

asyncio.run(create_user())
"
```

### Steps
1. **Browser 1 (Chrome)**: Login as `admin@videoapp.com`, start meeting
2. **Browser 2 (Edge)**: Login as `user2@videoapp.com`, join meeting using ID

---

## Method 3: Incognito/Private Windows

1. **Normal Chrome**: Login and start meeting
2. **Chrome Incognito**: Use guest join with the meeting ID

---

## Troubleshooting

### Camera Already in Use
If you see "Camera already in use by another application":
- Use two different browsers (Chrome + Edge)
- Or use one browser + one incognito window
- Or enable virtual camera (OBS/ManyCam)

### No Video/Audio
1. Check browser console for errors (F12)
2. Verify camera/mic permissions granted
3. Check WebSocket connection in Network tab
4. Backend logs should show "User connected to meeting"

### Participant Not Visible
1. Check browser console for WebRTC errors
2. Verify both participants are in "JOINED" status
3. Check backend logs for WebSocket messages
4. Try refreshing the page

---

## Quick Verification Script

```bash
# Test that meeting was created and guest can join
cd backend

# Create meeting
curl -X POST http://localhost:8000/api/v1/meetings/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Meeting"}'

# Join as guest
curl -X POST http://localhost:8000/api/v1/meetings/MEETING_ID/join/guest \
  -H "Content-Type: application/json" \
  -d '{"display_name":"Test Guest"}'
```
