#!/usr/bin/env node

/**
 * Newman Test Runner for WorldClass Video Platform
 * Automates Postman collection testing with comprehensive reporting
 */

const newman = require('newman');
const fs = require('fs');
const path = require('path');

// Configuration
const config = {
    collections: {
        api: path.join(__dirname, 'WorldClass_Video_Platform_API.postman_collection.json'),
        automated: path.join(__dirname, 'Automated_Tests.postman_collection.json')
    },
    environments: {
        local: path.join(__dirname, 'Local_Development.postman_environment.json'),
        production: path.join(__dirname, 'Production.postman_environment.json')
    },
    reports: {
        dir: path.join(__dirname, 'reports'),
        html: path.join(__dirname, 'reports', 'newman-report.html'),
        json: path.join(__dirname, 'reports', 'newman-report.json'),
        junit: path.join(__dirname, 'reports', 'newman-junit.xml')
    }
};

// Ensure reports directory exists
if (!fs.existsSync(config.reports.dir)) {
    fs.mkdirSync(config.reports.dir, { recursive: true });
}

/**
 * Run Newman collection with comprehensive reporting
 */
function runCollection(collectionPath, environmentPath, options = {}) {
    return new Promise((resolve, reject) => {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const reportPrefix = options.reportPrefix || 'newman';
        
        const newmanOptions = {
            collection: collectionPath,
            environment: environmentPath,
            reporters: ['cli', 'html', 'json', 'junit'],
            reporter: {
                html: {
                    export: path.join(config.reports.dir, `${reportPrefix}-${timestamp}.html`)
                },
                json: {
                    export: path.join(config.reports.dir, `${reportPrefix}-${timestamp}.json`)
                },
                junit: {
                    export: path.join(config.reports.dir, `${reportPrefix}-${timestamp}.xml`)
                }
            },
            iterationCount: options.iterations || 1,
            delayRequest: options.delay || 100,
            timeout: options.timeout || 30000,
            insecure: true,
            ...options.newmanOptions
        };

        console.log(`\n🚀 Running collection: ${path.basename(collectionPath)}`);
        console.log(`📁 Environment: ${path.basename(environmentPath)}`);
        console.log(`📊 Reports will be saved to: ${config.reports.dir}\n`);

        newman.run(newmanOptions, (err, summary) => {
            if (err) {
                reject(err);
                return;
            }

            console.log('\n📈 Test Summary:');
            console.log(`Total Requests: ${summary.run.stats.requests.total}`);
            console.log(`Passed: ${summary.run.stats.requests.total - summary.run.stats.requests.failed}`);
            console.log(`Failed: ${summary.run.stats.requests.failed}`);
            console.log(`Total Assertions: ${summary.run.stats.assertions.total}`);
            console.log(`Assertion Failures: ${summary.run.stats.assertions.failed}`);

            if (summary.run.stats.requests.failed > 0 || summary.run.stats.assertions.failed > 0) {
                console.log('\n❌ Some tests failed!');
                console.log('\nFailures:');
                
                summary.run.failures.forEach((failure, index) => {
                    console.log(`${index + 1}. ${failure.source.name || 'Unknown'}`);
                    console.log(`   Error: ${failure.error.message}`);
                    console.log(`   Test: ${failure.error.test}\n`);
                });
            } else {
                console.log('\n✅ All tests passed!');
            }

            resolve(summary);
        });
    });
}

/**
 * Run health check before main tests
 */
async function healthCheck(environmentPath) {
    console.log('🏥 Running health check...');
    
    try {
        const healthCollection = {
            info: {
                name: 'Health Check',
                schema: 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'
            },
            item: [{
                name: 'Health Check',
                request: {
                    method: 'GET',
                    header: [],
                    url: {
                        raw: '{{baseUrl}}/health',
                        host: ['{{baseUrl}}'],
                        path: ['health']
                    }
                },
                event: [{
                    listen: 'test',
                    script: {
                        exec: [
                            'pm.test("Server is healthy", function () {',
                            '    pm.response.to.have.status(200);',
                            '});'
                        ]
                    }
                }]
            }]
        };

        const tempCollection = path.join(config.reports.dir, 'health-check.json');
        fs.writeFileSync(tempCollection, JSON.stringify(healthCollection, null, 2));

        const summary = await runCollection(tempCollection, environmentPath, {
            reportPrefix: 'health-check',
            timeout: 5000
        });

        // Clean up temp file
        fs.unlinkSync(tempCollection);

        if (summary.run.stats.requests.failed > 0) {
            throw new Error('Health check failed - server is not responding correctly');
        }

        console.log('✅ Health check passed!\n');
        return true;
    } catch (error) {
        console.error('❌ Health check failed:', error.message);
        return false;
    }
}

/**
 * Main execution function
 */
