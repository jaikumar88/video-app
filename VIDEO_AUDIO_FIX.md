# Video/Audio WebRTC Fix

## Problem Analysis

### Issues Identified:
1. **WebRTC Handshake Not Initiating**: Peer connections were created but no offers were being sent
2. **Both Sides Waiting**: Both participants were waiting for the other to send an offer
3. **Local Video Black Screen**: Possible media track issues or browser permissions
4. **Audio Not Working**: WebRTC audio tracks not being transmitted

## Root Cause

The WebRTC connection flow requires one peer to create an **offer** and the other to respond with an **answer**. Our code was creating peer connections but not initiating the handshake.

### Original Flow (BROKEN):
```
New Participant Joins
  ↓
Existing participants create peer connection
  ↓
New participant creates peer connection
  ↓
❌ BOTH WAIT - No offer sent!
```

### Fixed Flow (WORKING):
```
New Participant Joins
  ↓
WebSocket broadcasts "participant_joined" event
  ↓
Existing participants receive event:
  - Create peer connection
  - Send WebRTC offer ✅
  ↓
New participant receives offer:
  - Already has peer connection created
  - Sends WebRTC answer ✅
  ↓
ICE candidates exchanged
  ↓
✅ Connection established!
```

## Changes Applied

### 1. FullMeetingRoom.tsx - Added Offer Initiation

**File**: `frontend/src/components/FullMeetingRoom.tsx`

#### Change 1: Existing participants send offers to new participants
```typescript
// Line ~324
const handleParticipantJoined = useCallback(
  async (participantId: string) => {
    // ... existing code to add participant to list ...
    
    // Initiate WebRTC connection with the new participant
    if (webrtcServiceRef.current) {
      console.log(`[FullMeetingRoom] Creating peer connection for: ${participantId}`);
      await webrtcServiceRef.current.createPeerConnection(participantId);
      
      // ✅ NEW: Create and send offer to initiate the connection
      console.log(`[FullMeetingRoom] Sending WebRTC offer to: ${participantId}`);
      await webrtcServiceRef.current.createOffer(participantId);
    }
  },
  [meetingId, user]
);
```

#### Change 2: New participants wait for offers from existing participants
```typescript
// Line ~227
// Create peer connections for existing participants
// Note: We don't send offers here - the existing participants will send offers to us
// when they receive our "participant_joined" WebSocket event
for (const participant of remoteParticipants) {
  console.log(
    `[FullMeetingRoom] Creating peer connection for existing participant:`,
    participant.user_id
  );
  await webrtcService.createPeerConnection(participant.user_id);
  console.log(
    `[FullMeetingRoom] Waiting for offer from existing participant:`,
    participant.user_id
  );
}
```

## WebRTC Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    PARTICIPANT A (Existing)                      │
│                                                                   │
│  1. Receives "participant_joined" WebSocket event                │
│  2. Creates RTCPeerConnection for Participant B                  │
│  3. Adds local audio/video tracks to peer connection             │
│  4. Creates SDP offer with createOffer()                         │
│  5. Sets local description with setLocalDescription()            │
│  6. Sends offer to Participant B via WebSocket                   │
│                                                                   │
│  8. Receives answer from Participant B                           │
│  9. Sets remote description with setRemoteDescription()          │
│                                                                   │
│  10. Exchanges ICE candidates                                    │
│  11. ✅ Connection established - video/audio flowing!            │
└─────────────────────────────────────────────────────────────────┘
                              ↕ WebSocket Signaling
┌─────────────────────────────────────────────────────────────────┐
│                    PARTICIPANT B (New)                           │
│                                                                   │
│  1. Joins meeting via REST API                                   │
│  2. Connects WebSocket                                           │
│  3. Creates RTCPeerConnection for Participant A                  │
│  4. Waits for offer...                                           │
│                                                                   │
│  7. Receives offer from Participant A                            │
│  8. Sets remote description with setRemoteDescription()          │
│  9. Creates SDP answer with createAnswer()                       │
│  10. Sets local description with setLocalDescription()           │
│  11. Sends answer to Participant A via WebSocket                 │
│                                                                   │
│  12. Exchanges ICE candidates                                    │
│  13. ✅ Connection established - video/audio flowing!            │
└─────────────────────────────────────────────────────────────────┘
```

## Testing Instructions

### Prerequisites:
1. Backend running on port 8000
2. Frontend running with `npm start` (uses .env.local)
3. Two different browsers (Chrome, Edge, Firefox, etc.)

### Test Steps:

#### Browser 1 (Admin - Chrome):
1. Navigate to `http://localhost:3000`
2. Login as admin:
   - Email: `admin@example.com`
   - Password: `admin123`
3. Click "Start New Meeting"
4. **Check console logs** for:
   ```
   [FullMeetingRoom] Local stream obtained: Success
   [FullMeetingRoom] Local video playing successfully
   ```
