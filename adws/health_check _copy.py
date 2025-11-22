#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "python-dotenv",
#     "pydantic",
# ]
# ///

"""
Health Check Script for ADW System

Usage:
uv run adws/health_check.py <issue_number>

This script performs comprehensive health checks:
1. Validates all required environment variables
2. Checks git repository configuration
3. Tests Claude Code CLI functionality
4. Returns structured results
"""

import os
import sys
import json
import subprocess
import tempfile
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import argparse

from dotenv import load_dotenv
from pydantic import BaseModel

# Import git repo functions from github module
from github import get_repo_url, extract_repo_path, make_issue_comment

# Load environment variables
load_dotenv()


class CheckResult(BaseModel):
    """Individual check result."""

    success: bool
    error: Optional[str] = None
    warning: Optional[str] = None
    details: Dict[str, Any] = {}


class HealthCheckResult(BaseModel):
    """Structure for health check results."""

    success: bool
    timestamp: str
    checks: Dict[str, CheckResult]
    warnings: List[str] = []
    errors: List[str] = []


def check_env_vars() -> CheckResult:
    """Check required environment variables."""
    required_vars = {
        "ANTHROPIC_API_KEY": "Anthropic API Key for Claude Code",
        "CLAUDE_CODE_PATH": "Path to Claude Code CLI (defaults to 'claude')",
    }

    optional_vars = {
        "GITHUB_PAT": "(Optional) GitHub Personal Access Token - only needed if you want ADW to use a different GitHub account than 'gh auth login'",
        "E2B_API_KEY": "(Optional) E2B API Key for sandbox environments",
        "CLOUDFLARED_TUNNEL_TOKEN": "(Optional) Cloudflare tunnel token for webhook exposure",
    }

    missing_required = []
    missing_optional = []

    # Check required vars
    for var, desc in required_vars.items():
        if not os.getenv(var):
            if var == "CLAUDE_CODE_PATH":
                # This has a default, so not critical
                continue
            missing_required.append(f"{var} ({desc})")

    # Check optional vars
    for var, desc in optional_vars.items():
        if not os.getenv(var):
            missing_optional.append(f"{var} ({desc})")

    success = len(missing_required) == 0

    return CheckResult(
        success=success,
        error="Missing required environment variables" if not success else None,
        details={
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "claude_code_path": os.getenv("CLAUDE_CODE_PATH", "claude"),
        },
    )


def check_git_repo() -> CheckResult:
    """Check git repository configuration using github module."""
    try:
        # Get repo URL using the github module function
        repo_url = get_repo_url()
        repo_path = extract_repo_path(repo_url)

        # Check if still using disler's repo
        is_disler_repo = "disler" in repo_path.lower()

        return CheckResult(
            success=True,
            warning=(
                "Repository still points to 'disler'. Please update to your own GitHub repository."
                if is_disler_repo
                else None
            ),
            details={
                "repo_url": repo_url,
                "repo_path": repo_path,
                "is_disler_repo": is_disler_repo,
            },
        )
    except ValueError as e:
        return CheckResult(success=False, error=str(e))


