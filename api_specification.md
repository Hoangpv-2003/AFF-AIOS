# API SPECIFICATION - AGENT PIPELINE v2.0
## Complete Interface Definitions

---

## TABLE OF CONTENTS
1. Core Data Types
2. Phase 1: Context Injection API
3. Phase 2: Intent Parser API
4. Phase 3: Planner API
5. Phase 4: Skill Router API
6. Phase 5: Realtime Fetcher API
7. Phase 6: Coder API
8. Phase 7: Skill Runner API
9. Phase 8: Result Validator API
10. Phase 9: Synthesizer API
11. Error Handler API
12. Session Management API

---

## PART 1: CORE DATA TYPES

```typescript
// ============================================
// FUNDAMENTAL TYPES
// ============================================

/** Unique identifier for session */
type SessionId = string & { readonly __brand: 'SessionId' };

/** Unique identifier for task/execution */
type TaskId = string & { readonly __brand: 'TaskId' };

/** Step identifier (S1, S2, etc) */
type StepId = string & { readonly __brand: 'StepId' };

/** Confidence score 0-1.0 */
type ConfidenceScore = number & { readonly __brand: 'ConfidenceScore' };

/** Execution status */
enum ExecutionStatus {
  PENDING = "pending",
  IN_PROGRESS = "in_progress",
  SUCCESS = "success",
  PARTIAL = "partial",
  FAILED = "failed",
  ABORTED = "aborted",
}

/** Phase names */
enum Phase {
  CONTEXT_INJECTION = "context_injection",
  INTENT_PARSER = "intent_parser",
  PLANNER = "planner",
  SKILL_ROUTER = "skill_router",
  REALTIME_FETCHER = "realtime_fetcher",
  CODER = "coder",
  SKILL_RUNNER = "skill_runner",
  RESULT_VALIDATOR = "result_validator",
  SYNTHESIZER = "synthesizer",
  DELIVERY = "delivery",
  ERROR_HANDLER = "error_handler",
}

/** Error severity tiers */
enum ErrorTier {
  TIER_1_TRANSIENT = 1,
  TIER_2_USER_RESOLVABLE = 2,
  TIER_3_FATAL = 3,
}

// ============================================
// CONTEXT STRUCTURES
// ============================================

interface ExecutionContext {
  session_id: SessionId;
  task_id: TaskId;
  user_message: string;
  current_phase: Phase;
  
  // Injected metadata
  datetime: {
    utc_timestamp: string;  // ISO-8601
    server_timezone: string;
    user_timezone: string;
    user_locale: string;
  };
  
  // Conversation history
  history: {
    total_turns: number;
    last_n_turns: Message[];  // max 10
    conversation_id: string;
  };
  
  // Tool availability
  tools_status: {
    [toolName: string]: {
      available: boolean;
      status: "available" | "degraded" | "unavailable";
      last_checked: string;
    };
  };
  
  // Session state
  session_state: {
    concurrent_tasks: number;
    max_concurrent: number;  // 3
    execution_time_elapsed: number;  // seconds
    max_execution_time: number;  // 600
  };
  
  // Realtime data cache
  realtime_cache: {
    [key: string]: {
      data: unknown;
      timestamp: string;
      freshness_minutes: number;
      data_age_minutes: number;
      source: string;
    };
  };
  
  // Step results
  step_results: {
    [stepId: string]: {
      status: ExecutionStatus;
      output: unknown;
      error?: Error;
      execution_time_ms: number;
      tokens_used: number;
    };
  };
  
  // Metadata
  metadata: {
    created_at: string;
    updated_at: string;
    version: string;
  };
}

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

// ============================================
// INTENT STRUCTURES
// ============================================

type ActionType = 
  | "create" | "read" | "transform" | "integrate" 
  | "search" | "decide" | "debug";

interface IntentOutput {
  action_type: ActionType;
  sub_actions: string[];
  
  // Data needs
  needs_realtime: boolean;
  realtime_data_types: ("sports" | "weather" | "news" | "web" | "location")[];
  needs_file_access: boolean;
  required_skills: string[];
  
  // Confidence metrics
  confidence: ConfidenceScore;
  confidence_breakdown: {
    clarity: ConfidenceScore;
    completeness: ConfidenceScore;
    feasibility: ConfidenceScore;
  };
  
  // Metadata
  assumptions: string[];
  clarifications_needed: boolean;
  clarification_count: number;
  complexity: "low" | "medium" | "high";
  
  // Next step
  next_phase: Phase;
  proceed_without_confirmation: boolean;
}

// ============================================
// EXECUTION PLAN STRUCTURES
// ============================================

interface ExecutionPlan {
  goal: string;
  
  steps: ExecutionStep[];
  
  // Dependency graph
  dependency_graph: {
    nodes: StepId[];
    edges: Array<[StepId, StepId]>;
    is_acyclic: boolean;
    cycle_check_passed: boolean;
    cycles_found?: Array<StepId[]>;  // if any
  };
  
  // Parallel execution groups
  parallelizable_groups: StepId[][];
  
  // Metadata
  total_steps: number;
  estimated_duration_seconds: number;
  total_estimated_tokens: number;
  
  // Abort conditions
  abort_conditions: string[];
  
  // Dependencies
  dependencies: {
    external_api: string[];
    file_system: ("read" | "write")[];
    user_interaction: boolean;
  };
  
  // Risk assessment
  risk_flags: string[];
}

interface ExecutionStep {
  step_id: StepId;
  action: string;
  
  // Execution details
  tool_required?: string;
  tool_type?: "skill" | "api" | "bash";
  
  // I/O specification
  input_requirements: string[];
  expected_output: {
    type: string;  // e.g., "file", "json", "text"
    schema?: unknown;
  };
  success_criteria: string;
  
  // Error handling
  error_modes: string[];
  error_recovery?: string;
  
  // Dependencies
  depends_on: StepId[];
  parallel_with: StepId[];
  
  // Execution constraints
  timeout_seconds: number;
  retry_allowed: boolean;
  max_retries: number;
  estimated_tokens: number;
  
  // Metadata
  complexity_score: number;  // 0-10
  critical: boolean;
}

// ============================================
// ROUTER DECISION STRUCTURES
// ============================================

type ExecutionPath = "REALTIME_FETCHER" | "SKILL_RUNNER" | "CODER" | "ERROR";

interface RouterDecision {
  step_id: StepId;
  execution_path: ExecutionPath;
  
  // Realtime needs
  realtime_needed: boolean;
  realtime_types: string[];
  fetch_timing: "NOW" | "DEFERRED" | "NONE";
  
  // Skill/tool info
  skill_name?: string;
  skill_available?: boolean;
  requires_patching?: boolean;
  
  // Coder action
  coder_action?: "PATCH" | "CREATE" | "NONE";
  
  // Metadata
  decision_rationale: string;
  confidence: ConfidenceScore;
}

// ============================================
// CODER STRUCTURES
// ============================================

enum CodeMode {
  PATCH = "patch",
  CREATE = "create",
}

interface CoderInput {
  mode: CodeMode;
  requirement: string;
  language: string;
  skill_source?: string;  // for PATCH mode
  constraints: string[];
}

interface CodeReviewResult {
  round: number;  // 1-3
  checks: {
    syntax: { passed: boolean; issues: string[] };
    logic: { passed: boolean; issues: string[] };
    error_handling: { passed: boolean; issues: string[] };
    performance: { passed: boolean; issues: string[] };
    security: { passed: boolean; issues: string[] };
    documentation: { passed: boolean; issues: string[] };
    edge_cases: { passed: boolean; issues: string[] };
    style: { passed: boolean; issues: string[] };
  };
  
  severity_score: number;  // 0-10
  quality_score: ConfidenceScore;
  
  issues_found: boolean;
  action: "APPROVED" | "NEEDS_FIX" | "REJECTED";
  recommended_fixes?: string[];
}

interface CoderOutput {
  code: string;
  language: string;
  mode: CodeMode;
  
  // Review results
  reviews: CodeReviewResult[];
  final_approval: boolean;
  quality_assessment: "PRODUCTION" | "ACCEPTABLE" | "DEGRADED" | "REJECTED";
  
  // Artifact info
  artifact_path: string;
  artifact_size_bytes: number;
  
  // Metadata
  completion_time_ms: number;
  tokens_used: number;
}

// ============================================
// SKILL RUNNER STRUCTURES
// ============================================

interface SkillRunnerInput {
  task_id: TaskId;
  steps_to_execute: ExecutionStep[];
  execution_context: ExecutionContext;
  parallelizable_groups: StepId[][];
}

interface StepExecution {
  step_id: StepId;
  status: ExecutionStatus;
  
  // Timing
  start_time: string;
  end_time: string;
  duration_ms: number;
  
  // Results
  output?: unknown;
  error?: Error;
  
  // Resource usage
  tokens_used: number;
  memory_used_mb: number;
  
  // Side effects
  files_created?: string[];
  state_changes?: Record<string, unknown>;
  
  // Logs
  stdout?: string;
  stderr?: string;
}

interface SkillRunnerOutput {
  task_id: TaskId;
  status: ExecutionStatus;
  
  // Results per step
  step_results: {
    [stepId: string]: StepExecution;
  };
  
  // Parallel group results
  parallel_group_results?: {
    [groupIndex: number]: {
      status: ExecutionStatus;
      merge_conflicts?: string[];
      merged_output?: unknown;
    };
  };
  
  // Aggregated metrics
  total_execution_time_ms: number;
  total_tokens_used: number;
  completed_steps: number;
  failed_steps: number;
}

// ============================================
// VALIDATOR STRUCTURES
// ============================================

interface ValidationCriteria {
  correctness: {
    weight: number;  // 0.4
    checks: string[];
  };
  completeness: {
    weight: number;  // 0.3
    checks: string[];
  };
  quality: {
    weight: number;  // 0.2
    checks: string[];
  };
  safety: {
    weight: number;  // 0.1
    checks: string[];
  };
}

interface ValidationResult {
  step_id: StepId;
  
  // Scores
  correctness_score: ConfidenceScore;
  completeness_score: ConfidenceScore;
  quality_score: ConfidenceScore;
  safety_score: ConfidenceScore;
  
  // Composite
  validation_score: ConfidenceScore;
  passed: boolean;  // score >= 0.80
  
  // Details
  issues: Array<{
    type: "correctness" | "completeness" | "quality" | "safety";
    severity: "warning" | "error";
    description: string;
    recoverable: boolean;
  }>;
}

interface ValidatorOutput {
  attempt: number;  // 1-2
  
  // Overall result
  all_passed: boolean;
  validation_results: ValidationResult[];
  
  // Decision
  action: "PROCEED" | "RETRY_WITH_ADJUSTMENTS" | "ASK_USER" | "ABORT";
  
  // Retry info (if action == RETRY)
  adjusted_parameters?: Record<string, unknown>;
  retry_step_ids?: StepId[];
  
  // User question (if action == ASK_USER)
  user_question?: string;
  user_options?: string[];
  
  // Abort reason (if action == ABORT)
  abort_reason?: string;
}

// ============================================
// SYNTHESIZER STRUCTURES
// ============================================

interface SynthesisInput {
  task_id: TaskId;
  execution_context: ExecutionContext;
  skill_runner_output: SkillRunnerOutput;
  errors?: Error[];
}

interface ArtifactReference {
  name: string;
  type: "file" | "code" | "document" | "dataset";
  path: string;
  size_bytes: number;
  mime_type: string;
  download_url?: string;
}

interface DataSource {
  name: string;
  type: "realtime" | "cached" | "knowledge_cutoff";
  freshness_minutes: number;
  url?: string;
  fetch_timestamp?: string;
}

interface SynthesisOutput {
  task_id: TaskId;
  
  // User-facing message
  message: {
    summary: string;  // 1-2 sentences
    body: string;  // Detailed explanation, max 5000 chars
    key_results: string[];  // Max 5
    next_steps?: string[];
  };
  
  // Artifacts
  artifacts: ArtifactReference[];
  
  // Data sources (for citations)
  data_sources: DataSource[];
  
  // Metadata
  execution_summary: {
    total_steps: number;
    steps_completed: number;
    execution_time_seconds: number;
    status: ExecutionStatus;
    confidence_score: ConfidenceScore;
  };
  
  tools_used: string[];
  files_created: {
    count: number;
    types: string[];
    total_size_mb: number;
  };
  
  errors_encountered: Array<{
    step?: string;
    type: string;
    severity: "warning" | "error";
    recovery: string;
  }>;
  
  quality_assessment: "production" | "acceptable" | "degraded";
}

// ============================================
// ERROR STRUCTURES
// ============================================

interface ErrorInfo {
  error_id: string;  // UUID
  timestamp: string;
  
  // Classification
  tier: ErrorTier;
  error_type: string;
  
  // Context
  phase: Phase;
  step_id?: StepId;
  
  // Details
  message: string;
  stack_trace?: string;
  context: Record<string, unknown>;
  
  // Recovery
  recovery_attempted: boolean;
  recovery_strategy?: "AUTO" | "USER_INPUT" | "ABORT";
  recovery_result?: "SUCCESS" | "FAILED" | "TIMEOUT";
}

interface ErrorResponse {
  error_id: string;
  problem: string;
  root_cause: string;
  
  // User guidance
  explanation: string;
  user_options: Array<{
    label: string;
    description: string;
    action: string;
  }>;
  
  // Context
  last_successful_step?: string;
  partial_results?: unknown;
  
  // Retry info
  can_retry: boolean;
  recovery_time_estimate_seconds?: number;
  
  // Escalation
  requires_support: boolean;
  support_contact?: string;
}

```

