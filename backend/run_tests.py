#!/usr/bin/env python3
"""
Test runner script for WorldClass Video Platform
Provides convenient commands for running different types of tests
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, cwd=None):
    """Run a shell command and return the result."""
    print(f"Running: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        if result.stderr:
            print(f"Warnings: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False


def setup_test_environment():
    """Setup test environment and dependencies."""
    backend_dir = Path(__file__).parent
    
    print("Setting up test environment...")
    
    # Install test dependencies
    if not run_command("pip install -r requirements.txt", cwd=backend_dir):
        return False
    
    # Create test database
    if not run_command("python -c \"from app.core.database import create_tables; import asyncio; asyncio.run(create_tables())\"", cwd=backend_dir):
        print("Warning: Could not create test database")
    
    return True


def run_unit_tests(coverage=True, verbose=True):
    """Run unit tests."""
    backend_dir = Path(__file__).parent
    
    cmd = "python -m pytest tests/unit"
    
    if coverage:
        cmd += " --cov=app --cov-report=html --cov-report=term-missing"
    
    if verbose:
        cmd += " -v"
    
    cmd += " --tb=short"
    
    return run_command(cmd, cwd=backend_dir)


def run_integration_tests(verbose=True):
    """Run integration tests."""
    backend_dir = Path(__file__).parent
    
    cmd = "python -m pytest tests/integration"
    
    if verbose:
        cmd += " -v"
    
    cmd += " --tb=short"
    
    return run_command(cmd, cwd=backend_dir)


def run_api_tests(verbose=True):
    """Run API tests."""
    backend_dir = Path(__file__).parent
    
    cmd = "python -m pytest tests/api"
    
    if verbose:
        cmd += " -v"
    
    cmd += " --tb=short"
    
    return run_command(cmd, cwd=backend_dir)


def run_all_tests(coverage=True, verbose=True):
    """Run all tests."""
    backend_dir = Path(__file__).parent
    
    cmd = "python -m pytest"
    
    if coverage:
        cmd += " --cov=app --cov-report=html --cov-report=term-missing"
    
    if verbose:
        cmd += " -v"
    
    cmd += " --tb=short"
    
    return run_command(cmd, cwd=backend_dir)


def run_performance_tests():
    """Run performance tests with Locust."""
    backend_dir = Path(__file__).parent
    
    print("Starting performance tests...")
    print("Make sure the server is running on http://localhost:8000")
    print("Access Locust web UI at http://localhost:8089")
    
    cmd = "locust -f tests/performance/test_load.py --host=http://localhost:8000"
    
    return run_command(cmd, cwd=backend_dir)


def run_security_tests():
    """Run security tests."""
    backend_dir = Path(__file__).parent
    
    cmd = "python -m pytest -m security -v"
    
    return run_command(cmd, cwd=backend_dir)


def run_linting():
    """Run code linting."""
    backend_dir = Path(__file__).parent
    
    print("Running code quality checks...")
    
    # Black formatting check
    print("\n=== Black (formatting) ===")
    if not run_command("black --check --diff app tests", cwd=backend_dir):
        print("Code formatting issues found. Run 'black app tests' to fix.")
    
    # isort import sorting check
    print("\n=== isort (import sorting) ===")
    if not run_command("isort --check-only --diff app tests", cwd=backend_dir):
        print("Import sorting issues found. Run 'isort app tests' to fix.")
    
    # flake8 linting
    print("\n=== flake8 (linting) ===")
    run_command("flake8 app tests", cwd=backend_dir)
    
    # mypy type checking
    print("\n=== mypy (type checking) ===")
    run_command("mypy app", cwd=backend_dir)
    
    return True


def fix_formatting():
    """Fix code formatting issues."""
    backend_dir = Path(__file__).parent
    
    print("Fixing code formatting...")
    
    # Black formatting
    run_command("black app tests", cwd=backend_dir)
    
    # isort import sorting
    run_command("isort app tests", cwd=backend_dir)
    
    print("Code formatting fixed!")
    return True


def generate_test_report():
    """Generate comprehensive test report."""
    backend_dir = Path(__file__).parent
    
    print("Generating comprehensive test report...")
    
    # Run tests with detailed reporting
    cmd = (
        "python -m pytest "
        "--cov=app "
        "--cov-report=html:reports/coverage "
        "--cov-report=xml:reports/coverage.xml "
        "--junitxml=reports/junit.xml "
        "--html=reports/pytest_report.html "
        "--self-contained-html "
        "-v"
    )
    
    # Create reports directory
    reports_dir = backend_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    return run_command(cmd, cwd=backend_dir)


def run_specific_test(test_path):
    """Run a specific test file or test function."""
    backend_dir = Path(__file__).parent
    
    cmd = f"python -m pytest {test_path} -v"
    
    return run_command(cmd, cwd=backend_dir)


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="WorldClass Video Platform Test Runner")
    
    parser.add_argument(
        "command",
        choices=[
            "setup", "unit", "integration", "api", "all", "performance", 
            "security", "lint", "fix", "report", "specific"
        ],
        help="Test command to run"
    )
    
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Skip coverage reporting"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Run tests in quiet mode"
    )
    
    parser.add_argument(
        "--test-path",
        help="Specific test path for 'specific' command"
    )
    
    args = parser.parse_args()
    
    coverage = not args.no_coverage
    verbose = not args.quiet
    
    success = True
    
    if args.command == "setup":
        success = setup_test_environment()
    elif args.command == "unit":
        success = run_unit_tests(coverage=coverage, verbose=verbose)
    elif args.command == "integration":
        success = run_integration_tests(verbose=verbose)
    elif args.command == "api":
        success = run_api_tests(verbose=verbose)
    elif args.command == "all":
        success = run_all_tests(coverage=coverage, verbose=verbose)
    elif args.command == "performance":
        success = run_performance_tests()
    elif args.command == "security":
        success = run_security_tests()
    elif args.command == "lint":
        success = run_linting()
    elif args.command == "fix":
        success = fix_formatting()
    elif args.command == "report":
        success = generate_test_report()
    elif args.command == "specific":
        if not args.test_path:
            print("Error: --test-path is required for 'specific' command")
            sys.exit(1)
        success = run_specific_test(args.test_path)
    
    if success:
        print(f"\n✅ {args.command.title()} completed successfully!")
    else:
        print(f"\n❌ {args.command.title()} failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()