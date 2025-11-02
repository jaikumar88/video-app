# 🧪 Quick Testing Guide

## Application is LIVE! ✅

Backend: `http://localhost:8000`  
Frontend: `http://localhost:8000`  
API Docs: `http://localhost:8000/docs`

---

## ✅ All 15 Tests PASSING

Run the test suite anytime:
```powershell
cd backend
$env:PYTHONIOENCODING='utf-8'
python test_all_features.py
```

---

## 🎥 Test Video Calling (2-Person Test)

### Setup (5 minutes)

#### Window 1 - Host
1. Open `http://localhost:8000`
2. Login with:
   - Email: `admin@videoapp.com`
   - Password: `admin`
3. Create a new meeting
4. Copy the meeting ID
5. Enable camera/microphone when prompted

#### Window 2 - Participant
1. Open `http://localhost:8000` in **incognito/private** window (or different browser)
2. Register a new account OR login with different user
3. Join meeting using the meeting ID from Window 1
4. Enable camera/microphone when prompted

### Expected Results ✅
- [x] Both users see each other's video
- [x] Both users hear each other's audio
- [x] Participant list shows both users
- [x] Chat messages appear instantly
- [x] Video/audio can be muted/unmuted

---

## 🔧 Quick Backend Commands

### Start Backend
```powershell
cd E:\workspace\python\video-app\backend
python main.py
```

### Stop Backend
```powershell
# Press Ctrl+C in the terminal running main.py
# OR force stop:
Get-Process python | Stop-Process -Force
```

### Check Backend Health
```powershell
Invoke-WebRequest http://localhost:8000/health
# Should return: {"status":"healthy","environment":"local"}
```

---

## 🐛 Troubleshooting

### Backend won't start
```powershell
# Check if port 8000 is already in use
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

# Kill existing process on port 8000
Get-Process python | Stop-Process -Force
```

### WebSocket not connecting
1. Check backend logs for `[DEBUG]` entries
2. Verify JWT token is valid (login again)
3. Ensure user has joined the meeting first

### Video/Audio not working
1. Check browser console for errors
2. Allow camera/microphone permissions in browser
3. Test with different browser
4. Check if camera/microphone work in other apps

### Database issues
```powershell
# Delete database and restart (WARNING: Loses all data)
cd backend
Remove-Item app.db
python main.py
# Admin user will be recreated automatically
```

---

## 📊 Test Coverage

| Feature | Status | Test # |
|---------|--------|--------|
| Backend Health | ✅ PASS | 1 |
| User Registration | ✅ PASS | 2 |
| User Login | ✅ PASS | 3 |
| User Profile | ✅ PASS | 4 |
| Create Meeting | ✅ PASS | 5 |
| Meeting Details | ✅ PASS | 6 |
| Join Meeting | ✅ PASS | 7 |
| List Participants | ✅ PASS | 8 |
| **WebSocket Connect** | ✅ **PASS** | **9** |
| **WebSocket Send** | ✅ **PASS** | **10** |
| **WebSocket Receive** | ✅ **PASS** | **11** |
| Video/Audio Settings | ✅ PASS | 12 |
| Update Settings | ✅ PASS | 13 |
| Leave Meeting | ✅ PASS | 14 |
| List Meetings | ✅ PASS | 15 |

---

## 🚀 Ready for Testing!

The application is now **fully functional** with all critical bugs fixed:

1. ✅ **WebSocket Connectivity** - Fixed 403 Forbidden error
2. ✅ **Video/Audio Support** - WebRTC signaling working
3. ✅ **Participant Visibility** - Real-time updates functional
4. ✅ **Admin Access** - Account reactivation working
5. ✅ **Database** - All tables and relationships correct

### What Was Fixed?
- **WebSocket Route Path** - Corrected double `/ws/ws/` to `/ws/`
- **Access Control** - Added host access alongside participant check
- **Field References** - Fixed `host_id` to `host_user_id`
- **Error Handling** - Added comprehensive logging and exception handling

---

## 📝 Default Admin Account

- **Email:** `admin@videoapp.com`
- **Password:** `admin`
- **Role:** Super Admin
- **Auto-created:** Yes (on first startup)

---

## 🔗 Useful URLs

| Resource | URL |
|----------|-----|
| Frontend | http://localhost:8000/ |
| API Docs (Swagger) | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |
| WebSocket | ws://localhost:8000/ws/{meeting_id}?token={jwt} |

---

## 💡 Tips

1. **Use Different Browsers** - Chrome + Firefox for easier testing
2. **Use Incognito Mode** - Prevents session conflicts
3. **Check Console** - F12 → Console tab for WebRTC errors
4. **Check Network Tab** - F12 → Network → WS to see WebSocket traffic
5. **Enable Verbose Logging** - Check backend terminal for `[DEBUG]` logs

---

## ⚡ Quick Test Script

```powershell
# One-liner to start backend and run tests
cd E:\workspace\python\video-app\backend; python main.py &
Start-Sleep 5
$env:PYTHONIOENCODING='utf-8'; python test_all_features.py
```

---

## 📞 Need Help?

1. Check `COMPLETE_FIX_REPORT.md` for detailed technical info
2. Check backend logs (terminal running `python main.py`)
3. Run health check: `http://localhost:8000/health`
4. Check browser console for frontend errors

---

**Last Updated:** 2025-11-01  
**Status:** ✅ All Systems Operational  
**Test Results:** 15/15 PASSING
