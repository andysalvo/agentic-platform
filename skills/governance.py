"""
Skill: Governance-Aware Agent Development

Makes agents better at designing systems that preserve human authority
over AI-mediated decisions. Based on the human-intent-systems research
framework (Run 1 Constitution, Coupled Authority Phenomenon).

Provenance: human-intent-systems repository, Phase 1 research closure.
Author: Andy Salvo. Auditable origin.
"""

SKILL_CONTENT = """
# Governance-Aware Agent Development

## Purpose
This skill makes you better at designing agent systems that preserve human
authority over decisions. Use it when building any system where AI agents
act on behalf of humans.

## The Three Core Invariants

### 1. No Silent Inference
Never infer, merge, normalize, or reinterpret meaning-bearing input without
an explicit, reviewable, documented decision. If the user said X, store X.
Do not silently convert X to Y because Y seems equivalent.

**Test:** Can a reviewer see exactly what the user provided vs. what the
system interpreted? If not, this invariant is violated.

**Common violations:**
- Auto-correcting user input without logging the correction
- Merging duplicate records without explicit user approval
- Normalizing dates, names, or categories silently
- Inferring intent from partial input

### 2. Auditability at the Decision Level
Users and agents must be able to reconstruct why the system is in its
current state by inspecting the decision history. Not logs. Decisions.

**Test:** Starting from the decision log alone, can you replay the system
to its current state? If not, there are hidden state changes.

**Implementation pattern:**
- Append-only decision log as source of truth
- Every state change traced to an explicit decision
- No state changes from side effects, cron jobs, or implicit triggers
  without a corresponding decision record

### 3. Explicit Authority Transfer
All actions that create, modify, or dissolve commitments require an explicit
typed decision. Convenience or inferred intent are insufficient.

**Test:** For every commitment in the system, can you point to the explicit
decision that created it? If any commitment exists without a traceable
origin, authority has leaked.

**Common violations:**
- "Subscribe" buttons that also opt into marketing
- Default selections that create obligations
- Cascading deletes that dissolve commitments the user didn't address

## The Coupled Authority Phenomenon

Authority transfer in human-tool interaction cannot be safely localized to
either API design OR governance alone. Under realistic usage, authority
redistributes to whichever layer is weakest.

**What this means for you:**
- Good APIs with bad governance: users find ways to bypass controls
- Good governance with bad APIs: the API becomes the de facto authority
- Both must be maintained jointly or trust leaks

**Design implication:** When building agent systems, audit BOTH the API
surface (what actions are possible) AND the governance layer (what actions
are permitted). If they diverge, trust will erode through the gap.

## Forbidden Failure Modes

Your agent system must never:
1. Create obligations without explicit user authorization
2. Modify the meaning of stored user input
3. Auto-resolve ambiguity (represent it as unresolved instead)
4. Allow AI to directly modify authoritative state (AI proposes, human decides)
5. Silently change what a service does across versions
6. Make audit trails optional or degradable
7. Infer authority from convenience patterns

## Decision Architecture Pattern

```
User Input -> Explicit Decision -> Append-Only Log -> State Change
                  ^                      |
                  |                      v
              Human reviews         Deterministic replay
              if ambiguous          (same decisions = same state)
```

Every arrow in this diagram must be traceable. If any step is implicit,
the system has a governance gap.

## When to Apply This Skill

Use this when:
- Designing agent-to-human interaction flows
- Building systems where agents act on behalf of users
- Creating multi-agent systems with shared state
- Implementing any system that creates, modifies, or dissolves commitments
- Auditing existing systems for authority leaks

## Provenance

This skill is derived from the human-intent-systems research framework,
specifically the Run 1 Constitution and the Coupled Authority Phenomenon
finding. The research was conducted over multiple phases with explicit
methodology, phase advancement criteria, and edge case enumeration.
Framework author: Andy Salvo.
"""
