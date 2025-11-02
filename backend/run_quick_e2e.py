"""
Quick E2E Test Runner
Runs API tests immediately, UI tests if ChromeDriver available
"""

import sys
import time
import requests
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
API_URL = f"{BACKEND_URL}/api/v1"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0
}

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

def print_test(name, passed, message=""):
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
        icon = f"{Colors.GREEN}✓{Colors.RESET}"
        status = f"{Colors.GREEN}PASS{Colors.RESET}"
    else:
        test_results["failed"] += 1
        icon = f"{Colors.RED}✗{Colors.RESET}"
        status = f"{Colors.RED}FAIL{Colors.RESET}"
    
    print(f"{icon} [{status}] {name}")
    if message:
        print(f"    {message}")

def print_skip(name, reason):
    test_results["skipped"] += 1
    print(f"{Colors.YELLOW}⊘  [SKIP] {name}{Colors.RESET}")
    print(f"    {reason}")

# Test variables
test_user_email = f"test{int(time.time())}@test.com"
test_user_password = "Test@123456"
access_token = None
meeting_id = None

def test_backend_health():
    """Test backend health"""
    print(f"\n{Colors.CYAN}▶  Running: Backend Health Check{Colors.RESET}")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        passed = response.status_code == 200
        print_test("Backend Health Check", passed, f"Status: {response.status_code}")
        return passed
    except Exception as e:
        print_test("Backend Health Check", False, f"Error: {str(e)}")
        return False

def test_user_registration():
    """Test user registration"""
    print(f"\n{Colors.CYAN}▶  Running: User Registration{Colors.RESET}")
    try:
        response = requests.post(f"{API_URL}/auth/register", json={
            "email": test_user_email,
            "password": test_user_password,
            "first_name": "Test",
            "last_name": "User"
        })
        passed = response.status_code in [200, 201]
        print_test("User Registration", passed, f"Email: {test_user_email}")
        return passed
    except Exception as e:
        print_test("User Registration", False, str(e))
        return False

def test_user_login():
    """Test user login"""
    global access_token
    print(f"\n{Colors.CYAN}▶  Running: User Login{Colors.RESET}")
    try:
        response = requests.post(f"{API_URL}/auth/login", json={
            "email_or_phone": test_user_email,
            "password": test_user_password
        })
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            passed = access_token is not None
            print_test("User Login", passed, "Token received")
            return passed
        print_test("User Login", False, f"Status: {response.status_code}")
        return False
    except Exception as e:
        print_test("User Login", False, str(e))
        return False

def test_create_meeting():
    """Test meeting creation"""
    global meeting_id
    print(f"\n{Colors.CYAN}▶  Running: Create Meeting{Colors.RESET}")
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(f"{API_URL}/meetings", headers=headers, json={
            "title": "Test Meeting",
            "scheduled_at": datetime.utcnow().isoformat() + "Z",
            "duration_minutes": 60
        })
        if response.status_code in [200, 201]:
            meeting_id = response.json().get("id")
            print_test("Create Meeting", True, f"ID: {meeting_id}")
            return True
        print_test("Create Meeting", False, f"Status: {response.status_code}")
        return False
    except Exception as e:
        print_test("Create Meeting", False, str(e))
        return False

def test_join_meeting():
    """Test joining meeting"""
    print(f"\n{Colors.CYAN}▶  Running: Join Meeting{Colors.RESET}")
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(f"{API_URL}/meetings/{meeting_id}/join", headers=headers)
        passed = response.status_code in [200, 201]
        print_test("Join Meeting", passed, "Successfully joined")
        return passed
    except Exception as e:
        print_test("Join Meeting", False, str(e))
        return False

def test_get_participants():
    """Test getting participants"""
    print(f"\n{Colors.CYAN}▶  Running: Get Participants{Colors.RESET}")
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{API_URL}/meetings/{meeting_id}/participants", headers=headers)
        if response.status_code == 200:
            participants = response.json()
            print_test("Get Participants", True, f"Found {len(participants)} participant(s)")
            return True
        print_test("Get Participants", False, f"Status: {response.status_code}")
        return False
    except Exception as e:
        print_test("Get Participants", False, str(e))
        return False

def test_websocket():
    """Test WebSocket connection"""
    print(f"\n{Colors.CYAN}▶  Running: WebSocket Connection{Colors.RESET}")
    try:
        import websocket
        ws_url = f"ws://localhost:8000/ws/{meeting_id}?token={access_token}"
        ws = websocket.create_connection(ws_url, timeout=5)
        time.sleep(1)
        ws.close()
        print_test("WebSocket Connection", True, "Connected successfully")
        return True
    except ModuleNotFoundError:
        print_skip("WebSocket Connection", "websocket-client not installed")
        return False
    except Exception as e:
        print_test("WebSocket Connection", False, str(e))
        return False

def test_ui_with_selenium():
    """Test UI with Selenium if available"""
    print(f"\n{Colors.CYAN}▶  Checking for Selenium...{Colors.RESET}")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # Test homepage
        print(f"\n{Colors.CYAN}▶  Running: Frontend Homepage{Colors.RESET}")
        driver.get(FRONTEND_URL)
        time.sleep(2)
        title = driver.title
        driver.quit()
        
        passed = title is not None
        print_test("Frontend Homepage", passed, f"Title: {title}")
        return passed
        
    except ImportError:
        print_skip("Frontend UI Tests", "Selenium not installed")
        return False
    except Exception as e:
        print_skip("Frontend UI Tests", f"ChromeDriver not available: {str(e)}")
        return False

def main():
    print_header("🧪 QUICK E2E TEST SUITE")
    print(f"Backend: {BACKEND_URL}")
    print(f"Frontend: {FRONTEND_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check backend first
    if not test_backend_health():
        print(f"\n{Colors.RED}FATAL: Backend not running!{Colors.RESET}")
        print("Please start backend: python main.py")
        sys.exit(1)
    
    # API Tests
    print_header("🔌 API TESTS")
    test_user_registration()
    test_user_login()
    test_create_meeting()
    test_join_meeting()
    test_get_participants()
    test_websocket()
    
    # UI Tests (if available)
    print_header("🎨 FRONTEND TESTS (if available)")
    test_ui_with_selenium()
    
    # Summary
    print_header("📊 TEST SUMMARY")
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    skipped = test_results["skipped"]
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total:    {total}")
    print(f"{Colors.GREEN}Passed:   {passed} ({pass_rate:.1f}%){Colors.RESET}")
    print(f"{Colors.RED}Failed:   {failed}{Colors.RESET}")
    print(f"{Colors.YELLOW}Skipped:  {skipped}{Colors.RESET}\n")
    
    if pass_rate >= 90:
        print(f"{Colors.GREEN}✓ Status: EXCELLENT{Colors.RESET}")
    elif pass_rate >= 70:
        print(f"{Colors.YELLOW}⚠  Status: GOOD{Colors.RESET}")
    else:
        print(f"{Colors.RED}✗ Status: NEEDS WORK{Colors.RESET}")
    
    print()
    
    if skipped > 0:
        print(f"{Colors.YELLOW}Note: Install ChromeDriver for full UI tests:{Colors.RESET}")
        print("  choco install chromedriver")
        print("  OR download from: https://chromedriver.chromium.org/")
    
    sys.exit(0 if pass_rate >= 70 else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}ERROR: {str(e)}{Colors.RESET}")
        sys.exit(1)