---

## PART 2: PHASE-BY-PHASE API DEFINITIONS

### PHASE 1: CONTEXT INJECTION API

```typescript
// ============================================
// CONTEXT INJECTION PHASE API
// ============================================

interface ContextInjectionRequest {
  user_message: string;
  session_id?: SessionId;  // null for new session
  include_history?: boolean;
  history_limit?: number;  // default 10
}

interface ContextInjectionResponse {
  status: "success" | "warning";
  
  execution_context: ExecutionContext;
  
  warnings?: Array<{
    field: string;
    message: string;
    severity: "info" | "warning";
  }>;
  
  // Next phase
  ready_for_phase2: boolean;
  phase2_input: Phase2Input;
}

// ============================================
// IMPLEMENTATION NOTES:
// ============================================
/*
POST /api/v1/context-injection
├─ Load server datetime (utc_timestamp)
├─ Validate timezone (user_timezone)
├─ Load conversation history (max 10 turns)
├─ Check tool availability (realtime)
├─ Check session state (concurrent tasks)
├─ Initialize realtime_cache if needed
└─ Return ExecutionContext

Timing: < 100ms
Dependencies: Database (history), Redis (cache), System (datetime)
Failure modes:
  ├─ History load fails: Continue with empty history (non-fatal)
  ├─ Timezone invalid: Use UTC fallback (non-fatal)
  └─ Tool status unavailable: Mark as "unknown" (non-fatal)
*/

// Example Request:
const request1: ContextInjectionRequest = {
  user_message: "Create a sales report from my Q4 data",
  include_history: true,
  history_limit: 10,
};

// Example Response:
const response1: ContextInjectionResponse = {
  status: "success",
  execution_context: {
    session_id: "sess_12345" as SessionId,
    task_id: "task_67890" as TaskId,
    user_message: "Create a sales report from my Q4 data",
    current_phase: Phase.CONTEXT_INJECTION,
    datetime: {
      utc_timestamp: "2026-03-24T10:30:00Z",
      server_timezone: "UTC",
      user_timezone: "America/New_York",
      user_locale: "en_US",
    },
    history: {
      total_turns: 2,
      last_n_turns: [
        {
          role: "user",
          content: "Hi there",
          timestamp: "2026-03-24T10:25:00Z",
        },
      ],
      conversation_id: "conv_abc",
    },
    tools_status: {
      web_search: { available: true, status: "available", last_checked: "2026-03-24T10:29:59Z" },
      create_file: { available: true, status: "available", last_checked: "2026-03-24T10:29:58Z" },
    },
    session_state: {
      concurrent_tasks: 1,
      max_concurrent: 3,
      execution_time_elapsed: 30,
      max_execution_time: 600,
    },
    realtime_cache: {},
    step_results: {},
    metadata: {
      created_at: "2026-03-24T10:30:00Z",
      updated_at: "2026-03-24T10:30:00Z",
      version: "2.0",
    },
  },
  ready_for_phase2: true,
  phase2_input: {
    user_message: "Create a sales report from my Q4 data",
    execution_context: { /* ... */ },
  },
};
```

