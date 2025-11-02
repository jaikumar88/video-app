# Postman API Testing Suite

## Overview

This directory contains comprehensive Postman collections and automated testing tools for the WorldClass Video Platform API. The testing suite includes manual testing collections, automated test scripts, and performance validation tools.

## Contents

```
postman/
├── WorldClass_Video_Platform_API.postman_collection.json     # Main API collection
├── Automated_Tests.postman_collection.json                   # Automated test suite
├── Local_Development.postman_environment.json                # Local environment
├── Production.postman_environment.json                       # Production environment
├── run-postman-tests.js                                      # Automated test runner
├── package.json                                              # Node.js dependencies
├── reports/                                                  # Generated test reports
└── README.md                                                 # This file
```

## Quick Start

### 1. Prerequisites

**Node.js & npm** (for automated testing):
```bash
# Install Node.js 14+ and npm 6+
node --version
npm --version
```

**Postman** (for manual testing):
- Download from: https://www.postman.com/downloads/
- Or use Postman web app

### 2. Setup

**Install Newman (command-line runner)**:
```bash
cd postman
npm install
npm run install-newman
```

**Import Collections in Postman**:
1. Open Postman
2. Click "Import"
3. Select all `.json` files from this directory
4. Choose "Local Development" environment

### 3. Running Tests

**Automated Testing (Newman)**:
```bash
# Run all tests on local environment
npm test

# Run on production
npm run test:prod

# Run specific test types
npm run test:api        # API collection only
npm run test:automated  # Automated tests only

# Load testing
npm run test:load       # 10 iterations with reduced delay

# Smoke testing
npm run test:smoke      # Quick API validation
```

**Manual Testing (Postman)**:
1. Select environment (Local Development/Production)
2. Run individual requests or entire collections
3. Review test results in Postman interface

## Collections

### 1. WorldClass Video Platform API

**Purpose**: Complete API reference and manual testing

**Features**:
- All API endpoints organized by functionality
- Environment variable usage
- Automatic token management
- Response validation
- Comprehensive documentation

**Folders**:
- **Authentication**: User registration, login, verification
- **Meetings**: Meeting management and video calling
- **WebRTC Signaling**: Video call setup and signaling
- **Health & Monitoring**: System health checks
- **Admin**: Administrative functions

### 2. Automated Tests

**Purpose**: Comprehensive automated testing workflows

**Features**:
- End-to-end test scenarios
- Data-driven testing
- Automatic cleanup
- Security validation
- Performance checks

**Test Flows**:
1. **Setup Tests**: Health checks and prerequisites
2. **Authentication Flow**: Complete user registration and login
3. **Meeting Flow**: Create, join, manage, and end meetings
4. **WebRTC Tests**: Signaling and connection validation
5. **Security Tests**: Authorization and vulnerability checks

## Environments

### Local Development

**Base URL**: `http://localhost:8000`

**Pre-configured Variables**:
- `baseUrl`: Local server endpoint
- `testEmail`: Default test user email
- `testPhone`: Default test phone number
- `testPassword`: Default test password
- Token variables (auto-populated)

### Production

**Base URL**: `https://your-domain.com` (update as needed)

**Security Notes**:
- Use real credentials (not default test values)
- Tokens are marked as secret variables
- Never commit production credentials

## Test Automation

### Newman Runner

The `run-postman-tests.js` script provides comprehensive test automation:

**Features**:
- Health check validation
- Multiple collection execution
- Comprehensive reporting
- Error handling and recovery
- Configurable test parameters

**Command Options**:
```bash
# Environment selection
--prod                    # Use production environment

# Test selection
--api-only               # Run only API collection
--automated-only         # Run only automated tests

# Configuration
--iterations=N           # Number of test iterations
--delay=N               # Delay between requests (ms)
--skip-health           # Skip health check

# Help
--help                  # Show usage information
```

**Examples**:
```bash
# Standard local testing
node run-postman-tests.js

# Production validation
node run-postman-tests.js --prod

# Load testing
node run-postman-tests.js --iterations=50 --delay=100

# Quick smoke test
node run-postman-tests.js --api-only --skip-health
```

### Reporting

