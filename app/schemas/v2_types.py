from typing import Any, Dict, List, Literal, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field

# ============================================
# FUNDAMENTAL TYPES
# ============================================

SessionId = str
TaskId = str
StepId = str
ConfidenceScore = float

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    ABORTED = "aborted"

class Phase(str, Enum):
    CONTEXT_INJECTION = "context_injection"
    INTENT_PARSER = "intent_parser"
    PLANNER = "planner"
    SKILL_ROUTER = "skill_router"
    REALTIME_FETCHER = "realtime_fetcher"
    CODER = "coder"
    SKILL_RUNNER = "skill_runner"
    RESULT_VALIDATOR = "result_validator"
    SYNTHESIZER = "synthesizer"
    DELIVERY = "delivery"
    ERROR_HANDLER = "error_handler"

class ErrorTier(int, Enum):
    TIER_1_TRANSIENT = 1
    TIER_2_USER_RESOLVABLE = 2
    TIER_3_FATAL = 3

# ============================================
# CONTEXT STRUCTURES
# ============================================

class DatetimeContext(BaseModel):
    utc_timestamp: str
    server_timezone: str
    user_timezone: str
    user_locale: str

class MessageItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: str

class HistoryContext(BaseModel):
    total_turns: int
    last_n_turns: List[MessageItem]
    conversation_id: str

class ToolAvailability(BaseModel):
    available: bool
    status: Literal["available", "degraded", "unavailable"]
    last_checked: str

class SessionStateInner(BaseModel):
    concurrent_tasks: int
    max_concurrent: int
    execution_time_elapsed: int
    max_execution_time: int

class RealtimeCacheEntry(BaseModel):
    data: Any
    timestamp: str
    freshness_minutes: int
    data_age_minutes: int
    source: str

class ExecutionStepResult(BaseModel):
    status: ExecutionStatus
    output: Any = None
    error: str = None
    execution_time_ms: int
    tokens_used: int
    memory_used_mb: float = 0.0
    files_created: List[str] = Field(default_factory=list)

class ContextMetadata(BaseModel):
    created_at: str
    updated_at: str
    version: str

class ExecutionContext(BaseModel):
    session_id: SessionId
    task_id: TaskId
    user_message: str
    current_phase: Phase
    datetime: DatetimeContext
    history: HistoryContext
    tools_status: Dict[str, ToolAvailability]
    session_state: SessionStateInner
    realtime_cache: Dict[str, RealtimeCacheEntry]
    step_results: Dict[str, ExecutionStepResult]
    metadata: ContextMetadata

# ============================================
# INTENT STRUCTURES
# ============================================

ActionType = Literal[
    "create", "read", "transform", "integrate", "search", "decide", "debug"
]

class ConfidenceBreakdown(BaseModel):
    clarity: ConfidenceScore
    completeness: ConfidenceScore
    feasibility: ConfidenceScore

class IntentOutput(BaseModel):
    action_type: ActionType
    sub_actions: List[str]
    needs_realtime: bool
    realtime_data_types: List[str]
    needs_file_access: bool
    required_skills: List[str]
    confidence: ConfidenceScore
    confidence_breakdown: ConfidenceBreakdown
    assumptions: List[str]
    clarifications_needed: bool
    clarification_count: int
    complexity: Literal["low", "medium", "high"]
    next_phase: Phase
    proceed_without_confirmation: bool

class IntentClarification(BaseModel):
    questions: List[str]
    max_questions: int
    timeout_seconds: int
    options: Optional[List[str]] = None

class IntentParserResponse(BaseModel):
    status: Literal["success", "clarification_needed"]
    intent_output: Optional[IntentOutput] = None
    clarification: Optional[IntentClarification] = None
    next_phase: Phase
    proceed_to_phase3: bool

# ============================================
# EXECUTION PLAN STRUCTURES
# ============================================

class ExpectedOutput(BaseModel):
    type: str
    schema_definition: Any = Field(default=None, alias="schema")

class ExecutionStep(BaseModel):
    step_id: StepId
    action: str
    tool_required: Optional[str] = None
    tool_type: Optional[Literal["skill", "api", "bash"]] = None
    input_requirements: List[str]
    expected_output: ExpectedOutput
    success_criteria: str
    error_modes: List[str]
    error_recovery: Optional[str] = None
    depends_on: List[StepId]
    parallel_with: List[StepId]
    timeout_seconds: int
    retry_allowed: bool
    max_retries: int
    estimated_tokens: int
    complexity_score: int
    critical: bool