---

### PHASE 2: INTENT PARSER API

```typescript
// ============================================
// INTENT PARSER PHASE API
// ============================================

interface Phase2Input {
  user_message: string;
  execution_context: ExecutionContext;
}

interface IntentParserRequest extends Phase2Input {
  confidence_threshold?: ConfidenceScore;  // default 0.75
  request_complexity?: "low" | "medium" | "high";
}

interface IntentParserResponse {
  status: "success" | "clarification_needed";
  
  intent_output?: IntentOutput;
  
  // If clarification needed
  clarification?: {
    questions: string[];
    max_questions: number;  // 3-5 depending on complexity
    timeout_seconds: number;  // 300
    options?: string[];
  };
  
  // Next step
  next_phase: Phase;
  proceed_to_phase3: boolean;
}

// ============================================
// IMPLEMENTATION NOTES:
// ============================================
/*
POST /api/v1/intent-parser
├─ Parse user message:
│  ├─ Extract action type
│  ├─ Identify sub-actions
│  ├─ Check for realtime data needs
│  └─ Assess complexity
│
├─ Calculate confidence:
│  ├─ Clarity (0-1.0)
│  ├─ Completeness (0-1.0)
│  ├─ Feasibility (0-1.0)
│  └─ Final = weighted average
│
├─ DECISION TREE:
│  ├─ IF confidence >= 0.75: RETURN IntentOutput
│  ├─ IF confidence < 0.75:
│  │  ├─ Determine complexity
│  │  ├─ IF low: Return with guess + disclaimer
│  │  ├─ IF medium: Return clarification (2-3 Q)
│  │  └─ IF high: Return clarification (4-5 Q)
│  └─ Timeout: If user doesn't respond in 5min, escalate
│
└─ RETURN IntentParserResponse

Timing: 1-5 seconds
Dependencies: NLP model, intent database
Failure modes:
  ├─ Invalid language: Escalate to TIER 2
  ├─ No matching action: Ask user to restate
  └─ Ambiguous: Ask clarifying questions
*/

// Example Request:
const request2: IntentParserRequest = {
  user_message: "Create a sales report from my Q4 data",
  execution_context: { /* ... */ },
  confidence_threshold: 0.75,
};

// Example Response (High Confidence):
const response2a: IntentParserResponse = {
  status: "success",
  intent_output: {
    action_type: "transform",
    sub_actions: ["locate_file", "analyze_data", "generate_report"],
    needs_realtime: false,
    realtime_data_types: [],
    needs_file_access: true,
    required_skills: ["xlsx", "docx"],
    confidence: 0.92,
    confidence_breakdown: {
      clarity: 0.95,
      completeness: 0.90,
      feasibility: 0.85,
    },
    assumptions: [
      "Q4 data is in user's uploaded files",
      "Business report format acceptable",
      "English output preferred",
    ],
    clarifications_needed: false,
    clarification_count: 0,
    complexity: "medium",
    next_phase: Phase.PLANNER,
    proceed_without_confirmation: true,
  },
  next_phase: Phase.PLANNER,
  proceed_to_phase3: true,
};

// Example Response (Low Confidence, Medium Complexity):
const response2b: IntentParserResponse = {
  status: "clarification_needed",
  clarification: {
    questions: [
      "Should the report include YoY comparisons?",
      "What format do you prefer (PDF, Word, or Excel)?",
      "Are there specific metrics you want highlighted?",
    ],
    max_questions: 3,
    timeout_seconds: 300,
  },
  next_phase: Phase.INTENT_PARSER,
  proceed_to_phase3: false,
};
```

---

### PHASE 3: PLANNER API

```typescript
// ============================================
// PLANNER PHASE API
// ============================================

interface Phase3Input {
  intent_output: IntentOutput;
  execution_context: ExecutionContext;
}

interface PlannerRequest extends Phase3Input {
  max_steps?: number;  // default 50
}

interface PlannerResponse {
  status: "success" | "error";
  
  // Success case
  execution_plan?: ExecutionPlan;
  
  // Error case (circular dependency)
  circular_dependency?: {
    detected: boolean;
    cycles: Array<StepId[]>;
    explanation: string;
    user_action_needed: string;
  };
  
  // Next phase
  next_phase: Phase;
}

// ============================================
// IMPLEMENTATION NOTES:
// ============================================
/*
POST /api/v1/planner
├─ Decompose intent into steps:
│  ├─ For each sub_action, create ExecutionStep
│  ├─ Determine dependencies (depends_on)
│  ├─ Identify parallel opportunities
│  └─ Estimate tokens/time per step
│
├─ BUILD DEPENDENCY GRAPH:
│  ├─ Create nodes: [S1, S2, S3, ...]
│  ├─ Create edges: from depends_on relationships
│  └─ Validate: Check for cycles
│
├─ CYCLE DETECTION (DFS):
│  ├─ FOR each unvisited node:
│  │  └─ dfs(node):
│  │     ├─ Mark visited[node] = true
│  │     ├─ Mark rec_stack[node] = true
│  │     ├─ FOR child in depends_on[node]:
│  │     │  ├─ IF NOT visited[child]: dfs(child)
│  │     │  └─ IF rec_stack[child]: CYCLE FOUND
│  │     └─ Mark rec_stack[node] = false
│  │
│  └─ IF cycle found:
│     ├─ Extract cycle path
│     ├─ RETURN circular_dependency error
│     ├─ Ask user to reorder requirements
│     └─ Return to PHASE 2
│
├─ PARALLEL GROUP IDENTIFICATION:
│  ├─ Find steps with no shared dependencies
│  ├─ Group into parallelizable sets
│  └─ Store in execution_plan.parallelizable_groups
│
└─ VALIDATE_PLAN:
   ├─ All success criteria defined? ✓
   ├─ All dependencies resolve? ✓
   ├─ Timeouts realistic? ✓
   └─ Resources sufficient? ✓

Timing: 1-3 seconds
Dependencies: Graph algorithms, task database
Failure modes:
  ├─ Circular dependency: Return error, ask user to clarify
  ├─ Too many steps (>50): Suggest breaking down
  └─ Missing critical steps: Ask user to clarify intent
*/

// Example Request:
const request3: PlannerRequest = {
  intent_output: { /* ... from response2a */ },
  execution_context: { /* ... */ },
};

// Example Response (Success):
const response3: PlannerResponse = {
  status: "success",
  execution_plan: {
    goal: "Generate comprehensive Q4 sales report",
    steps: [
      {
        step_id: "S1" as StepId,
        action: "Locate Q4 sales data file",
        tool_required: "bash_tool",
        input_requirements: ["user_uploads_directory"],
        expected_output: {
          type: "file_path",
          schema: { pattern: ".*\\.xlsx$" },
        },
        success_criteria: "File found and readable",
        error_modes: ["file_not_found", "permission_denied"],
        depends_on: [],
        parallel_with: [],
        timeout_seconds: 10,
        retry_allowed: true,
        max_retries: 1,
        estimated_tokens: 200,
        complexity_score: 2,
        critical: true,
      },
      {
        step_id: "S2" as StepId,
        action: "Analyze data structure and content",
        tool_required: "python_code",
        input_requirements: ["file_path_from_S1"],
        expected_output: {
          type: "json",
          schema: {
            record_count: "number",
            columns: "string[]",
            sample_row: "object",
          },
        },
        success_criteria: "Data structure identified, sample extracted",
        error_modes: ["invalid_format", "corrupted_data", "unsupported_format"],
        depends_on: ["S1" as StepId],
        parallel_with: [],
        timeout_seconds: 15,
        retry_allowed: true,
        max_retries: 1,
        estimated_tokens: 500,
        complexity_score: 5,
        critical: true,
      },
      {
        step_id: "S3" as StepId,
        action: "Generate formatted report document",
        tool_required: "docx_skill",
        input_requirements: ["analysis_from_S2", "metrics_template"],
        expected_output: {
          type: "file",
          schema: { ext: ".docx" },
        },
        success_criteria: "Professional report created with all metrics",
        error_modes: ["template_error", "formatting_error"],
        depends_on: ["S2" as StepId],
        parallel_with: [],
        timeout_seconds: 20,
        retry_allowed: true,
        max_retries: 1,
        estimated_tokens: 800,
        complexity_score: 6,
        critical: true,
      },
    ],
    dependency_graph: {
      nodes: ["S1" as StepId, "S2" as StepId, "S3" as StepId],
      edges: [
        ["S1" as StepId, "S2" as StepId],
        ["S2" as StepId, "S3" as StepId],
      ],
      is_acyclic: true,
      cycle_check_passed: true,
    },
    parallelizable_groups: [["S1" as StepId], ["S2" as StepId], ["S3" as StepId]],
    total_steps: 3,
    estimated_duration_seconds: 45,
    total_estimated_tokens: 1500,
    abort_conditions: [
      "S1 fails after retries",
      "total_execution_time > 60s",
      "user cancels",
    ],
    dependencies: {
      external_api: [],
      file_system: ["read"],
      user_interaction: false,
    },
    risk_flags: [],
  },
  next_phase: Phase.SKILL_ROUTER,
};
```

