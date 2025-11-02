# Tunnel Access Instructions

## Current Working Setup ✅

**ngrok Tunnel**: `https://uncurdling-joane-pantomimical.ngrok-free.dev`
- Status: Active and working
- No password required
- Direct access to your video platform

## If You See "Enter Password" or White Screen

This happens with LocalTunnel's security feature. Here's how to handle it:

### For LocalTunnel URLs (*.loca.lt):

1. **First Visit**: LocalTunnel shows a warning page asking for a password
2. **Password**: Use any password (it's just a security warning, not actual auth)
3. **After entering password**: You should see your video platform
4. **If White Screen**: 
   - Refresh the page
   - Try a different browser
   - Clear browser cache
   - Use the ngrok URL instead

### Recommended Solution: Use ngrok

**Primary URL**: `https://uncurdling-joane-pantomimical.ngrok-free.dev`
- No password prompts
- More reliable for video calling
- Better for sharing with participants

## How to Switch Between Tunnels

### Start ngrok (Recommended):
```bash
cd backend
.\ngrok.exe http 8000
```

### Start LocalTunnel (Alternative):
```bash
npx localtunnel --port 8000
```

## For Participants

**Share this URL**: `https://uncurdling-joane-pantomimical.ngrok-free.dev`

**Features they can access**:
- Register new account
- Login to existing account  
- Create video meetings
- Join meetings with room codes
- Full video/audio calling
- Screen sharing and chat

## Troubleshooting

### If ngrok shows "offline":
1. Stop ngrok (Ctrl+C)
2. Restart: `.\ngrok.exe http 8000`
3. Use the new URL provided

### If LocalTunnel asks for password:
1. Enter any password (like "123" or "password")
2. Click "Continue" or "Submit"
3. Should redirect to your app

### If you see white screen:
1. Check if backend is running: `curl http://localhost:8000/health`
2. Refresh the browser page
3. Try ngrok URL instead

**Current Status**: ngrok tunnel is active and working! 🎉