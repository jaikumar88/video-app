# Testing Guide - WorldClass Video Platform

## Overview

This document provides comprehensive guidance for testing the WorldClass Video Platform. The platform includes both automated testing suites and manual testing tools to ensure reliability, performance, and security.

## Table of Contents

1. [Test Structure](#test-structure)
2. [Running Tests](#running-tests)
3. [Test Types](#test-types)
4. [Postman Collections](#postman-collections)
5. [Performance Testing](#performance-testing)
6. [CI/CD Integration](#cicd-integration)
7. [Test Data Management](#test-data-management)
8. [Troubleshooting](#troubleshooting)

## Test Structure

### Backend Tests (Python/pytest)

```
backend/tests/
├── conftest.py              # Test fixtures and configuration
├── unit/                    # Unit tests
│   ├── test_auth.py        # Authentication service tests
│   ├── test_models.py      # Database model tests
│   └── test_utils.py       # Utility function tests
├── integration/             # Integration tests
│   ├── test_websocket.py   # WebSocket functionality
│   └── test_database.py    # Database integration
├── api/                     # API endpoint tests
│   ├── test_auth_api.py    # Authentication API tests
│   └── test_meetings_api.py # Meeting management API tests
└── performance/             # Performance tests
    └── test_load.py        # Load testing with Locust
```

### Frontend Tests (React/Jest)

```
frontend/src/
├── __tests__/              # Test files
├── components/             # Component tests
├── store/                  # Redux store tests
└── utils/                  # Utility tests
```

## Running Tests

### Prerequisites

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Setup Test Environment**
   ```bash
   python run_tests.py setup
   ```

### Test Runner Commands

The `run_tests.py` script provides convenient commands for different test scenarios:

#### Unit Tests
```bash
# Run all unit tests with coverage
python run_tests.py unit

# Run without coverage
python run_tests.py unit --no-coverage

# Run in quiet mode
python run_tests.py unit --quiet
```

#### Integration Tests
```bash
# Run all integration tests
python run_tests.py integration
```

#### API Tests
```bash
# Run all API tests
python run_tests.py api
```

#### All Tests
```bash
# Run complete test suite
python run_tests.py all

# Run without coverage reporting
python run_tests.py all --no-coverage
```

#### Performance Tests
```bash
# Start Locust performance testing
python run_tests.py performance
# Access web UI at http://localhost:8089
```

#### Security Tests
```bash
# Run security-focused tests
python run_tests.py security
```

#### Code Quality
```bash
# Check code formatting and linting
python run_tests.py lint

# Fix formatting issues
python run_tests.py fix
```

#### Specific Tests
```bash
# Run specific test file
python run_tests.py specific --test-path tests/unit/test_auth.py

# Run specific test function
python run_tests.py specific --test-path tests/unit/test_auth.py::test_create_user
```

#### Test Reports
```bash
# Generate comprehensive test reports
python run_tests.py report
```

### Direct pytest Commands

```bash
# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test markers
pytest -m "unit"
pytest -m "integration"
pytest -m "security"

# Run tests in parallel
pytest -n auto

# Stop on first failure
pytest -x
```

## Test Types

### 1. Unit Tests

**Purpose**: Test individual components in isolation

**Coverage**:
- Authentication service
- Database models
- Utility functions
- Service classes

**Example**:
```python
def test_create_user():
    """Test user creation with valid data."""
    user_data = {
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "full_name": "Test User"
    }
    user = create_user(user_data)
    assert user.email == "test@example.com"
    assert user.is_verified is False
```

### 2. Integration Tests

**Purpose**: Test component interactions and system integration

**Coverage**:
- Database operations
- WebSocket connections
- External service integrations
- Multi-component workflows

**Example**:
```python
async def test_websocket_chat():
    """Test WebSocket chat functionality."""
    async with client.websocket_connect("/ws/meeting/123") as websocket:
        await websocket.send_json({"type": "chat", "message": "Hello"})
        data = await websocket.receive_json()
        assert data["type"] == "chat"
        assert data["message"] == "Hello"
```

### 3. API Tests

**Purpose**: Test REST API endpoints end-to-end

**Coverage**:
- Authentication endpoints
- Meeting management
- User management
- Error handling
- Security controls

**Example**:
```python
def test_create_meeting_api(authenticated_client):
    """Test meeting creation API endpoint."""
    response = authenticated_client.post(
        "/api/v1/meetings",
        json={
            "title": "Test Meeting",
            "description": "Test Description"
        }
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Test Meeting"
```

### 4. Performance Tests

**Purpose**: Test system performance and scalability

**Tools**: Locust for load testing

**Scenarios**:
- User registration load
- Concurrent logins
- Meeting creation stress
- WebSocket connections
- Database performance

**Running Performance Tests**:
```bash
# Start Locust
python run_tests.py performance

# Access web interface
open http://localhost:8089
```

**Configuration**:
- **Users**: Start with 10, scale to 1000+
- **Spawn Rate**: 10 users per second
- **Duration**: 5-10 minutes for initial tests

### 5. Security Tests

**Purpose**: Validate security controls and identify vulnerabilities

**Coverage**:
- Authentication bypass attempts
- Authorization checks
- Input validation
- SQL injection protection
- XSS prevention
- CSRF protection

## Postman Collections

### 1. Main API Collection

**File**: `postman/WorldClass_Video_Platform_API.postman_collection.json`

**Features**:
- Complete API endpoint coverage
- Automatic token management
- Environment variable usage
- Response validation
- Error handling tests

### 2. Automated Test Collection

**File**: `postman/Automated_Tests.postman_collection.json`

**Features**:
- End-to-end workflow testing
- Comprehensive assertions
- Data-driven testing
- Security validation
- Performance checks

### 3. Environment Files

**Local Development**: `postman/Local_Development.postman_environment.json`
**Production**: `postman/Production.postman_environment.json`

### Importing Collections

1. Open Postman
2. Click "Import"
3. Select collection files
4. Import environment files
5. Select appropriate environment

### Running Postman Tests

#### Manual Testing
1. Select environment (Local Development/Production)
2. Run individual requests
3. Check response validation
4. Review test results

#### Automated Testing
1. Use Collection Runner
2. Select "Automated Tests" collection
3. Choose environment
4. Configure iterations
5. Run collection
6. Review test report

#### Newman (CLI)
```bash
# Install Newman
npm install -g newman

# Run collection
newman run postman/Automated_Tests.postman_collection.json \
  -e postman/Local_Development.postman_environment.json \
  --reporters cli,json \
  --reporter-json-export test-results.json
```

## Performance Testing

### Locust Configuration

**File**: `backend/tests/performance/test_load.py`

### Test Scenarios

#### 1. Authentication Load
- User registration
- Login attempts
- Token refresh
- Profile updates

#### 2. Meeting Operations
- Meeting creation
- Joining meetings
- Participant management
- Meeting termination

#### 3. WebRTC Stress
- WebSocket connections
- Signaling messages
- Media negotiation
- Connection stability

### Performance Metrics

**Key Metrics**:
- Response time (95th percentile < 200ms)
- Throughput (requests per second)
- Error rate (< 1%)
- Resource utilization
- Concurrent connections

**Targets for 1B Users**:
- **Peak Concurrent Users**: 100M
- **Meetings per Second**: 10K
- **Messages per Second**: 1M
- **Uptime**: 99.99%

### Monitoring

```bash
# Monitor during load tests
docker stats
htop
netstat -an | grep ESTABLISHED | wc -l
```

## CI/CD Integration

### GitHub Actions

**File**: `.github/workflows/test.yml`

```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r backend/requirements.txt
      - name: Run tests
        run: |
          cd backend
          python run_tests.py all
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### Quality Gates

**Minimum Requirements**:
- Code coverage > 80%
- All tests pass
- No critical security issues
- Performance benchmarks met
- Code quality checks pass

### Integration Tests

```bash
# Run integration tests in CI
pytest tests/integration/ --tb=short
```

## Test Data Management

### Fixtures

**Purpose**: Provide consistent test data

**Location**: `backend/tests/conftest.py`

**Key Fixtures**:
- `test_db`: Clean database session
- `client`: Test client instance
- `authenticated_user`: User with valid token
- `sample_meeting`: Pre-created meeting
- `mock_email_service`: Email service mock

### Test Database

**Setup**:
```python
# Auto-managed by pytest
# Fresh database for each test
# Automatic cleanup
```

**Cleanup**:
```python
# Handled by fixtures
# No manual cleanup needed
```

### Mock Services

**External Services**:
- Email service (SMTP)
- SMS service (Twilio)
- File storage (S3)
- Cache (Redis)

**Configuration**:
```python
@pytest.fixture
def mock_email_service():
    with patch('app.services.email.EmailService') as mock:
        mock.send_verification_email.return_value = True
        yield mock
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```bash
# Check database status
docker-compose ps
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d
```

#### 2. Import Errors
```bash
# Check Python path
echo $PYTHONPATH

# Install in development mode
pip install -e .
```

#### 3. Test Failures
```bash
# Run with verbose output
pytest -v --tb=long

# Debug specific test
pytest -s tests/unit/test_auth.py::test_specific_function
```

#### 4. Performance Issues
```bash
# Check system resources
top
free -h
df -h

# Monitor test database
docker stats
```

### Debugging Tests

#### 1. Pytest Debugging
```python
# Add breakpoints
import pdb; pdb.set_trace()

# Use pytest debugging
pytest --pdb
```

#### 2. Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 3. Test Isolation
```bash
# Run single test
pytest tests/unit/test_auth.py::test_create_user -v

# Run without parallel execution
pytest -n 0
```

### Environment Issues

#### 1. Local Development
```bash
# Ensure services are running
docker-compose up -d

# Check service health
curl http://localhost:8000/health
```

#### 2. Test Environment
```bash
# Setup fresh environment
python run_tests.py setup

# Verify configuration
python -c "from app.core.config import settings; print(settings.DATABASE_URL)"
```

#### 3. Dependencies
```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Check for conflicts
pip check
```

## Best Practices

### 1. Test Design
- Write tests before implementation (TDD)
- Keep tests simple and focused
- Use descriptive test names
- Test both positive and negative cases
- Mock external dependencies

### 2. Test Maintenance
- Update tests with code changes
- Remove obsolete tests
- Refactor test code regularly
- Document complex test scenarios
- Review test coverage regularly

### 3. Performance Testing
- Start with baseline metrics
- Test incrementally
- Monitor resource usage
- Test realistic scenarios
- Document performance requirements

### 4. Security Testing
- Test authentication flows
- Validate authorization controls
- Test input validation
- Check for common vulnerabilities
- Regular security audits

## Continuous Improvement

### Metrics Tracking
- Test execution time
- Coverage trends
- Failure rates
- Performance benchmarks
- Security scan results

### Regular Reviews
- Weekly test suite health
- Monthly performance reviews
- Quarterly security audits
- Annual testing strategy review

### Tool Updates
- Keep testing frameworks updated
- Evaluate new testing tools
- Update CI/CD pipelines
- Enhance reporting capabilities

---

## Quick Reference

### Common Commands
```bash
# Full test suite
python run_tests.py all

# Quick smoke test
python run_tests.py unit --quiet

# Performance test
python run_tests.py performance

# Code quality
python run_tests.py lint

# Generate reports
python run_tests.py report
```

### File Locations
- Test runner: `backend/run_tests.py`
- Test configuration: `backend/pyproject.toml`
- Test fixtures: `backend/tests/conftest.py`
- Postman collections: `postman/`
- Performance tests: `backend/tests/performance/`

### Key Metrics
- **Coverage Target**: > 80%
- **Response Time**: < 200ms (95th percentile)
- **Error Rate**: < 1%
- **Uptime**: 99.99%