---

### PHASE 4: SKILL ROUTER API

```typescript
// ============================================
// SKILL ROUTER PHASE API
// ============================================

interface Phase4Input {
  execution_plan: ExecutionPlan;
  execution_context: ExecutionContext;
}

interface SkillRouterRequest extends Phase4Input {}

interface SkillRouterResponse {
  status: "success";
  
  routing_decisions: RouterDecision[];
  
  // Execution sequence
  execution_sequence: {
    realtime_fetches: Array<{
      data_type: string;
      timing: "NOW" | "DEFERRED";
      step_id: StepId;
    }>;
    coder_tasks: Array<{
      step_id: StepId;
      action: CodeMode;
    }>;
    skill_executions: Array<{
      step_id: StepId;
      skill_name: string;
    }>;
  };
  
  // Next phase
  next_phase: Phase;
  ready_for_execution: boolean;
}

// ============================================
// IMPLEMENTATION NOTES:
// ============================================
/*
POST /api/v1/skill-router
├─ FOR each step in execution_plan:
│  │
│  ├─ DECISION 1: REALTIME DATA?
│  │  ├─ IF yes:
│  │  │  ├─ Check dependencies
│  │  │  ├─ IF no early deps: fetch_timing = NOW
│  │  │  ├─ ELSE: fetch_timing = DEFERRED
│  │  │  └─ Add to realtime_fetches
│  │  └─ ELSE: continue
│  │
│  ├─ DECISION 2: SKILL AVAILABLE?
│  │  ├─ Query skill registry
│  │  ├─ IF available:
│  │  │  ├─ Check if patching needed
│  │  │  ├─ Route to CODER (patch) or SKILL_RUNNER (direct)
│  │  │  └─ Create RouterDecision
│  │  └─ ELSE: Go to DECISION 3
│  │
│  └─ DECISION 3: WRITE CODE?
│     ├─ IF code creation needed:
│     │  ├─ Route to CODER (create)
│     │  └─ Create RouterDecision with mode=CREATE
│     └─ ELSE: ERROR (no path)
│
├─ BUILD execution_sequence:
│  ├─ Schedule realtime fetches
│  ├─ Schedule coder tasks
│  └─ Schedule skill executions
│
└─ RETURN SkillRouterResponse

Timing: <1 second
Dependencies: Skill registry, tool status
Failure modes:
  ├─ No tool available: ERROR_HANDLER TIER 3
  ├─ Skill not callable: Route to CODER
  └─ Permission denied: ERROR_HANDLER TIER 2
*/

// Example Request:
const request4: SkillRouterRequest = {
  execution_plan: { /* ... from response3 */ },
  execution_context: { /* ... */ },
};

// Example Response:
const response4: SkillRouterResponse = {
  status: "success",
  routing_decisions: [
    {
      step_id: "S1" as StepId,
      execution_path: "SKILL_RUNNER",
      realtime_needed: false,
      realtime_types: [],
      fetch_timing: "NONE",
      skill_name: "bash_tool",
      skill_available: true,
      coder_action: "NONE",
      decision_rationale: "bash_tool available, no patching needed",
      confidence: 0.99,
    },
    {
      step_id: "S2" as StepId,
      execution_path: "CODER",
      realtime_needed: false,
      realtime_types: [],
      fetch_timing: "NONE",
      requires_patching: false,
      coder_action: "CREATE",
      decision_rationale: "No existing skill for this analysis, generate Python code",
      confidence: 0.85,
    },
    {
      step_id: "S3" as StepId,
      execution_path: "SKILL_RUNNER",
      realtime_needed: false,
      realtime_types: [],
      fetch_timing: "NONE",
      skill_name: "docx_skill",
      skill_available: true,
      coder_action: "NONE",
      decision_rationale: "docx_skill available and sufficient",
      confidence: 0.98,
    },
  ],
  execution_sequence: {
    realtime_fetches: [],
    coder_tasks: [
      {
        step_id: "S2" as StepId,
        action: CodeMode.CREATE,
      },
    ],
    skill_executions: [
      {
        step_id: "S1" as StepId,
        skill_name: "bash_tool",
      },
      {
        step_id: "S3" as StepId,
        skill_name: "docx_skill",
      },
    ],
  },
  next_phase: Phase.CODER,
  ready_for_execution: true,
};
```

---

### PHASE 5: REALTIME FETCHER API

```typescript
// ============================================
// REALTIME FETCHER PHASE API
// ============================================

type DataType = "sports" | "weather" | "news" | "web" | "location";

interface RealtimeFetchRequest {
  data_type: DataType;
  parameters: Record<string, unknown>;
  
  required_freshness_minutes: number;
  timeout_seconds?: number;  // default 10
  allow_cached?: boolean;  // default true
  allow_fallback?: boolean;  // default true
}

interface RealtimeFetchResponse {
  status: "success" | "cached" | "stale" | "fallback" | "failed";
  
  data?: unknown;
  
  metadata: {
    fetch_timestamp: string;
    data_age_minutes: number;
    freshness_status: "LIVE" | "CACHED" | "STALE" | "FALLBACK";
    source: string;
    source_url?: string;
    confidence: ConfidenceScore;
  };
  
  error?: {
    error_type: string;
    message: string;
    recovery: string;
  };
}

// ============================================
// IMPLEMENTATION NOTES:
// ============================================
/*
POST /api/v1/realtime-fetch
├─ IDENTIFY data tool:
│  ├─ sports → fetch_sports_data
│  ├─ weather → weather_fetch
│  ├─ web → web_search
│  ├─ location → places_search
│  └─ full_page → web_fetch
│
├─ CHECK CACHE:
│  ├─ key = hash(data_type, parameters)
│  ├─ IF cached_entry exists:
│  │  ├─ age = now - cached.timestamp
│  │  ├─ IF age < required_freshness:
│  │  │  └─ RETURN cached (status=cached)
│  │  └─ ELSE: Continue to fresh fetch
│  └─ ELSE: Continue to fresh fetch
│
├─ EXECUTE FETCH (with retries):
│  ├─ attempt = 0
│  ├─ WHILE attempt < 2:
│  │  ├─ Try to fetch with 10s timeout
│  │  ├─ IF success: Validate response, cache, RETURN
│  │  ├─ IF timeout: Calculate backoff
│  │  │  ├─ delay = min(0.5 × 2^attempt, 30)
│  │  │  ├─ Wait(delay)
│  │  │  └─ attempt += 1
│  │  └─ IF error: Classify, attempt += 1
│  │
│  └─ IF all retries fail: Continue to fallback
│
├─ FALLBACK:
│  ├─ IF allow_cached AND stale_cache exists:
│  │  ├─ RETURN cached (status=stale) with warning
│  │  └─ age > required_freshness
│  ├─ ELSE IF allow_fallback AND knowledge_cutoff exists:
│  │  └─ RETURN knowledge_cutoff (status=fallback)
│  └─ ELSE: RETURN error (status=failed)
│
└─ CACHE & RETURN:
   ├─ Store in execution_context.realtime_cache
   ├─ Set expiration = required_freshness × 1.5
   └─ Return RealtimeFetchResponse

Timing: 100-10,000 ms (depend on network)
Dependencies: External APIs, Redis cache
Failure modes:
  ├─ Network timeout: Retry with backoff
  ├─ Rate limit: Wait and retry
  ├─ Invalid response: Fallback to cache
  └─ All fallbacks fail: Return error
*/

// Example Request:
const request5: RealtimeFetchRequest = {
  data_type: "weather",
  parameters: { location: "Hanoi", unit: "celsius" },
  required_freshness_minutes: 15,
  timeout_seconds: 10,
  allow_cached: true,
  allow_fallback: true,
};

// Example Response (Success):
const response5: RealtimeFetchResponse = {
  status: "success",
  data: {
    temperature: 28,
    condition: "Partly Cloudy",
    humidity: 65,
    wind_speed: 12,
  },
  metadata: {
    fetch_timestamp: "2026-03-24T10:30:15Z",
    data_age_minutes: 0,
    freshness_status: "LIVE",
    source: "weather.com",
    source_url: "https://weather.com/hanoi",
    confidence: 0.99,
  },
};
```

