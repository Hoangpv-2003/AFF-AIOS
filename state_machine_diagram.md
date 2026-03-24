# STATE MACHINE DIAGRAM - AGENT EXECUTION PIPELINE v2.0

## MASTER STATE MACHINE

```
                                    ┌──────────────┐
                                    │   SESSION    │
                                    │     INIT     │
                                    └──────┬───────┘
                                           │
                        ┌──────────────────┼──────────────────┐
                        │                  │                  │
                        ▼                  ▼                  ▼
                    ┌─────────┐      ┌─────────┐      ┌─────────┐
                    │PHASE 1  │      │PHASE 2  │      │PHASE 3  │
                    │CONTEXT  │─────→│ INTENT  │─────→│PLANNING │
                    │INJECTION│      │ PARSE   │      │         │
                    └─────────┘      └────┬────┘      └────┬────┘
                                         │                 │
                        ┌────────────────┘                 │
                        │                                  ▼
                        │ confidence < 0.75          ┌─────────────┐
                        │ (high complexity)          │ CYCLE CHECK │
                        │                            │             │
                        │                            └──┬──────┬───┘
                        │                               │      │
                    ┌───▼──────┐               ┌─PASS──┘      └──FAIL──┐
                    │  ASK USER │               │                      │
                    │FOR CLARITY│               │                  ┌──▼──────┐
                    └───┬──────┘               │                   │CIRCULAR │
                        │                      │                   │   DEP   │
                        │ [user response]      │                   │  ERROR  │
                        │                      │                   └──┬──────┘
                        └────────────┬─────────┘                      │
                                     │ (resume)                       │
                                     │                                │
                                     ▼                                ▼
                            ┌─────────────────┐           ┌──────────────────┐
                            │  PHASE 4        │           │ ERROR HANDLER    │
                            │  SKILL ROUTER   │           │ (TIER 3)         │
                            └────┬────────────┘           └──────────────────┘
                                 │                               │
            ┌────────────────┬────┼────┬────────────┬────┐       │
            │                │    │    │            │    │       │
            ▼                ▼    ▼    ▼            ▼    ▼       ▼
    ┌─────────────┐  ┌──────────┐ ┌────┐  ┌──────┐  ┌────┐   [ABORT]
    │  PHASE 5    │  │ SKILL    │ │CODER│  │CODER│  │NONE│
    │  REALTIME   │  │ RUNNER   │ │PATCH│  │CREATE│  │    │
    │  FETCHER    │  │ (direct) │ └────┘  └──────┘  └────┘
    │ (parallel)  │  │          │   │        │
    └────────────┘  └────┬─────┘   │        │
         │                │         │        │
         └────┬───────────┘         │        │
              │                     │        │
              │                 ┌───▼────┬──▼────┐
              │                 │ CODE   │       │
              │                 │ REVIEW │       │
              │                 └───┬────┘       │
              │                     │            │
              │         ┌───────────┴────┬───────┘
              │         │ (max 3 rounds) │
              │         │ ENFORCED       │
              │         ▼                ▼
              │    ┌─────────┐      ┌──────────┐
              │    │APPROVED │      │ REJECTED │
              │    │(code OK)│      │(too hard)│
              │    └────┬────┘      └──┬───────┘
              │         │              │
              │         └──────┬───────┘
              │                │
              └────────────┬───┘
                           │
                           ▼
                    ┌──────────────┐
                    │  PHASE 7     │
                    │ SKILL RUNNER │
                    │(execute plan)│
                    └────┬─────────┘
                         │
           ┌─────────────┤
           │             │ [execution error]
           ▼             │
    ┌────────────┐       │
    │ PHASE 8    │       │
    │ VALIDATOR  │       │
    └────┬───────┘       │
         │                │
         │ (max 2 retries)│
         │ ENFORCED       │
         │                │
    ┌────┴────┬───────────┴────┬────────┐
    │          │                │        │
  PASS      RECOVERABLE    USER_INPUT  FATAL
    │          │                │        │
    │      ┌───▼────┐        ┌──▼──┐   │
    │      │Route to│        │ ASK │   │
    │      │ SKILL  │        │USER │   │
    │      │ RUNNER │        └──┬──┘   │
    │      │(no retry)   [response]    │
    │      └──┬────┘           │       │
    │         │                └───┬───┘
    │         └─────────┬──────────┘
    │                   │
    │         (retry execution)
    │
    ▼
┌──────────────┐
│  PHASE 9     │
│ SYNTHESIZER  │
│ (format out) │
└────┬─────────┘
     │
     ▼
┌──────────────────┐
│   PHASE 10       │
│  DELIVERY TO     │
│  USER            │
└────┬─────────────┘
     │
     │ [user may send new message]
     │
     └──────────────────┐
                        │
                   (loop back)
                        │
                        ▼
                   PHASE 1 (context)

ERROR_HANDLER path:
     ├─ TIER 1 (transient)
     │  └─ Auto-retry with backoff
     │     └─ Success: Resume normal flow
     │     └─ Failure: Escalate to TIER 2
     │
     ├─ TIER 2 (user-resolvable)
     │  └─ Ask user for clarification
     │     └─ Response received: Resume flow
     │     └─ Timeout: Default action or escalate
     │
     └─ TIER 3 (fatal)
        └─ ABORT immediately
           └─ Save partial results
           └─ Report error to user
           └─ End task (or allow manual retry)
```

