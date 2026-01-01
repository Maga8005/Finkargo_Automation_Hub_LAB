#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW Test - AI Developer Workflow for agentic testing

Usage: 
  uv run adw_test.py <issue-number> [adw-id] [--skip-e2e]

Workflow:
1. Fetch GitHub issue details (if not in state)
2. Run application test suite
3. Report results to issue
4. Create commit with test results
5. Push and update PR

Environment Requirements:
- ANTHROPIC_API_KEY: Anthropic API key
- CLAUDE_CODE_PATH: Path to Claude CLI
- GITHUB_PAT: (Optional) GitHub Personal Access Token - only if using a different account than 'gh auth login'
"""

import json
import subprocess
import sys
import os
import logging
from typing import Tuple, Optional, List
from dotenv import load_dotenv
from adw_modules.data_types import (
    AgentTemplateRequest,
    GitHubIssue,
    AgentPromptResponse,
    TestResult,
    E2ETestResult,
    IssueClassSlashCommand,
)
from adw_modules.agent import execute_template
from adw_modules.github import (
    extract_repo_path,
    fetch_issue,
    make_issue_comment,
    get_repo_url,
)
from adw_modules.utils import make_adw_id, setup_logger, parse_json
from adw_modules.state import ADWState
from adw_modules.git_ops import commit_changes, finalize_git_operations
from adw_modules.workflow_ops import format_issue_message, create_commit, ensure_adw_id, classify_issue
# Removed create_or_find_branch - now using state directly

# Agent name constants
AGENT_TESTER = "test_runner"
AGENT_E2E_TESTER = "e2e_test_runner"
AGENT_API_TESTER = "api_integration_tester"
AGENT_STATIC_ANALYZER = "static_analyzer"  # Static analysis for semantic bugs
AGENT_BRANCH_GENERATOR = "branch_generator"

# Maximum number of test retry attempts after resolution
MAX_TEST_RETRY_ATTEMPTS = 4
MAX_E2E_TEST_RETRY_ATTEMPTS = 2  # E2E ui tests
MAX_API_TEST_RETRY_ATTEMPTS = 2  # API integration tests
MAX_STATIC_ANALYSIS_RETRY_ATTEMPTS = 2  # Static analysis retries

# API test configuration
API_TEST_BASE_URL = os.getenv("API_TEST_BASE_URL", "http://localhost:8000")
API_TEST_SERVER_TIMEOUT = 30  # seconds to wait for server startup


def check_env_vars(logger: Optional[logging.Logger] = None) -> None:
    """Check that all required environment variables are set.

    Note: ANTHROPIC_API_KEY is optional if using Claude Max subscription via OAuth.
    Run 'claude login' to authenticate with your Max subscription.
    """
    required_vars = [
        "CLAUDE_CODE_PATH",
    ]
    optional_vars = [
        "ANTHROPIC_API_KEY",  # Optional if using Claude Max via OAuth
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        error_msg = "Error: Missing required environment variables:"
        if logger:
            logger.error(error_msg)
            for var in missing_vars:
                logger.error(f"  - {var}")
        else:
            print(error_msg, file=sys.stderr)
            for var in missing_vars:
                print(f"  - {var}", file=sys.stderr)
        sys.exit(1)

    # Warn about optional vars that could improve functionality
    if not os.getenv("ANTHROPIC_API_KEY"):
        warn_msg = "Note: ANTHROPIC_API_KEY not set. Using Claude Max subscription via OAuth."
        if logger:
            logger.info(warn_msg)
        else:
            print(warn_msg)


def parse_args(
    state: Optional[ADWState] = None,
    logger: Optional[logging.Logger] = None,
) -> Tuple[Optional[str], Optional[str], bool, bool]:
    """Parse command line arguments.
    Returns (issue_number, adw_id, skip_e2e, skip_api) where issue_number and adw_id may be None."""
    skip_e2e = False
    skip_api = False

    # Check for --skip-e2e flag in args
    if "--skip-e2e" in sys.argv:
        skip_e2e = True
        sys.argv.remove("--skip-e2e")

    # Check for --skip-api flag in args
    if "--skip-api" in sys.argv:
        skip_api = True
        sys.argv.remove("--skip-api")

    # If we have state from stdin, we might not need issue number from args
    if state:
        # In piped mode, we might have no args at all
        if len(sys.argv) >= 2:
            # If an issue number is provided, use it
            return sys.argv[1], None, skip_e2e, skip_api
        else:
            # Otherwise, we'll get issue from state
            return None, None, skip_e2e, skip_api

    # Standalone mode - need at least issue number
    if len(sys.argv) < 2:
        usage_msg = [
            "Usage:",
            "  Standalone: uv run adw_test.py <issue-number> [adw-id] [--skip-e2e] [--skip-api]",
            "  Chained: ... | uv run adw_test.py [--skip-e2e] [--skip-api]",
            "Examples:",
            "  uv run adw_test.py 123",
            "  uv run adw_test.py 123 abc12345",
            "  uv run adw_test.py 123 --skip-e2e",
            "  uv run adw_test.py 123 --skip-api",
            "  echo '{\"issue_number\": \"123\"}' | uv run adw_test.py",
        ]
        if logger:
            for msg in usage_msg:
                logger.error(msg)
        else:
            for msg in usage_msg:
                print(msg)
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    return issue_number, adw_id, skip_e2e, skip_api


def git_branch(
    issue: GitHubIssue,
    issue_class: IssueClassSlashCommand,
    adw_id: str,
    logger: logging.Logger,
) -> Tuple[Optional[str], Optional[str]]:
    """Generate and create a git branch for the issue.
    Returns (branch_name, error_message) tuple."""
    # Remove the leading slash from issue_class for the branch name
    issue_type = issue_class.replace("/", "")

    request = AgentTemplateRequest(
        agent_name=AGENT_BRANCH_GENERATOR,
        slash_command="/generate_branch_name",
        args=[issue_type, adw_id, issue.model_dump_json(by_alias=True)],
        adw_id=adw_id,
        model="opus",
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    branch_name = response.output.strip()
    logger.info(f"Created branch: {branch_name}")
    return branch_name, None


# Removed duplicate git_commit function - now using create_commit from workflow_ops


# Removed duplicate pull_request function - now using finalize_git_operations from git_ops


def format_issue_message(
    adw_id: str, agent_name: str, message: str, session_id: Optional[str] = None
) -> str:
    """Format a message for issue comments with ADW tracking."""
    if session_id:
        return f"{adw_id}_{agent_name}_{session_id}: {message}"
    return f"{adw_id}_{agent_name}: {message}"


def log_test_results(
    state: ADWState,
    static_results: List[TestResult],
    results: List[TestResult],
    e2e_results: List[E2ETestResult],
    logger: logging.Logger
) -> None:
    """Log comprehensive test results summary to the issue."""
    issue_number = state.get("issue_number")
    adw_id = state.get("adw_id")

    if not issue_number:
        logger.warning("No issue number in state, skipping test results logging")
        return

    # Calculate counts
    static_passed = sum(1 for r in static_results if r.passed)
    static_failed = len(static_results) - static_passed
    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count
    e2e_passed_count = sum(1 for r in e2e_results if r.passed)
    e2e_failed_count = len(e2e_results) - e2e_passed_count

    # Create comprehensive summary
    summary = f"## 📊 Test Run Summary\n\n"

    # Static analysis summary
    if static_results:
        summary += f"### Static Analysis\n"
        summary += f"**Total Checks:** {len(static_results)}\n"
        summary += f"**Passed:** {static_passed} ✅\n"
        summary += f"**Failed:** {static_failed} ❌\n\n"

        if static_failed > 0:
            summary += "#### Failed Checks:\n"
            for result in static_results:
                if not result.passed:
                    summary += f"- ❌ **{result.test_name}**\n"
                    if result.error:
                        summary += f"  - Error: {result.error[:200]}...\n"

    # Unit tests summary
    summary += f"### Unit Tests\n"
    summary += f"**Total Tests:** {len(results)}\n"
    summary += f"**Passed:** {passed_count} ✅\n"
    summary += f"**Failed:** {failed_count} ❌\n\n"

    if results:
        summary += "#### Details:\n"
        for result in results:
            status = "✅" if result.passed else "❌"
            summary += f"- {status} **{result.test_name}**\n"
            if not result.passed and result.error:
                summary += f"  - Error: {result.error[:200]}...\n"

    # E2E tests summary if they were run
    if e2e_results:
        summary += f"\n### E2E Tests\n"
        summary += f"**Total Tests:** {len(e2e_results)}\n"
        summary += f"**Passed:** {e2e_passed_count} ✅\n"
        summary += f"**Failed:** {e2e_failed_count} ❌\n\n"

        summary += "#### Details:\n"
        for result in e2e_results:
            status = "✅" if result.passed else "❌"
            summary += f"- {status} **{result.test_name}**\n"
            if not result.passed and result.error:
                summary += f"  - Error: {result.error[:200]}...\n"
            if result.screenshots:
                summary += f"  - Screenshots: {', '.join(result.screenshots)}\n"

    # Overall status
    total_failures = static_failed + failed_count + e2e_failed_count
    if total_failures > 0:
        summary += f"\n### ❌ Overall Status: FAILED\n"
        summary += f"Total failures: {total_failures}\n"
    else:
        total_tests = len(static_results) + len(results) + len(e2e_results)
        summary += f"\n### ✅ Overall Status: PASSED\n"
        summary += f"All {total_tests} tests passed successfully!\n"

    # Post the summary to the issue
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "test_summary", summary)
    )

    logger.info(f"Posted comprehensive test results summary to issue #{issue_number}")


def run_tests(adw_id: str, logger: logging.Logger) -> AgentPromptResponse:
    """Run the test suite using the /test command."""
    test_template_request = AgentTemplateRequest(
        agent_name=AGENT_TESTER,
        slash_command="/test",
        args=[],
        adw_id=adw_id,
        model="opus",
    )

    logger.debug(
        f"test_template_request: {test_template_request.model_dump_json(indent=2, by_alias=True)}"
    )

    test_response = execute_template(test_template_request)

    logger.debug(
        f"test_response: {test_response.model_dump_json(indent=2, by_alias=True)}"
    )

    return test_response


def parse_test_results(
    output: str, logger: logging.Logger
) -> Tuple[List[TestResult], int, int]:
    """Parse test results JSON and return (results, passed_count, failed_count)."""
    try:
        # Use parse_json to handle markdown-wrapped JSON
        results = parse_json(output, List[TestResult])

        passed_count = sum(1 for test in results if test.passed)
        failed_count = len(results) - passed_count

        return results, passed_count, failed_count
    except Exception as e:
        logger.error(f"Error parsing test results: {e}")
        return [], 0, 0


def format_test_results_comment(
    results: List[TestResult], passed_count: int, failed_count: int
) -> str:
    """Format test results for GitHub issue comment with JSON blocks."""
    if not results:
        return "❌ No test results found"

    # Separate failed and passed tests
    failed_tests = [test for test in results if not test.passed]
    passed_tests = [test for test in results if test.passed]

    # Build comment
    comment_parts = []

    # Failed tests header
    if failed_tests:
        comment_parts.append("")
        comment_parts.append("## ❌ Failed Tests")
        comment_parts.append("")

        # Loop over each failed test
        for test in failed_tests:
            comment_parts.append(f"### {test.test_name}")
            comment_parts.append("")
            comment_parts.append("```json")
            comment_parts.append(json.dumps(test.model_dump(), indent=2))
            comment_parts.append("```")
            comment_parts.append("")

    # Passed tests header
    if passed_tests:
        comment_parts.append("## ✅ Passed Tests")
        comment_parts.append("")

        # Loop over each passed test
        for test in passed_tests:
            comment_parts.append(f"### {test.test_name}")
            comment_parts.append("")
            comment_parts.append("```json")
            comment_parts.append(json.dumps(test.model_dump(), indent=2))
            comment_parts.append("```")
            comment_parts.append("")

    # Remove trailing empty line
    if comment_parts and comment_parts[-1] == "":
        comment_parts.pop()

    return "\n".join(comment_parts)


def resolve_failed_tests(
    failed_tests: List[TestResult],
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    iteration: int = 1,
) -> Tuple[int, int]:
    """
    Attempt to resolve failed tests using the resolve_failed_test command.
    Returns (resolved_count, unresolved_count).
    """
    resolved_count = 0
    unresolved_count = 0

    for idx, test in enumerate(failed_tests):
        logger.info(
            f"\n=== Resolving failed test {idx + 1}/{len(failed_tests)}: {test.test_name} ==="
        )

        # Create payload for the resolve command
        test_payload = test.model_dump_json(indent=2)

        # Create agent name with iteration
        agent_name = f"test_resolver_iter{iteration}_{idx}"

        # Create template request
        resolve_request = AgentTemplateRequest(
            agent_name=agent_name,
            slash_command="/resolve_failed_test",
            args=[test_payload],
            adw_id=adw_id,
            model="opus",
        )

        # Post to issue
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                agent_name,
                f"❌ Attempting to resolve: {test.test_name}\n```json\n{test_payload}\n```",
            ),
        )

        # Execute resolution
        response = execute_template(resolve_request)

        if response.success:
            resolved_count += 1
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    agent_name,
                    f"✅ Successfully resolved: {test.test_name}",
                ),
            )
            logger.info(f"Successfully resolved: {test.test_name}")
        else:
            unresolved_count += 1
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    agent_name,
                    f"❌ Failed to resolve: {test.test_name}",
                ),
            )
            logger.error(f"Failed to resolve: {test.test_name}")

    return resolved_count, unresolved_count


def run_tests_with_resolution(
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    max_attempts: int = MAX_TEST_RETRY_ATTEMPTS,
) -> Tuple[List[TestResult], int, int, AgentPromptResponse]:
    """
    Run tests with automatic resolution and retry logic.
    Returns (results, passed_count, failed_count, last_test_response).
    """
    attempt = 0
    results = []
    passed_count = 0
    failed_count = 0
    test_response = None

    while attempt < max_attempts:
        attempt += 1
        logger.info(f"\n=== Test Run Attempt {attempt}/{max_attempts} ===")

        # Run tests
        test_response = run_tests(adw_id, logger)

        # If there was a high level - non-test related error, stop and report it
        if not test_response.success:
            logger.error(f"Error running tests: {test_response.output}")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    AGENT_TESTER,
                    f"❌ Error running tests: {test_response.output}",
                ),
            )
            break

        # Parse test results
        results, passed_count, failed_count = parse_test_results(
            test_response.output, logger
        )

        # If no failures or this is the last attempt, we're done
        if failed_count == 0:
            logger.info("All tests passed, stopping retry attempts")
            break
        if attempt == max_attempts:
            logger.info(f"Reached maximum retry attempts ({max_attempts}), stopping")
            break

        # If we have failed tests and this isn't the last attempt, try to resolve
        logger.info("\n=== Attempting to resolve failed tests ===")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "ops",
                f"❌ Found {failed_count} failed tests. Attempting resolution...",
            ),
        )

        # Get list of failed tests
        failed_tests = [test for test in results if not test.passed]

        # Attempt resolution
        resolved, unresolved = resolve_failed_tests(
            failed_tests, adw_id, issue_number, logger, iteration=attempt
        )

        # Report resolution results
        if resolved > 0:
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, "ops", f"✅ Resolved {resolved}/{failed_count} failed tests"
                ),
            )

            # Continue to next attempt if we resolved something
            logger.info(f"\n=== Re-running tests after resolving {resolved} tests ===")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    AGENT_TESTER,
                    f"🔄 Re-running tests (attempt {attempt + 1}/{max_attempts})...",
                ),
            )
        else:
            # No tests were resolved, no point in retrying
            logger.info("No tests were resolved, stopping retry attempts")
            break

    # Log final attempt status
    if attempt == max_attempts and failed_count > 0:
        logger.warning(
            f"Reached maximum retry attempts ({max_attempts}) with {failed_count} failures remaining"
        )
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "ops",
                f"⚠️ Reached maximum retry attempts ({max_attempts}) with {failed_count} failures",
            ),
        )

    return results, passed_count, failed_count, test_response


# ============================================================================
# API Integration Tests (curl-based endpoint testing)
# ============================================================================

def check_route_files_changed(logger: logging.Logger) -> List[str]:
    """Check if any route files have been modified in the current branch."""
    try:
        result = subprocess.run(
            ["git", "diff", "origin/main", "--name-only"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            logger.warning(f"Git diff failed: {result.stderr}")
            return []

        changed_files = result.stdout.strip().split("\n")
        route_files = [
            f for f in changed_files
            if f.startswith("backend/src/adapter/rest/") and f.endswith("_routes.py")
        ]
        return route_files
    except Exception as e:
        logger.warning(f"Error checking route files: {e}")
        return []


def start_test_server(logger: logging.Logger) -> Optional[subprocess.Popen]:
    """Start the backend server for API testing."""
    try:
        env = os.environ.copy()
        env["TESTING"] = "true"

        # Start uvicorn in background
        proc = subprocess.Popen(
            ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd="backend",
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        logger.info(f"Started test server (PID: {proc.pid})")
        return proc
    except Exception as e:
        logger.error(f"Failed to start test server: {e}")
        return None


def wait_for_server(base_url: str, timeout: int = API_TEST_SERVER_TIMEOUT) -> bool:
    """Wait for the server to be ready."""
    import time

    health_url = f"{base_url}/api/health"
    start = time.time()

    while time.time() - start < timeout:
        try:
            result = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", health_url],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.stdout.strip() == "200":
                return True
        except Exception:
            pass
        time.sleep(1)

    return False


def stop_test_server(proc: Optional[subprocess.Popen], logger: logging.Logger) -> None:
    """Stop the test server gracefully."""
    if proc is None:
        return

    try:
        proc.terminate()
        proc.wait(timeout=5)
        logger.info("Test server stopped")
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        logger.warning("Test server killed (did not terminate gracefully)")
    except Exception as e:
        logger.error(f"Error stopping test server: {e}")


def run_api_integration_tests(
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
) -> Tuple[List[TestResult], int, int]:
    """
    Run curl-based API integration tests for new/modified endpoints.

    This catches bugs like API response format issues that unit tests miss
    because they mock external API responses.

    Returns (results, passed_count, failed_count).
    """
    # Check if any route files changed
    changed_routes = check_route_files_changed(logger)
    if not changed_routes:
        logger.info("No route files changed, skipping API integration tests")
        return [], 0, 0

    logger.info(f"Found {len(changed_routes)} changed route files: {changed_routes}")

    # Start the backend server
    logger.info("Starting backend server for API integration tests...")
    server_proc = start_test_server(logger)

    if server_proc is None:
        return [TestResult(
            test_name="server_startup",
            passed=False,
            execution_command="uv run uvicorn main:app --host 0.0.0.0 --port 8000",
            test_purpose="Start backend server for API testing",
            error="Failed to start backend server",
        )], 0, 1

    try:
        # Wait for server to be ready
        logger.info(f"Waiting for server at {API_TEST_BASE_URL}...")
        if not wait_for_server(API_TEST_BASE_URL):
            logger.error("Server did not become ready in time")
            return [TestResult(
                test_name="server_health_check",
                passed=False,
                execution_command=f"curl {API_TEST_BASE_URL}/api/health",
                test_purpose="Verify server is ready to accept requests",
                error=f"Server health check failed after {API_TEST_SERVER_TIMEOUT}s",
            )], 0, 1

        logger.info("Server is ready, running API integration tests...")

        # Execute /test_api command via Claude
        request = AgentTemplateRequest(
            agent_name=AGENT_API_TESTER,
            slash_command="/test_api",
            args=[API_TEST_BASE_URL],
            adw_id=adw_id,
            model="sonnet",  # Use faster model for API tests
        )

        response = execute_template(request)

        if not response.success:
            logger.error(f"API integration tests failed: {response.output}")
            return [TestResult(
                test_name="api_test_execution",
                passed=False,
                execution_command="/test_api",
                test_purpose="Execute API integration test suite",
                error=response.output[:500],
            )], 0, 1

        # Parse results
        results, passed_count, failed_count = parse_test_results(response.output, logger)
        return results, passed_count, failed_count

    finally:
        # Always stop the server
        stop_test_server(server_proc, logger)


def format_api_test_results_comment(
    results: List[TestResult], passed_count: int, failed_count: int
) -> str:
    """Format API integration test results for GitHub issue comment."""
    if not results:
        return "ℹ️ No API integration tests executed (no route files changed)"

    comment_parts = []

    # Summary
    comment_parts.append(f"**Total:** {len(results)} | **Passed:** {passed_count} | **Failed:** {failed_count}")
    comment_parts.append("")

    # Failed tests first
    failed_tests = [t for t in results if not t.passed]
    if failed_tests:
        comment_parts.append("### ❌ Failed Tests")
        comment_parts.append("")
        for test in failed_tests:
            comment_parts.append(f"- **{test.test_name}**")
            if test.error:
                comment_parts.append(f"  - Error: {test.error[:200]}")
            comment_parts.append(f"  - Command: `{test.execution_command[:100]}...`")
        comment_parts.append("")

    # Passed tests
    passed_tests = [t for t in results if t.passed]
    if passed_tests:
        comment_parts.append("### ✅ Passed Tests")
        comment_parts.append("")
        for test in passed_tests:
            comment_parts.append(f"- {test.test_name}")

    return "\n".join(comment_parts)


# ============================================================================
# Static Analysis Tests (semantic validation)
# ============================================================================

def run_static_analysis_tests(
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
) -> Tuple[List[TestResult], int, int]:
    """
    Run static analysis tests to catch semantic bugs.

    This catches bugs like:
    - Enum case mismatches (Status.pending vs Status.PENDING)
    - Wrong field access (user_type vs role)
    - Import errors that only manifest at runtime

    Returns (results, passed_count, failed_count).
    """
    logger.info("Running static analysis tests...")

    # Execute /test_static command via Claude
    request = AgentTemplateRequest(
        agent_name=AGENT_STATIC_ANALYZER,
        slash_command="/test_static",
        args=[],
        adw_id=adw_id,
        model="sonnet",  # Use faster model for static analysis
    )

    response = execute_template(request)

    if not response.success:
        logger.error(f"Static analysis failed: {response.output}")
        return [TestResult(
            test_name="static_analysis_execution",
            passed=False,
            execution_command="/test_static",
            test_purpose="Execute static analysis for semantic bugs",
            error=response.output[:500],
        )], 0, 1

    # Parse results
    results, passed_count, failed_count = parse_test_results(response.output, logger)
    return results, passed_count, failed_count


def format_static_analysis_results_comment(
    results: List[TestResult], passed_count: int, failed_count: int
) -> str:
    """Format static analysis results for GitHub issue comment."""
    if not results:
        return "ℹ️ No static analysis results"

    comment_parts = []
    comment_parts.append(f"**Total:** {len(results)} | **Passed:** {passed_count} | **Failed:** {failed_count}")
    comment_parts.append("")

    # Failed checks first
    failed_checks = [t for t in results if not t.passed]
    if failed_checks:
        comment_parts.append("### ❌ Failed Checks")
        comment_parts.append("")
        for check in failed_checks:
            comment_parts.append(f"- **{check.test_name}**")
            if check.error:
                comment_parts.append(f"  - Error: {check.error[:300]}")
            comment_parts.append(f"  - Purpose: {check.test_purpose}")
        comment_parts.append("")

    # Passed checks
    passed_checks = [t for t in results if t.passed]
    if passed_checks:
        comment_parts.append("### ✅ Passed Checks")
        comment_parts.append("")
        for check in passed_checks:
            comment_parts.append(f"- {check.test_name}")

    return "\n".join(comment_parts)


# ============================================================================
# E2E Tests (browser automation)
# ============================================================================

def run_e2e_tests(
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    attempt: int = 1,
) -> List[E2ETestResult]:
    """Run all E2E tests found in .claude/commands/e2e/*.md sequentially."""
    import glob

    # Find all E2E test files
    e2e_test_files = glob.glob(".claude/commands/e2e/*.md")
    logger.info(f"Found {len(e2e_test_files)} E2E test files")

    if not e2e_test_files:
        logger.warning("No E2E test files found in .claude/commands/e2e/")
        return []

    results = []

    # Run tests sequentially
    for idx, test_file in enumerate(e2e_test_files):
        agent_name = f"{AGENT_E2E_TESTER}_{attempt - 1}_{idx}"
        result = execute_single_e2e_test(
            test_file, agent_name, adw_id, issue_number, logger
        )
        if result:
            results.append(result)
            # Break on first failure
            if not result.passed:
                logger.info(f"E2E test failed: {result.test_name}, stopping execution")
                break

    return results


def execute_single_e2e_test(
    test_file: str,
    agent_name: str,
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
) -> Optional[E2ETestResult]:
    """Execute a single E2E test and return the result."""
    test_name = os.path.basename(test_file).replace(".md", "")
    logger.info(f"Running E2E test: {test_name}")

    # Make issue comment
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, agent_name, f"✅ Running E2E test: {test_name}"),
    )

    # Create template request
    request = AgentTemplateRequest(
        agent_name=agent_name,
        slash_command="/test_e2e",
        args=[adw_id, agent_name, test_file],  # Pass ADW ID and agent name for screenshot directory
        adw_id=adw_id,
        model="opus",
    )

    # Execute test
    response = execute_template(request)

    if not response.success:
        logger.error(f"Error running E2E test {test_name}: {response.output}")
        return E2ETestResult(
            test_name=test_name,
            status="failed",
            test_path=test_file,
            error=f"Test execution error: {response.output}",
        )

    # Parse the response
    try:
        # Parse JSON from response
        result_data = parse_json(response.output, dict)

        # Create E2ETestResult
        e2e_result = E2ETestResult(
            test_name=result_data.get("test_name", test_name),
            status=result_data.get("status", "failed"),
            test_path=test_file,
            screenshots=result_data.get("screenshots", []),
            error=result_data.get("error"),
        )

        # Report complete and show payload
        status_emoji = "✅" if e2e_result.passed else "❌"
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                agent_name,
                f"{status_emoji} E2E test completed: {test_name}\n```json\n{e2e_result.model_dump_json(indent=2)}\n```",
            ),
        )

        return e2e_result
    except Exception as e:
        logger.error(f"Error parsing E2E test result for {test_name}: {e}")
        e2e_result = E2ETestResult(
            test_name=test_name,
            status="failed",
            test_path=test_file,
            error=f"Result parsing error: {str(e)}",
        )

        # Report complete and show payload
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                agent_name,
                f"❌ E2E test completed: {test_name}\n```json\n{e2e_result.model_dump_json(indent=2)}\n```",
            ),
        )

        return e2e_result


def format_e2e_test_results_comment(
    results: List[E2ETestResult], passed_count: int, failed_count: int
) -> str:
    """Format E2E test results for GitHub issue comment."""
    if not results:
        return "❌ No E2E test results found"

    # Separate failed and passed tests
    failed_tests = [test for test in results if not test.passed]
    passed_tests = [test for test in results if test.passed]

    # Build comment
    comment_parts = []

    # Failed tests header
    if failed_tests:
        comment_parts.append("")
        comment_parts.append("## ❌ Failed E2E Tests")
        comment_parts.append("")

        # Loop over each failed test
        for test in failed_tests:
            comment_parts.append(f"### {test.test_name}")
            comment_parts.append("")
            comment_parts.append("```json")
            comment_parts.append(json.dumps(test.model_dump(), indent=2))
            comment_parts.append("```")
            comment_parts.append("")

    # Passed tests header
    if passed_tests:
        comment_parts.append("## ✅ Passed E2E Tests")
        comment_parts.append("")

        # Loop over each passed test
        for test in passed_tests:
            comment_parts.append(f"### {test.test_name}")
            comment_parts.append("")
            if test.screenshots:
                comment_parts.append(f"Screenshots: {len(test.screenshots)} captured")
            comment_parts.append("")

    # Remove trailing empty line
    if comment_parts and comment_parts[-1] == "":
        comment_parts.pop()

    return "\n".join(comment_parts)


def resolve_failed_e2e_tests(
    failed_tests: List[E2ETestResult],
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    iteration: int = 1,
) -> Tuple[int, int]:
    """
    Attempt to resolve failed E2E tests using the resolve_failed_e2e_test command.
    Returns (resolved_count, unresolved_count).
    """
    resolved_count = 0
    unresolved_count = 0

    for idx, test in enumerate(failed_tests):
        logger.info(
            f"\n=== Resolving failed E2E test {idx + 1}/{len(failed_tests)}: {test.test_name} ==="
        )

        # Create payload for the resolve command
        test_payload = test.model_dump_json(indent=2)

        # Create agent name with iteration
        agent_name = f"e2e_test_resolver_iter{iteration}_{idx}"

        # Create template request
        resolve_request = AgentTemplateRequest(
            agent_name=agent_name,
            slash_command="/resolve_failed_e2e_test",
            args=[test_payload],
            adw_id=adw_id,
            model="opus",
        )

        # Post to issue
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                agent_name,
                f"🔧 Attempting to resolve E2E test: {test.test_name}\n```json\n{test_payload}\n```",
            ),
        )

        # Execute resolution
        response = execute_template(resolve_request)

        if response.success:
            resolved_count += 1
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    agent_name,
                    f"✅ Successfully resolved E2E test: {test.test_name}",
                ),
            )
            logger.info(f"Successfully resolved E2E test: {test.test_name}")
        else:
            unresolved_count += 1
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    agent_name,
                    f"❌ Failed to resolve E2E test: {test.test_name}",
                ),
            )
            logger.error(f"Failed to resolve E2E test: {test.test_name}")

    return resolved_count, unresolved_count


def run_e2e_tests_with_resolution(
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    max_attempts: int = MAX_E2E_TEST_RETRY_ATTEMPTS,
) -> Tuple[List[E2ETestResult], int, int]:
    """
    Run E2E tests with automatic resolution and retry logic.
    Returns (results, passed_count, failed_count).
    """
    attempt = 0
    results = []
    passed_count = 0
    failed_count = 0

    while attempt < max_attempts:
        attempt += 1
        logger.info(f"\n=== E2E Test Run Attempt {attempt}/{max_attempts} ===")

        # Run E2E tests
        results = run_e2e_tests(adw_id, issue_number, logger, attempt)

        if not results:
            logger.warning("No E2E test results to process")
            break

        # Count passes and failures
        passed_count = sum(1 for test in results if test.passed)
        failed_count = len(results) - passed_count

        # If no failures or this is the last attempt, we're done
        if failed_count == 0:
            logger.info("All E2E tests passed, stopping retry attempts")
            break
        if attempt == max_attempts:
            logger.info(
                f"Reached maximum E2E retry attempts ({max_attempts}), stopping"
            )
            break

        # If we have failed tests and this isn't the last attempt, try to resolve
        logger.info("\n=== Attempting to resolve failed E2E tests ===")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "ops",
                f"🔧 Found {failed_count} failed E2E tests. Attempting resolution...",
            ),
        )

        # Get list of failed tests
        failed_tests = [test for test in results if not test.passed]

        # Attempt resolution
        resolved, unresolved = resolve_failed_e2e_tests(
            failed_tests, adw_id, issue_number, logger, iteration=attempt
        )

        # Report resolution results
        if resolved > 0:
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    "ops",
                    f"✅ Resolved {resolved}/{failed_count} failed E2E tests",
                ),
            )

            # Continue to next attempt if we resolved something
            logger.info(
                f"\n=== Re-running E2E tests after resolving {resolved} tests ==="
            )
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    AGENT_E2E_TESTER,
                    f"🔄 Re-running E2E tests (attempt {attempt + 1}/{max_attempts})...",
                ),
            )
        else:
            # No tests were resolved, no point in retrying
            logger.info("No E2E tests were resolved, stopping retry attempts")
            break

    # Log final attempt status
    if attempt == max_attempts and failed_count > 0:
        logger.warning(
            f"Reached maximum E2E retry attempts ({max_attempts}) with {failed_count} failures remaining"
        )
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "ops",
                f"⚠️ Reached maximum E2E retry attempts ({max_attempts}) with {failed_count} failures",
            ),
        )

    return results, passed_count, failed_count


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse arguments
    arg_issue_number, arg_adw_id, skip_e2e, skip_api = parse_args(None)
    
    # Initialize state and issue number
    issue_number = arg_issue_number
    
    # Ensure we have an issue number
    if not issue_number:
        print("Error: No issue number provided", file=sys.stderr)
        sys.exit(1)
    
    # Ensure ADW ID exists with initialized state
    temp_logger = setup_logger(arg_adw_id, "adw_test") if arg_adw_id else None
    adw_id = ensure_adw_id(issue_number, arg_adw_id, temp_logger)
    
    # Load the state that was created/found by ensure_adw_id
    state = ADWState.load(adw_id, temp_logger)

    # Set up logger with ADW ID
    logger = setup_logger(adw_id, "adw_test")
    logger.info(f"ADW Test starting - ID: {adw_id}, Issue: {issue_number}")

    # Validate environment (now with logger)
    check_env_vars(logger)

    # Get repo information from git remote
    try:
        github_repo_url: str = get_repo_url()
        repo_path: str = extract_repo_path(github_repo_url)
    except ValueError as e:
        logger.error(f"Error getting repository URL: {e}")
        sys.exit(1)
    
    # We'll fetch issue details later only if needed
    issue = None
    issue_class = state.get("issue_class")

    # Handle branch - either use existing or create new test branch
    branch_name = state.get("branch_name")
    if branch_name:
        # Try to checkout existing branch
        result = subprocess.run(["git", "checkout", branch_name], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Failed to checkout branch {branch_name}: {result.stderr}")
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", f"❌ Failed to checkout branch {branch_name}")
            )
            sys.exit(1)
        logger.info(f"Checked out existing branch: {branch_name}")
    else:
        # No branch in state - create a test-specific branch
        logger.info("No branch in state, creating test branch")
        
        # Generate simple test branch name without classification
        branch_name = f"test-issue-{issue_number}-adw-{adw_id}"
        logger.info(f"Generated test branch name: {branch_name}")
        
        # Create the branch
        from adw_modules.git_ops import create_branch
        success, error = create_branch(branch_name)
        if not success:
            logger.error(f"Error creating branch: {error}")
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", f"❌ Error creating branch: {error}")
            )
            sys.exit(1)
        
        state.update(branch_name=branch_name)
        state.save("adw_test")
        logger.info(f"Created and checked out new test branch: {branch_name}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"✅ Created test branch: {branch_name}")
        )

    make_issue_comment(
        issue_number, format_issue_message(adw_id, "ops", "✅ Starting test suite")
    )

    # ============================================================
    # PHASE 0: Static Analysis (runs before all other tests)
    # Catches enum case mismatches, field access errors, import issues
    # ============================================================
    logger.info("\n=== Running static analysis ===")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_STATIC_ANALYZER, "🔍 Running static analysis..."),
    )

    static_results, static_passed, static_failed = run_static_analysis_tests(
        adw_id, issue_number, logger
    )

    # Format and post static analysis results
    static_results_comment = format_static_analysis_results_comment(
        static_results, static_passed, static_failed
    )
    make_issue_comment(
        issue_number,
        format_issue_message(
            adw_id, AGENT_STATIC_ANALYZER, f"📊 Static analysis results:\n{static_results_comment}"
        ),
    )

    logger.info(f"Static analysis results: {static_passed} passed, {static_failed} failed")

    # If static analysis fails, skip all other tests (fail fast)
    if static_failed > 0:
        logger.error("Static analysis failed, skipping remaining tests")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, "ops", "⚠️ Skipping unit/API/E2E tests due to static analysis failures"
            ),
        )
        # Initialize empty results for skipped test phases
        results = []
        passed_count = 0
        failed_count = 0
        test_response = None
        api_results = []
        api_passed_count = 0
        api_failed_count = 0
        e2e_results = []
        e2e_passed_count = 0
        e2e_failed_count = 0
    else:
        # ============================================================
        # PHASE 1: Unit Tests (only runs if static analysis passes)
        # ============================================================
        logger.info("\n=== Running test suite ===")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_TESTER, "✅ Running application tests..."),
        )

        # Run tests with resolution and retry logic
        results, passed_count, failed_count, test_response = run_tests_with_resolution(
            adw_id, issue_number, logger
        )

    # Format and post final results
    results_comment = format_test_results_comment(results, passed_count, failed_count)
    make_issue_comment(
        issue_number,
        format_issue_message(
            adw_id, AGENT_TESTER, f"📊 Final test results:\n{results_comment}"
        ),
    )

    # Log summary
    logger.info(f"Final test results: {passed_count} passed, {failed_count} failed")

    # Initialize API test results
    api_results = []
    api_passed_count = 0
    api_failed_count = 0

    # Run API integration tests if static analysis and unit tests passed
    if static_failed > 0:
        logger.warning("Skipping API integration tests due to static analysis failures")
    elif failed_count > 0:
        logger.warning("Skipping API integration tests due to unit test failures")
    elif skip_api:
        logger.info("Skipping API integration tests as requested via --skip-api flag")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, "ops", "⚠️ Skipping API integration tests as requested via --skip-api flag"
            ),
        )
    else:
        logger.info("\n=== Running API integration tests ===")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_API_TESTER, "🔌 Running API integration tests..."),
        )

        api_results, api_passed_count, api_failed_count = run_api_integration_tests(
            adw_id, issue_number, logger
        )

        # Format and post API test results
        api_results_comment = format_api_test_results_comment(
            api_results, api_passed_count, api_failed_count
        )
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, AGENT_API_TESTER, f"📊 API integration test results:\n{api_results_comment}"
            ),
        )

        logger.info(f"API integration test results: {api_passed_count} passed, {api_failed_count} failed")

    # If static analysis, unit tests, or API tests failed, skip E2E tests
    if static_failed > 0:
        skip_reason = "static analysis failures"
        logger.warning(f"Skipping E2E tests due to {skip_reason}")
        e2e_results = []
        e2e_passed_count = 0
        e2e_failed_count = 0
    elif failed_count > 0 or api_failed_count > 0:
        skip_reason = "unit test failures" if failed_count > 0 else "API integration test failures"
        logger.warning(f"Skipping E2E tests due to {skip_reason}")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, "ops", f"⚠️ Skipping E2E tests due to {skip_reason}"
            ),
        )
        e2e_results = []
        e2e_passed_count = 0
        e2e_failed_count = 0
    elif skip_e2e:
        logger.info("Skipping E2E tests as requested")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, "ops", "⚠️ Skipping E2E tests as requested via --skip-e2e flag"
            ),
        )
        e2e_results = []
        e2e_passed_count = 0
        e2e_failed_count = 0
    else:
        # Run E2E tests since unit tests passed
        logger.info("\n=== Running E2E test suite ===")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_E2E_TESTER, "✅ Starting E2E tests..."),
        )

        # Run E2E tests with resolution and retry logic
        e2e_results, e2e_passed_count, e2e_failed_count = run_e2e_tests_with_resolution(
            adw_id, issue_number, logger
        )

        # Format and post E2E results
        if e2e_results:
            e2e_results_comment = format_e2e_test_results_comment(
                e2e_results, e2e_passed_count, e2e_failed_count
            )
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    AGENT_E2E_TESTER,
                    f"📊 Final E2E test results:\n{e2e_results_comment}",
                ),
            )

            logger.info(
                f"Final E2E test results: {e2e_passed_count} passed, {e2e_failed_count} failed"
            )

    # Commit the test results (whether tests passed or failed)
    logger.info("\n=== Committing test results ===")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_TESTER, "✅ Committing test results"),
    )

    # Fetch issue details if we haven't already
    if not issue:
        issue = fetch_issue(issue_number, repo_path)
    
    # Get issue classification if we need it for commit
    if not issue_class:
        issue_class, error = classify_issue(issue, adw_id, logger)
        if error:
            logger.warning(f"Error classifying issue: {error}, defaulting to /chore for test commit")
            issue_class = "/chore"
        state.update(issue_class=issue_class)
        state.save("adw_test")
    
    commit_msg, error = create_commit(AGENT_TESTER, issue, issue_class, adw_id, logger)

    if error:
        logger.error(f"Error committing test results: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, AGENT_TESTER, f"❌ Error committing test results: {error}"
            ),
        )
        # Don't exit on commit error, continue to report final status
    else:
        logger.info(f"Test results committed: {commit_msg}")

    # Log comprehensive test results to the issue
    log_test_results(state, static_results, results, e2e_results, logger)
    
    # Finalize git operations (push and create/update PR)
    logger.info("\n=== Finalizing git operations ===")
    finalize_git_operations(state, logger)

    # Update state with test results
    # Note: test_results is not part of core state, but save anyway to track completion
    state.save("adw_test")
    
    # Output state for chaining
    state.to_stdout()
    
    # Exit with appropriate code
    total_failures = static_failed + failed_count + api_failed_count + e2e_failed_count
    if total_failures > 0:
        logger.info(f"Test suite completed with failures for issue #{issue_number}")
        failure_msg = f"❌ Test suite completed with failures:\n"
        if static_failed > 0:
            failure_msg += f"- Static analysis: {static_failed} failures\n"
        if failed_count > 0:
            failure_msg += f"- Unit tests: {failed_count} failures\n"
        if api_failed_count > 0:
            failure_msg += f"- API integration tests: {api_failed_count} failures\n"
        if e2e_failed_count > 0:
            failure_msg += f"- E2E tests: {e2e_failed_count} failures"
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", failure_msg),
        )
        sys.exit(1)
    else:
        logger.info(f"Test suite completed successfully for issue #{issue_number}")
        success_msg = f"✅ All tests passed successfully!\n"
        success_msg += f"- Static analysis: {static_passed} passed\n"
        success_msg += f"- Unit tests: {passed_count} passed\n"
        if api_results:
            success_msg += f"- API integration tests: {api_passed_count} passed\n"
        if e2e_results:
            success_msg += f"- E2E tests: {e2e_passed_count} passed"
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", success_msg),
        )


if __name__ == "__main__":
    main()