**Report Types**:
- **CLI Output**: Real-time console feedback
- **HTML Report**: Detailed visual report
- **JSON Report**: Machine-readable results
- **JUnit XML**: CI/CD integration format

**Report Location**: `./reports/`

**Report Files**:
- `newman-[timestamp].html`: Visual test report
- `newman-[timestamp].json`: Detailed JSON results
- `newman-[timestamp].xml`: JUnit XML for CI/CD

## Test Data Management

### Environment Variables

**Authentication**:
- `accessToken`: JWT access token (auto-managed)
- `refreshToken`: JWT refresh token (auto-managed)
- `userId`: Current user ID (auto-populated)

**Test Data**:
- `testEmail`: Generated unique email for tests
- `testPhone`: Test phone number
- `testPassword`: Secure test password

**Meeting Data**:
- `meetingId`: Current meeting ID (auto-populated)
- `scheduledTime`: Future meeting time (auto-generated)

### Dynamic Data Generation

The automated tests include pre-request scripts that generate unique test data:

```javascript
// Generate unique test user
const timestamp = Date.now();
const randomId = Math.floor(Math.random() * 1000);
const testEmail = `test.user.${timestamp}.${randomId}@example.com`;
pm.environment.set('testEmail', testEmail);
```

## Test Scenarios

### 1. User Registration Flow

**Steps**:
1. Generate unique user data
2. Register new user
3. Verify email (mock verification)
4. Login with credentials
5. Validate user profile
6. Update profile information

**Validations**:
- Registration success (201 status)
- Email uniqueness
- Password security requirements
- Token generation and format
- Profile data consistency

### 2. Meeting Management Flow

**Steps**:
1. Create new meeting
2. Validate meeting details
3. Join meeting as host
4. Generate invitation link
5. Get participant list
6. End meeting

**Validations**:
- Meeting creation permissions
- Participant management
- Meeting state transitions
- Authorization controls
- Data integrity

### 3. WebRTC Signaling Flow

**Steps**:
1. Get ICE server configuration
2. Send WebRTC offer
3. Receive and send answer
4. Exchange ICE candidates
5. Validate connection state

**Validations**:
- ICE server availability
- Signaling message format
- Real-time communication
- Connection stability

### 4. Security Validation

**Tests**:
- Unauthorized access attempts
- Invalid token handling
- SQL injection prevention
- XSS protection
- CSRF validation
- Rate limiting

**Expected Results**:
- Proper error responses (401, 403)
- Security headers present
- Input sanitization
- Session management

## Performance Testing

### Load Testing with Newman

**Configuration**:
```bash
# Moderate load testing
npm run test:load

# Heavy load testing
node run-postman-tests.js --iterations=100 --delay=50

# Stress testing
node run-postman-tests.js --iterations=500 --delay=10
```

**Metrics Tracked**:
- Response times
- Success/failure rates
- Throughput (requests/second)
- Error patterns
- Resource utilization

### Performance Benchmarks

**Target Metrics**:
- Average response time: < 200ms
- 95th percentile: < 500ms
- Error rate: < 1%
- Concurrent users: 1000+

**Load Testing Scenarios**:
1. **Authentication Load**: Concurrent registrations and logins
2. **Meeting Creation**: Rapid meeting creation and management
3. **API Throughput**: High-frequency API calls
4. **WebRTC Signaling**: Multiple simultaneous connections

## CI/CD Integration

### GitHub Actions

**Example workflow** (`.github/workflows/api-tests.yml`):
```yaml
name: API Tests
on: [push, pull_request]

jobs:
  api-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '16'
      - name: Install dependencies
        run: |
          cd postman
          npm install
      - name: Run API tests
        run: |
          cd postman
          npm test
      - name: Upload test reports
        uses: actions/upload-artifact@v2
        with:
          name: postman-reports
          path: postman/reports/
```

### Jenkins Integration

**Jenkinsfile example**:
```groovy
pipeline {
    agent any
    stages {
        stage('API Tests') {
            steps {
                dir('postman') {
                    sh 'npm install'
                    sh 'npm test'
                }
            }
            post {
                always {
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'postman/reports',
                        reportFiles: '*.html',
                        reportName: 'Postman Test Report'
                    ])
                }
            }
        }
    }
}
```

## Troubleshooting

### Common Issues

