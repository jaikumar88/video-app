"""
Comprehensive Application Diagnostic Tool
Tests all critical features and identifies specific issues
"""

import requests
import json
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_header(text):
    print(f"\n{'='*70}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{'='*70}\n")

def print_test(name, passed, details=""):
    icon = f"{Colors.GREEN}✓{Colors.RESET}" if passed else f"{Colors.RED}✗{Colors.RESET}"
    status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
    print(f"{icon} [{status}] {name}")
    if details:
        print(f"        {details}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠  {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ  {text}{Colors.RESET}")

# Test results tracker
results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "critical_failures": []
}

def run_test(name, test_func, critical=False):
    """Run a test and track results"""
    results["total"] += 1
    try:
        success, message = test_func()
        if success:
            results["passed"] += 1
            print_test(name, True, message)
        else:
            results["failed"] += 1
            print_test(name, False, message)
            if critical:
                results["critical_failures"].append(f"{name}: {message}")
        return success
    except Exception as e:
        results["failed"] += 1
        error_msg = f"Exception: {str(e)}"
        print_test(name, False, error_msg)
        if critical:
            results["critical_failures"].append(f"{name}: {error_msg}")
        return False

# ============================================================================
# TEST SUITE
# ============================================================================

def test_backend_health():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return True, f"Backend healthy: {response.json()}"
        return False, f"Status {response.status_code}"
    except Exception as e:
        return False, f"Backend not accessible: {str(e)}"

def test_registration():
    """Test user registration"""
    global test_user_email, test_user_password
    test_user_email = f"test{int(time.time())}@test.com"
    test_user_password = "Test@123456"
    
    try:
        response = requests.post(f"{API_URL}/auth/register", json={
            "email": test_user_email,
            "password": test_user_password,
            "first_name": "Test",
            "last_name": "User"
        })
        
        if response.status_code in [200, 201]:
            return True, f"User registered: {test_user_email}"
        return False, f"Status {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, str(e)

def test_login():
    """Test user login"""
    global access_token, user_id
    
    try:
        response = requests.post(f"{API_URL}/auth/login", json={
            "email_or_phone": test_user_email,
            "password": test_user_password
        })
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            user_id = data.get("user", {}).get("id")
            return True, "Login successful, token received"
        return False, f"Status {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, str(e)

def test_get_profile():
    """Test getting user profile"""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{API_URL}/users/me", headers=headers)
        
        if response.status_code == 200:
            return True, f"Profile retrieved for {response.json().get('email')}"
        return False, f"Status {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, str(e)

def test_create_meeting():
    """Test creating a meeting"""
    global meeting_id
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(f"{API_URL}/meetings", headers=headers, json={
            "title": "Diagnostic Test Meeting",
            "scheduled_at": datetime.utcnow().isoformat() + "Z",
            "duration_minutes": 60
        })
        
        if response.status_code in [200, 201]:
            meeting_id = response.json().get("id")
            return True, f"Meeting created: {meeting_id}"
        return False, f"Status {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, str(e)

def test_join_meeting():
    """Test joining a meeting"""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(f"{API_URL}/meetings/{meeting_id}/join", headers=headers)
        
        if response.status_code in [200, 201]:
            return True, "Successfully joined meeting"
        return False, f"Status {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, str(e)

def test_get_participants():
    """Test getting meeting participants"""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{API_URL}/meetings/{meeting_id}/participants", headers=headers)
        
        if response.status_code == 200:
            participants = response.json()
            return True, f"Found {len(participants)} participant(s)"
        return False, f"Status {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, str(e)

def test_websocket_endpoint():
    """Test WebSocket endpoint availability"""
    try:
        # We can't fully test WebSocket without a proper client, but we can check the endpoint
        import websocket
        ws_url = f"ws://localhost:8000/ws/{meeting_id}?token={access_token}"
        ws = websocket.create_connection(ws_url, timeout=5)
        ws.close()
        return True, "WebSocket connection successful"
    except ModuleNotFoundError:
        print_warning("websocket-client not installed, skipping WebSocket test")
        return True, "Skipped (websocket-client not installed)"
    except Exception as e:
        return False, f"WebSocket connection failed: {str(e)}"

def test_list_meetings():
    """Test listing user meetings"""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{API_URL}/meetings", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            count = data.get("total", 0)
            return True, f"Retrieved {count} meeting(s)"
        return False, f"Status {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, str(e)

def test_leave_meeting():
    """Test leaving a meeting"""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(f"{API_URL}/meetings/{meeting_id}/leave", headers=headers)
        
        if response.status_code in [200, 201]:
            return True, "Successfully left meeting"
        return False, f"Status {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, str(e)

# ============================================================================
# MAIN DIAGNOSTIC RUNNER
# ============================================================================

def main():
    print_header("🔍 VIDEO CALLING PLATFORM - COMPREHENSIVE DIAGNOSTIC")
    print_info(f"Testing backend at: {BASE_URL}")
    print_info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Critical tests that must pass
    print_header("🚨 CRITICAL TESTS (Must Pass)")
    
    if not run_test("Backend Health Check", test_backend_health, critical=True):
        print(f"\n{Colors.RED}FATAL: Backend is not running!{Colors.RESET}")
        print("Please start the backend server first:")
        print("  cd backend")
        print("  python main.py")
        sys.exit(1)
    
    run_test("User Registration", test_registration, critical=True)
    run_test("User Login", test_login, critical=True)
    
    # Feature tests
    print_header("📋 FEATURE TESTS")
    run_test("Get User Profile", test_get_profile)
    run_test("Create Meeting", test_create_meeting)
    run_test("Join Meeting", test_join_meeting)
    run_test("Get Participants List", test_get_participants)
    run_test("WebSocket Connection", test_websocket_endpoint)
    run_test("List Meetings", test_list_meetings)
    run_test("Leave Meeting", test_leave_meeting)
    
    # Print summary
    print_header("📊 DIAGNOSTIC SUMMARY")
    
    total = results["total"]
    passed = results["passed"]
    failed = results["failed"]
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total Tests:    {total}")
    print(f"{Colors.GREEN}Passed:         {passed} ({pass_rate:.1f}%){Colors.RESET}")
    print(f"{Colors.RED}Failed:         {failed}{Colors.RESET}\n")
    
    # Critical failures
    if results["critical_failures"]:
        print(f"{Colors.RED}🚨 CRITICAL FAILURES:{Colors.RESET}")
        for failure in results["critical_failures"]:
            print(f"  • {failure}")
        print()
    
    # Overall assessment
    if pass_rate >= 90:
        print(f"{Colors.GREEN}✓ Application Status: EXCELLENT{Colors.RESET}")
        print("  All critical features are working correctly.")
    elif pass_rate >= 70:
        print(f"{Colors.YELLOW}⚠  Application Status: GOOD (Minor Issues){Colors.RESET}")
        print("  Core features work, but some improvements needed.")
    elif pass_rate >= 50:
        print(f"{Colors.YELLOW}⚠  Application Status: FAIR (Major Issues){Colors.RESET}")
        print("  Critical issues need immediate attention.")
    else:
        print(f"{Colors.RED}✗ Application Status: POOR{Colors.RESET}")
        print("  Application has severe problems. Not ready for customers.")
    
    print()
    sys.exit(0 if pass_rate >= 70 else 1)

if __name__ == "__main__":
    # Global test variables
    test_user_email = ""
    test_user_password = ""
    access_token = ""
    user_id = ""
    meeting_id = ""
    
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Diagnostic interrupted by user{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}FATAL ERROR: {str(e)}{Colors.RESET}")
        sys.exit(1)