---

### PHASE 6: CODER API

```typescript
// ============================================
// CODER PHASE API
// ============================================

interface CoderRequest {
  step_id: StepId;
  
  // Code creation spec
  requirement: string;
  language: string;
  mode: CodeMode;
  
  // For PATCH mode
  existing_skill?: string;
  patch_scope?: string;
  
  // Constraints
  constraints: string[];
  expected_output_schema?: unknown;
  
  // Context
  execution_context: ExecutionContext;
}

interface CoderCheckResponse {
  status: "success" | "error";
  code?: string;
  language: string;
  
  reviews: CodeReviewResult[];
  final_approval: boolean;
  quality_assessment: "PRODUCTION" | "ACCEPTABLE" | "DEGRADED" | "REJECTED";
  
  artifact_path?: string;
  tokens_used: number;
  completion_time_ms: number;
}

// ============================================
// IMPLEMENTATION NOTES:
// ============================================
/*
POST /api/v1/coder
├─ DETERMINE MODE:
│  ├─ IF mode == PATCH:
│  │  └─ Go to PATCH_FLOW
│  └─ ELSE IF mode == CREATE:
│     └─ Go to CREATE_FLOW
│
├─ PATCH_FLOW:
│  ├─ Load existing_skill source
│  ├─ Identify what to change
│  ├─ Generate delta (< 20 lines)
│  ├─ REVIEW_ROUND_1:
│  │  ├─ Self-review (syntax, logic, compatibility)
│  │  ├─ IF pass: APPROVED, Continue
│  │  └─ IF fail: Fix and REVIEW_ROUND_2
│  ├─ REVIEW_ROUND_2:
│  │  ├─ Re-review fixed code
│  │  ├─ IF pass: APPROVED, Continue
│  │  └─ IF fail: Too complex, switch to CREATE_FLOW
│  └─ Max 2 rounds for PATCH
│
├─ CREATE_FLOW:
│  ├─ Analyze requirement spec
│  ├─ Generate_complete implementation
│  ├─ Include error handling & docs
│  │
│  ├─ REVIEW_ROUND_1:
│  │  ├─ Run 10-item checklist:
│  │  │  ├─ Syntax valid?
│  │  │  ├─ Logic implements spec?
│  │  │  ├─ Error handling complete?
│  │  │  ├─ Performance acceptable?
│  │  │  ├─ Security OK?
│  │  │  ├─ Documentation adequate?
│  │  │  ├─ Edge cases handled?
│  │  │  ├─ Code style consistent?
│  │  │  ├─ Dependencies listed?
│  │  │  └─ Testable?
│  │  │
│  │  ├─ Calculate severity (0-10)
│  │  ├─ IF severity > 6: Fix and continue to ROUND 2
│  │  ├─ IF severity <= 6: Log warnings, APPROVED
│  │  └─ Generate quality_score
│  │
│  ├─ REVIEW_ROUND_2 (if needed):
│  │  ├─ Fix issues from ROUND 1
│  │  ├─ Run same checklist
│  │  ├─ IF all_pass: APPROVED
│  │  └─ IF still_issues: Continue to ROUND 3
│  │
│  └─ REVIEW_ROUND_3 (final, if needed):
│     ├─ Run same checklist
│     ├─ IF all_pass: APPROVED
│     └─ IF fail: REJECTED, escalate to ERROR_HANDLER
│
├─ CREATE ARTIFACT:
│  ├─ Write to /mnt/user-data/outputs/
│  ├─ Name: [purpose]_[timestamp].[ext]
│  └─ Metadata: language, lines, tokens
│
└─ RETURN CoderCheckResponse

Timing: 5-30 seconds per code generation
Dependencies: LLM, code analysis tools
Failure modes:
  ├─ Invalid requirement: Ask for clarification
  ├─ Too complex: Simplify or break down
  ├─ Failed all reviews: Escalate to ERROR_HANDLER
  └─ Unsupported language: TIER 3 error
*/

// Example Request:
const request6: CoderRequest = {
  step_id: "S2" as StepId,
  requirement: `
    Write Python code to analyze sales data from Excel file.
    Input: File path to .xlsx with columns [date, region, revenue, product]
    Output: JSON with {total_revenue, top_region, top_product, growth_pct}
    Error handling: Catch corrupt data, missing columns
  `,
  language: "python",
  mode: CodeMode.CREATE,
  constraints: [
    "Use pandas for data processing",
    "Handle missing values",
    "Return JSON format",
  ],
  execution_context: { /* ... */ },
};

// Example Response:
const response6: CoderCheckResponse = {
  status: "success",
  code: `
import pandas as pd
import json
from pathlib import Path

def analyze_sales_data(file_path: str) -> dict:
    """Analyze sales data from Excel file."""
    try:
        # Load data
        df = pd.read_excel(file_path)
        
        # Validate columns
        required_cols = ['date', 'region', 'revenue', 'product']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns")
        
        # Analysis
        total_revenue = df['revenue'].sum()
        top_region = df.groupby('region')['revenue'].sum().idxmax()
        top_product = df.groupby('product')['revenue'].sum().idxmax()
        
        # Growth calculation
        recent = df[df['date'] >= df['date'].max() - pd.Timedelta(days=30)]
        earlier = df[df['date'] < df['date'].max() - pd.Timedelta(days=30)]
        growth_pct = ((recent['revenue'].sum() - earlier['revenue'].sum()) 
                      / earlier['revenue'].sum() * 100)
        
        return {
            "total_revenue": float(total_revenue),
            "top_region": str(top_region),
            "top_product": str(top_product),
            "growth_pct": float(growth_pct),
        }
    except Exception as e:
        raise RuntimeError(f"Analysis failed: {str(e)}")

if __name__ == "__main__":
    result = analyze_sales_data("sales_data.xlsx")
    print(json.dumps(result, indent=2))
  `,
  language: "python",
  reviews: [
    {
      round: 1,
      checks: {
        syntax: { passed: true, issues: [] },
        logic: { passed: true, issues: [] },
        error_handling: { passed: true, issues: [] },
        performance: { passed: true, issues: [] },
        security: { passed: true, issues: [] },
        documentation: { passed: true, issues: [] },
        edge_cases: { passed: true, issues: [] },
        style: { passed: true, issues: [] },
      },
      severity_score: 0,
      quality_score: 0.95,
      issues_found: false,
      action: "APPROVED",
    },
  ],
  final_approval: true,
  quality_assessment: "PRODUCTION",
  artifact_path: "/mnt/user-data/outputs/analyze_sales_20260324_103015.py",
  tokens_used: 1200,
  completion_time_ms: 8500,
};
```

---

### PHASE 7: SKILL RUNNER API