class DependencyGraph(BaseModel):
    nodes: List[StepId]
    edges: List[List[StepId]]
    is_acyclic: bool
    cycle_check_passed: bool
    cycles_found: Optional[List[List[StepId]]] = None

class ExecutionPlanDependencies(BaseModel):
    external_api: List[str]
    file_system: List[Literal["read", "write"]]
    user_interaction: bool

class ExecutionPlan(BaseModel):
    goal: str
    steps: List[ExecutionStep]
    dependency_graph: DependencyGraph
    parallelizable_groups: List[List[StepId]]
    total_steps: int
    estimated_duration_seconds: int
    total_estimated_tokens: int
    abort_conditions: List[str]
    dependencies: ExecutionPlanDependencies
    risk_flags: List[str]

class CyclicDependency(BaseModel):
    detected: bool
    cycles: List[List[StepId]]
    explanation: str
    user_action_needed: str

class PlannerResponse(BaseModel):
    status: Literal["success", "error"]
    execution_plan: Optional[ExecutionPlan] = None
    circular_dependency: Optional[CyclicDependency] = None
    next_phase: Phase

# ============================================
# ROUTER DECISION STRUCTURES
# ============================================

ExecutionPath = Literal["REALTIME_FETCHER", "SKILL_RUNNER", "CODER", "ERROR"]

class RouterDecision(BaseModel):
    step_id: StepId
    execution_path: ExecutionPath
    realtime_needed: bool
    realtime_types: List[str]
    fetch_timing: Literal["NOW", "DEFERRED", "NONE"]
    skill_name: Optional[str] = None
    skill_available: Optional[bool] = None
    requires_patching: Optional[bool] = None
    coder_action: Optional[Literal["PATCH", "CREATE", "NONE"]] = None
    decision_rationale: str
    confidence: ConfidenceScore

class RealtimeFetchSchedule(BaseModel):
    data_type: str
    timing: Literal["NOW", "DEFERRED"]
    step_id: StepId

class CoderTaskSchedule(BaseModel):
    step_id: StepId
    action: Literal["PATCH", "CREATE"]

class SkillExecutionSchedule(BaseModel):
    step_id: StepId
    skill_name: str

class ExecutionSequence(BaseModel):
    realtime_fetches: List[RealtimeFetchSchedule]
    coder_tasks: List[CoderTaskSchedule]
    skill_executions: List[SkillExecutionSchedule]

class SkillRouterResponse(BaseModel):
    status: Literal["success"]
    routing_decisions: List[RouterDecision]
    execution_sequence: ExecutionSequence
    next_phase: Phase
    ready_for_execution: bool

# ============================================
# CODER STRUCTURES
# ============================================

class CodeMode(str, Enum):
    PATCH = "patch"
    CREATE = "create"

class ReviewCheckNode(BaseModel):
    passed: bool
    issues: List[str]

class ReviewChecks(BaseModel):
    syntax: ReviewCheckNode
    logic: ReviewCheckNode
    error_handling: ReviewCheckNode
    performance: ReviewCheckNode
    security: ReviewCheckNode
    documentation: ReviewCheckNode
    edge_cases: ReviewCheckNode
    style: ReviewCheckNode

class CodeReviewResult(BaseModel):
    round: int
    checks: ReviewChecks
    severity_score: int
    quality_score: ConfidenceScore
    issues_found: bool
    action: Literal["APPROVED", "NEEDS_FIX", "REJECTED"]
    recommended_fixes: Optional[List[str]] = None

class CoderCheckResponse(BaseModel):
    status: Literal["success", "error"]
    code: Optional[str] = None
    language: str
    reviews: List[CodeReviewResult]
    final_approval: bool
    quality_assessment: Literal["PRODUCTION", "ACCEPTABLE", "DEGRADED", "REJECTED"]
    artifact_path: Optional[str] = None
    tokens_used: int
    completion_time_ms: int

# ============================================
# VALIDATOR STRUCTURES
# ============================================

class ValidationIssue(BaseModel):
    type: Literal["correctness", "completeness", "quality", "safety"]
    severity: Literal["warning", "error"]
    description: str
    recoverable: bool

class ValidationResult(BaseModel):
    step_id: StepId
    correctness_score: ConfidenceScore
    completeness_score: ConfidenceScore
    quality_score: ConfidenceScore
    safety_score: ConfidenceScore
    validation_score: ConfidenceScore
    passed: bool
    issues: List[ValidationIssue]