5. Verify your video appears in the main window

#### Browser 2 (Guest - Edge):
1. Navigate to `http://localhost:3000`
2. Copy the meeting ID or invite link from Browser 1
3. Click "Join as Guest"
4. Enter name and meeting ID
5. **Check console logs** for:
   ```
   [FullMeetingRoom] Waiting for offer from existing participant
   ```

#### In Browser 1 (after Browser 2 joins):
**Check console logs** for:
```
Participant joined: <user_id>
[FullMeetingRoom] Creating peer connection for: <user_id>
[FullMeetingRoom] Sending WebRTC offer to: <user_id>
Connection state with <user_id>: connecting
Connection state with <user_id>: connected
```

#### In Browser 2 (after connection):
**Check console logs** for:
```
Received WebRTC offer from: <user_id>
Sending WebRTC answer to: <user_id>
Connection state with <user_id>: connecting
Connection state with <user_id>: connected
[FullMeetingRoom] Received remote stream for participant: <user_id>
```

### Expected Results:
✅ Both participants see each other in the video grid  
✅ Admin video displays correctly (not black screen)  
✅ Guest video displays correctly  
✅ Audio works in both directions  
✅ Participant count shows "2"  
✅ Names display correctly  

## Debugging Tips

### If Video Still Shows Black Screen:

1. **Check Browser Console** for errors:
   ```javascript
   // Look for:
   NotAllowedError: Permission denied
   NotFoundError: No camera found
   AbortError: Camera in use by another app
   ```

2. **Check Media Tracks**:
   ```javascript
   // In browser console:
   const video = document.querySelector('video');
   const stream = video.srcObject;
   console.log('Video tracks:', stream.getVideoTracks());
   console.log('Audio tracks:', stream.getAudioTracks());
   
   // Check track state:
   stream.getVideoTracks().forEach(track => {
     console.log('Video track:', {
       enabled: track.enabled,
       muted: track.muted,
       readyState: track.readyState // should be "live"
     });
   });
   ```

3. **Browser Permissions**:
   - Chrome: `chrome://settings/content/camera`
   - Edge: `edge://settings/content/camera`
   - Allow camera/microphone for localhost

### If Audio Not Working:

1. **Check Audio Output**:
   - Verify system volume not muted
   - Check browser audio not muted (right-click tab)
   - Test with different speakers/headphones

2. **Check Audio Tracks**:
   ```javascript
   stream.getAudioTracks().forEach(track => {
     console.log('Audio track:', {
       enabled: track.enabled,
       muted: track.muted,
       readyState: track.readyState
     });
   });
   ```

3. **Remote Video Muted**:
   - Remote videos should NOT have `muted` attribute
   - Local video SHOULD have `muted` attribute (prevent echo)

### If Connection Fails:

1. **Check WebSocket Connection**:
   ```javascript
   // In browser console:
   // Look for WS connection in Network tab -> WS filter
   // Should show: ws://localhost:8000/ws/<meeting_id>?token=<jwt>
   ```

2. **Check ICE Candidate Exchange**:
   ```javascript
   // In console logs:
   // Should see: "Sending ICE candidate to: <user_id>"
   // Should see: "Remote stream received from: <user_id>"
   ```

3. **STUN Server Connectivity**:
   - Open Network tab
   - Look for connections to `stun.l.google.com:19302`
   - If blocked by firewall, may need TURN server

## Environment Configuration

### Local Testing (.env.local):
```env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_FRONTEND_URL=http://localhost:3000
```

### Production/Ngrok (.env.production):
```env
REACT_APP_API_URL=https://uncurdling-joane-pantomimical.ngrok-free.dev/api/v1
REACT_APP_WS_URL=wss://uncurdling-joane-pantomimical.ngrok-free.dev
REACT_APP_FRONTEND_URL=https://uncurdling-joane-pantomimical.ngrok-free.dev
```

**Note**: Secure WebSocket (wss://) required for production HTTPS sites to access camera/microphone

## Next Steps

1. ✅ Test with two participants in local environment
2. ⏳ Fix any remaining video/audio issues
3. ⏳ Test with ngrok for remote access
4. ⏳ Deploy frontend to GitHub Pages
5. ⏳ Test with multiple participants (3+)
6. ⏳ Add TURN server for production (firewall traversal)

## Known Limitations

- **STUN Only**: Currently using Google STUN servers. For production, add TURN server for NAT/firewall traversal
- **No Bandwidth Control**: May need to adjust video quality for poor connections
- **No Reconnection Logic**: If connection drops, user must rejoin manually
- **Browser Compatibility**: Tested on Chrome/Edge. Safari may need additional configuration

## References

- [WebRTC API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API)
- [RTCPeerConnection](https://developer.mozilla.org/en-US/docs/Web/API/RTCPeerConnection)
- [Perfect Negotiation Pattern](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Perfect_negotiation)