```typescript
// ============================================
// SKILL RUNNER PHASE API
// ============================================

interface SkillRunnerRequest {
  task_id: TaskId;
  steps_to_execute: ExecutionStep[];
  execution_context: ExecutionContext;
  parallelizable_groups: StepId[][];
}

interface SkillRunnerResponse {
  status: ExecutionStatus;
  
  step_results: {
    [stepId: string]: StepExecution;
  };
  
  parallel_group_results?: {
    [groupIndex: number]: {
      status: ExecutionStatus;
      merge_conflicts?: string[];
    };
  };
  
  metrics: {
    total_execution_time_ms: number;
    total_tokens_used: number;
    completed_steps: number;
    failed_steps: number;
  };
}

// ============================================
// IMPLEMENTATION NOTES:
// ============================================
/*
POST /api/v1/skill-runner
├─ FOR each parallelizable_group:
│  │
│  ├─ IF group has 1 step:
│  │  └─ Execute_sequential(step)
│  │
│  └─ IF group has multiple steps:
│     ├─ Create promises for each step
│     ├─ Promise.all(promises)
│     ├─ Timeout = max(step.timeout) + 5
│     ├─ Collect outputs
│     └─ Check for conflicts (shared state)
│
├─ FOR each step:
│  │
│  ├─ PRE_EXECUTION:
│  │  ├─ Verify inputs exist
│  │  ├─ Check tool availability
│  │  ├─ Authenticate
│  │  └─ Start timer
│  │
│  ├─ EXECUTION:
│  │  ├─ Load tool/skill handler
│  │  ├─ Call with parameters
│  │  ├─ Enforce timeout
│  │  └─ Capture output & logs
│  │
│  ├─ POST_EXECUTION:
│  │  ├─ Collect return value
│  │  ├─ Record side effects (files, state)
│  │  ├─ Log metrics (time, tokens)
│  │  └─ Store in step_results[step_id]
│  │
│  └─ ERROR HANDLING:
│     ├─ Catch and log
│     ├─ Mark step status = failed
│     └─ Continue (don't retry here)
│
└─ RETURN SkillRunnerResponse

Timing: Varies per step (typically 10-30s)
Dependencies: Tool/skill executors, filesystem
Failure modes:
  ├─ Tool timeout: Continue (let validator handle)
  ├─ Tool error: Log and continue
  ├─ Parallel conflict: Log warning, apply merge
  └─ File not found: Continue (validator will catch)
*/

// Example Request:
const request7: SkillRunnerRequest = {
  task_id: "task_67890" as TaskId,
  steps_to_execute: [
    { /* S1 ExecutionStep */ },
    { /* S2 ExecutionStep */ },
    { /* S3 ExecutionStep */ },
  ],
  execution_context: { /* ... */ },
  parallelizable_groups: [["S1" as StepId], ["S2" as StepId], ["S3" as StepId]],
};

// Example Response:
const response7: SkillRunnerResponse = {
  status: ExecutionStatus.SUCCESS,
  step_results: {
    "S1": {
      step_id: "S1" as StepId,
      status: ExecutionStatus.SUCCESS,
      start_time: "2026-03-24T10:31:00Z",
      end_time: "2026-03-24T10:31:08Z",
      duration_ms: 8000,
      output: "/mnt/user-data/uploads/sales_q4_2026.xlsx",
      tokens_used: 150,
      memory_used_mb: 45,
      files_created: ["/mnt/user-data/uploads/sales_q4_2026.xlsx"],
    },
    "S2": {
      step_id: "S2" as StepId,
      status: ExecutionStatus.SUCCESS,
      start_time: "2026-03-24T10:31:10Z",
      end_time: "2026-03-24T10:31:22Z",
      duration_ms: 12000,
      output: {
        record_count: 10245,
        columns: ["date", "region", "revenue", "product"],
        sample_row: {
          date: "2026-01-15",
          region: "Northeast",
          revenue: 15000,
          product: "Widget X",
        },
        total_revenue: 2300000,
        top_region: "Northeast",
        growth_pct: 18.5,
      },
      tokens_used: 800,
      memory_used_mb: 120,
    },
    "S3": {
      step_id: "S3" as StepId,
      status: ExecutionStatus.SUCCESS,
      start_time: "2026-03-24T10:31:25Z",
      end_time: "2026-03-24T10:31:40Z",
      duration_ms: 15000,
      output: "/mnt/user-data/outputs/Q4_Sales_Report_20260324.docx",
      tokens_used: 950,
      memory_used_mb: 85,
      files_created: ["/mnt/user-data/outputs/Q4_Sales_Report_20260324.docx"],
    },
  },
  metrics: {
    total_execution_time_ms: 35000,
    total_tokens_used: 1900,
    completed_steps: 3,
    failed_steps: 0,
  },
};
```

---

### PHASE 8: RESULT VALIDATOR API

```typescript
// ============================================
// RESULT VALIDATOR PHASE API
// ============================================

interface ValidatorRequest {
  skill_runner_output: SkillRunnerResponse;
  execution_context: ExecutionContext;
  execution_plan: ExecutionPlan;
  attempt: number;  // 1-2
}

interface ValidatorResponse {
  status: "success" | "needs_retry" | "needs_input" | "fatal";
  
  validation_results: ValidationResult[];
  overall_score: ConfidenceScore;
  
  // Decision
  action: "PROCEED" | "RETRY_WITH_ADJUSTMENTS" | "ASK_USER" | "ABORT";
  
  // Details per action
  retry_info?: {
    failing_steps: StepId[];
    adjusted_parameters: Record<string, unknown>;
  };
  
  user_question?: string;
  user_options?: string[];
  
  abort_reason?: string;
  
  // Metadata
  attempt: number;
  remaining_attempts: number;
}

// ============================================
// IMPLEMENTATION NOTES:
// ============================================
/*
POST /api/v1/result-validator
├─ Initialize:
│  ├─ validation_attempt = parameter from request
│  └─ MAX_ATTEMPTS = 2 (ENFORCED)
│
├─ FOR each step_output:
│  │
│  ├─ CORRECTNESS CHECKS (weight 0.4):
│  │  ├─ Output matches spec?
│  │  ├─ All fields present?
│  │  ├─ Data types correct?
│  │  └─ No corrupted data?
│  │
│  ├─ COMPLETENESS CHECKS (weight 0.3):
│  │  ├─ All sub-tasks done?
│  │  ├─ No missing pieces?
│  │  └─ All outputs created?
│  │
│  ├─ QUALITY CHECKS (weight 0.2):
│  │  ├─ Quality acceptable?
│  │  ├─ Performance OK?
│  │  └─ No critical warnings?
│  │
│  ├─ SAFETY CHECKS (weight 0.1):
│  │  ├─ No malicious content?
│  │  ├─ No PII exposed?
│  │  └─ Ethical OK?
│  │
│  └─ Score = weighted average
│
├─ DECISION LOGIC:
│  │
│  ├─ IF all_scores >= 0.80:
│  │  ├─ overall_score = avg(scores)
│  │  └─ action = PROCEED
│  │     └─ Continue to PHASE 9
│  │
│  ├─ IF some_scores < 0.80:
│  │  │
│  │  ├─ CATEGORIZE failures:
│  │  │  ├─ Type A: Recoverable
│  │  │  │  ├─ timeout, transient error, param issue
│  │  │  │  └─ CAN RETRY
│  │  │  │
│  │  │  ├─ Type B: User decision needed
│  │  │  │  ├─ Missing data, ambiguous output
│  │  │  │  └─ NEEDS USER INPUT
│  │  │  │
│  │  │  └─ Type C: Unrecoverable
│  │  │     ├─ Fundamental error, impossible task
│  │  │     └─ MUST ABORT
│  │  │
│  │  ├─ IF Type A AND attempt < 2:
│  │  │  ├─ Identify root cause
│  │  │  ├─ Adjust parameters:
│  │  │  │  ├─ timeout += 50%
│  │  │  │  ├─ retry_limit += 1
│  │  │  │  ├─ Normalize inputs
│  │  │  │  └─ Try alternative tool
│  │  │  │
│  │  │  ├─ Route to SKILL_RUNNER (not PLANNER!)
│  │  │  │  └─ REASON: Avoid infinite loop
│  │  │  │
│  │  │  ├─ action = RETRY_WITH_ADJUSTMENTS
│  │  │  └─ Loop back to SKILL_RUNNER
│  │  │
│  │  ├─ IF Type B:
│  │  │  ├─ Pause execution
│  │  │  ├─ Ask user question
│  │  │  ├─ Present options
│  │  │  ├─ action = ASK_USER
│  │  │  └─ WAIT for response (5min timeout)
│  │  │     └─ Resume VALIDATOR (attempt unchanged)
│  │  │
│  │  └─ IF Type C OR attempt >= 2:
│  │     ├─ action = ABORT
│  │     └─ Route to ERROR_HANDLER (TIER 3)
│  │
│  └─ ENFORCE: attempt < 2 (hard limit)
│
└─ RETURN ValidatorResponse

Timing: 1-5 seconds
Dependencies: Validation rules database
Failure modes:
  ├─ Ambiguous validation result: Score just below 0.80
  │  └─ Default to RETRY_WITH_ADJUSTMENTS
  ├─ User timeout on question: Apply default action
  └─ Unexpected error format: Log and ABORT
*/

// Example Request:
const request8: ValidatorRequest = {
  skill_runner_output: { /* ... from response7 */ },
  execution_context: { /* ... */ },
  execution_plan: { /* ... */ },
  attempt: 1,
};

// Example Response (All Pass):
const response8a: ValidatorResponse = {
  status: "success",
  validation_results: [
    {
      step_id: "S1" as StepId,
      correctness_score: 1.0,
      completeness_score: 1.0,
      quality_score: 0.95,
      safety_score: 1.0,
      validation_score: 0.99,
      passed: true,
      issues: [],
    },
    {
      step_id: "S2" as StepId,
      correctness_score: 0.98,
      completeness_score: 1.0,
      quality_score: 0.92,
      safety_score: 1.0,
      validation_score: 0.97,
      passed: true,
      issues: [],
    },
    {
      step_id: "S3" as StepId,
      correctness_score: 1.0,
      completeness_score: 0.99,
      quality_score: 0.98,
      safety_score: 1.0,
      validation_score: 0.99,
      passed: true,
      issues: [],
    },
  ],
  overall_score: 0.98,
  action: "PROCEED",
  attempt: 1,
  remaining_attempts: 1,
};

// Example Response (Recoverable Failure):
const response8b: ValidatorResponse = {
  status: "needs_retry",
  validation_results: [
    {
      step_id: "S2" as StepId,
      correctness_score: 0.65,
      completeness_score: 0.70,
      quality_score: 0.60,
      safety_score: 1.0,
      validation_score: 0.72,
      passed: false,
      issues: [
        {
          type: "completeness",
          severity: "error",
          description: "Missing 2 expected columns in output",
          recoverable: true,
        },
      ],
    },
  ],
  overall_score: 0.72,
  action: "RETRY_WITH_ADJUSTMENTS",
  retry_info: {
    failing_steps: ["S2" as StepId],
    adjusted_parameters: {
      timeout_seconds: 22.5,  // 15 * 1.5
      max_retries: 2,
      input_validation: true,
    },
  },
  attempt: 1,
  remaining_attempts: 1,
};
```