class ValidatorRetryInfo(BaseModel):
    failing_steps: List[StepId]
    adjusted_parameters: Dict[str, Any]

class ValidatorResponse(BaseModel):
    status: Literal["success", "needs_retry", "needs_input", "fatal"]
    validation_results: List[ValidationResult]
    overall_score: ConfidenceScore
    action: Literal["PROCEED", "RETRY_WITH_ADJUSTMENTS", "ASK_USER", "ABORT"]
    retry_info: Optional[ValidatorRetryInfo] = None
    user_question: Optional[str] = None
    user_options: Optional[List[str]] = None
    abort_reason: Optional[str] = None
    attempt: int
    remaining_attempts: int

# ============================================
# SYNTHESIZER STRUCTURES
# ============================================

class SynthesizerMessage(BaseModel):
    summary: str
    body: str
    key_results: List[str]
    next_steps: Optional[List[str]] = None

class ArtifactReference(BaseModel):
    name: str
    type: Literal["file", "code", "document", "dataset"]
    path: str
    size_bytes: int
    mime_type: str
    download_url: Optional[str] = None

class DataSource(BaseModel):
    name: str
    type: Literal["realtime", "cached", "knowledge_cutoff"]
    freshness_minutes: int
    url: Optional[str] = None
    fetch_timestamp: Optional[str] = None

class SynthesisExecutionSummary(BaseModel):
    total_steps: int
    steps_completed: int
    execution_time_seconds: float
    status: ExecutionStatus
    confidence_score: ConfidenceScore

class FilesCreatedMetdata(BaseModel):
    count: int
    types: List[str]
    total_size_mb: float

class SynthesizerError(BaseModel):
    step: Optional[str] = None
    type: str
    severity: Literal["warning", "error"]
    recovery: str

class SynthesisOutput(BaseModel):
    task_id: TaskId
    message: SynthesizerMessage
    artifacts: List[ArtifactReference]
    data_sources: List[DataSource]
    execution_summary: SynthesisExecutionSummary
    tools_used: List[str]
    files_created: FilesCreatedMetdata
    errors_encountered: List[SynthesizerError]
    quality_assessment: Literal["production", "acceptable", "degraded"]

class SynthesizerResponse(BaseModel):
    status: Literal["success"]
    synthesis_output: SynthesisOutput

# ============================================
# ERROR STRUCTURES
# ============================================

class ErrorInfo(BaseModel):
    error_id: str
    timestamp: str
    tier: ErrorTier
    error_type: str
    phase: Phase
    step_id: Optional[StepId] = None
    message: str
    stack_trace: Optional[str] = None
    context: Dict[str, Any]
    recovery_attempted: bool
    recovery_strategy: Optional[Literal["AUTO", "USER_INPUT", "ABORT"]] = None
    recovery_result: Optional[Literal["SUCCESS", "FAILED", "TIMEOUT"]] = None

class ErrorUserOption(BaseModel):
    label: str
    description: str
    action: str

class ErrorResponse(BaseModel):
    error_id: str
    problem: str
    root_cause: str
    explanation: str
    user_options: List[ErrorUserOption]
    last_successful_step: Optional[str] = None
    partial_results: Any = None
    can_retry: bool
    recovery_time_estimate_seconds: Optional[int] = None
    requires_support: bool
    support_contact: Optional[str] = None

class ErrorHandlerResponse(BaseModel):
    status: Literal["handled", "escalated"]
    recovery_strategy: Optional[Literal["AUTO", "USER_INPUT", "ABORT"]] = None
    recovery_action: Optional[str] = None
    recovery_successful: Optional[bool] = None
    error_response: ErrorResponse
    escalation_level: Optional[Literal[1, 2, 3]] = None
    next_phase: Optional[Phase] = None

# ============================================
# REALTIME FETCHER STRUCTURES
# ============================================

class RealtimeFetchMetadata(BaseModel):
    fetch_timestamp: str
    data_age_minutes: int
    freshness_status: Literal["LIVE", "CACHED", "STALE", "FALLBACK"]
    source: str
    source_url: Optional[str] = None
    confidence: ConfidenceScore

class RealtimeFetchError(BaseModel):
    error_type: str
    message: str
    recovery: str

class RealtimeFetchResponse(BaseModel):
    status: Literal["success", "cached", "stale", "fallback", "failed"]
    data: Any = None
    metadata: RealtimeFetchMetadata
    error: Optional[RealtimeFetchError] = None