def check_claude_code() -> CheckResult:
    """Test Claude Code CLI functionality."""
    claude_path = os.getenv("CLAUDE_CODE_PATH", "claude")

    # First check if Claude Code is installed
    try:
        result = subprocess.run(
            [claude_path, "--version"], capture_output=True, text=True
        )
        if result.returncode != 0:
            return CheckResult(
                success=False,
                error=f"Claude Code CLI not functional at '{claude_path}'",
            )
        print(f"🔍 DEBUG: Claude Code version: {result.stdout.strip()}")
    except FileNotFoundError:
        return CheckResult(
            success=False,
            error=f"Claude Code CLI not found at '{claude_path}'. Please install or set CLAUDE_CODE_PATH correctly.",
        )

    # Test with a simple prompt
    test_prompt = "What is 2+2? Just respond with the number, nothing else."

    # Prepare environment
    env = os.environ.copy()
    if os.getenv("GITHUB_PAT"):
        env["GH_TOKEN"] = os.getenv("GITHUB_PAT")

    try:
        # Run Claude Code - capture both stdout and stderr
        cmd = [
            claude_path,
            "-p",
            test_prompt,
            "--model",
            "claude-haiku-4-5-20251001",
            "--output-format",
            "stream-json",
            "--verbose",
            "--dangerously-skip-permissions",
        ]

        print(f"\n🔍 DEBUG: Running command: {' '.join(cmd)}")

        # Run command and capture everything
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            env=env, 
            timeout=30
        )

        print(f"🔍 DEBUG: Return code: {result.returncode}")
        print(f"🔍 DEBUG: Stdout length: {len(result.stdout)} chars")
        print(f"🔍 DEBUG: Stderr length: {len(result.stderr)} chars")
        
        if result.stdout:
            print(f"\n🔍 DEBUG: Full stdout (first 2000 chars):")
            print("-" * 50)
            print(result.stdout[:2000])
            print("-" * 50)
        
        if result.stderr:
            print(f"\n🔍 DEBUG: Full stderr:")
            print("-" * 50)
            print(result.stderr)
            print("-" * 50)

        # Parse output to verify it worked - don't fail on exit code if we got a response
        claude_responded = False
        response_text = ""
        has_error = False
        error_message = ""

        # The output is in stdout since we captured it
        for line in result.stdout.split('\n'):
            if line.strip():
                try:
                    msg = json.loads(line)
                    msg_type = msg.get("type")
                    
                    # Check for errors
                    if msg_type == "error":
                        has_error = True
                        error_message = msg.get("error", {}).get("message", "Unknown error")
                        print(f"🔍 DEBUG: Found error message: {error_message}")
                    
                    # Check for result
                    if msg_type == "result":
                        claude_responded = True
                        response_text = msg.get("result", "")
                        print(f"🔍 DEBUG: Found result: {response_text}")
                        break
                        
                except json.JSONDecodeError as e:
                    print(f"🔍 DEBUG: Failed to parse line as JSON: {line[:100]}")
                    continue

        print(f"🔍 DEBUG: Claude responded: {claude_responded}")
        print(f"🔍 DEBUG: Has error: {has_error}")
        print(f"🔍 DEBUG: Response text: {response_text[:100] if response_text else 'None'}")

        # If we got a response, consider it a success even if exit code is non-zero
        if claude_responded:
            return CheckResult(
                success=True,
                warning=f"Exit code was {result.returncode} but got valid response" if result.returncode != 0 else None,
                details={
                    "test_passed": "4" in response_text if response_text else False,
                    "response": response_text[:100] if response_text else "No response",
                    "exit_code": result.returncode,
                },
            )
        
        # If we found an error message, return that
        if has_error:
            return CheckResult(
                success=False,
                error=f"Claude Code returned error: {error_message}"
            )
        
        # Otherwise, fail with exit code info
        error_msg = result.stderr if result.stderr else result.stdout[:500]
        return CheckResult(
            success=False, 
            error=f"Claude Code test failed (exit code {result.returncode}). Check debug output above for details."
        )

    except subprocess.TimeoutExpired:
        return CheckResult(
            success=False, error="Claude Code test timed out after 30 seconds"
        )
    except Exception as e:
        print(f"🔍 DEBUG: Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return CheckResult(success=False, error=f"Claude Code test error: {str(e)}")


def check_github_cli() -> CheckResult:
    """Check if GitHub CLI is installed and authenticated."""
    try:
        # Check if gh is installed
        result = subprocess.run(["gh", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            return CheckResult(success=False, error="GitHub CLI (gh) is not installed")

        # Check authentication status
        env = os.environ.copy()
        if os.getenv("GITHUB_PAT"):
            env["GH_TOKEN"] = os.getenv("GITHUB_PAT")

        result = subprocess.run(
            ["gh", "auth", "status"], capture_output=True, text=True, env=env
        )

        authenticated = result.returncode == 0

        return CheckResult(
            success=authenticated,
            error="GitHub CLI not authenticated" if not authenticated else None,
            details={"installed": True, "authenticated": authenticated},
        )

    except FileNotFoundError:
        return CheckResult(
            success=False,
            error="GitHub CLI (gh) is not installed. Install with: brew install gh",
            details={"installed": False},
        )


def run_health_check() -> HealthCheckResult:
    """Run all health checks and return results."""
    result = HealthCheckResult(
        success=True, timestamp=datetime.now().isoformat(), checks={}
    )

    # Check environment variables
    env_check = check_env_vars()
    result.checks["environment"] = env_check
    if not env_check.success:
        result.success = False
        if env_check.error:
            result.errors.append(env_check.error)
        # Add specific missing vars to errors
        missing_required = env_check.details.get("missing_required", [])
        result.errors.extend(
            [f"Missing required env var: {var}" for var in missing_required]
        )
    # Don't add warnings for optional env vars - they're optional!

    # Check git repository
    git_check = check_git_repo()
    result.checks["git_repository"] = git_check
    if not git_check.success:
        result.success = False
        if git_check.error:
            result.errors.append(git_check.error)
    elif git_check.warning:
        result.warnings.append(git_check.warning)

    # Check GitHub CLI
    gh_check = check_github_cli()
    result.checks["github_cli"] = gh_check
    if not gh_check.success:
        result.success = False
        if gh_check.error:
            result.errors.append(gh_check.error)

    # Check Claude Code - only if we have the API key
    if os.getenv("ANTHROPIC_API_KEY"):
        claude_check = check_claude_code()
        result.checks["claude_code"] = claude_check
        if not claude_check.success:
            result.success = False
            if claude_check.error:
                result.errors.append(claude_check.error)
        elif claude_check.warning:
            result.warnings.append(claude_check.warning)
    else:
        result.checks["claude_code"] = CheckResult(
            success=False,
            details={"skipped": True, "reason": "ANTHROPIC_API_KEY not set"},
        )

    return result


def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="ADW System Health Check")
    parser.add_argument(
        "issue_number",
        nargs="?",
        help="Optional GitHub issue number to post results to",
    )
    args = parser.parse_args()

    print("🏥 Running ADW System Health Check...\n")

    result = run_health_check()

    # Print summary
    print(
        f"{'✅' if result.success else '❌'} Overall Status: {'HEALTHY' if result.success else 'UNHEALTHY'}"
    )
    print(f"📅 Timestamp: {result.timestamp}\n")

    # Print detailed results
    print("📋 Check Results:")
    print("-" * 50)

    for check_name, check_result in result.checks.items():
        status = "✅" if check_result.success else "❌"
        print(f"\n{status} {check_name.replace('_', ' ').title()}:")

        # Print check-specific details
        for key, value in check_result.details.items():
            if value is not None and key not in [
                "missing_required",
                "missing_optional",
            ]:
                print(f"   {key}: {value}")

        if check_result.error:
            print(f"   ❌ Error: {check_result.error}")
        if check_result.warning:
            print(f"   ⚠️  Warning: {check_result.warning}")

    # Print warnings
    if result.warnings:
        print("\n⚠️  Warnings:")
        for warning in result.warnings:
            print(f"   - {warning}")

    # Print errors
    if result.errors:
        print("\n❌ Errors:")
        for error in result.errors:
            print(f"   - {error}")

    # Print next steps
    if not result.success:
        print("\n📝 Next Steps:")
        if any("ANTHROPIC_API_KEY" in e for e in result.errors):
            print("   1. Set ANTHROPIC_API_KEY in your .env file")
        if any("GITHUB_PAT" in e for e in result.errors):
            print("   2. Set GITHUB_PAT in your .env file")
        if any("GitHub CLI" in e for e in result.errors):
            print("   3. Install GitHub CLI: brew install gh")
            print("   4. Authenticate: gh auth login")
        if any("disler" in w for w in result.warnings):
            print(
                "   5. Fork/clone the repository and update git remote to your own repo"
            )

    # If issue number provided, post comment
    if args.issue_number:
        print(f"\n📤 Posting health check results to issue #{args.issue_number}...")
        status_emoji = "✅" if result.success else "❌"
        comment = f"{status_emoji} Health check completed: {'HEALTHY' if result.success else 'UNHEALTHY'}"
        try:
            make_issue_comment(args.issue_number, comment)
            print(f"✅ Posted health check comment to issue #{args.issue_number}")
        except Exception as e:
            print(f"❌ Failed to post comment: {e}")

    # Return appropriate exit code
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()