---

### PHASE 9: SYNTHESIZER API

```typescript
// ============================================
// SYNTHESIZER PHASE API
// ============================================

interface SynthesizerRequest {
  task_id: TaskId;
  execution_context: ExecutionContext;
  skill_runner_output: SkillRunnerResponse;
  validation_results?: ValidationResult[];
  errors?: ErrorInfo[];
}

interface SynthesizerResponse {
  status: "success";
  synthesis_output: SynthesisOutput;
}

// ============================================
// IMPLEMENTATION NOTES:
// ============================================
/*
POST /api/v1/synthesizer
├─ AGGREGATE RESULTS:
│  ├─ Collect all step outputs
│  ├─ Merge parallel results
│  ├─ Compile final state
│  └─ Check for data loss
│
├─ PREPARE ARTIFACTS:
│  ├─ FOR files:
│  │  ├─ Move to /mnt/user-data/outputs/
│  │  ├─ Verify downloadable
│  │  └─ Generate links
│  │
│  ├─ FOR code:
│  │  ├─ Tag as [ARTIFACT]
│  │  ├─ Add usage instructions
│  │  ├─ List dependencies
│  │  └─ Provide integration guidance
│  │
│  ├─ FOR data:
│  │  ├─ Summarize findings
│  │  ├─ Highlight insights
│  │  ├─ Include charts/tables
│  │  └─ Note caveats
│  │
│  └─ FOR visuals:
│     ├─ Choose widget type
│     ├─ Optimize display
│     ├─ Add interactions
│     └─ Include context
│
├─ COMPOSE MESSAGE:
│  ├─ Opening summary (1-2 sentences)
│  ├─ Key results (max 5 items)
│  ├─ Detailed explanation
│  ├─ Artifacts section
│  ├─ Data sources (if realtime)
│  ├─ Confidence info
│  └─ Next steps (optional)
│
├─ CITE SOURCES:
│  ├─ IF realtime_data used:
│  │  ├─ Format: "According to [SOURCE] (fetched TIMESTAMP)"
│  │  ├─ Include URL
│  │  └─ Mark freshness
│  │
│  └─ COPYRIGHT COMPLIANCE:
│     ├─ NO quotes > 15 words
│     ├─ ONE quote per source MAX
│     ├─ Paraphrase everything else
│     └─ Proper attribution always
│
├─ COMPILE METADATA:
│  ├─ Execution summary (time, steps, status)
│  ├─ Tools used
│  ├─ Data sources
│  ├─ Files created
│  ├─ Errors (if any)
│  └─ Quality assessment
│
└─ RETURN SynthesizerResponse

Timing: 1-3 seconds
Dependencies: File I/O, formatting engine
Failure modes:
  ├─ File move fails: Log warning, continue (user notified)
  ├─ Format render fails: Fallback to text
  └─ URL generation fails: Provide file path instead
*/

// Example Request:
const request9: SynthesizerRequest = {
  task_id: "task_67890" as TaskId,
  execution_context: { /* ... */ },
  skill_runner_output: { /* ... from response7 */ },
  validation_results: [ /* ... from response8a */ ],
};

// Example Response:
const response9: SynthesizerResponse = {
  status: "success",
  synthesis_output: {
    task_id: "task_67890" as TaskId,
    message: {
      summary: "Q4 sales report generated successfully with comprehensive metrics and analysis.",
      body: `
Your Q4 2026 sales report has been completed and is ready for download.

The analysis processed 10,245 sales records spanning October through December 2026.

**Key Metrics:**
- Total Q4 Revenue: $2,300,000 (↑18.5% vs Q3)
- Top Performing Region: Northeast (34% of revenue)
- Best Product: Widget X ($787,500 in sales)
- Average Order Value: $225

**Regional Performance:**
Northeast led all regions with $782,000 in Q4 sales, followed by Southeast ($695,000) 
and Midwest ($549,000). The Northeast region showed consistent growth throughout the quarter.

**Product Analysis:**
Widget X emerged as the top product, representing 34% of Q4 sales. Widget B and Widget C 
followed with 28% and 25% respectively. Widget D underperformed (13%) and may warrant 
strategic review.

**Recommendations:**
1. Increase marketing investment in Northeast region
2. Investigate Widget D performance decline
3. Plan Q1 inventory based on Q4 demand patterns
4. Consider regional pricing optimization

The detailed report document includes month-by-month breakdowns, customer segment analysis, 
and growth trend analysis.
      `,
      key_results: [
        "Total Revenue: $2.3M (↑18.5% YoY)",
        "Top Region: Northeast (34% share)",
        "Top Product: Widget X ($787.5K)",
        "Customer Growth: +2,450 accounts",
        "Report Status: Complete & Verified",
      ],
      next_steps: [
        "Review detailed report for strategic planning",
        "Share with leadership team",
        "Use insights for Q1 budget allocation",
      ],
    },
    artifacts: [
      {
        name: "Q4_Sales_Report_20260324.docx",
        type: "document",
        path: "/mnt/user-data/outputs/Q4_Sales_Report_20260324.docx",
        size_bytes: 245680,
        mime_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        download_url: "https://claude.ai/download/Q4_Sales_Report_20260324.docx",
      },
    ],
    data_sources: [
      {
        name: "Q4 Sales Data",
        type: "cached",
        freshness_minutes: 0,
        url: "/mnt/user-data/uploads/sales_q4_2026.xlsx",
      },
    ],
    execution_summary: {
      total_steps: 3,
      steps_completed: 3,
      execution_time_seconds: 35,
      status: ExecutionStatus.SUCCESS,
      confidence_score: 0.98,
    },
    tools_used: ["bash_tool", "python_code", "docx_skill"],
    files_created: {
      count: 1,
      types: ["docx"],
      total_size_mb: 0.24,
    },
    errors_encountered: [],
    quality_assessment: "production",
  },
};
```

---

### PHASE 10: ERROR HANDLER API

