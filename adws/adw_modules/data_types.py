"""Data types for GitHub API responses and Claude Code agent."""

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field

# Supported slash commands for issue classification
# These should align with your custom slash commands in .claude/commands that you want to run
IssueClassSlashCommand = Literal["/chore", "/bug", "/feature"]

# ADW workflow types
ADWWorkflow = Literal[
    "adw_plan",           # Planning only
    "adw_build",          # Building only (excluded from webhook)
    "adw_test",           # Testing only  
    "adw_plan_build",     # Plan + Build
    "adw_plan_build_test" # Plan + Build + Test
]

# All slash commands used in the ADW system
# Includes issue classification commands and ADW-specific commands
SlashCommand = Literal[
    # Issue classification commands
    "/chore",
    "/bug",
    "/feature",
    # ADW workflow commands
    "/classify_issue",
    "/classify_adw",
    "/find_plan_file",
    "/generate_branch_name",
    "/commit",
    "/pull_request",
    "/implement",
    "/test",
    "/test_static",  # Static analysis for semantic bugs (enum case, field access)
    "/test_api",
    "/resolve_failed_test",
    "/test_e2e",
    "/resolve_failed_e2e_test",
    # Review and documentation commands
    "/review",
    "/patch",
    "/document",
]


class GitHubUser(BaseModel):
    """GitHub user model."""

    id: Optional[str] = None  # Not always returned by GitHub API
    login: str
    name: Optional[str] = None
    is_bot: bool = Field(default=False, alias="is_bot")


class GitHubLabel(BaseModel):
    """GitHub label model."""

    id: str
    name: str
    color: str
    description: Optional[str] = None


class GitHubMilestone(BaseModel):
    """GitHub milestone model."""

    id: str
    number: int
    title: str
    description: Optional[str] = None
    state: str


class GitHubComment(BaseModel):
    """GitHub comment model."""

    id: str
    author: GitHubUser
    body: str
    created_at: datetime = Field(alias="createdAt")
    updated_at: Optional[datetime] = Field(
        None, alias="updatedAt"
    )  # Not always returned


class GitHubIssueListItem(BaseModel):
    """GitHub issue model for list responses (simplified)."""

    number: int
    title: str
    body: str
    labels: List[GitHubLabel] = []
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    class Config:
        populate_by_name = True


class GitHubIssue(BaseModel):
    """GitHub issue model."""

    number: int
    title: str
    body: str
    state: str
    author: GitHubUser
    assignees: List[GitHubUser] = []
    labels: List[GitHubLabel] = []
    milestone: Optional[GitHubMilestone] = None
    comments: List[GitHubComment] = []
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    closed_at: Optional[datetime] = Field(None, alias="closedAt")
    url: str

    class Config:
        populate_by_name = True


class AgentPromptRequest(BaseModel):
    """Claude Code agent prompt configuration."""

    prompt: str
    adw_id: str
    agent_name: str = "ops"
    model: Literal["sonnet", "opus"] = "opus"
    dangerously_skip_permissions: bool = False
    output_file: str


class AgentPromptResponse(BaseModel):
    """Claude Code agent response."""

    output: str
    success: bool
    session_id: Optional[str] = None


class AgentTemplateRequest(BaseModel):
    """Claude Code agent template execution request."""

    agent_name: str
    slash_command: SlashCommand
    args: List[str]
    adw_id: str
    model: Literal["sonnet", "opus"] = "opus"


class ClaudeCodeResultMessage(BaseModel):
    """Claude Code JSONL result message (last line)."""

    type: str
    subtype: str
    is_error: bool
    duration_ms: int
    duration_api_ms: int
    num_turns: int
    result: str
    session_id: str
    total_cost_usd: float


class TestResult(BaseModel):
    """Individual test result from test suite execution."""

    test_name: str
    passed: bool
    execution_command: str
    test_purpose: str
    error: Optional[str] = None


class E2ETestResult(BaseModel):
    """Individual E2E test result from browser automation."""

    test_name: str
    status: Literal["passed", "failed"]
    test_path: str  # Path to the test file for re-execution
    screenshots: List[str] = []
    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        """Check if test passed."""
        return self.status == "passed"


# Static analysis check types
StaticAnalysisCheckType = Literal[
    "enum_validation",
    "field_access",
    "import_validation",
    "type_check"
]


class StaticAnalysisResult(BaseModel):
    """Result from static analysis check.

    Used to catch semantic bugs that pass linting but fail at runtime:
    - Enum case mismatches (Status.pending vs Status.PENDING)
    - Wrong field access (user_type vs role)
    - Import errors that manifest at runtime
    """

    check_name: str
    passed: bool
    check_type: StaticAnalysisCheckType
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    error: Optional[str] = None
    suggestion: Optional[str] = None

    @property
    def failed(self) -> bool:
        """Check if analysis failed."""
        return not self.passed


class ADWStateData(BaseModel):
    """Minimal persistent state for ADW workflow.

    Stored in agents/{adw_id}/adw_state.json
    Contains only essential identifiers to connect workflow steps.
    """

    adw_id: str
    issue_number: Optional[str] = None
    branch_name: Optional[str] = None
    plan_file: Optional[str] = None
    issue_class: Optional[IssueClassSlashCommand] = None


# Review severity levels
ReviewSeverity = Literal["blocker", "tech_debt", "skippable"]


class ReviewIssue(BaseModel):
    """Individual issue found during review."""

    review_issue_number: int
    screenshot_path: str = ""
    issue_description: str
    issue_resolution: str
    issue_severity: ReviewSeverity
    screenshot_url: Optional[str] = None  # Populated after R2 upload


class ReviewResult(BaseModel):
    """Result of a code review against specification."""

    success: bool
    review_issues: List[ReviewIssue] = []
    screenshots: List[str] = []  # File paths to screenshots
    screenshot_urls: List[str] = []  # Populated after R2 upload


class DocumentationResult(BaseModel):
    """Result of documentation generation."""

    success: bool
    documentation_created: bool
    documentation_path: Optional[str] = None
    error_message: Optional[str] = None
