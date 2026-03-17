"""
Skill: Intent-Preserving System Architecture

Makes agents better at designing deterministic, auditable systems that
preserve user intent across time. Event-sourced, replay-safe, refusal-first.

Provenance: human-intent-systems research framework, Phase 1 closure.
9 system invariants, 14 forbidden failure modes, minimal embodiment tests.
Author: Andy Salvo.
"""

SKILL_CONTENT = """
# Intent-Preserving System Architecture

## Purpose
This skill makes you better at building systems where user intent is never
silently lost, mutated, or reinterpreted. Use it when designing any system
that stores user decisions, manages state over time, or acts on behalf of users.

## Core Architecture Pattern

### The Decision Log as Source of Truth
The system's authoritative state is NOT a database of current values.
It is an append-only log of decisions. Current state is derived by
replaying the log.

```
Decision Log (append-only, immutable):
  [1] User created project "Alpha" (2026-03-01T10:00:00Z)
  [2] User renamed project to "Alpha v2" (2026-03-01T14:30:00Z)
  [3] User added member "bot-agent-1" with role "reader" (2026-03-02T09:00:00Z)
  [4] User removed member "bot-agent-1" (2026-03-03T11:15:00Z)

Current State (derived, rebuildable):
  Project: "Alpha v2", Members: []

Invariant: replaying decisions 1-4 on an empty state MUST produce
the same current state. If it doesn't, the system has hidden state.
```

### Why This Matters
- **Debugging:** You can see exactly how the system reached any state
- **Trust recovery:** After a bug, replay from the last known-good decision
- **Auditability:** Every state change has a traceable human decision
- **No hidden state:** If it's not in the log, it didn't happen

## The Nine Invariants

### 1. Append-Only Decision Log
Decisions are never edited or deleted. Corrections are new decisions
that reference the original.

### 2. Frozen Decision Types
The schema of decision types does not drift. A "create_project" decision
in month 1 has the same fields as in month 12. Schema changes are
explicit versioned migrations, not silent field additions.

### 3. Deterministic Replay
Same decisions replayed on empty state always produce the same current
state. No randomness, no external lookups during replay, no time-dependent
logic in state derivation.

### 4. No Silent Inference
The system never infers user intent. If the input is ambiguous, the
system represents it as ambiguous rather than guessing.

### 5. Explicit Authority Transfer
Every commitment traces to an explicit decision. No commitments arise
from defaults, inferences, or side effects.

### 6. Stable Identity Over Time
Entities preserve their identity across versions. A renamed project is
the same project. A versioned API is the same API. Identity is not
silently forked.

### 7. AI as Proposal, Not Authority
AI may generate suggestions, drafts, and recommendations. It may never
directly modify the decision log. Human (or explicitly authorized agent)
approval is required for every state change.

### 8. Ambiguity as First-Class State
When something is unresolved, it is stored as unresolved. The system
does not auto-resolve to reduce complexity. Ambiguity is surfaced to
the user for explicit resolution.

### 9. Decision-Level Auditability
Any observer can reconstruct the full history of how the system reached
its current state by reading the decision log. No hidden channels,
no undocumented side effects.

## Forbidden Failure Modes

Your system must never:

1. **Silent merge:** Combine two records without a decision record
2. **Phantom state:** Have state not traceable to any decision
3. **Retroactive edit:** Modify a past decision to change history
4. **Inference-as-authority:** Treat AI output as a committed decision
5. **Schema drift:** Silently add fields to decision types
6. **Identity fork:** Create a new entity when the old one should be updated
7. **Implicit commitment:** Create obligations from defaults or inferences
8. **Ambiguity suppression:** Auto-resolve unclear input
9. **Audit gap:** Have any state transition with no corresponding log entry
10. **Side-effect state:** Let cron jobs or triggers change state without decisions
11. **Cascading authority:** Let one decision implicitly authorize others
12. **Version confusion:** Silently change what a versioned entity does
13. **Convenience override:** Let UX shortcuts bypass authority requirements
14. **Memory rot:** Let system state diverge from decision log over time

## Minimal Embodiment Tests

Before deploying any intent-preserving system, verify:

### Test 1: Replay Equivalence
1. Record all decisions from a test session
2. Reset state to empty
3. Replay all decisions
4. Compare final state to the original
5. They must be identical. Any difference = hidden state.

### Test 2: Decision Traceability
1. Pick any piece of current state
2. Trace it back to the decision(s) that created it
3. Every piece of state must trace to at least one decision
4. Any orphaned state = audit gap.

### Test 3: Ambiguity Preservation
1. Submit ambiguous input
2. Verify the system stores it as ambiguous
3. Verify the system prompts for clarification
4. Verify the system does NOT auto-resolve

### Test 4: AI Boundary
1. Have AI generate a recommendation
2. Verify the recommendation exists as a proposal, not a decision
3. Verify the decision log has no entry until a human approves
4. Verify rejecting the proposal has no side effects

## When to Apply This Skill

Use this when:
- Building any system that stores user-generated state
- Designing event-sourced or CQRS architectures
- Creating agent workflows with durable state
- Building multi-user systems where decisions must be traceable
- Auditing existing systems for hidden state or authority leaks
- Designing rollback/recovery mechanisms

## Implementation Quick Start

```python
# Minimal decision log pattern
import json
from datetime import datetime, timezone

class DecisionLog:
    def __init__(self, path):
        self.path = path
        self.decisions = []
        self._load()

    def record(self, decision_type: str, payload: dict, author: str):
        decision = {
            "id": len(self.decisions) + 1,
            "type": decision_type,
            "payload": payload,
            "author": author,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.decisions.append(decision)
        self._save()
        return decision

    def replay(self, reducer):
        state = {}
        for decision in self.decisions:
            state = reducer(state, decision)
        return state

    def _load(self):
        try:
            with open(self.path) as f:
                self.decisions = json.load(f)
        except FileNotFoundError:
            self.decisions = []

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.decisions, f, indent=2)
```

## Provenance

This skill is derived from the human-intent-systems research framework
(Phase 1 closure). The framework includes 9 system invariants, 14
explicitly enumerated forbidden failure modes, and 4 minimal embodiment
tests. Research conducted with explicit methodology, phase advancement
criteria, and edge case analysis. Framework author: Andy Salvo.
"""