```typescript
// ============================================
// ERROR HANDLER PHASE API
// ============================================

interface ErrorHandlerRequest {
  error_info: ErrorInfo;
  execution_context: ExecutionContext;
  partial_results?: unknown;
}

interface ErrorHandlerResponse {
  status: "handled" | "escalated";
  
  recovery_strategy?: "AUTO" | "USER_INPUT" | "ABORT";
  recovery_action?: string;
  recovery_successful?: boolean;
  
  error_response: ErrorResponse;
  
  // If escalating
  escalation_level?: 1 | 2 | 3;
  next_phase?: Phase;
}

// ============================================
// IMPLEMENTATION NOTES:
// ============================================
/*
POST /api/v1/error-handler
├─ CLASSIFY ERROR:
│  ├─ tier_1_transient: Network, rate_limit, timeout
│  ├─ tier_2_user_input: Ambiguity, missing data, permission
│  └─ tier_3_fatal: Unsupported, impossible, security
│
├─ TIER 1 HANDLING:
│  ├─ Implement exponential backoff
│  ├─ delay = min(0.5 × 2^attempt, 30) + jitter
│  ├─ max_total_wait = 120s
│  ├─ Retry operation
│  ├─ IF success: Resume normal flow
│  └─ IF all_retries_fail: Escalate to TIER 2
│
├─ TIER 2 HANDLING:
│  ├─ Pause execution
│  ├─ Explain problem clearly
│  ├─ Present options
│  ├─ Wait for user (5min timeout)
│  ├─ IF response: Apply user choice, resume
│  └─ IF timeout: Escalate to TIER 3
│
├─ TIER 3 HANDLING:
│  ├─ ABORT immediately
│  ├─ Save partial results
│  ├─ Generate error report:
│  │  ├─ What happened
│  │  ├─ Why it failed
│  │  ├─ Last successful step
│  │  ├─ Partial results
│  │  └─ Suggested next steps
│  ├─ Present to user
│  └─ End task (allow manual retry)
│
└─ RETURN ErrorHandlerResponse

Timing: Varies (retry loop may be 1-130s)
Dependencies: Retry logic, user interaction
Failure modes:
  ├─ Recovery fails: Continue escalation
  ├─ User never responds: Apply timeout default
  └─ Partial result save fails: Log and continue
*/

// Example Tier 1 Error:
const error1: ErrorInfo = {
  error_id: "err_network_001",
  timestamp: "2026-03-24T10:32:15Z",
  tier: ErrorTier.TIER_1_TRANSIENT,
  error_type: "network_timeout",
  phase: Phase.REALTIME_FETCHER,
  message: "Connection timeout fetching weather data",
  context: {
    data_type: "weather",
    timeout_seconds: 10,
    attempt: 1,
  },
};

const errorResponse1: ErrorHandlerResponse = {
  status: "handled",
  recovery_strategy: "AUTO",
  recovery_action: "retry_with_backoff",
  recovery_successful: true,
  error_response: {
    error_id: "err_network_001",
    problem: "Temporary network timeout",
    root_cause: "Weather API not responding within 10 seconds",
    explanation: "Retried with 2 second delay - connection succeeded on second attempt",
    user_options: [
      {
        label: "Continue",
        description: "Using fresh weather data from retry",
        action: "proceed",
      },
    ],
    can_retry: true,
  },
};

// Example Tier 3 Error:
const error3: ErrorInfo = {
  error_id: "err_unsupported_001",
  timestamp: "2026-03-24T10:33:00Z",
  tier: ErrorTier.TIER_3_FATAL,
  error_type: "unsupported_operation",
  phase: Phase.CODER,
  step_id: "S2" as StepId,
  message: "Code review failed 3 times - too complex",
  context: {
    language: "python",
    rounds: 3,
    quality_scores: [0.65, 0.72, 0.68],
  },
};

const errorResponse3: ErrorHandlerResponse = {
  status: "escalated",
  recovery_strategy: "ABORT",
  escalation_level: 3,
  error_response: {
    error_id: "err_unsupported_001",
    problem: "Unable to automatically generate required code",
    root_cause: "Code complexity exceeded auto-generation capabilities after 3 review attempts",
    explanation: `
The required data analysis code is more complex than automatic generation can handle.
The code quality score was 0.72 (target: 0.85) after 3 optimization rounds.

This could be due to:
1. Ambiguous data structure requirements
2. Complex business logic that needs clarification
3. Missing specification details

Last successful step: S1 (data file located successfully)
Partial results: File path verified, ready for manual processing
    `,
    user_options: [
      {
        label: "Simplify Requirements",
        description: "Provide more specific requirements to narrow scope",
        action: "return_to_intent_parser",
      },
      {
        label: "Break Into Smaller Tasks",
        description: "Split into multiple simpler analysis steps",
        action: "replan",
      },
      {
        label: "Use Existing Template",
        description: "Select from pre-built analysis templates",
        action: "suggest_alternatives",
      },
      {
        label: "Contact Support",
        description: "Escalate to human support team",
        action: "escalate_to_support",
      },
    ],
    last_successful_step: "S1: Locate Q4 sales data file",
    partial_results: {
      file_path: "/mnt/user-data/uploads/sales_q4_2026.xlsx",
      file_status: "verified_readable",
    },
    can_retry: false,
    requires_support: true,
    support_contact: "support@claude.ai",
  },
};
```

---

### SESSION MANAGEMENT API

```typescript
// ============================================
// SESSION MANAGEMENT API
// ============================================

interface SessionInitRequest {
  user_id: string;
  initial_message?: string;
}

interface SessionInitResponse {
  session_id: SessionId;
  status: "initialized";
  execution_context: ExecutionContext;
}

interface SessionCleanupRequest {
  session_id: SessionId;
  end_reason: "completion" | "timeout" | "user_cancel" | "error";
}

interface SessionCleanupResponse {
  session_id: SessionId;
  status: "cleaned";
  
  summary: {
    total_tasks: number;
    successful_tasks: number;
    failed_tasks: number;
    total_execution_time_ms: number;
    total_tokens_used: number;
  };
  
  artifacts_created: string[];
}

// ============================================
// IMPLEMENTATION NOTES:
// ============================================
/*
POST /api/v1/session/init
├─ Generate session_id (UUID)
├─ Initialize execution_context
├─ Load user preferences
├─ Set concurrent_task_count = 0
├─ Initialize realtime_cache (empty)
├─ Start session timer
└─ Return SessionInitResponse

POST /api/v1/session/cleanup
├─ Save session state for resume capability
├─ Log execution summary
├─ Clean temporary files
├─ Archive logs
├─ Update user metrics
├─ Free resources
└─ Return SessionCleanupResponse

Session Persistence:
├─ Save session state every 30 seconds
├─ On graceful shutdown: Save and cleanup
├─ On timeout: Auto-cleanup + archive
└─ Resume capability: User can continue from last checkpoint
*/
```

---

## SUMMARY TABLE

| Phase | Request Type | Response Type | Timeout | Max Retries |
|-------|--------------|---------------|---------|-------------|
| 1 | ContextInjectionRequest | ContextInjectionResponse | 100ms | 0 |
| 2 | IntentParserRequest | IntentParserResponse | 5s | unbounded* |
| 3 | PlannerRequest | PlannerResponse | 3s | 0 (ask user on cycle) |
| 4 | SkillRouterRequest | SkillRouterResponse | 1s | 0 |
| 5 | RealtimeFetchRequest | RealtimeFetchResponse | 10s | 2 |
| 6 | CoderRequest | CoderCheckResponse | varies | 3 rounds max |
| 7 | SkillRunnerRequest | SkillRunnerResponse | per-step | 0 (in runner) |
| 8 | ValidatorRequest | ValidatorResponse | 5s | 2 max |
| 9 | SynthesizerRequest | SynthesizerResponse | 3s | 0 |
| 10 | ErrorHandlerRequest | ErrorHandlerResponse | varies | 2 (T1) |

*Unbounded = Until user clarifies (5min timeout per clarification)

---

## IMPORTANT NOTES

✅ **All APIs enforce CRITICAL LIMITS:**
- Max validator retries: **2** (ENFORCED)
- Max planner iterations: **3** (ENFORCED)
- Max code review rounds: **3** (ENFORCED)
- Max concurrent tasks: **3** (ENFORCED)
- No Validator→Planner loop (uses SKILL_RUNNER instead)

✅ **All error paths are bounded** with timeouts and max attempts

✅ **All loop termination conditions are explicit**

✅ **All API responses include status and metadata for monitoring**