async function main() {
    const args = process.argv.slice(2);
    const environment = args.includes('--prod') ? 'production' : 'local';
    const skipHealthCheck = args.includes('--skip-health');
    const apiOnly = args.includes('--api-only');
    const automatedOnly = args.includes('--automated-only');
    const iterations = parseInt(args.find(arg => arg.startsWith('--iterations='))?.split('=')[1]) || 1;
    const delay = parseInt(args.find(arg => arg.startsWith('--delay='))?.split('=')[1]) || 100;

    console.log('🎯 WorldClass Video Platform - API Test Suite');
    console.log('=' .repeat(50));
    console.log(`Environment: ${environment}`);
    console.log(`Iterations: ${iterations}`);
    console.log(`Request Delay: ${delay}ms`);
    console.log('=' .repeat(50));

    const environmentPath = config.environments[environment];

    try {
        // Health check
        if (!skipHealthCheck) {
            const isHealthy = await healthCheck(environmentPath);
            if (!isHealthy) {
                console.error('\n❌ Aborting tests due to failed health check');
                process.exit(1);
            }
        }

        const results = [];

        // Run API collection
        if (!automatedOnly) {
            console.log('📡 Running API Collection Tests...');
            const apiResult = await runCollection(
                config.collections.api,
                environmentPath,
                {
                    reportPrefix: 'api-collection',
                    iterations,
                    delay,
                    timeout: 30000
                }
            );
            results.push({ name: 'API Collection', result: apiResult });
        }

        // Run automated tests collection
        if (!apiOnly) {
            console.log('\n🤖 Running Automated Test Suite...');
            const automatedResult = await runCollection(
                config.collections.automated,
                environmentPath,
                {
                    reportPrefix: 'automated-tests',
                    iterations,
                    delay,
                    timeout: 60000
                }
            );
            results.push({ name: 'Automated Tests', result: automatedResult });
        }

        // Summary report
        console.log('\n' + '=' .repeat(50));
        console.log('📊 FINAL TEST SUMMARY');
        console.log('=' .repeat(50));

        let totalRequests = 0;
        let totalFailures = 0;
        let totalAssertions = 0;
        let totalAssertionFailures = 0;

        results.forEach(({ name, result }) => {
            console.log(`\n${name}:`);
            console.log(`  Requests: ${result.run.stats.requests.total} (${result.run.stats.requests.failed} failed)`);
            console.log(`  Assertions: ${result.run.stats.assertions.total} (${result.run.stats.assertions.failed} failed)`);
            
            totalRequests += result.run.stats.requests.total;
            totalFailures += result.run.stats.requests.failed;
            totalAssertions += result.run.stats.assertions.total;
            totalAssertionFailures += result.run.stats.assertions.failed;
        });

        console.log('\nOverall:');
        console.log(`  Total Requests: ${totalRequests} (${totalFailures} failed)`);
        console.log(`  Total Assertions: ${totalAssertions} (${totalAssertionFailures} failed)`);
        console.log(`  Success Rate: ${((totalRequests - totalFailures) / totalRequests * 100).toFixed(2)}%`);

        if (totalFailures > 0 || totalAssertionFailures > 0) {
            console.log('\n❌ Some tests failed! Check the detailed reports for more information.');
            process.exit(1);
        } else {
            console.log('\n✅ All tests passed successfully!');
        }

        console.log(`\n📁 Detailed reports saved to: ${config.reports.dir}`);
        console.log('=' .repeat(50));

    } catch (error) {
        console.error('\n💥 Test execution failed:', error.message);
        console.error(error.stack);
        process.exit(1);
    }
}

/**
 * Print usage information
 */
function printUsage() {
    console.log('Usage: node run-postman-tests.js [options]');
    console.log('');
    console.log('Options:');
    console.log('  --prod              Use production environment (default: local)');
    console.log('  --api-only          Run only API collection tests');
    console.log('  --automated-only    Run only automated test suite');
    console.log('  --skip-health       Skip health check before running tests');
    console.log('  --iterations=N      Number of test iterations (default: 1)');
    console.log('  --delay=N           Delay between requests in ms (default: 100)');
    console.log('  --help              Show this help message');
    console.log('');
    console.log('Examples:');
    console.log('  node run-postman-tests.js                    # Run all tests on local environment');
    console.log('  node run-postman-tests.js --prod             # Run all tests on production');
    console.log('  node run-postman-tests.js --api-only         # Run only API collection');
    console.log('  node run-postman-tests.js --iterations=5     # Run tests 5 times');
    console.log('  node run-postman-tests.js --delay=500        # 500ms delay between requests');
}

// Check for help flag or run main function
if (process.argv.includes('--help') || process.argv.includes('-h')) {
    printUsage();
} else {
    main().catch(error => {
        console.error('Unhandled error:', error);
        process.exit(1);
    });
}