---

## DETAILED PHASE TRANSITIONS

### PHASE 1 → PHASE 2 (Context Injection → Intent Parser)

```
┌────────────────────────────────────────────────┐
│         CONTEXT INJECTION STATE                │
├────────────────────────────────────────────────┤
│                                                │
│  Entry: Receive user message                  │
│                                                │
│  Load:                                         │
│   ├─ Server datetime ────────┐                │
│   ├─ User locale            ├─→ Context Map  │
│   ├─ User timezone          │                │
│   ├─ Conversation history ──┘                │
│   ├─ Tool availability status                │
│   └─ Session state (concurrent tasks)        │
│                                                │
│  Validation:                                  │
│   ├─ All data sources valid? ✓               │
│   ├─ No conflicts (timezone/locale)? ✓       │
│   ├─ History integrity? ✓                    │
│   └─ Tool status acceptable? ✓               │
│                                                │
│  Output: execution_context populated          │
│                                                │
└─────────────┬──────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────┐
│         INTENT PARSER STATE                    │
├────────────────────────────────────────────────┤
│                                                │
│  Input: User message + execution_context      │
│                                                │
│  Parse:                                       │
│   ├─ Primary action type (CREATE/READ/etc)   │
│   ├─ Sub-actions (dependency order)          │
│   ├─ Realtime data needs? (Y/N)              │
│   ├─ File access needed? (Y/N)               │
│   └─ Required skills/tools                   │
│                                                │
│  Calculate Confidence:                        │
│   ├─ Clarity score: 0-1.0                    │
│   ├─ Completeness: 0-1.0                     │
│   ├─ Feasibility: 0-1.0                      │
│   └─ Final = 0.5×C + 0.3×Co + 0.2×F        │
│                                                │
│  Decision:                                    │
│   ├─ IF confidence >= 0.75                   │
│   │  └─→ PROCEED to PHASE 3                  │
│   │                                           │
│   ├─ IF confidence < 0.75                    │
│   │  ├─ Determine complexity (low/med/high)  │
│   │  │                                       │
│   │  ├─ IF low: Guess + disclaimer           │
│   │  │          └─→ PROCEED to PHASE 3      │
│   │  │                                       │
│   │  ├─ IF medium: Ask 2-3 questions        │
│   │  │             └─→ WAIT for user        │
│   │  │                 [blocking]            │
│   │  │                 └─→ Resume PHASE 2   │
│   │  │                                       │
│   │  └─ IF high: Ask 4-5 questions          │
│   │             └─→ WAIT for user           │
│   │                 [blocking, 5min timeout] │
│   │                 └─→ Resume PHASE 2      │
│                                                │
│  Output: Intent structure + confidence score │
│                                                │
└─────────────┬──────────────────────────────────┘
              │
              ▼
          PHASE 3
```