#### 1. Connection Refused
```bash
# Check if server is running
curl http://localhost:8000/health

# Start local development server
cd ../backend
docker-compose up -d
```

#### 2. Authentication Failures
```bash
# Clear environment variables
# Re-run authentication flow
# Check token expiration
```

#### 3. Newman Installation Issues
```bash
# Install Newman globally
npm install -g newman

# Or use npx
npx newman run collection.json
```

#### 4. Environment Variable Issues
```bash
# Verify environment file import
# Check variable names and values
# Ensure proper environment selection in Postman
```

### Debugging

#### 1. Enable Verbose Logging
```bash
# Newman verbose output
newman run collection.json --verbose

# Custom debug logging in tests
console.log('Debug info:', pm.variables.get('variable'));
```

#### 2. Postman Console
- Open Postman Console (View → Show Postman Console)
- Run requests manually
- Review console logs and network requests

#### 3. Test Script Debugging
```javascript
// Add debug outputs in test scripts
console.log('Response:', pm.response.json());
console.log('Environment:', pm.environment.toObject());
```

## Best Practices

### 1. Test Design
- Use descriptive test names
- Include both positive and negative test cases
- Test edge cases and error conditions
- Validate response structure and data
- Use appropriate HTTP status code checks

### 2. Data Management
- Generate unique test data
- Clean up test data after tests
- Use environment variables for configuration
- Separate test and production data
- Mock external dependencies

### 3. Security
- Never commit sensitive credentials
- Use secret variables for tokens
- Rotate test credentials regularly
- Test authentication and authorization
- Validate input sanitization

### 4. Maintenance
- Keep collections updated with API changes
- Review and update test assertions
- Monitor test execution times
- Clean up obsolete tests
- Document test scenarios

## Advanced Usage

### Custom Reporters

**Install additional reporters**:
```bash
npm install newman-reporter-influxdb
npm install newman-reporter-slack
```

**Use custom reporters**:
```bash
newman run collection.json \
  --reporters cli,html,influxdb \
  --reporter-influxdb-server http://localhost:8086
```

### Data-Driven Testing

**Using CSV data files**:
```bash
newman run collection.json \
  --data test-data.csv \
  --iteration-count 10
```

**CSV format example** (`test-data.csv`):
```csv
email,password,full_name
user1@test.com,Password123!,User One
user2@test.com,Password456!,User Two
```

### Advanced Scripting

**Pre-request script example**:
```javascript
// Generate test data
pm.globals.set('timestamp', Date.now());
pm.globals.set('random', Math.floor(Math.random() * 1000));

// Custom authentication
if (!pm.environment.get('accessToken')) {
    // Trigger authentication flow
    pm.sendRequest({
        url: pm.environment.get('baseUrl') + '/api/v1/auth/login',
        method: 'POST',
        header: { 'Content-Type': 'application/json' },
        body: {
            mode: 'raw',
            raw: JSON.stringify({
                username: pm.environment.get('testEmail'),
                password: pm.environment.get('testPassword')
            })
        }
    }, (err, response) => {
        if (!err) {
            const data = response.json();
            pm.environment.set('accessToken', data.access_token);
        }
    });
}
```

**Test script example**:
```javascript
// Advanced response validation
pm.test('Response schema validation', function () {
    const schema = {
        type: 'object',
        properties: {
            id: { type: 'string' },
            title: { type: 'string' },
            status: { type: 'string', enum: ['waiting', 'active', 'ended'] }
        },
        required: ['id', 'title', 'status']
    };
    
    pm.response.to.have.jsonSchema(schema);
});

// Performance validation
pm.test('Response time is acceptable', function () {
    pm.expect(pm.response.responseTime).to.be.below(1000);
});

// Data consistency checks
pm.test('Data relationships are consistent', function () {
    const response = pm.response.json();
    pm.expect(response.host_id).to.equal(pm.environment.get('userId'));
});
```

---

## Support

For questions or issues with the Postman testing suite:

1. Check the troubleshooting section above
2. Review the main project documentation
3. Open an issue in the project repository
4. Contact the development team

## Contributing

When adding new API endpoints or modifying existing ones:

1. Update the main API collection
2. Add corresponding automated tests
3. Update environment variables if needed
4. Test both positive and negative scenarios
5. Update documentation