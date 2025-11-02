"""
WebRTC Connection Diagnostic Tool
Checks WebSocket and WebRTC peer connection status
"""
import asyncio
import aiohttp
import json

BACKEND_URL = "http://localhost:8000"
API_URL = f"{BACKEND_URL}/api/v1"

async def diagnose_webrtc():
    """Diagnose WebRTC connection issues"""
    
    print("=" * 60)
    print("WebRTC Connection Diagnostic")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        # Step 1: Login as admin
        print("\n1. Logging in as admin...")
        login_data = {
            "email_or_phone": "admin@videoapp.com",
            "password": "admin"
        }
        async with session.post(f"{API_URL}/auth/login", json=login_data) as resp:
            if resp.status != 200:
                print(f"❌ Login failed: {resp.status}")
                return
            result = await resp.json()
            token = result["access_token"]
            print("✅ Logged in")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 2: Get first available meeting
        print("\n2. Finding a meeting...")
        async with session.get(f"{API_URL}/meetings", headers=headers) as resp:
            if resp.status != 200:
                print(f"❌ Failed to get meetings: {resp.status}")
                return
            meetings = await resp.json()
            if not meetings:
                print("❌ No meetings found. Create one first!")
                return
            
            meeting = meetings[0]
            meeting_id = meeting["meeting_id"]
            print(f"✅ Found meeting: {meeting_id}")
        
        # Step 3: Join meeting
        print(f"\n3. Joining meeting {meeting_id}...")
        join_data = {"video_enabled": True, "audio_enabled": True}
        async with session.post(
            f"{API_URL}/meetings/{meeting_id}/join",
            json=join_data,
            headers=headers
        ) as resp:
            if resp.status != 200:
                print(f"❌ Join failed: {resp.status}")
                text = await resp.text()
                print(f"Response: {text}")
                return
            join_result = await resp.json()
            participant_id = join_result["participant_id"]
            websocket_url = join_result.get("websocket_url", "")
            print(f"✅ Joined as participant: {participant_id}")
            print(f"   WebSocket URL: {websocket_url}")
        
        # Step 4: Check meeting details
        print(f"\n4. Checking meeting status...")
        async with session.get(f"{API_URL}/meetings/{meeting_id}", headers=headers) as resp:
            if resp.status != 200:
                print(f"❌ Failed to get meeting: {resp.status}")
                return
            meeting_details = await resp.json()
            participant_count = meeting_details.get("current_participant_count", 0)
            print(f"✅ Current participants: {participant_count}")
            print(f"   Status: {meeting_details.get('status')}")
        
        print("\n" + "=" * 60)
        print("DIAGNOSIS COMPLETE")
        print("=" * 60)
        print("\n📋 Next Steps to Test Two Participants:")
        print("1. Keep this meeting open in browser as Admin")
        print("2. Open incognito window: http://localhost:8000/guest-join.html")
        print(f"3. Enter Meeting ID: {meeting_id}")
        print("4. Join as guest")
        print("\n🔍 Check Browser Console for:")
        print("   - 'User joined' messages")
        print("   - 'WebRTC signal received' messages")
        print("   - Any errors in red")
        print("\n⚠️  If no video/audio:")
        print("   - Both users must be in SAME meeting ID")
        print("   - Check browser console for WebRTC errors")
        print("   - Verify camera/mic permissions granted")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(diagnose_webrtc())