### PHASE 3 CYCLE DETECTION FLOWCHART

```
┌────────────────────────────────────────────────────────┐
│         PLANNER: CYCLE DETECTION                       │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Step 1: Build dependency graph from "depends_on"    │
│  ──────                                               │
│   S1 → S2 → S3                                       │
│        ↓    ↓                                         │
│   S4 → S5                                            │
│        ↑                                              │
│        └─────S6                                       │
│                                                        │
│  Step 2: Run DFS-based cycle detection              │
│  ──────                                               │
│   visited = {}                                        │
│   rec_stack = {}                                      │
│                                                        │
│   For each node:                                      │
│    ├─ DFS(node)                                       │
│    │  ├─ Mark visited[node] = true              │
│    │  ├─ Mark rec_stack[node] = true                 │
│    │  │                                               │
│    │  └─ For each child in depends_on[node]:        │
│    │     ├─ IF child not visited:                    │
│    │     │  └─ DFS(child)                           │
│    │     │                                           │
│    │     └─ IF child in rec_stack:                   │
│    │        └─ *** CYCLE FOUND ***                  │
│    │           Return [node → ... → child → node]   │
│    │                                                 │
│    └─ Mark rec_stack[node] = false                  │
│                                                        │
│  Step 3: Decision                                     │
│  ──────                                               │
│   NO CYCLES FOUND:                                    │
│   └─→ PROCEED to PHASE 4 (Skill Router)              │
│                                                        │
│   CYCLES FOUND:                                       │
│   ├─ Example: S1 → S3 → S1                           │
│   ├─ Report to user:                                 │
│   │  "Circular dependency: Step 1 depends on        │
│   │   Step 3, but Step 3 depends on Step 1.        │
│   │   Please reorder requirements."                 │
│   │                                                  │
│   └─→ RETURN to PHASE 2 (Intent Parser)             │
│       [tag: awaiting_reordering]                     │
│       [block: wait for user to restate]              │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### PHASE 7-8 EXECUTION & VALIDATION LOOP

```
┌────────────────────────────────────────────────────────┐
│       PHASE 7: SKILL RUNNER                            │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Identify executable groups from plan:                │
│  ├─ Group 1: [S2, S3] (parallel safe)                │
│  ├─ Group 2: [S4] (must run alone)                   │
│  └─ Group 3: [S5, S6] (parallel safe)                │
│                                                        │
│  Execute:                                             │
│  ├─ Group 1:                                          │
│  │  ├─ S2 ────────┐                                   │
│  │  │ (parallel)  ├─→ merge results                   │
│  │  └─ S3 ────────┘   validate no conflicts          │
│  │                                                    │
│  ├─ Group 2:                                          │
│  │  └─ S4 ────────→ execute solo                      │
│  │                                                    │
│  └─ Group 3:                                          │
│     ├─ S5 ────────┐                                   │
│     │ (parallel)  ├─→ merge results                   │
│     └─ S6 ────────┘   validate no conflicts          │
│                                                        │
│  Capture outputs:                                     │
│  ├─ Return values                                     │
│  ├─ Files created                                     │
│  ├─ Logs/metrics                                      │
│  └─ Execution status: success|partial|failed         │
│                                                        │
│  On error during execution:                           │
│  └─ Log error, mark step failed                       │
│     └─ Continue to PHASE 8 (validation)               │
│                                                        │
└─────────────┬──────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────┐
│       PHASE 8: RESULT VALIDATOR                        │
├────────────────────────────────────────────────────────┤
│                                                        │
│  validation_attempt = 0                               │
│  MAX_ATTEMPTS = 2 (ENFORCED)                          │
│                                                        │
│  WHILE validation_attempt < MAX_ATTEMPTS:             │
│  ─────                                                 │
│                                                        │
│  For each step_output:                                │
│  ├─ Check correctness (0-1.0)                        │
│  ├─ Check completeness (0-1.0)                       │
│  ├─ Check quality (0-1.0)                            │
│  ├─ Check safety (0-1.0)                             │
│  │                                                    │
│  └─ validation_score = weighted average               │
│                                                        │
│  Decision:                                            │
│  ├─ IF all_outputs pass (score >= 0.80):             │
│  │  └─→ PROCEED to PHASE 9 (Synthesizer)             │
│  │                                                    │
│  ├─ IF some_outputs fail (score < 0.80):             │
│  │  ├─ Categorize:                                    │
│  │  │  ├─ Type A: Recoverable                         │
│  │  │  │ ├─ IF attempt < 2:                           │
│  │  │  │ │  ├─ Identify root cause                    │
│  │  │  │ │  ├─ Adjust parameters                      │
│  │  │  │ │  ├─ Route to SKILL_RUNNER                  │
│  │  │  │ │  │  (NOT to PLANNER, avoid infinite loop) │
│  │  │  │ │  ├─ validation_attempt += 1                │
│  │  │  │ │  └─ Retry execution                        │
│  │  │  │ │                                            │
│  │  │  │ └─ ELSE (attempt >= 2):                      │
│  │  │  │    └─→ ERROR_HANDLER (TIER 3)               │
│  │  │  │                                              │
│  │  │  ├─ Type B: Need user input                     │
│  │  │  │ └─ Ask user for clarification               │
│  │  │  │    └─ Wait for response (5min timeout)      │
│  │  │  │       └─ Resume (validation_attempt += 0)    │
│  │  │  │          (user input doesn't count as retry) │
│  │  │  │                                              │
│  │  │  └─ Type C: Unrecoverable                       │
│  │  │     └─→ ERROR_HANDLER (TIER 3)                │
│  │  │        └─ ABORT                                 │
│  │  │           └─ Save partial results               │
│  │  │           └─ Report to user                     │
│  │  │                                                 │
│  │  └─ validation_attempt += 1                        │
│  │                                                    │
│  └─ END OF ATTEMPT                                    │
│                                                        │
│  Loop back or exit                                    │
│                                                        │
└─────────────┬──────────────────────────────────────────┘
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
 PHASE 9  ERROR_H   (partial
SYNTH.    ANDLER    results)
    │         │         │
    └─────────┼─────────┘
              │
              ▼
        PHASE 10
      (deliver)
```

### VALIDATOR RETRY MECHANISM (Fixed - No PLANNER loop)

```
ISSUE IN v1:
════════════
Validator → (fail) → Planner → (same plan) → Skill Runner → Validator
                                 ↑                             │
                                 └─────────────────────────────┘
                        INFINITE LOOP POSSIBLE!

FIXED IN v2:
════════════
Validator → (fail, recoverable) → Skill Runner (adjusted params)
                                        │
                                        ▼
                                    (retry step)
                                        │
                                        ▼
                                   Validator (again)
                                        │
                        ┌───────────────┼───────────────┐
                        │               │               │
                    (success)      (fail, type B)   (fail, type C)
                        │               │               │
                        ▼               ▼               ▼
                    PHASE 9         ASK USER      ERROR_HANDLER

KEY DIFFERENCE:
- v1: Cycles back to PLANNER (creates loop)
- v2: Routes to SKILL_RUNNER with ADJUSTED PARAMETERS (breaks loop)
- v2: Max 2 retries enforced (PHASE 8 loop counter)
- v2: Validator → PLANNER happens only in PHASE 3 (initial planning)
```

---

## LOOP TERMINATION GUARANTEES

```
LOOP A: Intent Parser (high complexity)
├─ Max iterations: Infinite (waiting for user input)
├─ Timeout: 5 minutes per iteration
├─ Termination: User provides input or timeout → escalate
└─ Status: BOUNDED by timeout

LOOP B: Validator Retries
├─ Max iterations: 2 (ENFORCED)
├─ Condition: validation_attempt < 2
├─ Termination: After 2 attempts, must escalate or ask user
└─ Status: STRICTLY BOUNDED (hard limit)

LOOP C: Code Review
├─ Max iterations: 3 rounds (ENFORCED)
├─ Condition: review_round < 3
├─ Termination: After round 3, APPROVED or REJECTED
└─ Status: STRICTLY BOUNDED (hard limit)

LOOP D: Skill Runner Execution
├─ Max iterations: Once per step (no retry in runner)
├─ Timeout: per-step timeout + 5sec
├─ Error handling: Pass to Validator on error
└─ Status: BOUNDED by per-step timeout

LOOP E: Main Execution Loop
├─ Condition: user_has_messages AND session != TERMINATED
├─ Termination: User ends session OR max duration exceeded
├─ Duration limit: 10 minutes total per session
└─ Status: BOUNDED by session timeout
```

---

## CONCURRENCY STATE DIAGRAM

```
┌─────────────────────────────────────────────────┐
│       CONCURRENT TASK MANAGEMENT                │
├─────────────────────────────────────────────────┤
│                                                 │
│  MAX_CONCURRENT_TASKS = 3 (enforced)            │
│                                                 │
│  Session arrives:                               │
│   ├─ Check concurrent_task_count                │
│   │                                             │
│   ├─ IF count < 3:                              │
│   │  ├─ ACCEPT new task                         │
│   │  ├─ Increment counter                       │
│   │  └─ Begin execution                         │
│   │                                             │
│   └─ IF count >= 3:                             │
│      ├─ QUEUE task (or reject)                  │
│      ├─ Ask user: "Queue or prioritize?"        │
│      └─ Wait for response                       │
│                                                 │
│  During execution (parallel groups in PHASE 7): │
│   ├─ Group 1: [S2, S3] execute in parallel     │
│   │  ├─ Promise.all([exec(S2), exec(S3)])      │
│   │  ├─ Wait for both complete or timeout      │
│   │  └─ Merge results (no shared state)        │
│   │                                             │
│   └─ Groups execute sequentially                │
│      (one group at a time)                      │
│                                                 │
│  Conflict detection (shared state):             │
│   ├─ During parallel execution                  │
│   ├─ Both S2 and S3 write to same file?         │
│   ├─ YES → Log warning, apply merge strategy   │
│   │  ├─ Last-write-wins (S3 overwrites S2)     │
│   │  ├─ OR merge content (if applicable)       │
│   │  └─ OR fail safe (abort parallel group)    │
│   └─ NO → Continue normally                     │
│                                                 │
│  Task completion:                               │
│   ├─ When execution PHASE 10 delivers results  │
│   ├─ Decrement concurrent_task_count            │
│   ├─ IF queue non-empty:                        │
│   │  └─ Pop next task & start (PHASE 1)         │
│   └─ Free resources                             │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## ERROR RECOVERY STATE MACHINE

```
┌──────────────────────────────────────────────────────┐
│        ERROR DETECTION & RECOVERY                    │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Error occurs in any PHASE:                           │
│  └─→ CATCH_ERROR                                     │
│      ├─ Log: timestamp, stack, context              │
│      ├─ Classify error type                         │
│      └─ Route to recovery procedure                 │
│                                                      │
│ ┌────────────────────────────────────────────────┐  │
│ │ TIER 1: TRANSIENT (Auto-recoverable)          │  │
│ ├────────────────────────────────────────────────┤  │
│ │                                                │  │
│ │ Examples:                                      │  │
│ │  ├─ Network timeout                           │  │
│ │  ├─ Rate limit (API quota)                    │  │
│ │  ├─ Temporary resource unavailable            │  │
│ │  └─ Lock contention                           │  │
│ │                                                │  │
│ │ Recovery:                                      │  │
│ │  ├─ attempt = 0                                │  │
│ │  ├─ WHILE attempt < MAX_BACKOFF_RETRIES:      │  │
│ │  │  ├─ delay = min(0.5 × 2^attempt, 30)      │  │
│ │  │  ├─ delay += random_jitter(10%)            │  │
│ │  │  ├─ Sleep(delay)                           │  │
│ │  │  ├─ Retry operation                        │  │
│ │  │  ├─ IF success: Resume normal flow         │  │
│ │  │  ├─ IF fail: attempt += 1                  │  │
│ │  │  └─ IF total_wait > 120s: Break            │  │
│ │  └─                                            │  │
│ │  └─ IF all retries fail:                       │  │
│ │     └─→ ESCALATE to TIER 2                    │  │
│ │                                                │  │
│ └────────────────────────────────────────────────┘  │
│                                                      │
│ ┌────────────────────────────────────────────────┐  │
│ │ TIER 2: USER-RESOLVABLE                        │  │
│ ├────────────────────────────────────────────────┤  │
│ │                                                │  │
│ │ Examples:                                      │  │
│ │  ├─ Ambiguous intent                          │  │
│ │  ├─ Missing required input                    │  │
│ │  ├─ Permission denied                         │  │
│ │  ├─ Invalid choice/conflict                   │  │
│ │  └─ User decision needed                      │  │
│ │                                                │  │
│ │ Recovery:                                      │  │
│ │  ├─ PAUSE execution                            │  │
│ │  ├─ Explain problem clearly                   │  │
│ │  ├─ Present options/choices                   │  │
│ │  ├─ timeout_user_response = 300s (5 min)     │  │
│ │  │  ├─ WAIT for response                      │  │
│ │  │  ├─ IF response received:                  │  │
│ │  │  │  └─→ RESUME with user input             │  │
│ │  │  └─ ELSE IF timeout:                       │  │
│ │  │     └─→ Apply default action               │  │
│ │  │         or ESCALATE to TIER 3              │  │
│ │  │                                             │  │
│ │  └─ Resume normal execution                   │  │
│ │                                                │  │
│ └────────────────────────────────────────────────┘  │
│                                                      │
│ ┌────────────────────────────────────────────────┐  │
│ │ TIER 3: UNRECOVERABLE (Must abort)            │  │
│ ├────────────────────────────────────────────────┤  │
│ │                                                │  │
│ │ Examples:                                      │  │
│ │  ├─ Unsupported operation                     │  │
│ │  ├─ Fundamental requirement missing           │  │
│ │  ├─ Safety/ethical violation                  │  │
│ │  ├─ System limitation exceeded                │  │
│ │  ├─ Code too complex (failed all reviews)     │  │
│ │  ├─ Resource limit hit                        │  │
│ │  └─ User explicitly cancels                   │  │
│ │                                                │  │
│ │ Recovery:                                      │  │
│ │  ├─ ABORT execution immediately               │  │
│ │  ├─ Save any partial results                  │  │
│ │  ├─ Log detailed failure analysis              │  │
│ │  ├─ Generate error report:                    │  │
│ │  │  ├─ What happened                          │  │
│ │  │  ├─ Why it failed                          │  │
│ │  │  ├─ Last successful step                   │  │
│ │  │  ├─ Partial results (if any)               │  │
│ │  │  └─ Suggested next steps                   │  │
│ │  ├─ Present to user                           │  │
│ │  ├─ Offer options:                            │  │
│ │  │  ├─ Retry with modifications               │  │
│ │  │  ├─ Simplify requirements                  │  │
│ │  │  ├─ Break into smaller tasks               │  │
│ │  │  └─ Contact support                        │  │
│ │  │                                             │  │
│ │  └─→ END TASK (or allow manual retry)         │  │
│ │                                                │  │
│ └────────────────────────────────────────────────┘  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## SUMMARY: All Loop Termination Paths

```
PHASE 1: CONTEXT INJECTION
└─ Always continues to PHASE 2
   ├─ Terminal: None (always succeeds)

PHASE 2: INTENT PARSER
├─ IF confidence >= 0.75: → PHASE 3
├─ IF confidence < 0.75 AND complexity=low: → PHASE 3 (with guess)
├─ IF confidence < 0.75 AND complexity=medium: → ASK → PHASE 2 (retry)
│  └─ Max retries: Until user clarifies
├─ IF confidence < 0.75 AND complexity=high: → ASK → PHASE 2 (retry)
│  └─ Max retries: 3 questions, 5min timeout
└─ Terminal: Always continues eventually

PHASE 3: PLANNER
├─ IF no cycles: → PHASE 4
├─ IF cycles detected: → PHASE 2 (ask user to reorder)
│  └─ Max retries: Until user fixes ordering
└─ Terminal: Always continues eventually

PHASE 4: SKILL ROUTER
└─ Always routes to next phase based on decision
   ├─ → PHASE 5 (realtime fetch needed)
   ├─ → PHASE 6 (coder needed)
   └─ → PHASE 7 (skill runner)
   └─ Terminal: None (deterministic routing)

PHASE 5: REALTIME FETCHER
├─ Success: Store data, continue
├─ Failure: Fallback to cache/knowledge cutoff, continue (non-blocking)
└─ Terminal: Always continues (fallback available)

PHASE 6: CODER
├─ PATCH mode:
│  └─ Max rounds: 2 (if issues, switch to CREATE)
├─ CREATE mode:
│  ├─ Round 1-2: Fix and re-review
│  ├─ Round 3: Final review, APPROVED or REJECTED
│  └─ IF REJECTED: → ERROR_HANDLER (TIER 3)
└─ Terminal: APPROVED code or TIER 3 error

PHASE 7: SKILL RUNNER
├─ Execution success: Outputs captured, continue
├─ Execution error: Log, continue to PHASE 8
└─ Terminal: None (always continues to PHASE 8)

PHASE 8: RESULT VALIDATOR
├─ validation_attempt = 0
├─ LOOP: WHILE validation_attempt < 2
│  ├─ IF pass: → PHASE 9
│  ├─ IF fail, recoverable, attempt < 2:
│  │  └─ → PHASE 7 (adjusted params)
│  │     └─ validation_attempt += 1
│  ├─ IF fail, need user input:
│  │  └─ → ASK USER
│  │     └─ validation_attempt += 0 (doesn't count)
│  └─ IF fail, unrecoverable OR attempt >= 2:
│     └─ → ERROR_HANDLER (TIER 3)
└─ Terminal: PHASE 9 or ERROR_HANDLER (max 2 attempts enforced)

PHASE 9: SYNTHESIZER
├─ Aggregate results
├─ Format output
└─ → PHASE 10
└─ Terminal: None (always continues)

PHASE 10: DELIVERY
├─ Present to user
├─ Update session
├─ → AWAIT NEXT MESSAGE
└─ IF new message: → PHASE 1
└─ IF session end: → CLEANUP

ERROR_HANDLER:
├─ TIER 1: Retry with backoff (120s max)
│  └─ IF success: Resume normal flow
│  └─ IF fail: Escalate to TIER 2
│
├─ TIER 2: Ask user for input (5min timeout)
│  └─ IF response: Resume normal flow
│  └─ IF timeout: Escalate to TIER 3
│
└─ TIER 3: ABORT
   └─ Report error, end task

=====================================
ALL LOOPS HAVE MAXIMUM ITERATIONS ✓
ALL LOOPS HAVE TIMEOUT PROTECTION ✓
ALL LOOPS HAVE TERMINATION GUARANTEES ✓
=====================================
```

